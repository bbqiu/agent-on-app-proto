# Agent Server

MLflow-compatible agent server with FastAPI that supports both streaming and non-streaming requests.

## Features

- **Single `/invocations` endpoint** that routes based on `stream` parameter
- **MLflow agent type validation** for `agent/v1/chat`, `agent/v2/chat`, and `agent/v1/responses`
- **Automatic MLflow tracing** for all requests and responses
- **Async/sync function detection** - works with both sync and async agent functions
- **Decorator-based registration** using `@predict` and `@predict_stream`

## Quick Start

1. **Install dependencies and activate the python env:**
   ```bash
   uv sync
   source .venv/bin/activate
   ```

2. **Run the server:**
   ```bash
   # Option 1: Using uv script (recommended)
   uv run agent-server
   
   # Option 2: Direct Python execution
   python src/agent_server/example_agent.py
  
   Both options automatically load the example agent functions and start the server on http://localhost:8000.

3. **Make requests:**
   ```bash
   # Non-streaming
   curl -X POST http://localhost:8000/invocations \
     -H "Content-Type: application/json" \
     -d '{
       "input": [
         {
           "role": "user",
           "content": "what is 4*3 in python?"
         }
       ]
     }'

   # Streaming  
   curl -X POST http://localhost:8000/invocations \
     -H "Content-Type: application/json" \
     -d '{
       "input": [
         {
           "role": "user", 
           "content": "what is 4*3 in python?"
         }
       ],
       "stream": true
     }'
   ```

## Usage

### Create Your Agent

```python
from agent_server import predict, predict_stream, create_server

@predict()
def my_predict(data):
    messages = data.get("messages", [])
    # Your logic here
    return "Response"

@predict_stream()
def my_stream(data):
    messages = data.get("messages", [])
    # Your streaming logic here
    for chunk in ["Hello", "World"]:
        yield chunk

# Create server for ChatModel
server = create_server("agent/v1/chat")
server.run()
```

# Deploying to Databricks Apps
- Ensure you have the Databricks CLI installed and configured.

Create a Databricks App to host your agent, server, and UI:
```bash
databricks apps create agent-proto
```

Upload the source code to Databricks and deploy the app:
```bash
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
databricks sync . "/Users/$DATABRICKS_USERNAME/agent-proto"
databricks apps deploy agent-proto --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/agent-proto"
```