from databricks.sdk import WorkspaceClient
from mlflow.genai.agent_server import get_request_headers


def get_user_workspace_client() -> WorkspaceClient:
    token = get_request_headers().get("x-forwarded-access-token")
    return WorkspaceClient(token=token, auth_type="pat")
