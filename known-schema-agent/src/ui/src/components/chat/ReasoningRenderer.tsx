import { useState } from "react";
import type { ResponseReasoningItem } from "../../schemas/validation";
import { Brain, ChevronDown, ChevronRight } from "lucide-react";

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
        <Brain style={{ width: "16px", height: "16px", color: "#9333ea" }} />
        <span style={{ fontWeight: "500", fontSize: "14px", color: "#6b21a8" }}>
          Reasoning
        </span>
        {isExpanded ? (
          <ChevronDown
            style={{ width: "16px", height: "16px", color: "#9333ea" }}
          />
        ) : (
          <ChevronRight
            style={{ width: "16px", height: "16px", color: "#9333ea" }}
          />
        )}
      </button>

      <div style={{ marginTop: "8px", fontSize: "14px", color: "#7c3aed" }}>
        <div style={{ fontWeight: "500" }}>{reasoning.summary}</div>

        {isExpanded && reasoning.content && (
          <div
            style={{
              marginTop: "8px",
              padding: "8px",
              backgroundColor: "white",
              borderRadius: "4px",
              border: "1px solid #e5e7eb",
            }}
          >
            <pre
              style={{
                whiteSpace: "pre-wrap",
                fontSize: "12px",
                color: "#374151",
              }}
            >
              {reasoning.content}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReasoningRenderer;
