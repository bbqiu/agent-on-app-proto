import type { ResponseToolCall } from "../../schemas/validation";
import { Wrench, Clock, CheckCircle, XCircle } from "lucide-react";

interface ToolCallRendererProps {
  toolCall: ResponseToolCall;
}

const ToolCallRenderer = ({ toolCall }: ToolCallRendererProps) => {
  const getStatusIcon = () => {
    switch (toolCall.status) {
      case "pending":
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Wrench className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = () => {
    switch (toolCall.status) {
      case "pending":
        return "border-yellow-200 bg-yellow-50";
      case "completed":
        return "border-green-200 bg-green-50";
      case "failed":
        return "border-red-200 bg-red-50";
      default:
        return "border-gray-200 bg-gray-50";
    }
  };

  return (
    <div className={`p-3 rounded-lg border ${getStatusColor()}`}>
      <div className="flex items-center gap-2 mb-2">
        {getStatusIcon()}
        <span className="font-medium text-sm">Tool Call: {toolCall.name}</span>
        {toolCall.status && (
          <span className="text-xs px-2 py-1 rounded bg-white border capitalize">
            {toolCall.status}
          </span>
        )}
      </div>

      <div className="text-sm text-gray-600">
        <div className="font-medium mb-1">Arguments:</div>
        <pre className="whitespace-pre-wrap text-xs bg-white p-2 rounded border">
          {JSON.stringify(JSON.parse(toolCall.arguments), null, 2)}
        </pre>
      </div>
    </div>
  );
};

export default ToolCallRenderer;
