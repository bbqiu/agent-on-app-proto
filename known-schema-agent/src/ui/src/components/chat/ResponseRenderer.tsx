import type { ResponseInputItem } from "../../schemas/validation";
import MessageRenderer from "./MessageRenderer";
import ToolCallRenderer from "./ToolCallRenderer";
import ToolCallOutputRenderer from "./ToolCallOutputRenderer";
import ReasoningRenderer from "./ReasoningRenderer";
import ErrorRenderer from "./ErrorRenderer";

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
          <p style={{ fontSize: "14px", color: "#6b7280" }}>
            Unknown message type
          </p>
        </div>
      );
  }
};

export default ResponseRenderer;
