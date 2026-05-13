
"""
Helper opcional para integrar V79 con el flujo existente de picks.

Uso recomendado cuando se crea un pick real:

from shark_ai_v79.prediction_engine import predict_pick

prediction = predict_pick({
    "pick_id": pick_id,
    "sport": sport,
    "league": league,
    "match_name": match_name,
    "market": market,
    "selection": selection,
    "odds": odds,
    "shark_score": shark_score,
})

if prediction["prediction_label"] == "RECHAZADO":
    # no enviar a Telegram / no mostrar como premium
    pass
"""

from .prediction_engine import predict_pick
