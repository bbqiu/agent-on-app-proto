import argparse
import contextvars
import inspect
import json
import logging
import os
import subprocess
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Literal, Optional, Type

import mlflow
from databricks.sdk import WorkspaceClient
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from mlflow.pyfunc import ResponsesAgent
from mlflow.tracing.trace_manager import InMemoryTraceManager
from mlflow.types.agent import ChatAgentChunk, ChatAgentRequest, ChatAgentResponse
from mlflow.types.llm import (
    ChatCompletionChunk,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
)
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)
from pydantic import BaseModel

_invoke_function: Optional[Callable] = None
_stream_function: Optional[Callable] = None
AgentType = Literal["agent/v1/responses", "agent/v1/chat", "agent/v2/chat"]


# Context-isolated storage for request headers, ensuring thread-safe access across async execution contexts
_request_headers: contextvars.ContextVar[Dict[str, str]] = contextvars.ContextVar(
    "request_headers", default={}
)


def set_request_headers(headers: Dict[str, str]) -> None:
    """Set request headers in the current context (called by server)"""
    _request_headers.set(headers)


def get_request_headers() -> Dict[str, str]:
    """Get all request headers from the current context"""
    return _request_headers.get()


def get_header(name: str, default: Optional[str] = None) -> Optional[str]:
    """Get a specific header value from the current context"""
    return get_request_headers().get(name, default)


def get_forwarded_access_token() -> Optional[str]:
    """Get the x-forwarded-access-token from the current request context."""
    return get_header("x-forwarded-access-token")


def get_obo_workspace_client() -> WorkspaceClient:
    """Get a workspace client with the token from the
    x-forwarded-access-token header for OBO authentication"""
    return WorkspaceClient(token=get_forwarded_access_token(), auth_type="pat")


def _configure_mlflow_tracking() -> None:
    """
    Configure MLflow tracking URI with robust authentication that works both locally and on Databricks Apps.

    Priority order:
    1. If DATABRICKS_HOST and DATABRICKS_TOKEN are set, use them directly
    2. If running on Databricks Apps (DATABRICKS_APP_NAME exists), use "databricks" URI
    3. If DATABRICKS_CONFIG_PROFILE is set, try to use profile-based authentication
    4. Fall back to "databricks" URI and let MLflow handle default authentication
    """
    # Check if explicit host and token are provided (most reliable method)
    databricks_host = os.getenv("DATABRICKS_HOST")
    databricks_token = os.getenv("DATABRICKS_TOKEN")

    if databricks_host and databricks_token:
        print("Using explicit DATABRICKS_HOST and DATABRICKS_TOKEN for authentication")
        mlflow.set_tracking_uri("databricks")
        return

    # Check if we're running in Databricks Apps environment
    app_name = os.getenv("DATABRICKS_APP_NAME")
    if app_name:
        print(
            f"Running in Databricks Apps environment (app: {app_name}), using default authentication"
        )
        mlflow.set_tracking_uri("databricks")
        return

    # Try profile-based authentication for local development
    profile = os.getenv("DATABRICKS_CONFIG_PROFILE")
    if profile:
        try:
            print(f"Attempting to use Databricks CLI profile: {profile}")
            mlflow.set_tracking_uri(f"databricks://{profile}")
            # Test the connection by trying to get the tracking URI
            tracking_uri = mlflow.get_tracking_uri()
            print(f"Successfully configured MLflow with profile '{profile}': {tracking_uri}")
            return
        except Exception as e:
            print(f"Failed to use profile '{profile}': {e}")
            print("Falling back to default authentication")

    # Final fallback: use default "databricks" URI
    print("Using default Databricks authentication (relies on environment or default profile)")
    mlflow.set_tracking_uri("databricks")


