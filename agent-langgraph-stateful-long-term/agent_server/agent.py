import json
import logging
import os
from typing import AsyncGenerator, Optional

import mlflow
from databricks.sdk import WorkspaceClient
from databricks_langchain import (
    ChatDatabricks,
    DatabricksMCPServer,
    DatabricksMultiServerMCPClient,
    DatabricksStore,
)
from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
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
sp_workspace_client = WorkspaceClient()


############################################
# Define your LLM endpoint and system prompt
############################################
LLM_ENDPOINT_NAME = "databricks-claude-sonnet-4-5"
SYSTEM_PROMPT = """You are a helpful assistant. Use the available tools to answer questions.

You have access to memory tools that allow you to remember information about users:
- Use get_user_memory to search for previously saved information about the user
- Use save_user_memory to remember important facts, preferences, or details the user shares
- Use delete_user_memory to forget specific information when asked

Always check for relevant memories at the start of a conversation to provide personalized responses."""

############################################
# Lakebase configuration for long-term memory
############################################
LAKEBASE_INSTANCE_NAME = os.getenv("LAKEBASE_INSTANCE_NAME", "lakebase")

# Embedding configuration for semantic memory search
EMBEDDING_ENDPOINT = "databricks-gte-large-en"
EMBEDDING_DIMS = 1024


#####################
# DatabricksStore for long-term memory
#####################

_store: Optional[DatabricksStore] = None


def get_store() -> DatabricksStore:
    """Get or initialize the DatabricksStore for long-term memory."""
    global _store
    if _store is None:
        logger.info(
            f"Initializing DatabricksStore with instance: {LAKEBASE_INSTANCE_NAME} "
            f"and embedding endpoint {EMBEDDING_ENDPOINT} with dims {EMBEDDING_DIMS}"
        )
        _store = DatabricksStore(
            instance_name=LAKEBASE_INSTANCE_NAME,
            embedding_endpoint=EMBEDDING_ENDPOINT,
            embedding_dims=EMBEDDING_DIMS,
        )
        _store.setup()
    return _store


#####################
# Memory tools
#####################


def create_memory_tools():
    """Create tools for reading and writing long-term user memory."""

    @tool
    def get_user_memory(query: str, config: RunnableConfig) -> str:
        """Search for relevant information about the user from long-term memory using semantic search.

        Use this tool to retrieve previously saved information about the user,
        such as their preferences, facts they've shared, or other personal details.

        Args:
            query: A search query describing what information you're looking for
        """
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            return "Memory not available - no user_id provided."

        namespace = ("user_memories", user_id.replace(".", "-"))
        store = get_store()
        results = store.search(namespace, query=query, limit=5)

        if not results:
            return "No memories found for this user."

        memory_items = []
        for item in results:
            memory_items.append(f"- [{item.key}]: {json.dumps(item.value)}")

        return f"Found {len(results)} relevant memories (ranked by semantic similarity):\n" + "\n".join(memory_items)

    @tool
    def save_user_memory(memory_key: str, memory_data_json: str, config: RunnableConfig) -> str:
        """Save information about the user to long-term memory with vector embeddings.

        Use this tool to remember important information the user shares about themselves,
        such as preferences, facts, or other personal details.

        Args:
            memory_key: A descriptive key for this memory (e.g., "preferences", "favorite_color", "location")
            memory_data_json: JSON string with the information to remember.
                Example: '{"favorite_color": "purple"}'
        """
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            return "Cannot save memory - no user_id provided."

        namespace = ("user_memories", user_id.replace(".", "-"))
        store = get_store()

        try:
            memory_data = json.loads(memory_data_json)
            if not isinstance(memory_data, dict):
                return f"Failed to save memory: memory_data must be a JSON object (dictionary), not {type(memory_data).__name__}"
            store.put(namespace, memory_key, memory_data)
            return f"Successfully saved memory with key '{memory_key}' for user."
        except json.JSONDecodeError as e:
            return f"Failed to save memory: Invalid JSON format - {str(e)}"

    @tool
    def delete_user_memory(memory_key: str, config: RunnableConfig) -> str:
        """Delete a specific memory from the user's long-term memory.

        Use this tool when the user asks you to forget something or remove
        a piece of information from their memory.

        Args:
            memory_key: The key of the memory to delete (e.g., "preferences", "location")
        """
        user_id = config.get("configurable", {}).get("user_id")
        if not user_id:
            return "Cannot delete memory - no user_id provided."

        namespace = ("user_memories", user_id.replace(".", "-"))
        store = get_store()
        store.delete(namespace, memory_key)
        return f"Successfully deleted memory with key '{memory_key}' for user."

    return [get_user_memory, save_user_memory, delete_user_memory]


