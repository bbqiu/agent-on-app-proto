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
  itemQueue: ResponseOutputItem[];
  feed(chunk: string): void;
  reset(): void;
}

export class AgentApiClient {
  private baseUrl: string;

  constructor() {
    if (typeof window !== "undefined") {
      if (window.location.origin.includes("localhost")) {
        this.baseUrl = "http://localhost:8000";
      } else {
        this.baseUrl = window.location.origin;
      }
    } else {
      // Fallback for SSR
      this.baseUrl = "http://localhost:8000";
    }
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
                console.log(
                  "✅ Storing item for yielding:",
                  validatedChunk.item,
                  new Date().toISOString()
                );
                (parser as ExtendedParser).itemQueue.push(
                  validatedChunk.item as ResponseOutputItem
                );
              } else if (validatedChunk.type === "error") {
                // Store the error item to be yielded
                console.log("❌ Storing error for yielding:", validatedChunk);
                (parser as ExtendedParser).itemQueue.push(
                  validatedChunk as ResponseOutputItem
                );
              } else {
                console.log(
                  "⏭️ Skipping chunk (not done/error):",
                  validatedChunk.type
                );
              }
            } catch (validationError) {
              console.warn("Chunk validation failed:", validationError, data);
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

    // Initialize the item queue
    (parser as ExtendedParser).itemQueue = [];

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        parser.feed(chunk);

        // Yield all queued items
        while (parser.itemQueue.length > 0) {
          const item = parser.itemQueue.shift();
          if (item) {
            console.log("🚀 YIELDING ITEM:", item, new Date().toISOString());
            yield item;
          }
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