def setup_mlflow(*, register_model_to_uc: bool = False) -> None:
    """Initialize MLflow tracking and set active model."""
    experiment_id = os.getenv("MLFLOW_EXPERIMENT_ID")
    assert experiment_id is not None, (
        "You must set MLFLOW_EXPERIMENT_ID in your environment to enable MLflow git-based logging and real time tracing. Refer to the README for more info."
    )

    # Configure MLflow tracking URI with robust authentication
    _configure_mlflow_tracking()
    mlflow.set_experiment(experiment_id=experiment_id)

    # in a Databricks App, the app name is set in the environment variable DATABRICKS_APP_NAME
    # in local development, we use a fallback app name
    # TODO: add a fallback app name
    app_name = os.getenv("DATABRICKS_APP_NAME", "local-dev")

    # Get current git commit hash for versioning
    try:
        git_commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()[:8]
        )
        version_identifier = f"git-{git_commit}"
    except subprocess.CalledProcessError:
        version_identifier = "no-git-repo"  # Fallback if not in a git repo
    logged_model_name = f"{app_name}-{version_identifier}"

    # Set the active model context
    active_model_info = mlflow.set_active_model(name=logged_model_name)
    print(
        f"Active LoggedModel: '{active_model_info.name}', Model ID: '{active_model_info.model_id}'"
    )

    if register_model_to_uc:
        mlflow.set_registry_uri(os.getenv("MLFLOW_REGISTRY_URI"))
        # TODO: fill in the catalog, schema, and model name for the UC model
        catalog = "main"
        schema = "default"
        model_name = ""
        assert model_name, "Please set the catalog, schema, and model name for the UC model"
        UC_MODEL_NAME = f"{catalog}.{schema}.{model_name}"
        uc_registered_model_info = mlflow.register_model(
            model_uri=active_model_info.model_uri, name=UC_MODEL_NAME
        )
        print(f"Registered model to UC: {uc_registered_model_info}")


def invoke() -> Callable:
    """Decorator to register a function as an invoke endpoint. Can only be used once."""

    def decorator(func: Callable):
        global _invoke_function
        if _invoke_function is not None:
            raise ValueError("invoke decorator can only be used once")
        _invoke_function = func
        return func

    return decorator


def get_invoke_function():
    return _invoke_function


def stream() -> Callable:
    """Decorator to register a function as a stream endpoint. Can only be used once."""

    def decorator(func: Callable):
        global _stream_function
        if _stream_function is not None:
            raise ValueError("stream decorator can only be used once")
        _stream_function = func
        return func

    return decorator


class AgentValidator:
    def __init__(self, agent_type: Optional[AgentType] = None):
        self.agent_type = agent_type
        self.logger = logging.getLogger(__name__)

    def validate_pydantic(self, pydantic_class: Type[BaseModel], data: Any) -> None:
        """Generic pydantic validator that throws an error if the data is invalid"""
        if isinstance(data, pydantic_class):
            return
        try:
            if isinstance(data, BaseModel):
                pydantic_class(**data.model_dump())
                return
            pydantic_class(**data)
        except Exception as e:
            raise ValueError(
                f"Invalid data for {pydantic_class.__name__} (agent_type: {self.agent_type}): {e}"
            )

    def validate_dataclass(self, dataclass_class: Any, data: Any) -> None:
        """Generic dataclass validator that throws an error if the data is invalid"""
        if isinstance(data, dataclass_class):
            return
        try:
            dataclass_class(**data)
        except Exception as e:
            raise ValueError(
                f"Invalid data for {dataclass_class.__name__} (agent_type: {self.agent_type}): {e}"
            )

    def validate_and_convert_request(self, data: dict) -> None:
        """Validate request parameters based on agent type"""
        if self.agent_type is None:
            return data
        elif self.agent_type == "agent/v1/responses":
            self.validate_pydantic(ResponsesAgentRequest, data)
            return ResponsesAgentRequest(**data)
        elif self.agent_type == "agent/v1/chat":
            for msg in data.get("messages", []):
                self.validate_dataclass(ChatMessage, msg)
            return ChatCompletionRequest(**data)
        elif self.agent_type == "agent/v2/chat":
            self.validate_pydantic(ChatAgentRequest, data)
            return ChatAgentRequest(**data)

    def validate_invoke_response(self, result: Any) -> None:
        """Validate the invoke response"""
        if self.agent_type == "agent/v1/responses":
            self.validate_pydantic(ResponsesAgentResponse, result)
        elif self.agent_type == "agent/v1/chat":
            self.validate_dataclass(ChatCompletionResponse, result)
        elif self.agent_type == "agent/v2/chat":
            self.validate_pydantic(ChatAgentResponse, result)

    def validate_stream_response(self, result: Any) -> None:
        """Validate a stream event for agent/v1/responses (ResponsesAgent)"""
        if self.agent_type == "agent/v1/responses":
            self.validate_pydantic(ResponsesAgentStreamEvent, result)
        elif self.agent_type == "agent/v1/chat":
            self.validate_dataclass(ChatCompletionChunk, result)
        elif self.agent_type == "agent/v2/chat":
            self.validate_dataclass(ChatAgentChunk, result)

    def validate_and_convert_result(self, result: Any, stream: bool = False) -> dict:
        """Validate and convert the result into a dictionary if necessary"""
        if stream:
            self.validate_stream_response(result)
        else:
            self.validate_invoke_response(result)

        if isinstance(result, BaseModel):
            return result.model_dump(exclude_none=True)
        elif is_dataclass(result):
            return asdict(result)
        elif isinstance(result, dict):
            return result
        else:
            raise ValueError(
                f"Result needs to be a pydantic model, dataclass, or dict. Unsupported result type: {type(result)}, result: {result}"
            )


