import { useEffect, useRef } from "react";
import type { ResponseInputItem } from "../../schemas/validation";
import ResponseRenderer from "./ResponseRenderer";
import LoadingIndicator from "../common/LoadingIndicator";

interface MessageListProps {
  messages: ResponseInputItem[];
  isLoading: boolean;
}

const MessageList = ({ messages, isLoading }: MessageListProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  console.log(messages);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full text-gray-500">
          <div className="text-center">
            <div className="text-6xl mb-4">💬</div>
            <h3 className="text-lg font-medium mb-2">Start a conversation</h3>
            <p className="text-sm">
              Send a message to begin chatting with the agent
            </p>
          </div>
        </div>
      ) : (
        <>
          {messages.map((message, index) => (
            <div key={`${message.type}-${index}`} className="mb-4">
              <ResponseRenderer item={message} />
            </div>
          ))}
          {isLoading && (
            <div className="mb-4">
              <LoadingIndicator />
            </div>
          )}
        </>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
