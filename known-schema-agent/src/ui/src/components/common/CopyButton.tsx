import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { Button } from '@databricks/design-system';

interface CopyButtonProps {
  text: string;
}

const CopyButton = ({ text }: CopyButtonProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  return (
    <Button
      onClick={handleCopy}
      type="tertiary"
      size="small"
      componentId="copy-button"
      endIcon={copied ? <Check style={{ width: '16px', height: '16px', color: '#10b981' }} /> : <Copy style={{ width: '16px', height: '16px', color: '#6b7280' }} />}
      title="Copy to clipboard"
      style={{ padding: '4px' }}
    />
  );
};

export default CopyButton;