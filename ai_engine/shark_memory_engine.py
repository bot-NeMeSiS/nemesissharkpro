
class SharkMemoryEngine:
    def __init__(self):
        self.memory = []

    def save_snapshot(self, snapshot):
        self.memory.append(snapshot)
