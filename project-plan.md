# Agents on Apps Project Plan

Last updated: Sep 9, 2025

## Core CUJ Enablement - End of October (Subject to change based on customer feedback)

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
- Revamped databricks app template UI with oauth, tool call confirmation, and trace viewer

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

- Support querying an agent-tagged deployed app from the OpenAI Client

#### Testing / Release

- Decide where to ship the async agent server (MLflow or databricks-ai-bridge?)

#### Observability

- Use Apps tags to track usage of agents on apps and differentiate between known / unknown schemas

#### Docs

- Migration guide from serving endpoint
- Langchain Example
- OpenAI Client Example
