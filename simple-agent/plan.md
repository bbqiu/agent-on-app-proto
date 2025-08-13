# App Architecture Plan

## 3-Component Design

### 1. Server Component (FastAPI-based)

- a `/invocations` endpoint that routes to predict or predict_stream depending on whether or not `"stream": true` was in the POST request payload
- Custom decorators `@predict` and `@predict_stream` to mark handler functions that do type checking based on the task type
- should detect if the predict and predict_stream methods are async or sync and call them accordingly
- MLflow tracing integration for request/response logging
- Route discovery system to find decorated functions
- Async support for streaming responses

### 2. Agent Code Component

- Arbitrary business logic functions decorated with `@predict`/`@predict_stream`
- Called by the server when requests come in
- Can be modular/pluggable for different agent implementations

### 3. UI Component (Future)

- Rich display of requests/responses
- Sends requests to server endpoints
- Could use Streamlit, Gradio, or React-based frontend

## Implementation Steps

1. ✅ Create plan file under `../agent`
2. Build server component with decorator system
3. Implement MLflow tracing integration
4. Create example agent functions to test the flow
5. UI component to be added later

## Tech Stack

- **FastAPI** for server (async, type hints, automatic docs)
- **MLflow** for tracing
- **Custom decorator framework** for route registration

## Architecture Flow

```
Client Request → FastAPI Server → Decorated Agent Function → MLflow Tracing → Response
```
