import type {
  ResponsesAgentRequest,
  ResponsesResponse,
  ResponseOutputItem,
} from "../schemas/validation";
import {
  ResponsesResponseSchema,
  ResponsesStreamEventSchema,
} from "../schemas/validation";
import { createParser, type EventSourceMessage } from "eventsource-parser";

// Extend the parser type to include our custom property
interface ExtendedParser {
  lastItem?: ResponseOutputItem | null;
  feed(chunk: string): void;
  reset(): void;
}

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

    // Create the SSE parser
    const parser = createParser({
      onEvent(event: EventSourceMessage) {
        if (event.data === "[DONE]") {
          return;
        }

        try {
          const data = JSON.parse(event.data);

          if (data.error) {
            throw new Error(data.error.message || "Stream error");
          }

          if (data) {
            // Validate the chunk
            try {
              const validatedChunk = ResponsesStreamEventSchema.parse(data);
              if (
                validatedChunk.type === "response.output_item.done" &&
                validatedChunk.item
              ) {
                // Store the item to be yielded
                (parser as ExtendedParser).lastItem =
                  validatedChunk.item as ResponseOutputItem;
              } else if (validatedChunk.type === "error") {
                // Store the error item to be yielded
                (parser as ExtendedParser).lastItem =
                  validatedChunk as ResponseOutputItem;
              }
            } catch (validationError) {
              console.warn("Chunk validation failed:", validationError);
              // Store anyway for development
              if (data.item) {
                (parser as ExtendedParser).lastItem =
                  data.item as ResponseOutputItem;
              }
            }
          }
        } catch (parseError) {
          console.warn("Failed to parse SSE data:", event.data, parseError);
        }
      },
      onError(error) {
        console.error("SSE parsing error:", error);
      },
    }) as ExtendedParser;

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        parser.feed(chunk);

        // Check if we have an item to yield
        if (parser.lastItem) {
          yield parser.lastItem;
          parser.lastItem = null;
        }
      }
    } finally {
      reader.releaseLock();
      parser.reset();
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
