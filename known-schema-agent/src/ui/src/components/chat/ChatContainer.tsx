import { useState } from "react";
import { useStreamingChat } from "../../hooks/useAgentApi";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import ConfigPanel from "../config/ConfigPanel";
import type { AgentConfig } from "../../schemas/validation";
import { Button, Layout } from "@databricks/design-system";
import { Settings2, Trash2 } from "lucide-react";

const defaultConfig: AgentConfig = {
  endpoint: "http://0.0.0.0:8000",
  systemPrompt: undefined,
};

// Modal component for settings
const SettingsModal = ({
  isOpen,
  onClose,
  config,
  onConfigChange,
}: {
  isOpen: boolean;
  onClose: () => void;
  config: AgentConfig;
  onConfigChange: (config: AgentConfig) => void;
}) => {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.6)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        backdropFilter: "blur(4px)",
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: "white",
          borderRadius: "16px",
          width: "90%",
          maxWidth: "480px",
          maxHeight: "85vh",
          overflow: "hidden",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
          border: "1px solid rgba(0, 0, 0, 0.05)",
          animation: "modalSlideIn 0.2s ease-out",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <style>
          {`
            @keyframes modalSlideIn {
              from {
                opacity: 0;
                transform: scale(0.95) translateY(-10px);
              }
              to {
                opacity: 1;
                transform: scale(1) translateY(0);
              }
            }
          `}
        </style>
        <ConfigPanel
          config={config}
          onConfigChange={onConfigChange}
          onClose={onClose}
        />
      </div>
    </div>
  );
};

const ChatContainer = () => {
  const [config, setConfig] = useState<AgentConfig>(defaultConfig);
  const [showConfig, setShowConfig] = useState(false);

  const {
    messages,
    isStreaming,
    sendStreamingMessage,
    stopStreaming,
    clearMessages,
  } = useStreamingChat(config.endpoint);

  const handleSendMessage = async (content: string, systemPrompt?: string) => {
    await sendStreamingMessage(content, systemPrompt || config.systemPrompt);
  };

  const handleClearChat = () => {
    clearMessages();
  };

  return (
    <Layout style={{ height: "100%" }}>
      {/* Main chat area */}
      <Layout.Content style={{ display: "flex", flexDirection: "column" }}>
        {/* Header */}
        <Layout.Header
          style={{
            padding: "16px 24px",
            borderBottom: "1px solid #e5e7eb",
            backgroundColor: "white",
            height: "64px",
            display: "flex",
            alignItems: "center",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              width: "100%",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              <h1
                style={{
                  fontSize: "20px",
                  fontWeight: "600",
                  margin: 0,
                  color: "#1f2937",
                }}
              >
                Playground
              </h1>
            </div>
            <div style={{ display: "flex", gap: "16px" }}>
              <Button
                onClick={() => setShowConfig(true)}
                type="tertiary"
                size="small"
                componentId="settings-button"
                style={{
                  border: "1px solid #d1d5db",
                  borderRadius: "6px",
                  padding: "8px",
                  minWidth: "auto",
                }}
              >
                <Settings2 style={{ width: "16px", height: "16px" }} />
              </Button>
              <Button
                onClick={handleClearChat}
                type="tertiary"
                size="small"
                componentId="clear-chat-button"
                style={{
                  border: "1px solid #d1d5db",
                  borderRadius: "6px",
                  padding: "8px",
                  minWidth: "auto",
                }}
              >
                <Trash2 style={{ width: "16px", height: "16px" }} />
              </Button>
            </div>
          </div>
        </Layout.Header>

        {/* Messages area */}
        <div style={{ flex: 1, overflow: "hidden" }}>
          <MessageList messages={messages} isLoading={isStreaming} />
        </div>

        {/* Input area */}
        <div style={{ backgroundColor: "white" }}>
          <MessageInput
            onSendMessage={handleSendMessage}
            disabled={isStreaming}
            defaultSystemPrompt={config.systemPrompt}
          />
          {isStreaming && (
            <div
              style={{
                maxWidth: "800px",
                margin: "0 auto",
                padding: "0 24px 16px",
              }}
            >
              <Button
                onClick={stopStreaming}
                type="link"
                size="small"
                componentId="stop-generating-button"
                style={{ color: "#dc2626" }}
              >
                Stop generating
              </Button>
            </div>
          )}
        </div>
      </Layout.Content>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showConfig}
        onClose={() => setShowConfig(false)}
        config={config}
        onConfigChange={setConfig}
      />
    </Layout>
  );
};

export default ChatContainer;
