import LiveTradingCard from "../components/LiveTradingCard";

export default function LiveTradingCenter() {
  const sampleReading = {
    match: "Partido Real Core Live",
    minute: "LIVE",
    scoreline: "Datos reales del feed",
    pick: "Pick activo",
    pressure: "AI",
    cashout_signal: "Según señal",
    live_signal: "READY",
    alerts: [
      "Conecta esta pantalla a /api/v101/live-trading/center con partidos reales.",
      "No usa demos: interpreta datos que ya existan en Real Core."
    ],
    trading_reading: "Live Trading Center preparado para señales de entrada, value live, momentum y cashout."
  };

  return (
    <div style={{ minHeight: "100vh", background: "#070b14", color: "white", padding: 32 }}>
      <h1>📡 V101 Live Trading Center</h1>
      <p style={{ opacity: 0.75 }}>
        Centro premium para momentum live, señales de entrada, value y protección de cashout.
      </p>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        gap: 16,
        marginTop: 24,
        marginBottom: 24
      }}>
        <Metric title="Live Matches" value="Real Core" />
        <Metric title="Strong Entries" value="AI" />
        <Metric title="Value Live" value="AI" />
        <Metric title="Cashout Alerts" value="AI" />
      </div>

      <LiveTradingCard reading={sampleReading} />
    </div>
  );
}

function Metric({ title, value }) {
  return (
    <div style={{
      background: "#111827",
      borderRadius: 16,
      padding: 18,
      border: "1px solid rgba(255,255,255,0.06)"
    }}>
      <div style={{ opacity: 0.6, fontSize: 13 }}>{title}</div>
      <div style={{ fontSize: 24, fontWeight: 800 }}>{value}</div>
    </div>
  );
}
