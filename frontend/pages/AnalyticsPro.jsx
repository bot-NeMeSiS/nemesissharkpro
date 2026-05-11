import AnalyticsMetricCard from "../components/AnalyticsMetricCard";
import AnalyticsTable from "../components/AnalyticsTable";

export default function AnalyticsPro() {
  const sample = {
    summary: {
      total_picks: "Real Core",
      roi: "AI",
      winrate: "AI",
      profit_units: "AI",
      avg_odds: "AI",
      pending_picks: "AI"
    },
    by_sport: [],
    by_league: [],
    by_risk: [],
    by_market: []
  };

  return (
    <div style={{ minHeight: "100vh", background: "#070b14", color: "white", padding: 32 }}>
      <h1>📊 V102 Analytics PRO</h1>
      <p style={{ opacity: 0.75 }}>
        Dashboard premium de ROI, winrate, profit/loss y rendimiento por deporte, liga, riesgo y mercado.
      </p>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(6, 1fr)",
        gap: 16,
        marginTop: 24,
        marginBottom: 24
      }}>
        <AnalyticsMetricCard title="Picks" value={sample.summary.total_picks} />
        <AnalyticsMetricCard title="ROI" value={sample.summary.roi} />
        <AnalyticsMetricCard title="Winrate" value={sample.summary.winrate} />
        <AnalyticsMetricCard title="Profit" value={sample.summary.profit_units} />
        <AnalyticsMetricCard title="Avg Odds" value={sample.summary.avg_odds} />
        <AnalyticsMetricCard title="Pendientes" value={sample.summary.pending_picks} />
      </div>

      <div style={{
        background: "linear-gradient(135deg, #07111f, #101827)",
        border: "1px solid rgba(0, 208, 132, 0.35)",
        borderRadius: 18,
        padding: 22,
        marginBottom: 24
      }}>
        <h2>Equity Curve</h2>
        <p style={{ opacity: 0.75 }}>
          Conecta esta pantalla a /api/v102/analytics/dashboard con picks cerrados reales para pintar la curva.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
        <AnalyticsTable title="Rendimiento por deporte" rows={sample.by_sport} labelKey="sport" />
        <AnalyticsTable title="Rendimiento por liga" rows={sample.by_league} labelKey="league" />
        <AnalyticsTable title="Rendimiento por riesgo" rows={sample.by_risk} labelKey="risk" />
        <AnalyticsTable title="Rendimiento por mercado" rows={sample.by_market} labelKey="market" />
      </div>
    </div>
  );
}
