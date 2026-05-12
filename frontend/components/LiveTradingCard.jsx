export default function LiveTradingCard({ reading }) {
  if (!reading) return null;

  const signal = reading.live_signal || "NO_LIVE_ENTRY";

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
          <h2 style={{ margin: 0 }}>📡 LIVE TRADING</h2>
          <p style={{ opacity: 0.75 }}>{reading.match}</p>
        </div>
        <div style={{
          background: signal.includes("STRONG") ? "#00d084" : "#1f2937",
          color: signal.includes("STRONG") ? "#06111f" : "white",
          borderRadius: 14,
          padding: "10px 14px",
          fontWeight: 800
        }}>
          {signal}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12, marginTop: 18 }}>
        <Info label="Minuto" value={reading.minute} />
        <Info label="Marcador" value={reading.scoreline} />
        <Info label="Pick" value={reading.pick} />
        <Info label="Presión" value={reading.pressure} />
        <Info label="Cashout" value={reading.cashout_signal} />
      </div>

      <div style={{ marginTop: 18, padding: 16, background: "rgba(255,255,255,0.04)", borderRadius: 14 }}>
        <strong>Lectura trading:</strong>
        <p style={{ marginBottom: 0 }}>{reading.trading_reading}</p>
      </div>

      <div style={{ marginTop: 16 }}>
        <strong>Alertas:</strong>
        <ul>
          {(reading.alerts || []).map((alert, idx) => (
            <li key={idx}>{alert}</li>
          ))}
        </ul>
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
