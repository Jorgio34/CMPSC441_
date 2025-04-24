# agents/crafting_agent.py

from agents.base_agent import BaseAgent

class CraftingAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.materials = {}

    def set_materials(self, player_name, materials):
        """Assign materials to a player."""
        self.materials[player_name] = materials

    def craft(self, player_name, item_name, required_materials, upgrade_value):
        """Crafts or upgrades an item using the provided materials."""
        if player_name not in self.materials:
            return f"❌ {player_name} does not have any materials."

        player_materials = self.materials[player_name]
        
        # Check if player has required materials
        for material, qty in required_materials.items():
            if player_materials.get(material, 0) < qty:
                return f"❌ {player_name} does not have enough {material}."

        # Perform crafting: consume materials and upgrade item
        for material, qty in required_materials.items():
            player_materials[material] -= qty
        
        # Craft/Upgrade the item
        item = {"name": item_name, "upgrade": upgrade_value}
        return f"✅ {player_name} successfully crafted/ upgraded {item_name}. New stats: {item}"

    def respond(self, *args, **kwargs):
        return "Use `.craft()` method to craft items."
