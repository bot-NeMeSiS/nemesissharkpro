export default function MembershipPage() {
  const plans = [
    { name: "FREE", color: "#555" },
    { name: "PRO", color: "#00d084" },
    { name: "ELITE", color: "#ffb703" },
  ];

  return (
    <div style={{ padding: 40, background: "#0b1220", minHeight: "100vh", color: "white" }}>
      <h1>NeMeSiS SHARK PRO Memberships</h1>
      <div style={{ display: "flex", gap: 20 }}>
        {plans.map((plan) => (
          <div key={plan.name} style={{
            background: "#111827",
            padding: 20,
            borderRadius: 16,
            border: `2px solid ${plan.color}`,
            width: 240
          }}>
            <h2>{plan.name}</h2>
            <p>Premium access system ready.</p>
          </div>
        ))}
      </div>
    </div>
  );
}
