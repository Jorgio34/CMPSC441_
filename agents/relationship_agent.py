# agents/relationship_agent.py

from agents.base_agent import BaseAgent

class RelationshipAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.relationships = {}

    def interact(self, player1, player2, interaction_type):
        key = tuple(sorted([player1, player2]))
        if key not in self.relationships:
            self.relationships[key] = 0

        # Example: positive interaction increases relationship
        if "help" in interaction_type.lower():
            self.relationships[key] += 10
            return f"{player1} helped {player2}. ❤️ Relationship improved to {self.relationships[key]}."
        elif "argue" in interaction_type.lower():
            self.relationships[key] -= 10
            return f"{player1} argued with {player2}. 💔 Relationship dropped to {self.relationships[key]}."
        else:
            return f"{player1} and {player2} interacted. 🤝 No major change."

    def get_relationship(self, player1, player2):
        key = tuple(sorted([player1, player2]))
        return self.relationships.get(key, 0)

    def respond(self, *args, **kwargs):
        return "Use `.interact()` to engage in relationship actions."
