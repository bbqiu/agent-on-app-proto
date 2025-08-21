import { Loader2 } from 'lucide-react';

interface LoadingIndicatorProps {
  message?: string;
}

const LoadingIndicator = ({ message = 'Thinking...' }: LoadingIndicatorProps) => {
  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border">
      <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
        <Loader2 className="w-4 h-4 animate-spin text-gray-600" />
      </div>
      
      <div className="flex-1">
        <div className="text-sm text-gray-600">{message}</div>
        <div className="flex gap-1 mt-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-100" />
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-200" />
        </div>
      </div>
    </div>
  );
};

export default LoadingIndicator;