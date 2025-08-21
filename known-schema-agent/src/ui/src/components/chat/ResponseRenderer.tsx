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
    case "tool_call":
      return <ToolCallRenderer toolCall={item} />;
    case "tool_call_output":
      return <ToolCallOutputRenderer output={item} />;
    case "reasoning":
      return <ReasoningRenderer reasoning={item} />;
    case "error":
      return <ErrorRenderer error={item} />;
    default:
      return (
        <div className="p-3 bg-gray-100 rounded-lg">
          <p className="text-sm text-gray-600">Unknown message type</p>
        </div>
      );
  }
};

export default ResponseRenderer;
