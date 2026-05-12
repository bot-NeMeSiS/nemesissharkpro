
export default function ClientTopActions() {
  return (
    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
      <a href="/cliente/partidos?filtro=hoy">Partidos de hoy</a>
      <a href="/cliente/picks?estado=activos">Picks activos</a>
      <a href="/en-directo">Live</a>
      <a href="/cliente/cuenta">Mi cuenta</a>
      <a href="/logout">Cerrar sesión</a>
    </div>
  );
}
