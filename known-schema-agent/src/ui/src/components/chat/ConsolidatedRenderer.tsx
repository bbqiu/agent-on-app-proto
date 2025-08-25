import { useState } from "react";
import type {
  ResponseOutputMessage,
  ResponseInputItem,
  ResponseOutputText,
  ResponseToolCall,
  ResponseToolCallOutput,
  ResponseReasoningItem,
  ResponseErrorItem,
} from "../../schemas/validation";
import AgentAvatar from "../agents/AgentAvatar";
import CopyButton from "../common/CopyButton";
import { formatTimestamp, getTimestampFromId } from "../../utils/time";
import { Button, CheckIcon, WrenchIcon } from "@databricks/design-system";
import ReadOnlyCodeBlock from "../common/ReadOnlyCodeBlock";

// TextRenderer Component
interface TextRendererProps {
  content: ResponseOutputText;
  isUser?: boolean;
}

const TextRenderer = ({ content, isUser = false }: TextRendererProps) => {
  const renderTextWithAnnotations = (text: string) => {
    if (!content.annotations || content.annotations.length === 0) {
      return text;
    }

    // Sort annotations by start index
    const sortedAnnotations = [...content.annotations].sort(
      (a, b) => a.start_index - b.start_index
    );

    const parts = [];
    let lastIndex = 0;

    sortedAnnotations.forEach((annotation, index) => {
      // Add text before annotation
      if (annotation.start_index > lastIndex) {
        parts.push(text.slice(lastIndex, annotation.start_index));
      }

      // Add annotated text
      const annotatedText = text.slice(
        annotation.start_index,
        annotation.end_index
      );

      const getAnnotationStyle = () => {
        switch (annotation.type) {
          case "file_citation":
            return {
              backgroundColor: "#dbeafe",
              color: "#1e40af",
              border: "1px solid #93c5fd",
            };
          case "url_citation":
            return {
              backgroundColor: "#dcfce7",
              color: "#166534",
              border: "1px solid #86efac",
            };
          default:
            return {
              backgroundColor: "#f3e8ff",
              color: "#7c3aed",
              border: "1px solid #c4b5fd",
            };
        }
      };

      parts.push(
        <span
          key={index}
          style={{
            display: "inline-block",
            padding: "2px 4px",
            borderRadius: "4px",
            ...getAnnotationStyle(),
          }}
          title={annotation.url || annotation.file_id || "Annotation"}
        >
          {annotatedText}
        </span>
      );

      lastIndex = annotation.end_index;
    });

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }

    return parts;
  };

  // Clean up the text to remove role prefixes for display
  let displayText = content.text;
  if (displayText.startsWith("User: ")) {
    displayText = displayText.slice(6);
  } else if (displayText.startsWith("Assistant: ")) {
    displayText = displayText.slice(11);
  }

  return (
    <div
      style={{
        fontSize: "14px",
        lineHeight: "1.5",
        color: isUser ? "white" : "#111827",
        fontFamily:
          "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        fontWeight: "400",
      }}
    >
      {renderTextWithAnnotations(displayText)}
    </div>
  );
};

// ToolCallRenderer Component
interface ToolCallRendererProps {
  toolCall: ResponseToolCall;
}

const ToolCallRenderer = ({ toolCall }: ToolCallRendererProps) => {
  const getStatusIcon = () => {
    switch (toolCall.status) {
      case "pending":
        return <WrenchIcon width={16} height={16} color="warning" />;
      case "completed":
        return <CheckIcon width={16} height={16} color="success" />;
      case "failed":
        return <span style={{ color: "#ef4444", fontSize: "16px" }}>✗</span>;
      default:
        return <WrenchIcon width={16} height={16} color="warning" />;
    }
  };

  return (
    <div
      style={{
        marginBottom: "16px",
        padding: "0",
      }}
    >
      {/* Tool call header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          marginBottom: "12px",
          fontSize: "14px",
          color: "#6b7280",
        }}
      >
        {getStatusIcon()}
        <span
          style={{
            fontFamily: "Monaco, 'Cascadia Code', 'Roboto Mono', monospace",
          }}
        >
          system.ai.{toolCall.name}
        </span>
        {toolCall.status && (
          <span
            style={{
              fontSize: "12px",
              padding: "2px 6px",
              borderRadius: "3px",
              backgroundColor: "#f3f4f6",
              color: "#6b7280",
              textTransform: "capitalize",
            }}
          >
            {toolCall.status}
          </span>
        )}
      </div>

      {/* Code block */}
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
        language="Python"
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
    <div
      style={{
        marginBottom: "16px",
      }}
    >
      {/* Output header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          marginBottom: "12px",
          fontSize: "14px",
          color: "#6b7280",
        }}
      >
        <span style={{ fontSize: "16px" }}>⚡</span>
        <span>Output</span>
      </div>

      {/* Output content */}
      <ReadOnlyCodeBlock
        code={output.output}
        language="Output"
        title="Tool Result"
      />
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
        <span style={{ fontWeight: "500", fontSize: "14px", color: "#6b21a8" }}>
          Reasoning
        </span>
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
              language="Reasoning"
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
  const isInputMessage = typeof (message as any).content === "string";
  const isUser = isInputMessage
    ? (message as any).role === "user"
    : (message as ResponseOutputMessage).content.some((content) =>
        content.text.startsWith("User:")
      );

  const timestamp = (message as any).id
    ? getTimestampFromId((message as any).id)
    : Date.now();
  const messageText = isInputMessage
    ? (message as any).content
    : (message as ResponseOutputMessage).content.map((c) => c.text).join("\n");

  return (
    <div
      style={{
        display: "flex",
        gap: "16px",
        marginBottom: "24px",
        position: "relative",
      }}
    >
      <div style={{ flexShrink: 0 }}>
        <AgentAvatar
          role={isUser ? "user" : "assistant"}
          agentId={(message as any).id || "unknown"}
          size="md"
        />
      </div>

      <div
        style={{
          flex: 1,
          minWidth: 0,
        }}
      >
        {/* Role label */}
        <div
          style={{
            fontSize: "14px",
            fontWeight: "600",
            color: "#374151",
            marginBottom: "8px",
          }}
        >
          {isUser ? "You" : "Agent"}
        </div>

        {/* Message content */}
        <div
          style={{
            fontSize: "15px",
            lineHeight: "1.6",
            color: "#111827",
          }}
        >
          {isInputMessage ? (
            <div>{messageText}</div>
          ) : (
            (message as ResponseOutputMessage).content.map((content, index) => (
              <TextRenderer key={index} content={content} isUser={false} />
            ))
          )}
        </div>

        {/* Timestamp */}
        <div
          style={{
            fontSize: "12px",
            marginTop: "12px",
            color: "#9ca3af",
          }}
        >
          {formatTimestamp(timestamp)}
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
