export default function AnalyticsMetricCard({ title, value, subtitle }) {
  return (
    <div style={{
      background: "#111827",
      border: "1px solid rgba(255,255,255,0.06)",
      borderRadius: 16,
      padding: 18,
      color: "white"
    }}>
      <div style={{ opacity: 0.6, fontSize: 13 }}>{title}</div>
      <div style={{ fontSize: 28, fontWeight: 900, marginTop: 6 }}>{value}</div>
      {subtitle && <div style={{ opacity: 0.65, fontSize: 12, marginTop: 6 }}>{subtitle}</div>}
    </div>
  );
}
