"""Agent server package for MLflow-compatible endpoints."""

import logging

# Configure logging for Databricks Apps at package level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

from .server import AgentServer, create_server, invoke, parse_server_args, stream

__all__ = ["AgentServer", "create_server", "invoke", "stream", "parse_server_args"]
