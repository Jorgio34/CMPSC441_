from agents.relationship_agent import RelationshipAgent

def main():
    agent = RelationshipAgent()

    print("📜 Welcome to the AI Adventure!")
    player = "Aria"
    npc = "Thorn the Ranger"

    # Simulate an action
    print(agent.respond("", {"player": player, "npc": npc}))
    agent.adjust_relationship(player, npc, 15)
    print(agent.respond("", {"player": player, "npc": npc}))
    agent.adjust_relationship(player, npc, -40)
    print(agent.respond("", {"player": player, "npc": npc}))

if __name__ == "__main__":
    main()