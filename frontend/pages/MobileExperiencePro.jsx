import MobileProShell from "../components/MobileProShell";
import PWAInstallCard from "../components/PWAInstallCard";

export default function MobileExperiencePro() {
  return (
    <MobileProShell>
      <PWAInstallCard />

      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 12,
        marginTop: 18
      }}>
        <MobileFeature title="Picks rápidos" icon="🎯" />
        <MobileFeature title="Live Center" icon="📡" />
        <MobileFeature title="SHARK AI" icon="🦈" />
        <MobileFeature title="Analytics" icon="📊" />
      </div>

      <div style={{
        marginTop: 18,
        background: "#111827",
        borderRadius: 18,
        padding: 18,
        border: "1px solid rgba(255,255,255,0.06)"
      }}>
        <h3 style={{ marginTop: 0 }}>Push-ready</h3>
        <p style={{ opacity: 0.75 }}>
          La base queda preparada para futuras notificaciones push premium cuando conectemos el sistema de permisos y backend de alertas.
        </p>
      </div>
    </MobileProShell>
  );
}

function MobileFeature({ title, icon }) {
  return (
    <div style={{
      background: "#0f172a",
      borderRadius: 18,
      padding: 18,
      minHeight: 90,
      border: "1px solid rgba(255,255,255,0.06)"
    }}>
      <div style={{ fontSize: 28 }}>{icon}</div>
      <div style={{ fontWeight: 800, marginTop: 8 }}>{title}</div>
    </div>
  );
}
