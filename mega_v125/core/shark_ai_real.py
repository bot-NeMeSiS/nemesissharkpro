
from datetime import datetime

def shark_answer(question, context=None):
    q = (question or "").lower().strip()
    context = context or {}

    if not q:
        answer = "Pregúntame por un pick, stake, riesgo, value, live o rendimiento."
    elif "stake" in q:
        answer = "Para stake miro SHARK Score, riesgo, cuota y EV. Si falta dato real, recomiendo bajar stake o esperar."
    elif "value" in q or "ev" in q:
        answer = "El value solo se considera cuando los datos reales apoyan la cuota. Sin datos reales, no fuerzo entrada."
    elif "live" in q or "momentum" in q:
        answer = "En live priorizo momentum, presión y cambio de cuota. Si el feed no trae eventos, la señal queda en espera."
    elif "riesgo" in q:
        answer = "Riesgo alto implica stake bajo o no entrar. SHARK no fuerza picks por intuición."
    else:
        answer = "SHARK AI usa Real Core, picks reales y contexto disponible. Si faltan datos, responde con prudencia y no inventa."

    return {
        "version": "V123_SHARK_AI_REAL",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "question": question,
        "answer": answer,
        "context_used": bool(context),
        "no_fake_policy": True
    }
