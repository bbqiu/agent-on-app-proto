import type { ResponseErrorItem } from "../../schemas/validation";
import { AlertCircle, RefreshCw } from "lucide-react";
import { Alert, Button } from "@databricks/design-system";

interface ErrorRendererProps {
  error: ResponseErrorItem;
  onRetry?: () => void;
}

const ErrorRenderer = ({ error, onRetry }: ErrorRendererProps) => {
  return (
    <Alert
      type="error"
      message={
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <AlertCircle style={{ width: '16px', height: '16px', color: '#dc2626' }} />
            <span style={{ fontWeight: '500', fontSize: '14px', color: '#991b1b' }}>Error</span>
            <span style={{ fontSize: '12px', color: '#dc2626', backgroundColor: '#fef2f2', padding: '4px 8px', borderRadius: '4px' }}>
              {error.code}
            </span>
          </div>

          <div style={{ fontSize: '14px', color: '#b91c1c', marginBottom: '8px' }}>{error.message}</div>

          {onRetry && (
            <Button
              onClick={onRetry}
              type="tertiary"
              size="small"
              componentId="retry-button"
              endIcon={<RefreshCw style={{ width: '12px', height: '12px' }} />}
              style={{ marginTop: '8px' }}
            >
              Retry
            </Button>
          )}
        </div>
      }
      componentId="error-alert"
    />
  );
};

export default ErrorRenderer;
