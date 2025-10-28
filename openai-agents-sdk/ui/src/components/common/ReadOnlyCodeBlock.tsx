import React from "react";
import { Body } from "./Typography";

interface ReadOnlyCodeBlockProps {
  code: string;
  title: string;
  showLanguageHeader?: boolean;
  style?: React.CSSProperties;
}

const ReadOnlyCodeBlock: React.FC<ReadOnlyCodeBlockProps> = ({
  code,
  title,
  showLanguageHeader = true,
  style,
}) => {
  return (
    <div
      style={{
        backgroundColor: "#f8fafc",
        border: "1px solid #e2e8f0",
        borderRadius: "8px",
        overflow: "hidden",
        ...style,
      }}
    >
      {/* Language header */}
      {showLanguageHeader && (
        <div
          style={{
            padding: "8px 12px",
            backgroundColor: "#f1f5f9",
            borderBottom: "1px solid #e2e8f0",
            fontSize: "12px",
            color: "#64748b",
            fontWeight: "500",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Body size="small">{title}</Body>
        </div>
      )}

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
          whiteSpace: "pre-wrap",
          overflow: "auto",
          maxHeight: "400px",
        }}
      >
        {code}
      </pre>
    </div>
  );
};

export default ReadOnlyCodeBlock;
