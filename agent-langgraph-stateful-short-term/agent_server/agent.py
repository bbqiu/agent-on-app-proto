import logging
import os
import uuid
from typing import Annotated, Any, AsyncGenerator, Optional, Sequence, TypedDict

import mlflow
from databricks.sdk import WorkspaceClient
from databricks_langchain import (
    AsyncCheckpointSaver,
    ChatDatabricks,
    DatabricksMCPServer,
    DatabricksMultiServerMCPClient,
)
from langchain_core.messages import AIMessage, AnyMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt.tool_node import ToolNode
from mlflow.genai.agent_server import invoke, stream
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    to_chat_completions_input,
)

from agent_server.utils import (
    get_databricks_host_from_env,
    get_user_workspace_client,
    process_agent_astream_events,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

mlflow.langchain.autolog()


############################################
# Define your LLM endpoint and system prompt
############################################
LLM_ENDPOINT_NAME = "databricks-claude-sonnet-4-5"
SYSTEM_PROMPT = """You are a helpful assistant. Use the available tools to answer questions."""

############################################
# Lakebase configuration for statefulness
############################################
LAKEBASE_INSTANCE_NAME = os.getenv("LAKEBASE_INSTANCE_NAME", "")

_checkpoint_setup_done = False


#####################
# Define agent state
#####################


class AgentState(TypedDict):
    """State for the agent graph."""
    messages: Annotated[Sequence[AnyMessage], add_messages]
    custom_inputs: Optional[dict[str, Any]]
    custom_outputs: Optional[dict[str, Any]]


#####################
# MCP Client and Agent initialization
#####################


def init_mcp_client(workspace_client: WorkspaceClient) -> DatabricksMultiServerMCPClient:
    host_name = get_databricks_host_from_env()
    return DatabricksMultiServerMCPClient(
        [
            DatabricksMCPServer(
                name="system-ai",
                url=f"{host_name}/api/2.0/mcp/functions/system/ai",
            ),
        ]
    )


async def init_agent(
    workspace_client: Optional[WorkspaceClient] = None,
    checkpointer: Optional[Any] = None,
):
    """Initialize the agent with MCP tools and optional checkpointing for statefulness."""
    mcp_client = init_mcp_client(workspace_client or get_user_workspace_client)
    tools = await mcp_client.get_tools()
    
    model = ChatDatabricks(endpoint=LLM_ENDPOINT_NAME)
    model_with_tools = model.bind_tools(tools) if tools else model

    def should_continue(state: AgentState):
        """Determine if the agent should continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "continue"
        return "end"

    preprocessor = RunnableLambda(
        lambda state: [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
    )
    model_runnable = preprocessor | model_with_tools

    async def call_model(state: AgentState, config: RunnableConfig):
        """Call the model with the current state asynchronously."""
        response = await model_runnable.ainvoke(state, config)
        return {"messages": [response]}

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)

    if tools:
        workflow.add_node("tools", ToolNode(tools))
        workflow.add_conditional_edges(
            "agent", should_continue, {"continue": "tools", "end": END}
        )
        workflow.add_edge("tools", "agent")
    else:
        workflow.add_edge("agent", END)

    workflow.set_entry_point("agent")
    return workflow.compile(checkpointer=checkpointer)


#####################
# Checkpoint setup
#####################


async def _ensure_checkpoint_tables_setup():
    """Initialize Lakebase checkpoint tables on first use."""
    global _checkpoint_setup_done
    
    if _checkpoint_setup_done:
        return
    
    try:
        logger.info(f"Setting up checkpoint tables for Lakebase instance: {LAKEBASE_INSTANCE_NAME}")
        async with AsyncCheckpointSaver(instance_name=LAKEBASE_INSTANCE_NAME) as saver:
            await saver.setup()
        logger.info("✅ Checkpoint tables are ready.")
    except Exception as e:
        logger.warning(
            f"Could not setup checkpoint tables for instance '{LAKEBASE_INSTANCE_NAME}': {e}. "
            "Please verify the lakebase instance exists and you have proper permissions to create tables."
        )
    finally:
        _checkpoint_setup_done = True


#####################
# Thread ID management
#####################


def _get_or_create_thread_id(request: ResponsesAgentRequest) -> str:
    """Get thread_id from request or create a new one."""
    ci = dict(request.custom_inputs or {})

    if "thread_id" in ci:
        logger.info(f"Using thread_id from custom_inputs: {ci['thread_id']}")
        return ci["thread_id"]

    if request.context and getattr(request.context, "conversation_id", None):
        logger.info(f"Using conversation_id from context: {request.context.conversation_id}")
        return request.context.conversation_id

    new_thread_id = str(uuid.uuid4())
    logger.info(f"Generated new thread_id: {new_thread_id}")
    return new_thread_id


@invoke()
async def non_streaming(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    thread_id = _get_or_create_thread_id(request)
    request.custom_inputs = dict(request.custom_inputs or {})
    request.custom_inputs["thread_id"] = thread_id
    
    outputs = [
        event.item
        async for event in streaming(request)
        if event.type == "response.output_item.done"
    ]
    return ResponsesAgentResponse(output=outputs, custom_outputs={"thread_id": thread_id})


@stream()
async def streaming(
    request: ResponsesAgentRequest,
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    thread_id = _get_or_create_thread_id(request)
    checkpoint_config = {"configurable": {"thread_id": thread_id}}
    
    logger.info(f"Starting async message stream with thread_id: {thread_id}")
    
    messages = {"messages": to_chat_completions_input([i.model_dump() for i in request.input])}

    try:
        await _ensure_checkpoint_tables_setup()
        
        async with AsyncCheckpointSaver(instance_name=LAKEBASE_INSTANCE_NAME) as checkpointer:
            agent = await init_agent(checkpointer=checkpointer)
            
            async for event in process_agent_astream_events(
                agent.astream(
                    messages,
                    checkpoint_config,
                    stream_mode=["updates", "messages"],
                )
            ):
                yield event
        
        logger.info(f"Finished async message stream! thread_id: {thread_id}")
    except Exception as e:
        logger.exception(f"Error in streaming for thread_id {thread_id}: {e}")
        raise
