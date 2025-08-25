import { Spinner } from "@databricks/design-system";

interface LoadingIndicatorProps {
  message?: string;
}

const LoadingIndicator = ({
  message = "Generating response...",
}: LoadingIndicatorProps) => {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: "12px",
        backgroundColor: "#f9fafb",
        borderRadius: "8px",
        border: "1px solid #e5e7eb",
      }}
    >
      <div
        style={{
          width: "32px",
          height: "32px",
          backgroundColor: "#d1d5db",
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Spinner size="small" />
      </div>
      <div
        style={{
          fontSize: "14px",
          color: "#6b7280",
          fontFamily:
            "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        }}
      >
        {message}
      </div>
    </div>
  );
};

export default LoadingIndicator;
