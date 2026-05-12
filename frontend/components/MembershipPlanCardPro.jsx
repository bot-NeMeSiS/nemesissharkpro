
import MembershipBadgePro from "./MembershipBadgePro";

export default function MembershipPlanCardPro({ plan = "PRO", title, children }) {
  const normalized = normalizePlan(plan);
  const colors = {
    FREE: "#38bdf8",
    PRO: "#00d084",
    ELITE: "#fbbf24",
    ADMIN: "#a78bfa"
  };

  return (
    <div style={{
      background: "#0f172a",
      border: `1px solid ${colors[normalized]}66`,
      borderRadius: 22,
      padding: 22,
      color: "white",
      boxShadow: `0 0 32px ${colors[normalized]}22`
    }}>
      <MembershipBadgePro plan={normalized} />
      <h2>{title || normalized}</h2>
      <div style={{ opacity: 0.78 }}>{children}</div>
    </div>
  );
}

function normalizePlan(plan) {
  const value = String(plan || "FREE").toUpperCase();
  if (value === "VIP" || value === "PREMIUM") return "PRO";
  if (["FREE", "PRO", "ELITE", "ADMIN"].includes(value)) return value;
  return "FREE";
}
