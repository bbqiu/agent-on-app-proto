import { useState } from 'react';
import { useStreamingChat } from '../../hooks/useAgentApi';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import ConfigPanel from '../config/ConfigPanel';
import type { AgentConfig } from '../../schemas/validation';

const defaultConfig: AgentConfig = {
  endpoint: 'http://0.0.0.0:8000',
  systemPrompt: 'You are a helpful AI assistant.',
};

const ChatContainer = () => {
  const [config, setConfig] = useState<AgentConfig>(defaultConfig);
  const [showConfig, setShowConfig] = useState(false);

  const {
    messages,
    isStreaming,
    error,
    sendStreamingMessage,
    stopStreaming,
    clearMessages,
  } = useStreamingChat(config.endpoint);

  const handleSendMessage = async (content: string) => {
    await sendStreamingMessage(content, config.systemPrompt);
  };

  const handleClearChat = () => {
    clearMessages();
  };

  return (
    <div className="flex h-full">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-gray-900">Agent Chat</h1>
          <div className="flex gap-2">
            <button
              onClick={handleClearChat}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            >
              Clear Chat
            </button>
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-md transition-colors"
            >
              Config
            </button>
          </div>
        </header>

        {/* Messages area */}
        <div className="flex-1 overflow-hidden">
          <MessageList messages={messages} isLoading={isStreaming} />
        </div>

        {/* Input area */}
        <div className="border-t border-gray-200 bg-white">
          <MessageInput onSendMessage={handleSendMessage} disabled={isStreaming} />
          {isStreaming && (
            <div className="px-4 pb-2">
              <button
                onClick={stopStreaming}
                className="text-sm text-red-600 hover:text-red-700 transition-colors"
              >
                Stop generating
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Config panel */}
      {showConfig && (
        <div className="w-80 border-l border-gray-200 bg-white">
          <ConfigPanel
            config={config}
            onConfigChange={setConfig}
            onClose={() => setShowConfig(false)}
          />
        </div>
      )}
    </div>
  );
};

export default ChatContainer;