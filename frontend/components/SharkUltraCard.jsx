export default function SharkUltraCard({ reading }) {
  if (!reading) return null;

  return (
    <div style={{
      background: "linear-gradient(135deg, #07111f, #101827)",
      border: "1px solid rgba(0, 208, 132, 0.35)",
      borderRadius: 18,
      padding: 22,
      color: "white",
      boxShadow: "0 0 30px rgba(0, 208, 132, 0.12)"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
        <div>
          <h2 style={{ margin: 0 }}>🦈 SHARK AI ULTRA</h2>
          <p style={{ opacity: 0.75 }}>{reading.match}</p>
        </div>
        <div style={{
          background: "#00d084",
          color: "#06111f",
          borderRadius: 14,
          padding: "10px 14px",
          fontWeight: 800
        }}>
          {reading.shark_score}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginTop: 18 }}>
        <Info label="Pick" value={reading.pick} />
        <Info label="Stake" value={reading.stake} />
        <Info label="Riesgo" value={reading.risk} />
        <Info label="EV" value={reading.ev} />
      </div>

      <div style={{ marginTop: 18, padding: 16, background: "rgba(255,255,255,0.04)", borderRadius: 14 }}>
        <strong>Recomendación:</strong>
        <p style={{ marginBottom: 0 }}>{reading.recommendation}</p>
      </div>

      <div style={{ marginTop: 16 }}>
        <strong>Lectura tipster:</strong>
        <p style={{ opacity: 0.85 }}>{reading.tipster_reading}</p>
      </div>
    </div>
  );
}

function Info({ label, value }) {
  return (
    <div style={{ background: "rgba(255,255,255,0.05)", borderRadius: 12, padding: 12 }}>
      <div style={{ fontSize: 12, opacity: 0.6 }}>{label}</div>
      <div style={{ fontWeight: 700 }}>{value || "N/A"}</div>
    </div>
  );
}
