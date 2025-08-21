import type {
  ResponsesAgentRequest,
  ResponsesResponse,
  ResponseOutputItem,
} from "../schemas/validation";
import {
  ResponsesResponseSchema,
  ResponsesStreamEventSchema,
} from "../schemas/validation";

export class AgentApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = "http://0.0.0.0:8000") {
    this.baseUrl = baseUrl.replace(/\/$/, ""); // Remove trailing slash
  }

  updateBaseUrl(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async sendMessage(
    request: ResponsesAgentRequest
  ): Promise<ResponsesResponse> {
    const response = await fetch(`${this.baseUrl}/invocations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    // Validate response with Zod
    try {
      return ResponsesResponseSchema.parse(data);
    } catch (validationError) {
      console.warn("Response validation failed:", validationError);
      // Return the data anyway for development
      return data as ResponsesResponse;
    }
  }

  async *streamMessage(
    request: ResponsesAgentRequest
  ): AsyncGenerator<ResponseOutputItem, void, unknown> {
    const streamRequest = { ...request, stream: true };

    const response = await fetch(`${this.baseUrl}/invocations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(streamRequest),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    if (!response.body) {
      throw new Error("No response body for streaming");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.trim() === "") continue;
          if (line === "data: [DONE]") return;

          if (line.startsWith("data: ")) {
            console.log("line", line);
            try {
              const jsonStr = line.slice(6);
              const data = JSON.parse(jsonStr);

              console.log("data", data);

              if (data.error) {
                throw new Error(data.error.message || "Stream error");
              }

              if (data) {
                // Validate the chunk
                try {
                  const validatedChunk = ResponsesStreamEventSchema.parse(data);
                  console.log("validatedChunk", validatedChunk);
                  if (validatedChunk.type === "response.output_item.done" && validatedChunk.item) {
                    yield validatedChunk.item as ResponseOutputItem;
                  } else if (validatedChunk.type === "error") {
                    yield validatedChunk as ResponseOutputItem;
                  }
                } catch (validationError) {
                  console.warn("Chunk validation failed:", validationError);
                  // Yield anyway for development
                  if (data.item) {
                    yield data.item as ResponseOutputItem;
                  }
                }
              }
            } catch (parseError) {
              console.warn("Failed to parse stream line:", line, parseError);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: "GET",
        signal: AbortSignal.timeout(5000), // 5 second timeout
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}
