
def build_shark_alert(match):
    return f"""
🔥 SHARK ALERT

⚽ {match.get('home')} vs {match.get('away')}

✅ PICK:
{match.get('pick')}

📊 SHARK SCORE: {match.get('score')}
💰 STAKE: {match.get('stake')}
📈 EV: {match.get('ev')}
⚠️ RISK: {match.get('risk')}

🧠 IA SHARK:
{match.get('analysis')}
"""
