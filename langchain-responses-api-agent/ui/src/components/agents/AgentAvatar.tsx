import { UserIcon, SparkleDoubleIcon } from "@databricks/design-system";
import { Paragraph } from "../common/Typography";

interface AgentAvatarProps {
  role: "user" | "assistant";
  agentId?: string;
  size?: "sm" | "md" | "lg";
}

const AgentAvatar = ({ role }: AgentAvatarProps) => {
  // Simple color scheme: light blue for user, light green for others
  const getAvatarColor = () => {
    return role === "user" ? "#93c5fd" : "#86efac";
  };

  const color = getAvatarColor();

  return (
    <div
      style={{
        width: "24px",
        height: "24px",
        backgroundColor: color,
        borderRadius: "4px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "white",
        flexShrink: 0,
      }}
    >
      {role === "user" ? <UserIcon onPointerEnterCapture={undefined} onPointerLeaveCapture={undefined} /> : <SparkleDoubleIcon onPointerEnterCapture={undefined} onPointerLeaveCapture={undefined} />}
    </div>
  );
};

interface AvatarLabelProps {
  role: "user" | "assistant";
}

const AvatarLabel = ({ role }: AvatarLabelProps) => {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        marginBottom: "12px",
      }}
    >
      <AgentAvatar role={role} />
      <Paragraph size="large" color="#1f2937">
        {role === "user" ? "You" : "Agent"}
      </Paragraph>
    </div>
  );
};

export default AgentAvatar;
export { AvatarLabel };
