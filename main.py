# main.py

from agents.relationship_agent import RelationshipAgent
from agents.trade_agent import TradeAgent
from agents.crafting_agent import CraftingAgent

def main():
    print("⚔️ AI Adventure System Starting...\n")

    # === Relationship Scenario ===
    relationship_agent = RelationshipAgent()
    print("👫 Relationship Scenario:")
    response = relationship_agent.interact("Aria", "Thorn", "helped during combat")
    print(response)
    print("-" * 50)

    # === Trade Scenario ===
    trade_agent = TradeAgent()
    print("🏪 Trade Scenario:")

    trade_agent.set_inventory("Aria", {"potion": 2, "elven blade": 1})
    trade_agent.set_inventory("Thorn", {"gold": 5, "scroll": 1})

    print("Initial Inventories:")
    print("Aria:", trade_agent.inventories["Aria"])
    print("Thorn:", trade_agent.inventories["Thorn"])

    result = trade_agent.trade(
        from_player="Aria",
        to_player="Thorn",
        offered_items={"elven blade": 1},
        requested_items={"gold": 3}
    )

    print("\n📦 Trade Result:")
    print(result)

    print("\nUpdated Inventories:")
    print("Aria:", trade_agent.inventories["Aria"])
    print("Thorn:", trade_agent.inventories["Thorn"])
    print("-" * 50)

    # === Crafting Scenario ===
    crafting_agent = CraftingAgent()
    print("⚒️ Crafting Scenario:")

    crafting_agent.set_materials("Aria", {"iron ore": 5, "elven wood": 2})
    crafting_agent.set_materials("Thorn", {"gold nugget": 3})

    # Try to craft an upgrade for a sword
    result = crafting_agent.craft(
        player_name="Aria",
        item_name="Elven Blade",
        required_materials={"iron ore": 3, "elven wood": 1},
        upgrade_value="+5 Attack"
    )

    print("\nCrafting Result:")
    print(result)

    print("\nUpdated Materials for Aria:")
    print(crafting_agent.materials["Aria"])

    print("\n✅ Scenario Simulations Complete.")

if __name__ == "__main__":
    main()
