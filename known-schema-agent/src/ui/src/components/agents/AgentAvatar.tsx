import { UserIcon, SparkleDoubleIcon } from "@databricks/design-system";

interface AgentAvatarProps {
  role: "user" | "assistant";
  agentId?: string;
  size?: "sm" | "md" | "lg";
}

const AgentAvatar = ({ role, agentId, size = "md" }: AgentAvatarProps) => {
  // Generate consistent colors based on agent ID
  const getAvatarColor = (id?: string) => {
    if (!id || role === "user") {
      return role === "user" ? "#3b82f6" : "#10b981";
    }

    // Simple hash function for consistent colors
    let hash = 0;
    for (let i = 0; i < id.length; i++) {
      hash = ((hash << 5) - hash + id.charCodeAt(i)) & 0xffffffff;
    }

    const colors = [
      "#8b5cf6",
      "#ec4899",
      "#6366f1",
      "#14b8a6",
      "#f97316",
      "#ef4444",
      "#eab308",
      "#10b981",
    ];

    return colors[Math.abs(hash) % colors.length];
  };

  const getSize = () => {
    switch (size) {
      case "sm":
        return 24;
      case "lg":
        return 48;
      default:
        return 32;
    }
  };

  const color = getAvatarColor(agentId);
  const sizePx = getSize();

  return (
    <div
      style={{
        width: sizePx,
        height: sizePx,
        backgroundColor: color,
        borderRadius: "50%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "white",
        flexShrink: 0,
      }}
    >
      {role === "user" ? <UserIcon /> : <SparkleDoubleIcon />}
    </div>
  );
};

export default AgentAvatar;
