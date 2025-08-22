import { useState } from "react";
import type { AgentConfig } from "../../schemas/validation";
import { X, Settings, Save } from "lucide-react";
import { Button, Input, Layout } from "@databricks/design-system";

interface ConfigPanelProps {
  config: AgentConfig;
  onConfigChange: (config: AgentConfig) => void;
  onClose: () => void;
}

const ConfigPanel = ({ config, onConfigChange, onClose }: ConfigPanelProps) => {
  const [localConfig, setLocalConfig] = useState<AgentConfig>(config);
  const [hasChanges, setHasChanges] = useState(false);

  const handleConfigChange = (field: keyof AgentConfig, value: string) => {
    const newConfig = { ...localConfig, [field]: value };
    setLocalConfig(newConfig);
    setHasChanges(newConfig.endpoint !== config.endpoint);
  };

  const handleSave = () => {
    onConfigChange(localConfig);
    setHasChanges(false);
  };

  const handleReset = () => {
    setLocalConfig(config);
    setHasChanges(false);
  };

  return (
    <Layout
      style={{ height: "100%", display: "flex", flexDirection: "column" }}
    >
      {/* Header */}
      <div
        style={{
          padding: "24px 24px 20px 24px",
          borderBottom: "1px solid #f1f5f9",
          backgroundColor: "#fafbfc",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "10px",
                backgroundColor: "#3b82f6",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Settings
                style={{ width: "20px", height: "20px", color: "white" }}
              />
            </div>
            <div>
              <h2
                style={{
                  margin: 0,
                  fontSize: "18px",
                  fontWeight: "600",
                  color: "#1e293b",
                  lineHeight: "1.4",
                }}
              >
                Settings
              </h2>
              <p
                style={{
                  margin: "4px 0 0 0",
                  fontSize: "14px",
                  color: "#64748b",
                  lineHeight: "1.4",
                }}
              >
                Configure your agent connection
              </p>
            </div>
          </div>
          <Button
            onClick={onClose}
            type="tertiary"
            componentId="close-config-button"
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              padding: 0,
              border: "1px solid #e2e8f0",
              backgroundColor: "white",
            }}
            endIcon={
              <X style={{ width: "16px", height: "16px", color: "#64748b" }} />
            }
          />
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, padding: "24px", overflowY: "auto" }}>
        <div style={{ width: "100%" }}>
          {/* Endpoint Configuration */}
          <div>
            <label
              style={{
                fontWeight: "500",
                display: "block",
                marginBottom: "8px",
                fontSize: "14px",
                color: "#374151",
              }}
            >
              API Endpoint
            </label>
            <Input
              type="url"
              value={localConfig.endpoint}
              onChange={(e) => handleConfigChange("endpoint", e.target.value)}
              placeholder="http://0.0.0.0:8000"
              componentId="endpoint-input"
              style={{
                borderRadius: "8px",
                border: "1px solid #d1d5db",
                fontSize: "14px",
                padding: "12px 16px",
              }}
            />
            <p
              style={{
                fontSize: "13px",
                marginTop: "8px",
                color: "#6b7280",
                lineHeight: "1.4",
              }}
            >
              The URL of your agent server
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      {hasChanges && (
        <div
          style={{
            padding: "20px 24px",
            borderTop: "1px solid #f1f5f9",
            backgroundColor: "#fafbfc",
          }}
        >
          <div style={{ display: "flex", gap: "12px", width: "100%" }}>
            <Button
              onClick={handleSave}
              type="primary"
              componentId="save-config-button"
              endIcon={<Save style={{ width: "16px", height: "16px" }} />}
              style={{
                flex: 1,
                borderRadius: "8px",
                padding: "12px 20px",
                fontSize: "14px",
                fontWeight: "500",
              }}
            >
              Save Changes
            </Button>
            <Button
              onClick={handleReset}
              type="tertiary"
              componentId="reset-config-button"
              style={{
                borderRadius: "8px",
                padding: "12px 20px",
                fontSize: "14px",
                fontWeight: "500",
                border: "1px solid #d1d5db",
                backgroundColor: "white",
                color: "#374151",
              }}
            >
              Reset
            </Button>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default ConfigPanel;
