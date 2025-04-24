# agents/combat_agent.py

import random
from agents.base_agent import BaseAgent

class CombatAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.players = {}

    def add_player(self, player_name, health, attack_power):
        """Add a player with health and attack power."""
        self.players[player_name] = {"health": health, "attack_power": attack_power}

    def attack(self, attacker, defender):
        """Simulate an attack between two players."""
        if attacker not in self.players or defender not in self.players:
            return "❌ Both players must be added first."

        attack_roll = random.randint(1, 20) + self.players[attacker]["attack_power"]
        print(f"{attacker} rolls: {attack_roll}")

        if attack_roll >= 15:  # Attack hits if the roll is 15 or greater
            damage = random.randint(5, 10)  # Random damage between 5 and 10
            self.players[defender]["health"] -= damage
            return f"✅ {attacker} hit {defender} for {damage} damage. {defender} has {self.players[defender]['health']} health left."
        else:
            return f"❌ {attacker} missed the attack."

    def respond(self, *args, **kwargs):
        return "Use `.attack()` method to attack another player."
