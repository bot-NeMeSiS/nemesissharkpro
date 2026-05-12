
window.NEMESIS_MEMBERSHIP_THEME = {
  FREE: { color: "#38bdf8", className: "badge-free" },
  PRO: { color: "#00d084", className: "badge-pro" },
  ELITE: { color: "#fbbf24", className: "badge-elite" },
  ADMIN: { color: "#a78bfa", className: "badge-admin" }
};

window.normalizeMembershipPlan = function(plan){
  const value = String(plan || "FREE").toUpperCase();
  if(value === "VIP" || value === "PREMIUM") return "PRO";
  if(["FREE","PRO","ELITE","ADMIN"].includes(value)) return value;
  return "FREE";
};

window.applyMembershipBadge = function(el, plan){
  if(!el) return;
  const normalized = window.normalizeMembershipPlan(plan);
  el.classList.add("membership-badge", "badge-" + normalized.toLowerCase());
  el.textContent = normalized;
};
