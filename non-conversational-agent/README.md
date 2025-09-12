# Non-Conversational Agent on Databricks Apps

A demonstration of a non-conversational agent deployed on Databricks Apps that processes structured financial document questions and provides yes/no answers with detailed reasoning.

## Overview

This example showcases how to build and deploy a **non-conversational agent** that handles specific, well-defined tasks without maintaining conversation context. Unlike conversational agents that engage in back-and-forth dialogue, this agent processes discrete requests and returns structured responses with full MLflow traceability.

## Example Use Case

The agent processes structured questions about financial document content and provides yes/no answers with reasoning. Users provide both the document text and questions directly in the input, eliminating the need for vector search infrastructure in this simplified example. This demonstrates how non-conversational agents can handle specific, well-defined tasks without conversation context, while maintaining full traceability through MLflow 3.

### Sample Input/Output

**Input:**
```json
{
  "document_text": "Total assets: $2,300,000. Total liabilities: $1,200,000. Shareholder's equity: $1,100,000. Net income for the period was $450,000. Revenues: $1,700,000. Expenses: $1,250,000. Net cash provided by operating activities: $80,000. Cash flows from investing activities: -$20,000",
  "questions": [
    {"text": "Do the documents contain a balance sheet?"},
    {"text": "Do the documents contain an income statement?"},
    {"text": "Do the documents contain a cash flow statement?"}
  ]
}
```

**Output:**
```json
{
  "results": [
    {
      "question_text": "Do the documents contain a balance sheet?",
      "answer": "Yes",
      "chain_of_thought": "Looking at the document chunks, I can see: Total assets: $2,300,000, Total liabilities: $1,200,000, Shareholder's equity: $1,100,000. These three elements are the core components of a balance sheet...",
      "span_id": "db60a98146dd8ba2"
    }
  ],
  "trace_id": "tr-db0aa59eaa7ab0f42e4489f5cf1fad7c"
}
```

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   cd non-conversational-agent
   uv sync
   ```

2. **Set up environment:**
   ```bash
   export DATABRICKS_CONFIG_PROFILE="your-profile"
   export MLFLOW_EXPERIMENT_ID="your-experiment-id"
   ```

3. **Start the server:**
   ```bash
   uv run agent-server
   ```

4. **Test the agent:**
   ```bash
   python test_agent.py --check-health
   python test_agent.py
   ```

### Databricks Apps Deployment

1. **Deploy to Databricks Apps:**
   ```bash
   databricks apps deploy
   ```

2. **Test the deployed app:**
   ```bash
   python test_agent.py --url https://your-app-url.databricksapps.com
   ```

## API Endpoints

- `GET /` - Server information and available endpoints
- `GET /health` - Health check (returns `{"status": "healthy"}`)
- `POST /invocations` - Main agent endpoint for processing questions

## Real-World Extensions

This simplified example can be easily extended for production use cases by integrating additional tools and capabilities. Examples include:

- **Vector Search**: Integrate Databricks Vector Search for document retrieval instead of direct text input
- **MCP Tools**: Add Model Context Protocol tools for external system integrations
- **Databricks Agents**: Combine with other Databricks agents like Genie for structured data access
- **Custom Tools**: Add domain-specific tools for specialized financial analysis
- **Streaming Responses**: Support streaming for long-running analysis tasks

The core MLflow tracing and monitoring patterns demonstrated here remain consistent regardless of the underlying system complexity.

## Testing

The included `test_agent.py` script supports both local and remote testing:

```bash
# Local testing
python test_agent.py --url http://localhost:8000

# Remote testing (auto-fetches OAuth token)
python test_agent.py --url https://your-app.databricksapps.com

# Manual token
python test_agent.py --url https://your-app.com --token your-token

# Health check only
python test_agent.py --check-health
```

## Configuration

Key environment variables:

- `DATABRICKS_CONFIG_PROFILE`: Databricks CLI profile for authentication
- `MLFLOW_EXPERIMENT_ID`: MLflow experiment ID for tracing
- `MONITORING_EXPERIMENT_ID`: (Optional) Separate experiment for monitoring
- `PORT`: Server port (default: 8000)

## Development Notes

- Uses `agent_type=None` for non-conversational behavior
- Bypasses MLflow conversational agent validation
- Supports flexible return types (dict, dataclass, pydantic models)
- Includes comprehensive error handling and logging
