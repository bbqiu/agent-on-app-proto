import type { ResponseOutputMessage, ResponseInputItem } from '../../schemas/validation';
import AgentAvatar from '../agents/AgentAvatar';
import TextRenderer from './TextRenderer';
import CopyButton from '../common/CopyButton';
import { formatTimestamp, getTimestampFromId } from '../../utils/time';

interface MessageRendererProps {
  message: ResponseInputItem;
}

const MessageRenderer = ({ message }: MessageRendererProps) => {
  // Handle both ResponseInputMessage (content: string) and ResponseOutputMessage (content: array)
  const isInputMessage = typeof (message as any).content === 'string';
  const isUser = isInputMessage 
    ? (message as any).role === 'user'
    : (message as ResponseOutputMessage).content.some(content => 
        content.text.startsWith('User:')
      );

  const timestamp = (message as any).id ? getTimestampFromId((message as any).id) : Date.now();
  const messageText = isInputMessage 
    ? (message as any).content 
    : (message as ResponseOutputMessage).content.map(c => c.text).join('\n');

  return (
    <div className={`group flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <AgentAvatar 
        role={isUser ? 'user' : 'assistant'} 
        agentId={(message as any).id || 'unknown'}
      />
      
      <div className={`flex-1 max-w-3xl ${isUser ? 'flex justify-end' : ''}`}>
        <div className={`
          p-3 rounded-lg relative
          ${isUser 
            ? 'bg-blue-500 text-white ml-12' 
            : 'bg-white border border-gray-200'
          }
        `}>
          {/* Copy button */}
          <div className={`absolute top-2 opacity-0 group-hover:opacity-100 transition-opacity ${isUser ? 'left-2' : 'right-2'}`}>
            <CopyButton text={messageText} />
          </div>

          {/* Message content */}
          {isInputMessage ? (
            <div className={`text-sm ${isUser ? 'text-white' : 'text-gray-900'}`}>
              {messageText}
            </div>
          ) : (
            (message as ResponseOutputMessage).content.map((content, index) => (
              <TextRenderer 
                key={index} 
                content={content} 
                isUser={isUser}
              />
            ))
          )}

          {/* Timestamp */}
          <div className={`text-xs mt-2 opacity-70 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
            {formatTimestamp(timestamp)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MessageRenderer;