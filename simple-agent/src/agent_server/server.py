import asyncio
import inspect
import json
import logging
import time
from dataclasses import asdict, is_dataclass
from typing import Any, Callable, Literal, Optional

import mlflow
import mlflow.tracing
from fastapi import FastAPI, HTTPException, Request
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
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.app = FastAPI(title="Agent Server", version="0.0.1")
        self.logger = logging.getLogger(__name__)
        self._setup_routes()

    def _validate_responses_agent_request(self, data: dict) -> bool:
        """Validate parameters for agent/v1/responses (ResponsesAgent)"""
        try:
            ResponsesAgentRequest(**data)
            return True
        except Exception as e:
            self.logger.warning(f"Invalid parameters for {self.agent_type}: {e}")
            return False

    def _validate_responses_agent_response(self, result: Any) -> dict:
        """Validate an invoke response for agent/v1/responses (ResponsesAgent)"""
        try:
            ResponsesAgentResponse(**result)
            return True
        except Exception as e:
            self.logger.warning(f"Invalid invoke response for {self.agent_type}: {e}")
            return False

    def _validate_request(self, data: dict) -> bool:
        """Validate request parameters based on agent type"""
        if self.agent_type == "agent/v1/responses":
            return self._validate_responses_agent_request(data)
        return True

    def _validate_invoke_response(self, result: Any) -> dict:
        """Validate the invoke response"""
        if self.agent_type == "agent/v1/responses":
            return self._validate_responses_agent_response(result)
        return result

    def _validate_and_convert_result(self, result: Any) -> dict:
        """Validate and convert the result into a dictionary if necessary"""

        if isinstance(result, BaseModel):
            return result.model_dump(exclude_none=True)
        elif is_dataclass(result):
            return asdict(result)
        elif isinstance(result, dict):
            return result
        else:
            raise ValueError(f"Unsupported result type: {type(result)}, result: {result}")

    def _get_databricks_output(self, trace_id: str) -> dict:
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
            if not self._validate_request(request_data):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid parameters for {self.agent_type}. Expected format based on MLflow agent type.",
                )

            if is_streaming:
                return await self._handle_stream_request(request_data, start_time, return_trace)
            else:
                return await self._handle_invoke_request(request_data, start_time, return_trace)

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

                result = self._validate_and_convert_result(result)

                if return_trace:
                    result["databricks_output"] = self._get_databricks_output(span.trace_id)

                duration = round(time.time() - start_time, 2)
                span.set_attribute("duration_ms", duration)
                span.end(result)

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
            span.end(f"Error: {str(e)}")

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
                            chunk = self._validate_and_convert_result(chunk)
                            all_chunks.append(chunk)
                            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    else:
                        for chunk in func(data):
                            chunk = self._validate_and_convert_result(chunk)
                            all_chunks.append(chunk)
                            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    if return_trace:
                        databricks_output = self._get_databricks_output(span.trace_id)
                        yield f"data: {json.dumps({'databricks_output': databricks_output})}\n\n"

                    # Send [DONE] signal
                    yield "data: [DONE]\n\n"

                    # Log the full streaming session
                    duration = round(time.time() - start_time, 2)
                    span.set_attribute("duration_ms", duration)
                    span.end(ResponsesAgent.responses_agent_output_reducer(all_chunks))

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
                span.end(f"Error: {str(e)}")

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

        return StreamingResponse(generate(), media_type="text/event-stream")

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        import uvicorn

        uvicorn.run(self.app, host=host, port=port)


# Factory function to create server with specific agent type
def create_server(agent_type: AgentType) -> AgentServer:
    return AgentServer(agent_type)
