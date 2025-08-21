import { useState } from 'react';
import type { AgentConfig } from '../../schemas/validation';
import { X, Settings, Save } from 'lucide-react';

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
    setHasChanges(
      newConfig.endpoint !== config.endpoint || 
      newConfig.systemPrompt !== config.systemPrompt
    );
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
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-gray-600" />
            <h2 className="font-semibold text-gray-900">Configuration</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
          >
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-4 space-y-4 overflow-y-auto">
        {/* Endpoint Configuration */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            API Endpoint
          </label>
          <input
            type="url"
            value={localConfig.endpoint}
            onChange={(e) => handleConfigChange('endpoint', e.target.value)}
            placeholder="http://0.0.0.0:8000"
            className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            The URL of your agent server
          </p>
        </div>

        {/* System Prompt Configuration */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            System Prompt
          </label>
          <textarea
            value={localConfig.systemPrompt}
            onChange={(e) => handleConfigChange('systemPrompt', e.target.value)}
            placeholder="You are a helpful AI assistant..."
            rows={6}
            className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
          />
          <p className="text-xs text-gray-500 mt-1">
            Instructions that guide the agent's behavior
          </p>
        </div>

        {/* Connection Status */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Connection Status
          </label>
          <div className="p-2 bg-gray-50 rounded border">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-gray-400 rounded-full" />
              <span className="text-sm text-gray-600">Not connected</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Connection status will be checked when sending messages
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      {hasChanges && (
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
            >
              <Save className="w-4 h-4" />
              Save Changes
            </button>
            <button
              onClick={handleReset}
              className="px-3 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded transition-colors"
            >
              Reset
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConfigPanel;