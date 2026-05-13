
export default function ClientAccountMenu({ plan = "PRO" }) {
  return (
    <div style={{
      background: "#0f172a",
      border: "1px solid rgba(255,255,255,.08)",
      borderRadius: 22,
      padding: 20,
      color: "white"
    }}>
      <h2>Mi cuenta</h2>
      <p>Plan actual: <strong>{plan}</strong></p>
      <a href="/cliente/cuenta">Gestionar cuenta</a>
      <br />
      <a href="/logout">Cerrar sesión</a>
    </div>
  );
}
