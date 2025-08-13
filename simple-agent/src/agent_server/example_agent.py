import asyncio
import subprocess
from typing import AsyncGenerator

import mlflow
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)

from agent_server.server import create_server, predict, predict_stream

mlflow.set_tracking_uri("databricks")
mlflow.set_experiment("/Users/bryan.qiu@databricks.com/bbqiu-agent-proto1")

# Define your application and its version identifier
app_name = "bbqiu-agent-proto1"

# Get current git commit hash for versioning
try:
    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()[:8]
    version_identifier = f"git-{git_commit}"
except subprocess.CalledProcessError:
    version_identifier = "local-dev"  # Fallback if not in a git repo
logged_model_name = f"{app_name}-{version_identifier}"

# Set the active model context
active_model_info = mlflow.set_active_model(name=logged_model_name)
print(f"Active LoggedModel: '{active_model_info.name}', Model ID: '{active_model_info.model_id}'")


# Example for ResponsesAgent
@predict()
async def invoke(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    """Responses agent predict function - expects inputs format."""
    return {
        "id": "id",
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "id": "id",
                "content": [{"type": "output_text", "text": "Hello, world!"}],
            },
        ],
    }


@predict_stream()
async def stream(request: ResponsesAgentRequest) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    yield {
        "type": "response.output_item.done",
        "item": {
            "type": "message",
            "role": "assistant",
            "id": "id",
            "content": [{"type": "output_text", "text": "Hello, world!"}],
        },
    }
    await asyncio.sleep(0.5)

    yield {
        "type": "response.output_item.done",
        "item": {
            "type": "message",
            "role": "assistant",
            "id": "id",
            "content": [{"type": "output_text", "text": "Hello again!"}],
        },
    }


def main():
    server = create_server("agent/v1/responses")
    print("Single endpoint: POST /invocations")

    server.run()


if __name__ == "__main__":
    main()
