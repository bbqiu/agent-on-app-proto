import { useState } from 'react';
import type { ResponseReasoningItem } from '../../schemas/validation';
import { Brain, ChevronDown, ChevronRight } from 'lucide-react';

interface ReasoningRendererProps {
  reasoning: ResponseReasoningItem;
}

const ReasoningRenderer = ({ reasoning }: ReasoningRendererProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="p-3 rounded-lg border border-purple-200 bg-purple-50">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 w-full text-left"
      >
        <Brain className="w-4 h-4 text-purple-600" />
        <span className="font-medium text-sm text-purple-800">Reasoning</span>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-purple-600" />
        ) : (
          <ChevronRight className="w-4 h-4 text-purple-600" />
        )}
      </button>
      
      <div className="mt-2 text-sm text-purple-700">
        <div className="font-medium">{reasoning.summary}</div>
        
        {isExpanded && reasoning.content && (
          <div className="mt-2 p-2 bg-white rounded border">
            <pre className="whitespace-pre-wrap text-xs text-gray-700">
              {reasoning.content}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReasoningRenderer;