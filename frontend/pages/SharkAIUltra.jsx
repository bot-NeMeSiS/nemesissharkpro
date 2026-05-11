import { useState } from "react";
import SharkUltraCard from "../components/SharkUltraCard";

export default function SharkAIUltra() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  async function askShark() {
    const res = await fetch("/api/v100/shark-ai-ultra/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });
    const data = await res.json();
    setAnswer(data.answer);
  }

  const sampleReading = {
    match: "Partido Real Core",
    pick: "Selecciona un pick real",
    stake: "Según sistema",
    risk: "MEDIUM",
    ev: "N/A",
    shark_score: "AI",
    recommendation: "Usa la API con datos reales del feed",
    tipster_reading: "SHARK AI Ultra queda preparado para analizar picks reales del Real Core."
  };

  return (
    <div style={{ minHeight: "100vh", background: "#070b14", color: "white", padding: 32 }}>
      <h1>🦈 SHARK AI ULTRA</h1>
      <p style={{ opacity: 0.75 }}>Análisis premium tipo tipster profesional conectado al Real Core.</p>

      <div style={{ marginTop: 24, marginBottom: 24 }}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Pregunta por stake, value, riesgo, momentum..."
          style={{
            width: "70%",
            padding: 14,
            borderRadius: 12,
            border: "1px solid #1f2937",
            background: "#0f172a",
            color: "white"
          }}
        />
        <button onClick={askShark} style={{
          marginLeft: 10,
          padding: "14px 18px",
          borderRadius: 12,
          border: 0,
          background: "#00d084",
          fontWeight: 800
        }}>
          Preguntar
        </button>
      </div>

      {answer && (
        <div style={{ background: "#111827", padding: 18, borderRadius: 14, marginBottom: 24 }}>
          {answer}
        </div>
      )}

      <SharkUltraCard reading={sampleReading} />
    </div>
  );
}
