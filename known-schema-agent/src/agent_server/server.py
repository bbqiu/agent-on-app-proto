import inspect
import json
import logging
import time
from dataclasses import asdict, is_dataclass
from typing import Any, Callable, Literal, Optional, Type

import mlflow
import mlflow.tracing
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from mlflow.pyfunc import ResponsesAgent
from mlflow.tracing.trace_manager import InMemoryTraceManager
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)
from pydantic import BaseModel

_invoke_function: Optional[Callable] = None
_stream_function: Optional[Callable] = None


def invoke():
    """Decorator to register a function as an invoke endpoint. Can only be used once."""

    def decorator(func: Callable):
        global _invoke_function
        if _invoke_function is not None:
            raise ValueError("invoke decorator can only be used once")
        _invoke_function = func
        return func

    return decorator


def stream():
    """Decorator to register a function as a stream endpoint. Can only be used once."""

    def decorator(func: Callable):
        global _stream_function
        if _stream_function is not None:
            raise ValueError("stream decorator can only be used once")
        _stream_function = func
        return func

    return decorator


AgentType = Literal["agent/v1/responses"]


class AgentServer:
    def __init__(self, agent_type: Optional[AgentType] = None):
        self.agent_type = agent_type
        self.validator = AgentValidator(agent_type)
        self.app = FastAPI(title="Agent Server", version="0.0.1")

        # Add CORS middleware to allow frontend connections
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:5173",
                "http://localhost:5174",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:5174",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.logger = logging.getLogger(__name__)
        self._setup_routes()

    @staticmethod
    def _get_databricks_output(trace_id: str) -> dict:
        with InMemoryTraceManager.get_instance().get_trace(trace_id) as trace:
            return {"trace": trace.to_mlflow_trace().to_dict()}

    def _setup_routes(self):
        @self.app.post("/invocations")
        async def invocations_endpoint(request: Request):
            start_time = time.time()

            try:
                data = await request.json()
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid JSON in request body: {str(e)}"
                )

            # Log incoming request
            self.logger.info(
                "Request received",
                extra={
                    "agent_type": self.agent_type,
                    "request_size": len(json.dumps(data)),
                    "stream_requested": data.get("stream", False),
                },
            )

            # Check if streaming is requested
            is_streaming = data.get("stream", False)
            return_trace = data.get("databricks_options", {}).get("return_trace", False)

            # Remove stream parameter from data before validation
            request_data = {k: v for k, v in data.items() if k != "stream"}

            # Validate request parameters based on agent type
            try:
                self.validator.validate_request(request_data)
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
        async def health_check():
            """Health check endpoint for frontend connection testing"""
            return {"status": "healthy", "server": "agent-server", "version": "0.0.1"}

    async def _handle_invoke_request(self, data: dict, start_time: float, return_trace: bool):
        """Handle non-streaming invoke requests"""
        # Use the single invoke function
        if _invoke_function is None:
            raise HTTPException(status_code=500, detail="No invoke function registered")

        func = _invoke_function
        func_name = func.__name__

        # Check if function is async or sync and execute with tracing
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
                span.set_outputs(result)

                if return_trace:
                    databricks_output = self._get_databricks_output(span.trace_id)

            result["databricks_output"] = databricks_output

            # Log response details
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

    async def _handle_stream_request(self, data: dict, start_time: float, return_trace: bool):
        """Handle streaming requests"""
        # Use the single stream function
        if _stream_function is None:
            raise HTTPException(status_code=500, detail="No stream function registered")

        func = _stream_function
        func_name = func.__name__

        # Collect all chunks for tracing
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

                    # Log the full streaming session
                    duration = round(time.time() - start_time, 2)
                    span.set_attribute("duration_ms", duration)
                    if self.agent_type == "agent/v1/responses":
                        span.set_outputs(ResponsesAgent.responses_agent_output_reducer(all_chunks))
                    # TODO: add additional streaming output reducers for different agent types
                    else:
                        span.set_outputs(all_chunks)

                    if return_trace:
                        databricks_output = self._get_databricks_output(span.trace_id)
                        yield f"data: {json.dumps({'databricks_output': databricks_output})}\n\n"

                    # Send [DONE] signal
                    yield "data: [DONE]\n\n"

                # Log streaming response completion
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

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        import uvicorn

        uvicorn.run(self.app, host=host, port=port)


class AgentValidator:
    def __init__(self, agent_type: Optional[AgentType] = None):
        self.agent_type = agent_type
        self.logger = logging.getLogger(__name__)

    def validate_pydantic(self, pydantic_class: Type[BaseModel], data: Any) -> None:
        """Generic pydantic validator that throws an error if the data is invalid"""
        if isinstance(data, pydantic_class):
            return
        try:
            pydantic_class(**data)
        except Exception as e:
            raise ValueError(
                f"Invalid data for {pydantic_class.__name__} (agent_type: {self.agent_type}): {e}"
            )

    def validate_invoke_response(self, result: Any) -> None:
        """Validate the invoke response"""
        if self.agent_type == "agent/v1/responses":
            self.validate_pydantic(ResponsesAgentResponse, result)
        # TODO: add additional validation for different agent types

    def validate_stream_response(self, result: Any) -> None:
        """Validate a stream event for agent/v1/responses (ResponsesAgent)"""
        if self.agent_type == "agent/v1/responses":
            self.validate_pydantic(ResponsesAgentStreamEvent, result)
        # TODO: add additional validation for different agent types

    def validate_request(self, data: dict) -> None:
        """Validate request parameters based on agent type"""
        if self.agent_type == "agent/v1/responses":
            self.validate_pydantic(ResponsesAgentRequest, data)
        # TODO: add additional validation for different agent types

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


# Factory function to create server with specific agent type
def create_server(agent_type: Optional[AgentType] = None) -> AgentServer:
    return AgentServer(agent_type)
