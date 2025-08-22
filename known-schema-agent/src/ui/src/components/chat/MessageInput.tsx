import { useState, type KeyboardEvent } from "react";

interface MessageInputProps {
  onSendMessage: (message: string, systemPrompt?: string) => void;
  disabled?: boolean;
  defaultSystemPrompt?: string;
}

const MessageInput = ({
  onSendMessage,
  disabled = false,
  defaultSystemPrompt,
}: MessageInputProps) => {
  const [message, setMessage] = useState("");
  const [systemPrompt, setSystemPrompt] = useState(defaultSystemPrompt || "");
  const [showSystemPrompt, setShowSystemPrompt] = useState(false);

  const handleSubmit = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !disabled) {
      onSendMessage(trimmedMessage, systemPrompt.trim() || undefined);
      setMessage("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSystemPromptKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      setShowSystemPrompt(false);
    }
  };

  const handleResetSystemPrompt = () => {
    setSystemPrompt(defaultSystemPrompt || "");
  };

  const handleSaveSystemPrompt = () => {
    setShowSystemPrompt(false);
  };

  const handleCancelSystemPrompt = () => {
    setSystemPrompt(defaultSystemPrompt || "");
    setShowSystemPrompt(false);
  };

  return (
    <div
      style={{
        padding: "24px",
        borderTop: "1px solid #e5e7eb",
        backgroundColor: "white",
      }}
    >
      <div style={{ maxWidth: "800px", margin: "0 auto" }}>
        {/* System Prompt Section */}
        {showSystemPrompt && (
          <div
            style={{
              marginBottom: "16px",
              padding: "12px",
              paddingLeft: "16px",
              paddingBottom: "20px",
              backgroundColor: "#f9fafb",
              borderTopRightRadius: "8px",
              borderTopLeftRadius: "8px",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "12px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "inherit",
                  minWidth: 0,
                  whiteSpace: "nowrap",
                }}
              >
                <span
                  style={{
                    fontSize: "14px",
                    fontWeight: "500",
                    color: "#374151",
                    fontFamily: "inherit",
                  }}
                >
                  System Prompt:
                </span>
                {!showSystemPrompt && (
                  <span
                    style={{
                      color: systemPrompt ? "#6b7280" : "#9ca3af",
                      minWidth: 0,
                      fontSize: "14px",
                    }}
                  >
                    {systemPrompt || "Optionally override the system prompt."}
                  </span>
                )}
              </div>
            </div>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              onKeyDown={handleSystemPromptKeyDown}
              placeholder="Optionally override the system prompt."
              style={{
                padding: "8px 16px",
                border: "2px solid #2563eb",
                borderRadius: "8px",
                fontSize: "14px",
                backgroundColor: "white",
                resize: "none",
                fontFamily: "inherit",
                outline: "none",
              }}
            />
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: "12px",
                flexWrap: "wrap",
              }}
            >
              <button
                onClick={handleResetSystemPrompt}
                style={{
                  background: "none",
                  border: "none",
                  color: "#2563eb",
                  cursor: "pointer",
                  fontSize: "14px",
                  padding: "6px 12px",
                }}
              >
                Reset
              </button>
              <button
                onClick={handleCancelSystemPrompt}
                style={{
                  padding: "6px 12px",
                  border: "1px solid #d1d5db",
                  borderRadius: "6px",
                  backgroundColor: "white",
                  color: "#374151",
                  cursor: "pointer",
                  fontSize: "14px",
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSaveSystemPrompt}
                style={{
                  padding: "6px 12px",
                  border: "none",
                  borderRadius: "6px",
                  backgroundColor: "#2563eb",
                  color: "white",
                  cursor: "pointer",
                  fontSize: "14px",
                }}
              >
                Save
              </button>
            </div>
          </div>
        )}

        {/* Add System Prompt Button */}
        {!showSystemPrompt && (
          <div
            style={{
              marginBottom: "16px",
              padding: "12px 16px",
              backgroundColor: "white",
              borderRadius: "12px",
              border: "1px solid #e5e7eb",
              boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
            onClick={() => setShowSystemPrompt(true)}
          >
            <div
              style={{
                width: "16px",
                height: "16px",
                backgroundColor: "#2563eb",
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "white",
                fontSize: "12px",
                fontWeight: "bold",
              }}
            >
              +
            </div>
            <span style={{ color: "#2563eb", fontSize: "14px" }}>
              Add system prompt
            </span>
          </div>
        )}

        {/* Main Message Input */}
        <div
          style={{
            position: "relative",
            border: "1px solid #d1d5db",
            borderRadius: "12px",
            backgroundColor: "white",
            overflow: "hidden",
          }}
        >
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Start typing ..."
            style={{
              width: "100%",
              padding: "16px 50px 16px 16px",
              border: "none",
              outline: "none",
              fontFamily: "inherit",
              fontSize: "15px",
              lineHeight: "1.5",
              backgroundColor: "transparent",
            }}
          />

          <button
            onClick={handleSubmit}
            disabled={disabled || !message.trim()}
            style={{
              position: "absolute",
              right: "12px",
              top: "50%",
              transform: "translateY(-50%)",
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              border: "none",
              backgroundColor:
                disabled || !message.trim() ? "#f3f4f6" : "#2563eb",
              color: "white",
              cursor: disabled || !message.trim() ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "background-color 0.2s",
            }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"
                fill="currentColor"
              />
            </svg>
          </button>
        </div>

        <div
          style={{
            fontSize: "12px",
            color: "#9ca3af",
            marginTop: "12px",
            textAlign: "center",
          }}
        >
          Press Enter to send
        </div>
      </div>
    </div>
  );
};

export default MessageInput;
