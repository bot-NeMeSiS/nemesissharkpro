
LIVE_HEAT_LEVELS = ["BAJO", "MEDIO", "ALTO", "EXTREMO"]

def calcular_intensidad(ataques, tiros, corners):
    intensidad = ataques * 0.4 + tiros * 0.4 + corners * 0.2
    return min(round(intensidad), 100)

def obtener_estado_ia(intensidad):
    if intensidad >= 80:
        return "🔥 EXTREMO"
    elif intensidad >= 60:
        return "🟠 ALTO"
    elif intensidad >= 40:
        return "🟡 MEDIO"
    return "🟢 BAJO"
