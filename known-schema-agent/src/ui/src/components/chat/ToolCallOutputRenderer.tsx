import type { ResponseToolCallOutput } from '../../schemas/validation';
import { Terminal, AlertCircle } from 'lucide-react';

interface ToolCallOutputRendererProps {
  output: ResponseToolCallOutput;
}

const ToolCallOutputRenderer = ({ output }: ToolCallOutputRendererProps) => {
  return (
    <div className="p-3 rounded-lg border border-blue-200 bg-blue-50">
      <div className="flex items-center gap-2 mb-2">
        <Terminal className="w-4 h-4 text-blue-600" />
        <span className="font-medium text-sm text-blue-800">Tool Output</span>
        <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
          {output.tool_call_id}
        </span>
      </div>
      
      <div className="text-sm">
        {output.error ? (
          <div className="bg-red-50 border border-red-200 rounded p-2">
            <div className="flex items-center gap-2 text-red-700 mb-1">
              <AlertCircle className="w-4 h-4" />
              <span className="font-medium">Error</span>
            </div>
            <pre className="whitespace-pre-wrap text-xs text-red-600">
              {output.error}
            </pre>
          </div>
        ) : (
          <pre className="whitespace-pre-wrap text-xs bg-white p-2 rounded border text-gray-700">
            {output.output}
          </pre>
        )}
      </div>
    </div>
  );
};

export default ToolCallOutputRenderer;