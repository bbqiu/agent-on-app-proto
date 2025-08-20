import subprocess

import mlflow


def setup_mlflow():
    """Initialize MLflow tracking and set active model."""
    mlflow.set_tracking_uri("databricks")
    mlflow.set_experiment("/Users/bryan.qiu@databricks.com/bbqiu-agent-proto1")

    # Define your application and its version identifier
    app_name = "bbqiu-agent-proto1"

    # Get current git commit hash for versioning
    try:
        git_commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()[:8]
        )
        version_identifier = f"git-{git_commit}"
    except subprocess.CalledProcessError:
        version_identifier = "local-dev"  # Fallback if not in a git repo
    logged_model_name = f"{app_name}-{version_identifier}"

    # Set the active model context
    active_model_info = mlflow.set_active_model(name=logged_model_name)
    print(
        f"Active LoggedModel: '{active_model_info.name}', Model ID: '{active_model_info.model_id}'"
    )
