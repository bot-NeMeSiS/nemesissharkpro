
export default function MembershipBadgePro({ plan = "FREE" }) {
  const normalized = normalizePlan(plan);
  const colors = {
    FREE: "#38bdf8",
    PRO: "#00d084",
    ELITE: "#fbbf24",
    ADMIN: "#a78bfa"
  };

  return (
    <span style={{
      display: "inline-flex",
      padding: "7px 12px",
      borderRadius: 999,
      border: `1px solid ${colors[normalized]}66`,
      background: `${colors[normalized]}22`,
      color: colors[normalized],
      fontWeight: 900,
      fontSize: 12,
      letterSpacing: ".04em"
    }}>
      {normalized}
    </span>
  );
}

function normalizePlan(plan) {
  const value = String(plan || "FREE").toUpperCase();
  if (value === "VIP" || value === "PREMIUM") return "PRO";
  if (["FREE", "PRO", "ELITE", "ADMIN"].includes(value)) return value;
  return "FREE";
}
