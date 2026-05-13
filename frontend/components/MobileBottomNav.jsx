const items = [
  { label: "Inicio", href: "/", icon: "🏠" },
  { label: "Picks", href: "/picks", icon: "🎯" },
  { label: "Live", href: "/live-trading", icon: "📡" },
  { label: "IA", href: "/shark-ai-ultra", icon: "🦈" },
  { label: "Cuenta", href: "/account", icon: "👤" },
];

export default function MobileBottomNav() {
  return (
    <nav style={{
      position: "fixed",
      left: 12,
      right: 12,
      bottom: 12,
      zIndex: 999,
      display: "grid",
      gridTemplateColumns: `repeat(${items.length}, 1fr)`,
      gap: 6,
      background: "rgba(7, 11, 20, 0.92)",
      backdropFilter: "blur(14px)",
      border: "1px solid rgba(255,255,255,0.08)",
      borderRadius: 22,
      padding: 8,
      boxShadow: "0 16px 40px rgba(0,0,0,0.35)"
    }}>
      {items.map((item) => (
        <a
          key={item.href}
          href={item.href}
          style={{
            color: "white",
            textDecoration: "none",
            textAlign: "center",
            fontSize: 11,
            padding: "8px 4px",
            borderRadius: 16
          }}
        >
          <div style={{ fontSize: 18 }}>{item.icon}</div>
          <div style={{ opacity: 0.78 }}>{item.label}</div>
        </a>
      ))}
    </nav>
  );
}
