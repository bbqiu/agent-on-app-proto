import type { ResponseToolCall } from "../../schemas/validation";
import { Wrench, Clock, CheckCircle, XCircle } from "lucide-react";

interface ToolCallRendererProps {
  toolCall: ResponseToolCall;
}

const ToolCallRenderer = ({ toolCall }: ToolCallRendererProps) => {
  const getStatusIcon = () => {
    switch (toolCall.status) {
      case "pending":
        return (
          <Clock style={{ width: "16px", height: "16px", color: "#eab308" }} />
        );
      case "completed":
        return (
          <CheckCircle
            style={{ width: "16px", height: "16px", color: "#10b981" }}
          />
        );
      case "failed":
        return (
          <XCircle
            style={{ width: "16px", height: "16px", color: "#ef4444" }}
          />
        );
      default:
        return (
          <Wrench style={{ width: "16px", height: "16px", color: "#6b7280" }} />
        );
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
      <div
        style={{
          backgroundColor: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: "8px",
          overflow: "hidden",
        }}
      >
        {/* Language header */}
        <div
          style={{
            padding: "8px 12px",
            backgroundColor: "#f1f5f9",
            borderBottom: "1px solid #e2e8f0",
            fontSize: "12px",
            color: "#64748b",
            fontWeight: "500",
          }}
        >
          Python
        </div>

        {/* Code content */}
        <pre
          style={{
            margin: 0,
            padding: "16px",
            fontSize: "14px",
            lineHeight: "1.5",
            fontFamily: "Monaco, 'Cascadia Code', 'Roboto Mono', monospace",
            color: "#1e293b",
            backgroundColor: "transparent",
            overflow: "auto",
          }}
        >
          {(() => {
            try {
              const args = JSON.parse(toolCall.arguments);
              return Object.entries(args)
                .map(([key, value]) => `${key} = ${JSON.stringify(value)}`)
                .join("\n");
            } catch {
              return toolCall.arguments;
            }
          })()}
        </pre>
      </div>
    </div>
  );
};

export default ToolCallRenderer;
