# Agents on Apps

The Databricks Agent Platform team is prototyping the development experience of deploying Agents on Databricks Apps instead of Databricks Model Serving.

By deploying agents on Databricks Apps instead of Model Serving, you can:

- Validate authentication with tools, endpoints, genie spaces etc. in seconds instead of having to wait ~15 min for an endpoint to deploy
- Use [MLflow git-based logged models](https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/version-tracking/track-application-versions-with-mlflow) and real time tracing
- Use AI coding tools like Claude Code or Cursor to develop your agent locally
- Tweak behaviors within the async server to handle agent invocation exactly how you desire

Today, there are some rough edges with this CUJ, but we have a lot of future work planned. You can take a look at this [Project Plan](https://docs.google.com/document/d/155XkF9LrgZt8gNBnn0DSnkYXmWeK-lZGTwXxX9UP5vU) to see if a feature you'd like is already planned.

Please feel free to reach out to agent-feedback@databricks.com if you have any feedback or questions!

### In this repo

Please refer to each individual template's README.md for more details. The templates in this repo all have:

- Built-in MLflow tracing
- An async server to query your agent, configured to route requests from `/invocations` to your agent implementation
- Decorators to easily specify stream and invoke methods

Click on each of the links below to see more details about each agent template:

- [responses-api-agent](/responses-api-agent/README.md)
- [chat-completions-agent](/chat-completions-agent/README.md)
- 🚧 (IN PROGRESS) [non-conversational-agent](/non-conversational-agent/README.md)
