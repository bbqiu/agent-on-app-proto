from operator import itemgetter
from typing import AsyncGenerator

import mlflow
from databricks_langchain import ChatDatabricks
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableLambda
from mlflow.langchain.output_parsers import ChatCompletionOutputParser

from agent_server.mlflow_config import setup_mlflow
from agent_server.server import create_server, invoke, stream

# Enable MLflow tracing
mlflow.langchain.autolog()

llm = ChatDatabricks(model="databricks-claude-sonnet-4")

# Define components
prompt = ChatPromptTemplate.from_template(
    """Previous conversation:
{chat_history}

User's question:
{question}"""
)

# Chain definition
chain = (
    {
        "question": itemgetter("messages")
        | RunnableLambda(lambda messages: messages[-1]["content"]),
        "chat_history": itemgetter("messages") | RunnableLambda(lambda messages: messages[:-1]),
    }
    | prompt
    | llm
    | ChatCompletionOutputParser()
)


# Example for ResponsesAgent
@invoke()
async def invoke(messages: list[BaseMessage]) -> BaseMessage:
    """Responses agent predict function - expects inputs format."""
    return await chain.ainvoke(messages)


@stream()
async def stream(
    messages: list[BaseMessage],
) -> AsyncGenerator[BaseMessage, None]:
    async for chunk in chain.astream(messages):
        yield chunk


def main():
    server = create_server()
    setup_mlflow()
    print("Single endpoint: POST /invocations")

    server.run()


if __name__ == "__main__":
    main()
