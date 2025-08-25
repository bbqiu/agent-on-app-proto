import { Button, CopyIcon } from "@databricks/design-system";

interface CopyButtonProps {
  text: string;
}

const CopyButton = ({ text }: CopyButtonProps) => {
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      console.error("Failed to copy text:", err);
    }
  };

  return (
    <Button
      onClick={handleCopy}
      size="small"
      componentId="copy-button"
      icon={<CopyIcon size={14} />}
      title="Copy to clipboard"
      style={{ padding: "4px" }}
    />
  );
};

export default CopyButton;
