import type { ResponseToolCallOutput } from "../../schemas/validation";
import { Terminal } from "lucide-react";

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
        <Terminal style={{ width: "16px", height: "16px" }} />
        <span>Output</span>
      </div>

      {/* Output content */}
      <div
        style={{
          backgroundColor: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: "8px",
          overflow: "hidden",
        }}
      >
        <pre
          style={{
            margin: 0,
            padding: "16px",
            fontSize: "14px",
            lineHeight: "1.5",
            fontFamily: "Monaco, 'Cascadia Code', 'Roboto Mono', monospace",
            color: "#1e293b",
            backgroundColor: "transparent",
            whiteSpace: "pre-wrap",
            overflow: "auto",
          }}
        >
          {output.output}
        </pre>
      </div>
    </div>
  );
};

export default ToolCallOutputRenderer;
