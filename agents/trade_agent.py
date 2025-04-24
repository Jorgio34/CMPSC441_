# agents/trade_agent.py

from agents.base_agent import BaseAgent

class TradeAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.inventories = {}

    def set_inventory(self, player_name, items):
        self.inventories[player_name] = items

    def trade(self, from_player, to_player, offered_items, requested_items):
        if from_player not in self.inventories or to_player not in self.inventories:
            return f"❌ One of the players doesn't exist."

        from_inv = self.inventories[from_player]
        to_inv = self.inventories[to_player]

        # Check if players have the items
        for item in offered_items:
            if from_inv.get(item, 0) < offered_items[item]:
                return f"❌ {from_player} doesn't have enough {item}."

        for item in requested_items:
            if to_inv.get(item, 0) < requested_items[item]:
                return f"❌ {to_player} doesn't have enough {item}."

        # Perform trade
        for item, qty in offered_items.items():
            from_inv[item] -= qty
            to_inv[item] = to_inv.get(item, 0) + qty

        for item, qty in requested_items.items():
            to_inv[item] -= qty
            from_inv[item] = from_inv.get(item, 0) + qty

        return f"✅ Trade complete! {from_player} gave {dict(offered_items)} and received {dict(requested_items)}."

    def respond(self, *args, **kwargs):
        return "Use `.trade()` method for trading between players."
