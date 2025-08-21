import { useState, useCallback, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { AgentApiClient } from "../api/client";
import type {
  ResponsesAgentRequest,
  ResponseOutputItem,
  ResponseInputItem,
  ResponseInputMessage,
} from "../schemas/responses";

export const useAgentApi = (endpoint: string) => {
  const clientRef = useRef(new AgentApiClient(endpoint));

  // Update client when endpoint changes
  if (clientRef.current) {
    clientRef.current.updateBaseUrl(endpoint);
  }

  const sendMessageMutation = useMutation({
    mutationFn: async (request: ResponsesAgentRequest) => {
      return clientRef.current.sendMessage(request);
    },
  });

  return {
    sendMessage: sendMessageMutation.mutateAsync,
    isLoading: sendMessageMutation.isPending,
    error: sendMessageMutation.error,
    client: clientRef.current,
  };
};

export const useStreamingChat = (endpoint: string) => {
  const [messages, setMessages] = useState<ResponseInputItem[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const clientRef = useRef(new AgentApiClient(endpoint));
  const abortControllerRef = useRef<AbortController | null>(null);

  // Update client when endpoint changes
  if (clientRef.current) {
    clientRef.current.updateBaseUrl(endpoint);
  }

  const sendStreamingMessage = useCallback(
    async (userMessage: string, systemPrompt?: string) => {
      // Cancel any ongoing stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      // Add user message to chat
      const userMessageItem: ResponseInputMessage = {
        type: "message",
        role: "user", // Display role, actual role is in the API request
        content: userMessage,
      };

      setMessages((prev) => [...prev, userMessageItem]);
      setIsStreaming(true);
      setError(null);

      try {
        const items: ResponseInputItem[] = [
          ...(systemPrompt
            ? [
                {
                  type: "message" as const,
                  role: "system" as const,
                  content: systemPrompt,
                },
              ]
            : []),
          { type: "message", role: "user", content: userMessage },
        ];

        const request: ResponsesAgentRequest = {
          input: items,
          stream: true,
        };

        const streamGenerator = clientRef.current.streamMessage(request);

        for await (const chunk of streamGenerator) {
          if (abortController.signal.aborted) {
            break;
          }

          console.log("chunk", chunk);

          setMessages((prev) => [...prev, chunk]);
        }
      } catch (err) {
        if (!abortController.signal.aborted) {
          const errorMessage =
            err instanceof Error ? err.message : "Unknown error";
          setError(errorMessage);

          const errorItem: ResponseOutputItem = {
            type: "error",
            code: "STREAM_ERROR",
            message: errorMessage,
          };

          setMessages((prev) => [...prev, errorItem]);
        }
      } finally {
        if (!abortController.signal.aborted) {
          setIsStreaming(false);
        }
        abortControllerRef.current = null;
      }
    },
    []
  );

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isStreaming,
    error,
    sendStreamingMessage,
    stopStreaming,
    clearMessages,
  };
};
