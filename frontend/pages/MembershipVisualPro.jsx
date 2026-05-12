
import MembershipPlanCardPro from "../components/MembershipPlanCardPro";

export default function MembershipVisualPro() {
  return (
    <div style={{ minHeight: "100vh", background: "#070b14", color: "white", padding: 32 }}>
      <h1>V107 Membership Visual PRO</h1>
      <p style={{ opacity: .75 }}>FREE, PRO, ELITE y ADMIN con estética unificada.</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 18, marginTop: 24 }}>
        <MembershipPlanCardPro plan="FREE" title="FREE">Azul básico para acceso inicial.</MembershipPlanCardPro>
        <MembershipPlanCardPro plan="PRO" title="PRO">Verde neón para experiencia premium.</MembershipPlanCardPro>
        <MembershipPlanCardPro plan="ELITE" title="ELITE">Dorado para máximo nivel.</MembershipPlanCardPro>
        <MembershipPlanCardPro plan="ADMIN" title="ADMIN">Morado para control interno.</MembershipPlanCardPro>
      </div>
    </div>
  );
}
