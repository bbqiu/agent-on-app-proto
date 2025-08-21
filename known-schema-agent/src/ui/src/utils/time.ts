export const formatTimestamp = (timestamp: number | Date): string => {
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMinutes < 1) {
    return 'Just now';
  } else if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays < 7) {
    return `${diffDays}d ago`;
  } else {
    return date.toLocaleDateString();
  }
};

export const getTimestampFromId = (id: string): number => {
  // Extract timestamp from IDs like "user-1234567890" or "assistant-1234567890"
  const parts = id.split('-');
  const timestamp = parseInt(parts[parts.length - 1]);
  return isNaN(timestamp) ? Date.now() : timestamp;
};