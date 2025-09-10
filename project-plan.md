# Agents on Apps Project Plan

Last updated: Sep 9, 2025

## End of November (Subject to change based on customer feedback)

### Work Items:

#### Authoring UX

- Custom template for Responses API
- Custom template for Chat Completions API
- Custom template for non-conversational agents
- Add a new tab to databricks app templates for agents

#### UI

- Add compatibility for ChatCompletions API
- Stream LLM generated text
- Make UI display errors
- Use the E2E chatbot example, potentially switching to playground open source

#### Deployment UX

- Update server code to work with OBO (workspace client auth via thread context vars)
- Add MCP as an OBO scope to a Databricks App
- Add UC Function as a resource to a Databricks App
- Add VS Index as a resource to a Databricks App
- Add UC Connections as a resource to a Databricks App
- App deployment versioning via git backed apps

#### Tracing UX

- Add a ChatCompletions and ChatAgent output_reducer for streaming output
  Add MLflow experiment as a resource to a Databricks App
- Check that trace server via MLflow client works within a Databricks App

#### Evaluation UX

- Support mlflow.genai.to_predict_fn for "apps:/<app-name>" (mint oauth token w/ right scopes or notebook oauth)
- Include snippets on how to use mlflow.genai.evaluate() locally

#### Querying UX

- Add agent-tagged databricks apps to a review app
- Query agent-tagged databricks apps from playground
- Revamped databricks app template UI with oauth, tool call confirmation, and trace viewer
- Support querying an agent-tagged deployed app from the OpenAI Client

#### Testing / Release

- Test our examples with Apps integration testing
- Decide where to ship the async agent server (MLflow or databricks-ai-bridge?)

#### Observability

- Use Apps tags to track usage of agents on apps and differentiate between known / unknown schemas

#### Docs

- Migration guide from serving endpoint
- Langchain Example
- OpenAI Client Example

## GA and additional polish (Q4)

### Work Items

#### Authoring UX

- Agent export from playground
- Support non-local developer personas (databricks editor, interactive notebooks)
- Add elements from claude-databricks-app-template

#### Deployment UX

- Once real-time tracing is via delta tables only, will need to add UC Tables as a resource to Databricks Apps
- Load test (compare with model serving concurrency)
- Long running queries with fastapi server auto-reconnect (slack)
- Automatically create experiment on app creation
- Typescript agent server

#### Tracing UX

- how-to replace request ID on traces + how to query (docs link)
- MLflow client links source to Databricks App
- Add a trace_buffer to the MLflow span exporter (slack)

#### Observability

- Rate limits

#### Docs

- Switch out all authoring agents in code docs to recommend deploying agents on apps
- Stateful Lakebase example
- claude.md to help customers iterate on their agent with eval results from MLflow evaluate
