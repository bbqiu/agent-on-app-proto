import { useState } from "react";
import type {
  ResponseOutputMessage,
  ResponseInputItem,
  ResponseInputMessage,
  ResponseToolCall,
  ResponseToolCallOutput,
  ResponseReasoningItem,
  ResponseErrorItem,
} from "../../schemas/validation";
import { AvatarLabel } from "../agents/AgentAvatar";
import CopyButton from "../common/CopyButton";
import { Button } from "@databricks/design-system";
import ReadOnlyCodeBlock from "../common/ReadOnlyCodeBlock";
import { Paragraph, Body } from "../common/Typography";

// TextRenderer Component
const TextRenderer = ({ text }: { text: string }) => {
  return <Body color="inherit">{text}</Body>;
};

// ToolCallRenderer Component
interface ToolCallRendererProps {
  toolCall: ResponseToolCall;
}

const ToolCallRenderer = ({ toolCall }: ToolCallRendererProps) => {
  return (
    <div
      style={{
        marginBottom: "16px",
        padding: "0",
      }}
    >
      <ReadOnlyCodeBlock
        code={(() => {
          try {
            const args = JSON.parse(toolCall.arguments);
            return Object.entries(args)
              .map(([key, value]) => `${key} = ${JSON.stringify(value)}`)
              .join("\n");
          } catch {
            return toolCall.arguments;
          }
        })()}
        title={`system.ai.${toolCall.name}`}
      />
    </div>
  );
};

// ToolCallOutputRenderer Component
interface ToolCallOutputRendererProps {
  output: ResponseToolCallOutput;
}

const ToolCallOutputRenderer = ({ output }: ToolCallOutputRendererProps) => {
  return (
    <div style={{ marginBottom: "8px" }}>
      <ReadOnlyCodeBlock code={output.output} title="Output" />
    </div>
  );
};

// ReasoningRenderer Component
interface ReasoningRendererProps {
  reasoning: ResponseReasoningItem;
}

const ReasoningRenderer = ({ reasoning }: ReasoningRendererProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div
      style={{
        padding: "12px",
        borderRadius: "8px",
        border: "1px solid #e9d5ff",
        backgroundColor: "#faf5ff",
      }}
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          width: "100%",
          textAlign: "left",
          background: "none",
          border: "none",
          cursor: "pointer",
        }}
      >
        <span style={{ fontSize: "16px", color: "#9333ea" }}>🧠</span>
        <Paragraph weight="medium" color="#6b21a8">
          Reasoning
        </Paragraph>
        {isExpanded ? (
          <span style={{ fontSize: "16px", color: "#9333ea" }}>▼</span>
        ) : (
          <span style={{ fontSize: "16px", color: "#9333ea" }}>▶</span>
        )}
      </button>

      <div style={{ marginTop: "8px", fontSize: "14px", color: "#7c3aed" }}>
        <div style={{ fontWeight: "500" }}>{reasoning.summary}</div>

        {isExpanded && reasoning.content && (
          <div style={{ marginTop: "8px" }}>
            <ReadOnlyCodeBlock
              code={reasoning.content}
              title="Reasoning"
              showLanguageHeader={false}
              style={{
                fontSize: "12px",
                maxHeight: "200px",
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

// ErrorRenderer Component
interface ErrorRendererProps {
  error: ResponseErrorItem;
  onRetry?: () => void;
}

const ErrorRenderer = ({ error, onRetry }: ErrorRendererProps) => {
  return (
    <div
      style={{
        padding: "16px",
        backgroundColor: "#fef2f2",
        border: "1px solid #fecaca",
        borderRadius: "8px",
        display: "flex",
        alignItems: "flex-start",
        gap: "12px",
      }}
    >
      {/* Red circular icon with white exclamation mark */}
      <div
        style={{
          width: "20px",
          height: "20px",
          backgroundColor: "#dc2626",
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          marginTop: "2px",
        }}
      >
        <span style={{ color: "white", fontSize: "12px", fontWeight: "bold" }}>
          !
        </span>
      </div>

      {/* Error content */}
      <div style={{ flex: 1 }}>
        <div
          style={{
            fontSize: "14px",
            fontWeight: "600",
            color: "#991b1b",
            marginBottom: "4px",
          }}
        >
          Error
        </div>
        <div
          style={{
            fontSize: "13px",
            color: "#991b1b",
            lineHeight: "1.4",
          }}
        >
          {error.message}
        </div>
        {onRetry && (
          <Button
            onClick={onRetry}
            type="tertiary"
            size="small"
            componentId="retry-button"
            style={{ marginTop: "8px" }}
          >
            Retry
          </Button>
        )}
      </div>
    </div>
  );
};

// MessageRenderer Component
interface MessageRendererProps {
  message: ResponseInputItem;
}

const MessageRenderer = ({ message }: MessageRendererProps) => {
  // Handle both ResponseInputMessage (content: string) and ResponseOutputMessage (content: array)
  const isInputMessage =
    typeof (message as ResponseInputMessage).content === "string";
  const isUser = isInputMessage
    ? (message as ResponseInputMessage).role === "user"
    : (message as ResponseOutputMessage).content.some((content) =>
        content.text.startsWith("User:")
      );

  const messageText = isInputMessage
    ? (message as ResponseInputMessage).content
    : (message as ResponseOutputMessage).content.map((c) => c.text).join("\n");

  return (
    <div
      style={{
        marginBottom: "24px",
        position: "relative",
      }}
    >
      {/* Avatar and role label */}
      <AvatarLabel role={isUser ? "user" : "assistant"} />

      {/* Message content */}
      <div
        style={{
          fontSize: "15px",
          lineHeight: "1.6",
          color: "#111827",
        }}
      >
        {isInputMessage ? (
          <TextRenderer text={messageText} />
        ) : (
          (message as ResponseOutputMessage).content.map((content, index) => (
            <TextRenderer key={index} text={content.text} />
          ))
        )}
      </div>

      {/* Copy button */}
      <div
        style={{
          position: "absolute",
          top: "8px",
          right: "8px",
          opacity: 0,
          transition: "opacity 0.2s",
        }}
        className="group-hover:opacity-100"
      >
        <CopyButton text={messageText} />
      </div>
    </div>
  );
};

// Main ResponseRenderer Component
interface ResponseRendererProps {
  item: ResponseInputItem;
}

const ResponseRenderer = ({ item }: ResponseRendererProps) => {
  switch (item.type) {
    case "message":
      return <MessageRenderer message={item} />;
    case "function_call":
      return <ToolCallRenderer toolCall={item} />;
    case "function_call_output":
      return <ToolCallOutputRenderer output={item} />;
    case "reasoning":
      return <ReasoningRenderer reasoning={item} />;
    case "error":
      return <ErrorRenderer error={item} />;
    default:
      return (
        <div
          style={{
            padding: "12px",
            backgroundColor: "#f3f4f6",
            borderRadius: "8px",
          }}
        >
          <p
            style={{
              fontSize: "14px",
              color: "#6b7280",
              fontFamily:
                "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            }}
          >
            Unknown message type
          </p>
        </div>
      );
  }
};

export default ResponseRenderer;
export {
  TextRenderer,
  ToolCallRenderer,
  ToolCallOutputRenderer,
  ReasoningRenderer,
  ErrorRenderer,
  MessageRenderer,
};
