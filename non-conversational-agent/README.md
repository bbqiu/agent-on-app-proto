# Non-Conversational Agent

This example is a non-conversational agent that processes structured financial document questions and provides yes/no answers with detailed reasoning. Users provide both the document text and questions directly in the input, eliminating the need for vector search infrastructure in this simplified example. This demonstrates how non-conversational agents can handle specific, well-defined tasks without conversation context, while maintaining full traceability through MLflow 3.

## Get started

0. **Set up your local environment**
   Install the latest versions of `uv` (python package manager) and `nvm` (node version manager):

   - [`uv` installation docs](https://docs.astral.sh/uv/getting-started/installation/)
   - [`nvm` installation](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating)
   - Run the following to use Node 20 LTS:
     ```bash
     nvm use 20
     ```

1. **Set up local authentication to Databricks**

   In order to access Databricks resources from your local machine while developing your agent, you need to authenticate with Databricks. Modify `.env.local` with one of the following options:

   - **Use OAuth via the Databricks CLI (Recommended)**

     Authenticate with Databricks using the CLI. Refer to the [CLI OAuth documentation](https://docs.databricks.com/aws/en/dev-tools/cli/authentication#oauth-user-to-machine-u2m-authentication) for more info.

     ```bash
     databricks auth login
     ```

   After logging in, set the `DATABRICKS_CONFIG_PROFILE` environment variable in your .env.local file to the profile you used to authenticate.

   ```bash
   DATABRICKS_CONFIG_PROFILE="DEFAULT" # change to the profile name you chose
   ```

   - **Use a personal access token (PAT)**

     Refer to the [PAT documentation](https://docs.databricks.com/aws/en/dev-tools/auth/pat#databricks-personal-access-tokens-for-workspace-users) for more info.

     ```bash
     # Add these to your .env.local file
     # DATABRICKS_HOST="https://host.databricks.com"
     # DATABRICKS_TOKEN="dapi_token"
     ```

   See the [Databricks SDK authentication docs](https://docs.databricks.com/aws/en/dev-tools/sdk-python#authenticate-the-databricks-sdk-for-python-with-your-databricks-account-or-workspace) for more info.

2. **Create and link an MLflow experiment to your app**

   To enable MLflow tracing and version tracking, create an MLflow experiment in Databricks.

   - **Automatic setup (Recommended)**
     Run the `setup-mlflow.sh` script to automatically create the MLflow experiment and link it to your app. This will create a new experiment in your workspace and update the `MLFLOW_EXPERIMENT_ID` in your `.env.local` (for local testing) and `app.yaml` (for deployment) files.

     ```bash
     ./setup-mlflow.sh
     ```

   - **Manual setup**
     Create the MLflow experiment manually via the CLI.

     ```bash
     DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
     databricks experiments create-experiment /Users/$DATABRICKS_USERNAME/agents-on-apps
     ```

     Make a copy of `.env.example` to `.env.local` and update the `MLFLOW_EXPERIMENT_ID` in your `.env.local` file with the experiment ID you created. The `.env.local` file will be automatically loaded when starting the server.

     ```bash
     cp .env.example .env.local
     # Edit .env.local and fill in your experiment ID
     ```

   Refer to the [MLflow experiments documentation](https://docs.databricks.com/aws/en/mlflow/experiments#create-experiment-from-the-workspace) for more info.

### Modifying your agent

`agent.py` currently contains a very simple non-conversational document analysis agent. Please modify this file to create your custom non-conversational agent. In order to work with the agent server provided, inside of `agent.py`, we require you to:

- Create an `AgentServer` instance in order to initialize the server.

  - For non-conversational agents that don't follow the standard chat APIs, use: **`AgentServer(agent_type=None)`**
    - This bypasses MLflow's conversational agent validation while still providing structured response handling
    - Supports flexible return types (dict, dataclass, pydantic models)

- Create an app module that is importable via some import path like `agent_server.start_server:app`. This is used if your FastAPI server has multiple workers.
- Use `parse_server_args()` to parse the server arguments.
- Decorate your method with `@invoke()` for structured response handling.
  - For non-conversational agents that return structured data, we focus on the `@invoke()` decorator.
  - The method can be async or sync, but we recommend async in order to achieve greater request concurrency.
  - The method decorated with `@invoke()` will be called when requests are made to `/invocations`.

Very minimal example:

`agent.py`:

```python
from agent_server.server import invoke

@invoke()
async def process_request(request: dict) -> dict:
   return request
```

`start_server.py`:

```python
from dotenv import load_dotenv

# need to import the agent to register the functions with the server
import agent_server.agent  # noqa: F401
from agent_server.server import AgentServer, parse_server_args, setup_mlflow

# Load environment variables from .env.local if it exists
load_dotenv(dotenv_path=".env.local", override=True)

agent_server = AgentServer(agent_type=None)  # Non-conversational agent
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
```

Common changes to make:

- Feel free to add as many files or folders as you want to your agent, just make sure that the script within `pyproject.toml` runs the right script that will start the server and set up MLflow tracing.
- To add dependencies to your agent, run `uv add <package_name>` (ex. `uv add "databricks-vectorsearch"`). Refer to the [python pyproject.toml guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#dependencies-and-requirements) for more info.
- **Real-world extensions**: This simplified example can be easily extended for production use cases by integrating additional tools and capabilities. Examples include:
  - **Vector Search**: Integrate Databricks Vector Search for document retrieval instead of direct text input
  - **MCP Tools**: Add Model Context Protocol tools for external system integrations
  - **Databricks Agents**: Combine with other Databricks agents like Genie for structured data access
  - **Custom Tools**: Add domain-specific tools for specialized analysis
- While we have built-in MLflow tracing when calling the methods annotated with `@invoke()` and `@stream()`, you can also further instrument your own agent. Refer to the [MLflow tracing documentation](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/app-instrumentation/) for more info.
  - Search for `"start_span"` within `src/agent_server/server.py` for the built-in implementation.
- Refer to the Agent Framework ["Author AI Agents in Code" documentation](https://docs.databricks.com/aws/en/generative-ai/agent-framework/author-agent) for more information.

### Modifying the server

You can modify the server to your liking. Refer to the [server.py](src/agent_server/server.py) file for more info. Run the `start-server` script to start the server locally:

```bash
uv run start-server
uv run start-server --port 8001
uv run start-server --workers 4
# To hot-reload the server on code changes, you can use the --reload command. Note that this doesn't work with multiple workers.
uv run start-server --reload
```

### Testing out your local agent

Start up the agent server locally:

```bash
uv run start-server --reload
```

Now you can test your agent using the provided test script:

```bash
# Test locally
python test_agent.py

# Test with specific URL
python test_agent.py --url http://localhost:8000

# Test with health check only
python test_agent.py --url http://localhost:8000 --check-health
```

Or query your agent via REST API request:

```bash
curl -X POST http://localhost:8000/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "document_text": "Total assets: $2,300,000. Total liabilities: $1,200,000. Shareholder equity: $1,100,000. Net income: $450,000. Revenues: $1,700,000. Expenses: $1,250,000.",
    "questions": [
      {"text": "Do the documents contain a balance sheet?"},
      {"text": "Do the documents contain an income statement?"}
    ]
  }'
```

### Evaluating your agent

Evaluate your agent by calling the invoke function you defined for the agent locally.

- Update your `evaluate_agent.py` file with the preferred evaluation dataset and scorers.
- Your evaluation dataset must match the predict function signature. The wrapper takes a single argument named `data`, so each row should use `{"inputs": {"data": {...}}}` and the inner dict must match `AgentInput` (ex `document_text`, `questions: [{"text": str}]`).

Run the evaluation using the evaluation script:

```bash
uv run agent-evaluate
```

After it completes, open the MLflow UI link for your experiment to inspect results.

## Deploying to Databricks Apps

0. **Create a Databricks App**:
   Ensure you have the [Databricks CLI](https://docs.databricks.com/aws/en/dev-tools/cli/tutorial) installed and configured.

   ```bash
   databricks apps create agent-proto
   ```

1. **Set up authentication to Databricks resources**

   **App Authentication via Service Principal (SP)**: To access resources like serving endpoints, genie spaces, SQL warehouses, and lakebase instances, you can click `edit` on your app home page to grant the App's SP permission. Refer to the [Databricks Apps resources documentation](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/resources) for more info.

   For resources that are not supported yet, refer to the [Agent Framework authentication documentation](https://docs.databricks.com/aws/en/generative-ai/agent-framework/deploy-agent#automatic-authentication-passthrough) for the correct permission level to grant to your app SP. MLflow experiments, UC connections, UC functions, and vector search indexes will be added to the UI soon.

   **On-behalf-of (OBO) User Authentication**: Use `get_obo_workspace_client()` from `agent_server.server` to authenticate as the requesting user instead of the app service principal. Refer to the [OBO authentication documentation](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth?language=Streamlit#retrieve-user-authorization-credentials) for more info.

2. **Set the value of `MLFLOW_EXPERIMENT_ID` in `app.yaml`**

   Refer to the [Databricks Apps environment variable documentation](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/environment-variables) for more info.

   ```yml
   env:
     - name: MLFLOW_TRACKING_URI
       value: "databricks"
     - name: MLFLOW_REGISTRY_URI
       value: "databricks-uc"
     - name: MLFLOW_EXPERIMENT_ID
       value: "" # fill in with your experiment ID
   ```

3. **Sync local files to your workspace**

   Refer to the [Databricks Apps deploy documentation](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy?language=Databricks+CLI#deploy-the-app) for more info.

   ```bash
   DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
   databricks sync . "/Users/$DATABRICKS_USERNAME/agent-proto"
   ```

4. **Deploy your Databricks App**

   Refer to the [Databricks Apps deploy documentation](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy?language=Databricks+CLI#deploy-the-app) for more info.

   ```bash
   databricks apps deploy agent-proto --source-code-path /Workspace/Users/$DATABRICKS_USERNAME/agent-proto
   ```

5. **Query your agent hosted on Databricks Apps**

   You can now test your deployed agent using the test script with authentication:

   ```bash
   # Test with automatic OAuth token
   python test_agent.py --url <app-url.databricksapps.com>

   # Test with specific profile
   python test_agent.py --url <app-url.databricksapps.com> --profile your-profile

   # Test with manual token
   python test_agent.py --url <app-url.databricksapps.com> --token <oauth-token>
   ```

   Or send a request manually to the `/invocations` endpoint. Databricks Apps are _only_ queryable via OAuth token. You cannot use a PAT to query your agent. Generate an [OAuth token with your credentials using the Databricks CLI](https://docs.databricks.com/aws/en/dev-tools/cli/authentication#u2m-auth):

   ```bash
   databricks auth login --host <https://host.databricks.com>
   databricks auth token
   ```

   and send the request:

   ```bash
   curl -X POST <app-url.databricksapps.com>/invocations \
      -H "Authorization: Bearer <oauth token>" \
      -H "Content-Type: application/json" \
      -d '{
        "document_text": "Total assets: $2,300,000. Total liabilities: $1,200,000. Shareholder equity: $1,100,000. Net income: $450,000.",
        "questions": [
          {"text": "Do the documents contain a balance sheet?"},
          {"text": "Do the documents contain an income statement?"}
        ]
      }'
   ```

For future updates to the agent, you only need to sync and redeploy your agent.

### FAQ

- How is my agent being versioned in MLflow?
  - In `setup_mlflow()` from `src/agent_server/utils.py`, we get the current git commit hash and use it to create a logged model, and all traces from that version of the agent will be logged to the corresponding model in MLflow on Databricks.
- How do I register my logged model to the UC model registry?
  - Fill in the catalog, schema, and model name for your UC model in `setup_mlflow()` from `src/agent_server/utils.py`.
  - Call `setup_mlflow(register_model_to_uc=True)` within the startup script in `main()` from `src/agent_server/agent.py`.
- How does this differ from a conversational agent?
  - Non-conversational agents process discrete requests without maintaining conversation context. They use `agent_type=None` to bypass conversational validation and support flexible input/output formats for task-specific processing.
- When querying my agent, I get a 302 error. What's going on?
  - Please make sure you are using an OAuth token to query your agent. You cannot use a PAT to query your agent.
