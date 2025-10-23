import React from "react";

interface TypographyProps {
  children: React.ReactNode;
  variant?: "paragraph" | "title" | "body";
  size?: "small" | "medium" | "large";
  weight?: "normal" | "medium" | "semibold" | "bold";
  color?: string;
  style?: React.CSSProperties;
  className?: string;
}

const Typography: React.FC<TypographyProps> = ({
  children,
  variant = "paragraph",
  size = "medium",
  weight = "normal",
  color,
  style = {},
  className,
}) => {
  const getBaseStyles = (): React.CSSProperties => {
    // Base font family matching Databricks Design System
    const baseStyles: React.CSSProperties = {
      fontFamily:
        '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      margin: 0,
      lineHeight: 1.5,
    };

    // Variant-specific styles
    switch (variant) {
      case "title":
        return {
          ...baseStyles,
          fontSize:
            size === "small" ? "18px" : size === "large" ? "24px" : "20px",
          fontWeight:
            weight === "normal"
              ? "600"
              : weight === "medium"
              ? "600"
              : weight === "semibold"
              ? "700"
              : "700",
          lineHeight: 1.3,
        };
      case "body":
        return {
          ...baseStyles,
          fontSize:
            size === "small" ? "12px" : size === "large" ? "16px" : "14px",
          fontWeight:
            weight === "normal"
              ? "400"
              : weight === "medium"
              ? "500"
              : weight === "semibold"
              ? "600"
              : "700",
          color: color || "#64748b",
        };
      case "paragraph":
      default:
        return {
          ...baseStyles,
          fontSize:
            size === "small" ? "13px" : size === "large" ? "16px" : "14px",
          fontWeight:
            weight === "normal"
              ? "400"
              : weight === "medium"
              ? "500"
              : weight === "semibold"
              ? "600"
              : "700",
          color: color || "#374151",
        };
    }
  };

  const finalStyles = {
    ...getBaseStyles(),
    ...(color && { color }),
    ...style,
  };

  // Choose the appropriate HTML element based on variant
  const Component = variant === "title" ? "h3" : "p";

  return (
    <Component style={finalStyles} className={className}>
      {children}
    </Component>
  );
};

// Convenience components
export const Paragraph: React.FC<Omit<TypographyProps, "variant">> = (
  props
) => <Typography {...props} variant="paragraph" />;

export const Title: React.FC<Omit<TypographyProps, "variant">> = (props) => (
  <Typography {...props} variant="title" />
);

export const Body: React.FC<Omit<TypographyProps, "variant">> = (props) => (
  <Typography {...props} variant="body" />
);

// Alias for body (for caption-like usage)
export const Caption: React.FC<Omit<TypographyProps, "variant">> = (props) => (
  <Typography {...props} variant="body" />
);

export default Typography;
