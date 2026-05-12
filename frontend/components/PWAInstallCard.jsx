import { useEffect, useState } from "react";

export default function PWAInstallCard() {
  const [promptEvent, setPromptEvent] = useState(null);
  const [installed, setInstalled] = useState(false);

  useEffect(() => {
    const onPrompt = (event) => {
      event.preventDefault();
      setPromptEvent(event);
    };

    const onInstalled = () => {
      setInstalled(true);
      setPromptEvent(null);
    };

    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);

    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  async function installApp() {
    if (!promptEvent) return;
    promptEvent.prompt();
    await promptEvent.userChoice;
    setPromptEvent(null);
  }

  return (
    <div style={{
      background: "linear-gradient(135deg, #07111f, #101827)",
      border: "1px solid rgba(0, 208, 132, 0.35)",
      borderRadius: 20,
      padding: 22,
      color: "white",
      boxShadow: "0 0 30px rgba(0, 208, 132, 0.12)"
    }}>
      <h2 style={{ marginTop: 0 }}>📲 SHARK PRO Mobile App</h2>
      <p style={{ opacity: 0.75 }}>
        Instala NeMeSiS SHARK PRO como app móvil para entrar rápido al panel, picks, live center y alertas.
      </p>

      {installed ? (
        <div style={{ padding: 12, borderRadius: 12, background: "rgba(0,208,132,0.12)" }}>
          App instalada correctamente.
        </div>
      ) : (
        <button
          onClick={installApp}
          disabled={!promptEvent}
          style={{
            marginTop: 8,
            padding: "13px 18px",
            borderRadius: 14,
            border: 0,
            background: promptEvent ? "#00d084" : "#1f2937",
            color: promptEvent ? "#06111f" : "white",
            fontWeight: 900,
            cursor: promptEvent ? "pointer" : "default"
          }}
        >
          {promptEvent ? "Instalar App" : "Disponible desde el navegador compatible"}
        </button>
      )}
    </div>
  );
}
