export default function AnalyticsTable({ title, rows, labelKey }) {
  return (
    <div style={{
      background: "#0f172a",
      border: "1px solid rgba(255,255,255,0.06)",
      borderRadius: 18,
      padding: 20,
      color: "white"
    }}>
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ opacity: 0.65, textAlign: "left" }}>
              <th>{labelKey}</th>
              <th>ROI</th>
              <th>Winrate</th>
              <th>Profit</th>
              <th>Picks</th>
            </tr>
          </thead>
          <tbody>
            {(rows || []).map((row, idx) => (
              <tr key={idx} style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                <td style={{ padding: "10px 0", fontWeight: 700 }}>{row[labelKey]}</td>
                <td>{row.roi}%</td>
                <td>{row.winrate}%</td>
                <td>{row.profit_units}u</td>
                <td>{row.total}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
