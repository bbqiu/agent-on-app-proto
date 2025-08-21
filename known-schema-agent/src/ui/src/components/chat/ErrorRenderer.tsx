import type { ResponseErrorItem } from '../../schemas/validation';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorRendererProps {
  error: ResponseErrorItem;
  onRetry?: () => void;
}

const ErrorRenderer = ({ error, onRetry }: ErrorRendererProps) => {
  return (
    <div className="p-3 rounded-lg border border-red-200 bg-red-50">
      <div className="flex items-center gap-2 mb-2">
        <AlertCircle className="w-4 h-4 text-red-600" />
        <span className="font-medium text-sm text-red-800">Error</span>
        <span className="text-xs text-red-600 bg-red-100 px-2 py-1 rounded">
          {error.code}
        </span>
      </div>
      
      <div className="text-sm text-red-700 mb-2">
        {error.message}
      </div>

      {error.details && (
        <details className="text-xs text-red-600">
          <summary className="cursor-pointer font-medium mb-1">Details</summary>
          <pre className="whitespace-pre-wrap bg-red-100 p-2 rounded border">
            {JSON.stringify(error.details, null, 2)}
          </pre>
        </details>
      )}

      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 flex items-center gap-1 px-2 py-1 text-xs bg-red-100 hover:bg-red-200 border border-red-200 rounded transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
          Retry
        </button>
      )}
    </div>
  );
};

export default ErrorRenderer;