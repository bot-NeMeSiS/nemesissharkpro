import MobileBottomNav from "./MobileBottomNav";
import PWAInstallCard from "./PWAInstallCard";

export default function MobileProShell({ children }) {
  return (
    <div style={{
      minHeight: "100vh",
      background: "#070b14",
      color: "white",
      padding: "20px 16px 96px"
    }}>
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 18
      }}>
        <div>
          <div style={{ opacity: 0.6, fontSize: 12 }}>NeMeSiS</div>
          <h1 style={{ margin: 0, fontSize: 24 }}>SHARK PRO</h1>
        </div>
        <div style={{
          background: "rgba(0,208,132,0.12)",
          border: "1px solid rgba(0,208,132,0.28)",
          borderRadius: 999,
          padding: "8px 12px",
          fontSize: 12,
          fontWeight: 800
        }}>
          MOBILE PRO
        </div>
      </div>

      {children || <PWAInstallCard />}

      <MobileBottomNav />
    </div>
  );
}
