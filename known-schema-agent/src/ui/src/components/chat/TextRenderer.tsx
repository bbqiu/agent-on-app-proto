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
      parts.push(
        <span
          key={index}
          className={`
            inline-block px-1 rounded
            ${annotation.type === 'file_citation' 
              ? 'bg-blue-100 text-blue-800 border border-blue-200' 
              : annotation.type === 'url_citation'
              ? 'bg-green-100 text-green-800 border border-green-200'
              : 'bg-purple-100 text-purple-800 border border-purple-200'
            }
          `}
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
    <div className={`text-sm ${isUser ? 'text-white' : 'text-gray-900'}`}>
      {renderTextWithAnnotations(displayText)}
    </div>
  );
};

export default TextRenderer;