from dotenv import load_dotenv

# need to import the agent to register the functions with the server
import agent_server.agent  # noqa: F401
from agent_server.server import AgentServer, parse_server_args, setup_mlflow

# Load environment variables from .env.local if it exists
load_dotenv(dotenv_path=".env.local", override=True)

agent_server = AgentServer()
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