# Initialize memory tools
MEMORY_TOOLS = create_memory_tools()


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


async def init_agent(workspace_client: Optional[WorkspaceClient] = None):
    """Initialize the agent with MCP tools and memory tools."""
    mcp_client = init_mcp_client(workspace_client or sp_workspace_client)
    mcp_tools = await mcp_client.get_tools()
    
    # Combine MCP tools with memory tools
    all_tools = list(mcp_tools) + MEMORY_TOOLS
    
    return create_agent(
        tools=all_tools,
        model=ChatDatabricks(endpoint=LLM_ENDPOINT_NAME),
    )


#####################
# User ID management
#####################


def _get_user_id(request: ResponsesAgentRequest) -> Optional[str]:
    """Get user_id from request context or custom_inputs.
    
    Priority:
    1. user_id from custom_inputs
    2. user_id from chat context
    """
    ci = dict(request.custom_inputs or {})
    
    if "user_id" in ci:
        return ci["user_id"]
    
    if request.context and getattr(request.context, "user_id", None):
        return request.context.user_id
    
    return None


#####################
# Invoke and Stream handlers
#####################


@invoke()
async def non_streaming(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    """Handle non-streaming invocation by collecting all stream events."""
    user_id = _get_user_id(request)
    
    if not user_id:
        logger.warning("No user_id provided - memory features will not be available")
    
    ci = dict(request.custom_inputs or {})
    if user_id:
        ci["user_id"] = user_id
    request.custom_inputs = ci
    
    outputs = [
        event.item
        async for event in streaming(request)
        if event.type == "response.output_item.done"
    ]
    
    custom_outputs = {}
    if user_id:
        custom_outputs["user_id"] = user_id
    
    return ResponsesAgentResponse(output=outputs, custom_outputs=custom_outputs if custom_outputs else None)


@stream()
async def streaming(
    request: ResponsesAgentRequest,
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    """Handle streaming invocation with long-term memory support.
    
    Features:
    - User-based long-term memory stored in DatabricksStore
    - Semantic search for memory retrieval
    - Memory tools for save/get/delete operations
    
    Usage via API:
        # With user_id in custom_inputs
        curl -X POST http://localhost:8000/invocations \\
            -H "Content-Type: application/json" \\
            -d '{
                "input": [{"role": "user", "content": "I live in San Francisco"}],
                "custom_inputs": {"user_id": "jenny@example.com"}
            }'
    """    
    user_id = _get_user_id(request)
    
    if not user_id:
        logger.warning("No user_id provided - memory features will not be available")
    else:
        logger.info(f"Starting message stream with user_id: {user_id}")
    
    agent = await init_agent()
    
    # Prepend system prompt to messages
    input_messages = to_chat_completions_input([i.model_dump() for i in request.input])
    messages_with_system = [{"role": "system", "content": SYSTEM_PROMPT}] + input_messages
    messages = {"messages": messages_with_system}
    
    config = {"configurable": {}}
    if user_id:
        config["configurable"]["user_id"] = user_id

    async for event in process_agent_astream_events(
        agent.astream(input=messages, config=config, stream_mode=["updates", "messages"])
    ):
        yield event
