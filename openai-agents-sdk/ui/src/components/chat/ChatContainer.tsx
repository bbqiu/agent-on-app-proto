import { useStreamingChat } from "../../hooks/useAgentApi";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import { Button, ListClearIcon } from "@databricks/design-system";
import { Title } from "../common/Typography";

const ChatContainer = () => {
  const {
    messages,
    isStreaming,
    sendStreamingMessage,
    stopStreaming,
    clearMessages,
  } = useStreamingChat();

  const handleSendMessage = async (content: string) => {
    await sendStreamingMessage(content);
  };

  const handleClearChat = () => {
    clearMessages();
  };

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <div
        style={{
          padding: "16px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid #e5e7eb",
        }}
      >
        <Title>Chat with Agent</Title>
        <Button
          onClick={handleClearChat}
          size="small"
          componentId="clear-chat-button"
          style={{
            border: "1px solid #d1d5db",
            borderRadius: "6px",
            padding: "8px",
            minWidth: "auto",
          }}
          icon={
            <ListClearIcon
              size={16}
              onPointerEnterCapture={undefined}
              onPointerLeaveCapture={undefined}
            />
          }
        />
      </div>
      <div style={{ flex: 1, overflow: "hidden" }}>
        <MessageList messages={messages} isLoading={isStreaming} />
      </div>
      <div
        style={{
          position: "sticky",
          bottom: 0,

          zIndex: 10,
        }}
      >
        <MessageInput
          onSendMessage={handleSendMessage}
          disabled={false}
          isStreaming={isStreaming}
          onStopStreaming={stopStreaming}
        />
      </div>
    </div>
  );
};

export default ChatContainer;
