import { User, Bot } from 'lucide-react';

interface AgentAvatarProps {
  role: 'user' | 'assistant';
  agentId?: string;
  size?: 'sm' | 'md' | 'lg';
}

const AgentAvatar = ({ role, agentId, size = 'md' }: AgentAvatarProps) => {
  // Generate consistent colors based on agent ID
  const getAvatarColor = (id?: string) => {
    if (!id || role === 'user') {
      return role === 'user' ? 'bg-blue-500' : 'bg-green-500';
    }

    // Simple hash function for consistent colors
    let hash = 0;
    for (let i = 0; i < id.length; i++) {
      hash = ((hash << 5) - hash + id.charCodeAt(i)) & 0xffffffff;
    }

    const colors = [
      'bg-purple-500',
      'bg-pink-500',
      'bg-indigo-500',
      'bg-teal-500',
      'bg-orange-500',
      'bg-red-500',
      'bg-yellow-500',
      'bg-green-500',
    ];

    return colors[Math.abs(hash) % colors.length];
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'w-6 h-6';
      case 'lg':
        return 'w-12 h-12';
      default:
        return 'w-8 h-8';
    }
  };

  const getIconSize = () => {
    switch (size) {
      case 'sm':
        return 'w-3 h-3';
      case 'lg':
        return 'w-6 h-6';
      default:
        return 'w-4 h-4';
    }
  };

  const colorClass = getAvatarColor(agentId);

  return (
    <div className={`
      ${getSizeClasses()} 
      ${colorClass} 
      rounded-full flex items-center justify-center text-white flex-shrink-0
    `}>
      {role === 'user' ? (
        <User className={getIconSize()} />
      ) : (
        <Bot className={getIconSize()} />
      )}
    </div>
  );
};

export default AgentAvatar;