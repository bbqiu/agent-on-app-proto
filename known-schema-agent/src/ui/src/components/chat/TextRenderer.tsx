import type { ResponseOutputText } from '../../schemas/validation';

interface TextRendererProps {
  content: ResponseOutputText;
  isUser?: boolean;
}

const TextRenderer = ({ content, isUser = false }: TextRendererProps) => {
  const renderTextWithAnnotations = (text: string) => {
    if (!content.annotations || content.annotations.length === 0) {
      return text;
    }

    // Sort annotations by start index
    const sortedAnnotations = [...content.annotations].sort((a, b) => a.start_index - b.start_index);
    
    const parts = [];
    let lastIndex = 0;

    sortedAnnotations.forEach((annotation, index) => {
      // Add text before annotation
      if (annotation.start_index > lastIndex) {
        parts.push(text.slice(lastIndex, annotation.start_index));
      }

      // Add annotated text
      const annotatedText = text.slice(annotation.start_index, annotation.end_index);
      
      const getAnnotationStyle = () => {
        switch (annotation.type) {
          case 'file_citation':
            return {
              backgroundColor: '#dbeafe',
              color: '#1e40af',
              border: '1px solid #93c5fd'
            };
          case 'url_citation':
            return {
              backgroundColor: '#dcfce7',
              color: '#166534',
              border: '1px solid #86efac'
            };
          default:
            return {
              backgroundColor: '#f3e8ff',
              color: '#7c3aed',
              border: '1px solid #c4b5fd'
            };
        }
      };

      parts.push(
        <span
          key={index}
          style={{
            display: 'inline-block',
            padding: '2px 4px',
            borderRadius: '4px',
            ...getAnnotationStyle()
          }}
          title={annotation.url || annotation.file_id || 'Annotation'}
        >
          {annotatedText}
        </span>
      );

      lastIndex = annotation.end_index;
    });

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }

    return parts;
  };

  // Clean up the text to remove role prefixes for display
  let displayText = content.text;
  if (displayText.startsWith('User: ')) {
    displayText = displayText.slice(6);
  } else if (displayText.startsWith('Assistant: ')) {
    displayText = displayText.slice(11);
  }

  return (
    <div style={{ fontSize: '14px', color: isUser ? 'white' : '#111827' }}>
      {renderTextWithAnnotations(displayText)}
    </div>
  );
};

export default TextRenderer;