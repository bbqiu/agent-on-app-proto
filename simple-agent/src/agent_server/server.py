import asyncio
import inspect
import json
import logging
import time
from typing import Any, Callable, Literal, Optional

import mlflow
import mlflow.tracing
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)

# Single function storage - only one of each decorator allowed
_predict_function: Optional[Callable] = None
_predict_stream_function: Optional[Callable] = None


def predict(name: Optional[str] = None):
    """Decorator to register a function as a predict endpoint. Can only be used once."""

    def decorator(func: Callable):
        global _predict_function
        if _predict_function is not None:
            raise ValueError("predict decorator can only be used once")
        _predict_function = func
        return func

    return decorator


def predict_stream(name: Optional[str] = None):
    """Decorator to register a function as a predict_stream endpoint. Can only be used once."""

    def decorator(func: Callable):
        global _predict_stream_function
        if _predict_stream_function is not None:
            raise ValueError("predict_stream decorator can only be used once")
        _predict_stream_function = func
        return func

    return decorator


AgentType = Literal["agent/v1/responses"]


class AgentServer:
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.app = FastAPI(title="Agent Server", version="0.0.1")
        self.logger = logging.getLogger(__name__)
        self._setup_routes()

    def _trace_request(self, endpoint: str, data: dict, result: Any, duration: float):
        """Log request/response to MLflow"""
        try:
            with mlflow.start_span(name=f"{self.agent_type}_{endpoint}") as span:
                span.set_inputs(data)
                span.set_outputs({"result": result})
                span.set_attribute("agent_type", self.agent_type)
                span.set_attribute("endpoint", endpoint)
                span.set_attribute("duration_ms", duration * 1000)
        except Exception as e:
            print(f"Error logging to MLflow: {e}")

    def _validate_responses_agent_params(self, data: dict) -> bool:
        """Validate parameters for agent/v1/responses (ResponsesAgent)"""
        try:
            ResponsesAgentRequest(**data)
            return True
        except Exception as e:
            self.logger.warning(f"Invalid parameters for {self.agent_type}: {e}")
            return False

    def _validate_request_params(self, data: dict) -> bool:
        """Validate request parameters based on agent type"""
        if self.agent_type == "agent/v1/chat":
            return self._validate_chat_model_params(data)
        elif self.agent_type == "agent/v2/chat":
            return self._validate_chat_agent_params(data)
        elif self.agent_type == "agent/v1/responses":
            return self._validate_responses_agent_params(data)
        return False

    def _setup_routes(self):
        @self.app.post("/invocations")
        async def invocations_endpoint(request: Request):
            start_time = time.time()
            # TODO: return a 400 if the request is not a valid JSON
            data = await request.json()

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

            # Remove stream parameter from data before validation
            request_data = {k: v for k, v in data.items() if k != "stream"}

            # Validate request parameters based on agent type
            if not self._validate_request_params(request_data):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid parameters for {self.agent_type}. Expected format based on MLflow agent type.",
                )

            if is_streaming:
                return await self._handle_streaming_request(request_data, start_time, request)
            else:
                return await self._handle_predict_request(request_data, start_time)

    async def _handle_predict_request(self, data: dict, start_time: float):
        """Handle non-streaming predict requests"""
        # Use the single predict function
        if _predict_function is None:
            raise HTTPException(status_code=500, detail="No predict function registered")

        func = _predict_function
        func_name = func.__name__

        # Check if function is async or sync and execute with tracing
        try:
            with mlflow.start_span(name=f"{func_name}_predict") as span:
                span.set_inputs(data)
                if inspect.iscoroutinefunction(func):
                    result = await func(data)
                else:
                    result = func(data)
                span.set_outputs({"result": result})

            # Log the full request/response
            duration = time.time() - start_time
            self._trace_request("predict", data, result, duration)

            # Log response details
            response = {"result": result}
            self.logger.info(
                "Response sent",
                extra={
                    "endpoint": "predict",
                    "agent_type": self.agent_type,
                    "duration_ms": duration * 1000,
                    "response_size": len(json.dumps(response)),
                    "function_name": func_name,
                },
            )

            return response

        except Exception as e:
            duration = time.time() - start_time
            self._trace_request("predict", data, f"Error: {str(e)}", duration)

            # Log error response
            self.logger.error(
                "Error response sent",
                extra={
                    "endpoint": "predict",
                    "agent_type": self.agent_type,
                    "duration_ms": duration * 1000,
                    "error": str(e),
                    "function_name": func_name,
                },
            )

            raise HTTPException(status_code=500, detail=str(e))

    async def _handle_streaming_request(
        self, data: dict, start_time: float, request: Request = None
    ):
        """Handle streaming predict requests"""
        # Use the single predict_stream function
        if _predict_stream_function is None:
            raise HTTPException(status_code=500, detail="No predict_stream function registered")

        func = _predict_stream_function
        func_name = func.__name__

        # Collect all chunks for tracing
        all_chunks = []

        async def generate():
            nonlocal all_chunks
            try:
                with mlflow.start_span(name=f"{func_name}_predict_stream") as span:
                    span.set_inputs(data)

                    # Check if function is async or sync
                    if inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func):
                        async for chunk in func(data):
                            all_chunks.append(chunk)
                            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    else:
                        for chunk in func(data):
                            all_chunks.append(chunk)
                            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

                    span.set_outputs({"chunks": all_chunks, "total_chunks": len(all_chunks)})

                # Send [DONE] signal
                yield "data: [DONE]\n\n"

                # Log the full streaming session
                duration = time.time() - start_time
                self._trace_request("predict_stream", data, {"chunks": all_chunks}, duration)

                # Log streaming response completion
                self.logger.info(
                    "Streaming response completed",
                    extra={
                        "endpoint": "predict_stream",
                        "agent_type": self.agent_type,
                        "duration_ms": duration * 1000,
                        "total_chunks": len(all_chunks),
                        "function_name": func_name,
                    },
                )

            except Exception as e:
                duration = time.time() - start_time
                self._trace_request("predict_stream", data, f"Error: {str(e)}", duration)

                # Log streaming error
                self.logger.error(
                    "Streaming response error",
                    extra={
                        "endpoint": "predict_stream",
                        "agent_type": self.agent_type,
                        "duration_ms": duration * 1000,
                        "error": str(e),
                        "function_name": func_name,
                        "chunks_sent": len(all_chunks),
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