class AgentServer:
    def __init__(self, agent_type: Optional[AgentType] = None):
        self.agent_type = agent_type
        self.validator = AgentValidator(agent_type)
        self.app = FastAPI(title="Agent Server", version="0.0.1")

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.logger = logging.getLogger(__name__)
        self._setup_static_files()
        self._setup_routes()

    def _setup_static_files(self) -> None:
        """Setup static file serving for the UI"""
        ui_dist_path = Path(__file__).parent.parent.parent / "ui/static"

        if ui_dist_path.exists():
            self.app.mount(
                "/assets", StaticFiles(directory=str(ui_dist_path / "assets")), name="assets"
            )

            from fastapi.responses import FileResponse

            @self.app.get("/")
            async def serve_ui():
                return FileResponse(str(ui_dist_path / "index.html"))

            @self.app.get("/databricks.svg")
            async def serve_databricks_svg():
                return FileResponse(str(ui_dist_path / "databricks.svg"))
        else:
            self.logger.warning(
                f"UI dist folder not found at {ui_dist_path}. UI will not be served."
            )

    @staticmethod
    def _get_databricks_output(trace_id: str) -> dict:
        with InMemoryTraceManager.get_instance().get_trace(trace_id) as trace:
            return {"trace": trace.to_mlflow_trace().to_dict()}

    def _setup_routes(self) -> None:
        @self.app.post("/invocations")
        async def invocations_endpoint(request: Request):
            # capture headers such as x-forwarded-access-token
            # https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth?language=Streamlit#retrieve-user-authorization-credentials
            set_request_headers(dict(request.headers))

            start_time = time.time()

            try:
                data = await request.json()
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid JSON in request body: {str(e)}"
                )

            self.logger.info(
                "Request received",
                extra={
                    "agent_type": self.agent_type,
                    "request_size": len(json.dumps(data)),
                    "stream_requested": data.get("stream", False),
                },
            )

            is_streaming = data.get("stream", False)
            return_trace = data.get("databricks_options", {}).get("return_trace", False)

            request_data = {k: v for k, v in data.items() if k != "stream"}

            try:
                request_data = self.validator.validate_and_convert_request(request_data)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid parameters for {self.agent_type}: {e}",
                )

            if is_streaming:
                return await self._handle_stream_request(request_data, start_time, return_trace)
            else:
                return await self._handle_invoke_request(request_data, start_time, return_trace)

        @self.app.get("/health")
        async def health_check() -> dict:
            """Health check endpoint for frontend connection testing"""
            return {"status": "healthy", "server": "agent-server", "version": "0.0.1"}

    async def _handle_invoke_request(
        self, data: dict, start_time: float, return_trace: bool
    ) -> dict:
        """Handle non-streaming invoke requests"""
        if _invoke_function is None:
            raise HTTPException(status_code=500, detail="No invoke function registered")

        func = _invoke_function
        func_name = func.__name__

        try:
            with mlflow.start_span(name=f"{func_name}_invoke") as span:
                span.set_inputs(data)
                if inspect.iscoroutinefunction(func):
                    result = await func(data)
                else:
                    result = func(data)

                result = self.validator.validate_and_convert_result(result)
                duration = round(time.time() - start_time, 2)
                span.set_attribute("duration_ms", duration)
                if self.agent_type == "agent/v1/responses":
                    span.set_attribute("mlflow.message.format", "openai")
                span.set_outputs(result)

                if return_trace:
                    databricks_output = self._get_databricks_output(span.trace_id)
                    result["databricks_output"] = databricks_output

            self.logger.info(
                "Response sent",
                extra={
                    "endpoint": "invoke",
                    "duration_ms": duration,
                    "response_size": len(json.dumps(result)),
                    "function_name": func_name,
                    "return_trace": return_trace,
                },
            )

            return result

        except Exception as e:
            duration = round(time.time() - start_time, 2)
            span.set_attribute("duration_ms", duration)
            span.set_outputs(f"Error: {str(e)}")

            self.logger.error(
                "Error response sent",
                extra={
                    "endpoint": "invoke",
                    "duration_ms": duration,
                    "error": str(e),
                    "function_name": func_name,
                    "return_trace": return_trace,
                },
            )

            raise HTTPException(status_code=500, detail=str(e))

    async def _handle_stream_request(
        self, data: dict, start_time: float, return_trace: bool
    ) -> StreamingResponse:
        """Handle streaming requests"""
        if _stream_function is None:
            raise HTTPException(status_code=500, detail="No stream function registered")

        func = _stream_function
        func_name = func.__name__

        all_chunks = []

        async def generate():
            nonlocal all_chunks
            try:
                with mlflow.start_span(name=f"{func_name}_stream") as span:
                    span.set_inputs(data)
                    if inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func):
                        async for chunk in func(data):
                            chunk = self.validator.validate_and_convert_result(chunk, stream=True)
                            all_chunks.append(chunk)
                            yield f"data: {json.dumps(chunk)}\n\n"
                    else:
                        for chunk in func(data):
                            chunk = self.validator.validate_and_convert_result(chunk, stream=True)
                            all_chunks.append(chunk)
                            yield f"data: {json.dumps(chunk)}\n\n"

                    duration = round(time.time() - start_time, 2)
                    span.set_attribute("duration_ms", duration)
                    if self.agent_type == "agent/v1/responses":
                        span.set_attribute("mlflow.message.format", "openai")
                        span.set_outputs(ResponsesAgent.responses_agent_output_reducer(all_chunks))
                    elif self.agent_type == "agent/v1/chat":

                        def _extract_content(chunk: ChatCompletionChunk | dict) -> str:
                            if isinstance(chunk, dict):
                                return (
                                    chunk.get("choices", [])[0].get("delta", {}).get("content", "")
                                )
                            if not chunk.choices:
                                return ""
                            return chunk.choices[0].delta.content or ""

                        content = "".join(map(_extract_content, all_chunks))
                        span.set_outputs({"choices": [{"role": "assistant", "content": content}]})
                    elif self.agent_type == "agent/v2/chat":
                        span.set_outputs({"messages": [chunk["delta"] for chunk in all_chunks]})
                    else:
                        span.set_outputs(all_chunks)

                    if return_trace:
                        databricks_output = self._get_databricks_output(span.trace_id)
                        yield f"data: {json.dumps({'databricks_output': databricks_output})}\n\n"

                    yield "data: [DONE]\n\n"

                self.logger.info(
                    "Streaming response completed",
                    extra={
                        "endpoint": "stream",
                        "duration_ms": duration,
                        "total_chunks": len(all_chunks),
                        "function_name": func_name,
                        "return_trace": return_trace,
                    },
                )

            except Exception as e:
                duration = round(time.time() - start_time, 2)
                span.set_attribute("duration_ms", duration)
                span.set_outputs(f"Error: {str(e)}")

                self.logger.error(
                    "Streaming response error",
                    extra={
                        "endpoint": "stream",
                        "duration_ms": duration,
                        "error": str(e),
                        "function_name": func_name,
                        "chunks_sent": len(all_chunks),
                        "return_trace": return_trace,
                    },
                )

                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    def set_agent_type(self, agent_type: AgentType) -> None:
        self.agent_type = agent_type
        self.validator = AgentValidator(agent_type)

    def run(
        self,
        app_import_string: str,
        host: str = "0.0.0.0",
        port: int = 8000,
        workers: int = 1,
        reload: bool = False,
    ) -> None:
        import uvicorn

        uvicorn.run(app_import_string, host=host, port=port, workers=workers, reload=reload)


def parse_server_args():
    """Parse command line arguments for the agent server"""
    parser = argparse.ArgumentParser(description="Start the agent server")
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to run the server on (default: 8000)"
    )
    parser.add_argument(
        "--workers", type=int, default=1, help="Number of workers to run the server on (default: 1)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Reload the server on code changes (default: False)",
    )
    return parser.parse_args()
