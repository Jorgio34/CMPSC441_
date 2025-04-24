# main.py
class RelationshipAgent:
    def __init__(self):
        self.relationships = {}

    def interact(self, character_1, character_2, action):
        if (character_1, character_2) not in self.relationships:
            self.relationships[(character_1, character_2)] = 0  # Initial relationship level

        # Update relationship based on action
        if action == "helped during combat":
            self.relationships[(character_1, character_2)] += 10  # Increase by 10 if helped in combat
        elif action == "gifted an item":
            self.relationships[(character_1, character_2)] += 5  # Increase by 5 if gifted

        return f"❤️ Relationship improved to {self.relationships[(character_1, character_2)]}."


class TradeAgent:
    def __init__(self):
        self.transactions = {}

    def trade(self, giver, receiver, giver_inventory, receiver_inventory):
        # This is a sample trade logic
        item_to_trade = "elven blade"
        trade_value = 3  # Example trade value for gold

        if item_to_trade in giver_inventory and giver_inventory[item_to_trade] > 0:
            giver_inventory[item_to_trade] -= 1
            receiver_inventory[item_to_trade] = receiver_inventory.get(item_to_trade, 0) + 1
            giver_inventory["gold"] = giver_inventory.get("gold", 0) + trade_value
            receiver_inventory["gold"] = receiver_inventory.get("gold", 0) - trade_value

            return f"✅ Trade complete! {giver} gave {{'elven blade': 1}} and received {{'gold': 3}}."

        return f"❌ Trade failed! {giver} does not have the item to trade."


class CraftingAgent:
    def __init__(self):
        self.materials = {}

    def craft(self, character, item, materials_needed):
        # Check if the character has enough materials
        for material, quantity in materials_needed.items():
            if self.materials.get(material, 0) < quantity:
                return f"❌ {character} does not have enough {material} to craft {item}."

        # Craft the item and update materials
        for material, quantity in materials_needed.items():
            self.materials[material] -= quantity  # Subtract used materials

        # Successful crafting result
        return f"✅ {character} successfully crafted/ upgraded {item}. New stats: {{'name': '{item}', 'upgrade': '+5 Attack'}}"


def main():
    print("⚔️ AI Adventure System Starting...\n")

    # Initialize agents
    relationship_agent = RelationshipAgent()
    trade_agent = TradeAgent()
    crafting_agent = CraftingAgent()

    # Example scenario simulations

    # Relationship Scenario
    print("👫 Relationship Scenario:")
    relationship_result = relationship_agent.interact("Aria", "Thorn", "helped during combat")
    print(f"Aria helped Thorn. {relationship_result}")
    print("-" * 50)

    # Trade Scenario
    print("🏪 Trade Scenario:")
    giver_inventory = {"potion": 2, "elven blade": 1}
    receiver_inventory = {"gold": 5, "scroll": 1}

    print("Initial Inventories:")
    print(f"Aria: {giver_inventory}")
    print(f"Thorn: {receiver_inventory}")

    trade_result = trade_agent.trade("Aria", "Thorn", giver_inventory, receiver_inventory)
    print("\n📦 Trade Result:")
    print(trade_result)

    print("\nUpdated Inventories:")
    print(f"Aria: {giver_inventory}")
    print(f"Thorn: {receiver_inventory}")
    print("-" * 50)

    # Crafting Scenario
    print("⚒️ Crafting Scenario:")
    crafting_result = crafting_agent.craft("Aria", "Elven Blade", {"iron ore": 2, "elven wood": 1})
    print(f"\nCrafting Result:\n{crafting_result}")

    print("\nUpdated Materials for Aria:")
    print(crafting_agent.materials)
    print("-" * 50)

    print("✅ Scenario Simulations Complete.")


if __name__ == "__main__":
    main()
