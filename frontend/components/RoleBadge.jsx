export default function RoleBadge({ role }) {
  return (
    <span style={{
      padding: "6px 12px",
      borderRadius: 12,
      background: "#1f2937",
      color: "#fff"
    }}>
      {role}
    </span>
  );
}
