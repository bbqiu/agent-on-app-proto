import { useState, useCallback, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { AgentApiClient } from "../api/client";
import type {
  ResponsesAgentRequest,
  ResponseInputItem,
  ResponseInputMessage,
  ResponseErrorItem,
} from "../schemas/validation";

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
        role: "user",
        content: userMessage,
      };
      setIsStreaming(true);

      try {
        const request: ResponsesAgentRequest = {
          input: [
            ...(systemPrompt
              ? [
                  {
                    type: "message" as const,
                    role: "system" as const,
                    content: systemPrompt,
                  },
                ]
              : []),
            ...messages,
            userMessageItem,
          ],
          stream: true,
        };

        setMessages((prev) => [...prev, userMessageItem]);
        const streamGenerator = clientRef.current.streamMessage(request);

        for await (const chunk of streamGenerator) {
          if (abortController.signal.aborted) {
            break;
          }

          // TODO: handle parsing the chunk?
          // need a separate internal state + state that is used for rendering?
          setMessages((prev) => [...prev, chunk]);
        }
      } catch (err) {
        if (!abortController.signal.aborted) {
          const errorMessage =
            err instanceof Error ? err.message : "Unknown error";

          const errorItem: ResponseErrorItem = {
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
    [messages]
  );

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isStreaming,
    sendStreamingMessage,
    stopStreaming,
    clearMessages,
  };
};
