from backend.core.shark_ai_ultra_engine import build_shark_ultra_reading, build_chat_answer

class SharkAIUltraService:
    def analyze(self, match):
        return build_shark_ultra_reading(match)

    def chat(self, question, context=None):
        return build_chat_answer(question, context)
