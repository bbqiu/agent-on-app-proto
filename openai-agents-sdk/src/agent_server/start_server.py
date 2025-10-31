import os

from dotenv import load_dotenv

# Load environment variables from .env.local if it exists
load_dotenv(dotenv_path=".env.local", override=True)
from mlflow.pyfunc.agent_server import AgentServer, parse_server_args, setup_mlflow

print(os.getenv("MLFLOW_AGENT_SERVER_UI_PATH"))
print(os.getenv("DATABRICKS_HOST"))
print(os.getenv("DATABRICKS_TOKEN"))
print(os.getenv("MLFLOW_EXPERIMENT_ID"))

# need to import the agent to register the functions with the server
# set the env vars before
import agent_server.agent  # noqa: F401

agent_server = AgentServer("agent/v1/responses")
# define the app as a module level variable to enable multiple workers
app = agent_server.app  # noqa: F841

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
