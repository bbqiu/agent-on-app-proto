import type {
  ResponseOutputMessage,
  ResponseInputItem,
} from "../../schemas/validation";
import AgentAvatar from "../agents/AgentAvatar";
import TextRenderer from "./TextRenderer";
import CopyButton from "../common/CopyButton";
import { formatTimestamp, getTimestampFromId } from "../../utils/time";

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

export default MessageRenderer;
