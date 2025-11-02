import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from mlflow.genai.agent_server import AgentServer, parse_server_args, setup_mlflow

# Load environment variables from .env.local if it exists
load_dotenv(dotenv_path=".env.local", override=True)

# Need to import the agent to register the functions with the server
# Set the env vars before importing the agent for proper auth
import agent_server.agent  # noqa: E402

agent_server = AgentServer("agent/v1/responses")
# Define the app as a module level variable to enable multiple workers
app = agent_server.app  # noqa: F841

ui_dist_path = Path(os.getenv("MLFLOW_AGENT_SERVER_UI_PATH")).resolve()
if ui_dist_path.exists():
    app.mount("/assets", StaticFiles(directory=str(ui_dist_path / "assets")), name="assets")

    from fastapi.responses import FileResponse

    @app.get("/")
    async def serve_ui():
        return FileResponse(str(ui_dist_path / "index.html"))
else:
    print(f"UI dist folder not found at {ui_dist_path}. UI will not be served.")

args = parse_server_args()

setup_mlflow()
print(f"Running server on port {args.port} with {args.workers} workers and reload: {args.reload}")


def main():
    # to support multiple workers, import the app defined above as a string
    agent_server.run(
        app_import_string="agent_server.start_server:app",
        port=args.port,
        workers=args.workers,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
