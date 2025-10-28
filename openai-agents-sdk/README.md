# Responses API Agent

This example is a simple agent that follows the [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses) with one tool, `system.ai.python_exec`, roughly following the example in the ["Author AI agents in code" documentation](https://docs.databricks.com/aws/en/generative-ai/agent-framework/author-agent).

Refer to [the ResponsesAgent MLflow docs](https://mlflow.org/docs/latest/genai/flavors/responses-agent-intro/) for more about input and output formats for streaming and non-streaming requests, tracing requirements, and other agent authoring details.

## Local Devloop

### Set up your local environment

Install the latest versions of `uv` (python package manager) and `nvm` (node version manager):

- [`uv` installation docs](https://docs.astral.sh/uv/getting-started/installation/)
- [`nvm` installation](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating)
- Run the following to use Node 20 LTS:
  ```bash
  nvm use 20
  ```

### Create and link an MLflow experiment to your app

Create an MLflow experiment in Databricks. Refer to the [MLflow experiments documentation](https://docs.databricks.com/aws/en/mlflow/experiments#create-experiment-from-the-workspace) for more info.

```bash
export MLFLOW_EXPERIMENT_ID="1234567890" # fill in with your experiment ID
export MLFLOW_TRACKING_URI="databricks"
export MLFLOW_REGISTRY_URI="databricks-uc"
```

### Set up local authentication to Databricks

In order to access Databricks resources from your local machine while developing your agent, you need to authenticate with Databricks. As stated in the [Databricks SDK authentication docs](https://docs.databricks.com/aws/en/dev-tools/sdk-python#authenticate-the-databricks-sdk-for-python-with-your-databricks-account-or-workspace), there are a few ways to authenticate:

- **Use a Databricks configuration profile**

  Refer to the [configuration profiles documentation](https://docs.databricks.com/aws/en/dev-tools/auth/config-profiles) for more info.

  ```bash
  databricks configure
  # Set the configuration profile
  export DATABRICKS_CONFIG_PROFILE="DEFAULT"
  ```

- **Use a personal access token (PAT)**

  Refer to the [PAT documentation](https://docs.databricks.com/aws/en/dev-tools/auth/pat#databricks-personal-access-tokens-for-workspace-users) for more info.

  ```bash
  export DATABRICKS_HOST="https://host.databricks.com"
  export DATABRICKS_TOKEN="dapi_token"
  ```

### Modifying the UI

Note that the UI only works with streamed `response.output_item.done` events from the agent server. Read more in the [MLflow docs for streaming ResponsesAgent output](https://mlflow.org/docs/latest/genai/flavors/responses-agent-intro/#streaming-agent-output).

To run the UI locally while changing it to see live changes, simultaneously run the following two commands in separate terminal windows:

```bash
(cd ui && npm run dev)
uv run agent-server
```

Common changes to make:

- Edit `index.html` to change the UI title and icon.
- Change the port in `ui/src/api/client.ts` if running on a different port. Note that Databricks Apps serve port 8000 by default, which is why it's set to 8000.

### Modifying your agent

#### TODO: update this section with more details about MCP and openai agents sdk auth refresh

`agent.py` currently contains a Responses API agent. Please modify this file to create your custom agent. In order to work with the agent server provided, inside of `agent.py`, we require you to:

- Call `create_server()` in order to initialize the server.

  - If your agent matches one of `ChatCompletions`, `ChatAgent` or `Responses` API, you can use the server's built-in validators by initializing the server with the following task types:
    - `ChatCompletions`: `create_server("agent/v1/chat")`
    - `ChatAgent`: `create_server("agent/v2/chat")`
    - **`Responses`: `create_server("agent/v1/responses")`**
      - This specific example follows the Responses API, matching up with ResponsesAgent from MLflow.

- Create an app module that is importable via some import path like `agent_server.agent:app`. This is used if your FastAPI server has multiple workers.
- Use `parse_server_args()` to parse the server arguments.
- Decorate your non-streaming method with `@invoke()` and your streaming method with `@stream()`.
  - Neither is required, but in order for your agent to be served, at least one decorator must be used.
  - The method(s) can be async or sync, but we recommend async in order to achieve greater request concurrency.
  - The method decorated with `@invoke()` will be called when requests are made to `/invocations` with `"stream": false"` or without a `"stream"` param in the payload.
  - The method decorated with `@stream()` will be called when requests are made to `/invocations` with `"stream": true"`.

Very minimal example:

```python
from agent_server.utils import setup_mlflow
from agent_server.server import create_server, invoke, stream

@invoke()
async def non_streaming(request: dict) -> dict:
   return dict

@stream()
async def streaming(request: dict) -> AsyncGenerator[dict, None]:
   yield dict


agent_server = create_server("agent/v1/responses")
app = agent_server.app

def main(): # called in the pyproject.toml `agent-server` script
    args = parse_server_args()
    setup_mlflow()
    agent_server.run(
        "agent_server.agent:app",
        port=args.port,
        workers=args.workers,
        reload=args.reload,
    )
```

Common changes to make:

- Feel free to add as many files or folders as you want to your agent, just make sure that the script within `pyproject.toml` runs the right script that will start the server and set up MLflow tracing.
- To add dependencies to your agent, run `uv add <package_name>` (ex. `uv add "mlflow-skinny[databricks]"`). Refer to the [python pyproject.toml guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#dependencies-and-requirements) for more info.
- While we have built-in MLflow tracing when calling the methods annotated with `@invoke()` and `@stream()`, you can also further instrument your own agent. Refer to the [MLflow tracing documentation](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/app-instrumentation/) for more info.
  - Search for `"start_span"` within `src/agent_server/server.py` for the built-in implementation.
- Refer to the Agent Framework ["Author AI Agents in Code" documentation](https://docs.databricks.com/aws/en/generative-ai/agent-framework/author-agent) for more information.

### Modifying the server

You can modify the server to your liking. Refer to the [server.py](src/agent_server/server.py) file for more info. Run the `agent-server` script to start the server locally:

```bash
uv run agent-server
uv run agent-server --port 8001
uv run agent-server --workers 4
# To hot-reload the server on code changes, you can use the --reload command. Note that this doesn't work with multiple workers.
uv run agent-server --reload
```

### Testing out your local agent

Build the UI and start up the agent server locally:

```bash
(cd ui && npm run build) # build the UI to be served statically
uv run agent-server --reload
```

Now you can either query your agent via the built in UI (served by default at http://localhost:8000) or via REST API request:

- Example streaming request:
  ```bash
  curl -X POST http://localhost:8000/invocations \
   -H "Content-Type: application/json" \
   -d '{ "input": [{ "role": "user", "content": "hi" }], "stream": true }'
  ```
- Example non-streaming request:
  ```bash
  curl -X POST http://localhost:8000/invocations  \
   -H "Content-Type: application/json" \
   -d '{ "input": [{ "role": "user", "content": "hi" }] }'
  ```

### Evaluating your agent

Evaluate your agent by calling the invoke function you defined for the agent locally.

- Update your `evaluate_agent.py` file with the preferred evaluation dataset and scorers.

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

   **On-behalf-of (OBO) User Authentication**: Use `get_obo_workspace_client()` from `agent_server.utils` to authenticate as the requesting user instead of the app service principal. Refer to the [OBO authentication documentation](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth?language=Streamlit#retrieve-user-authorization-credentials) for more info.

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

3. **Build the UI**

   ```bash
   (cd ui && npm run build)
   ```

4. **Sync local files to your workspace**

   Refer to the [Databricks Apps deploy documentation](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy?language=Databricks+CLI#deploy-the-app) for more info.

   ```bash
   DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
   databricks sync . "/Users/$DATABRICKS_USERNAME/agent-proto"
   ```

5. **Deploy your Databricks App**

   Refer to the [Databricks Apps deploy documentation](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy?language=Databricks+CLI#deploy-the-app) for more info.

   ```bash
   databricks apps deploy agent-proto --source-code-path /Workspace/Users/$DATABRICKS_USERNAME/agent-proto
   ```

6. **Query your agent hosted on Databricks Apps**

   Databricks Apps are _only_ queryable via OAuth token. You cannot use a PAT to query your agent. Generate an [OAuth token with your credentials using the Databricks CLI](https://docs.databricks.com/aws/en/dev-tools/cli/authentication#u2m-auth):

   ```bash
   databricks auth login --host <https://host.databricks.com>
   databricks auth token
   ```

   You can now send a request to the `/invocations` endpoint, where your agent is hosted:

   - Example streaming request:

     ```bash
     curl -X POST <app-url.databricksapps.com>/invocations \
        -H "Authorization: Bearer <oauth token>" \
        -H "Content-Type: application/json" \
        -d '{ "input": [{ "role": "user", "content": "hi" }], "stream": true }'
     ```

   - Example non-streaming request:

     ```bash
     curl -X POST <app-url.databricksapps.com>/invocations \
        -H "Authorization: Bearer <oauth token>" \
        -H "Content-Type: application/json" \
        -d '{ "input": [{ "role": "user", "content": "hi" }] }'
     ```

For future updates to the agent, you only need to sync and redeploy your agent. If making changes to the UI, you'll also have to rebuild the UI.

### FAQ

- For a streaming response, I see a 200 OK in the logs, but an error in the actual stream. What's going on?
  - This is expected. The server will return a 200 OK if the stream is set up without error, but any errors during the stream will not change the initial status code.
- How is my agent being versioned in MLflow?
  - In `setup_mlflow()` from `src/agent_server/utils.py`, we get the current git commit hash and use it to create a logged model, and all traces from that version of the agent will be logged to the corresponding model in MLflow on Databricks.
- How do I register my logged model to the UC model registry?
  - Fill in the catalog, schema, and model name for your UC model in `setup_mlflow()` from `src/agent_server/utils.py`.
  - Call `setup_mlflow(register_model_to_uc=True)` within the startup script in `main()` from `src/agent_server/agent.py`.
- When querying my agent, I get a 302 error. What's going on?
  - Please make sure you are using an OAuth token to query your agent. You cannot use a PAT to query your agent.
