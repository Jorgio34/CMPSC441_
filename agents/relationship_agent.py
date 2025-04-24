from .base_agent import BaseAgent

class RelationshipAgent(BaseAgent):
    def __init__(self):
        self.relationships = {}  # (player, npc): score

    def adjust_relationship(self, player, npc, delta):
        key = (player, npc)
        self.relationships[key] = self.relationships.get(key, 50) + delta

    def get_status(self, player, npc):
        score = self.relationships.get((player, npc), 50)
        if score >= 80:
            return "Trusted Ally"
        elif score >= 60:
            return "Friendly"
        elif score >= 40:
            return "Neutral"
        elif score >= 20:
            return "Suspicious"
        else:
            return "Hostile"

    def respond(self, input_text: str, context: dict) -> str:
        player = context.get("player")
        npc = context.get("npc")
        status = self.get_status(player, npc)
        return f"{npc} views {player} as a {status}."
