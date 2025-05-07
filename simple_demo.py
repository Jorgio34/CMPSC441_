# very_simple_demo.py
import random

# Very simple dice rolling function
def roll_dice(dice_notation):
    """Simple dice roll function (e.g., '2d6' or '1d20')"""
    # For simplicity, only handle basic dice notation without modifiers
    if 'd' in dice_notation:
        parts = dice_notation.split('d')
        num_dice = int(parts[0]) if parts[0] else 1
        dice_size = int(parts[1])
        return sum(random.randint(1, dice_size) for _ in range(num_dice))
    else:
        return int(dice_notation)

# Combat demo with hardcoded values to avoid any potential issues
def demo_combat():
    print("\n===== COMBAT DEMO =====\n")
    
    # Hardcoded player and enemy data
    player = {
        "name": "Thorin",
        "hit_points": 45,
        "armor_class": 18,
        "attack_bonus": 6,
        "damage_dice": "1d8",
        "damage_bonus": 4
    }
    
    enemy = {
        "name": "Goblin Boss",
        "hit_points": 21,
        "armor_class": 15,
        "attack_bonus": 4,
        "damage_dice": "1d8",
        "damage_bonus": 2
    }
    
    print(f"Combat: {player['name']} vs. {enemy['name']}\n")
    
    # Initiative
    player_initiative = roll_dice("1d20") + 2
    enemy_initiative = roll_dice("1d20") + 2
    
    print(f"{player['name']} rolls initiative: {player_initiative}")
    print(f"{enemy['name']} rolls initiative: {enemy_initiative}\n")
    
    if player_initiative >= enemy_initiative:
        print(f"{player['name']} goes first!")
        turn_order = [player, enemy]
    else:
        print(f"{enemy['name']} goes first!")
        turn_order = [enemy, player]
    
    # Combat rounds
    round_num = 1
    while player["hit_points"] > 0 and enemy["hit_points"] > 0 and round_num <= 3:
        print(f"\nRound {round_num}")
        print("-" * 20)
        
        for attacker in turn_order:
            # Determine target
            target = enemy if attacker == player else player
            
            # Attack roll
            attack_roll = roll_dice("1d20")
            attack_total = attack_roll + attacker["attack_bonus"]
            
            print(f"{attacker['name']}'s turn. Attacking {target['name']}...")
            print(f"Attack roll: {attack_roll} + {attacker['attack_bonus']} = {attack_total}")
            
            if attack_total >= target["armor_class"]:
                # Hit
                damage_roll = roll_dice(attacker["damage_dice"])
                total_damage = damage_roll + attacker["damage_bonus"]
                target["hit_points"] -= total_damage
                
                print(f"Hit! Deals {damage_roll} + {attacker['damage_bonus']} = {total_damage} damage.")
                print(f"{target['name']} has {max(0, target['hit_points'])} HP remaining.")
                
                if target["hit_points"] <= 0:
                    print(f"{target['name']} has been defeated!")
                    break
            else:
                print(f"Miss! Attack roll of {attack_total} didn't meet AC {target['armor_class']}.")
                
            # Check if combat should end
            if player["hit_points"] <= 0 or enemy["hit_points"] <= 0:
                break
        
        round_num += 1
    
    # Combat results
    if player["hit_points"] <= 0:
        print("\nDefeat! You have been defeated by the enemy.")
    elif enemy["hit_points"] <= 0:
        print("\nVictory! You have defeated the enemy.")
    else:
        print("\nDemo combat completed after 3 rounds.")

# Quest generation demo
def demo_quest_generation():
    print("\n===== QUEST GENERATION DEMO =====\n")
    
    # Predefined quest templates
    quest_templates = [
        {
            "name": "The Missing Villager",
            "type": "Rescue",
            "difficulty": "Easy",
            "location": "Dark Forest",
            "objective": "Rescue the missing villager who was kidnapped by goblins",
            "challenges": ["Goblin patrols", "Forest maze"],
            "rewards": {
                "gold": 100,
                "items": ["Potion of Healing"]
            }
        },
        {
            "name": "The Lost Artifact",
            "type": "Fetch",
            "difficulty": "Medium",
            "location": "Ancient Ruins",
            "objective": "Retrieve the magical artifact from the ruins",
            "challenges": ["Ancient traps", "Guardian constructs"],
            "rewards": {
                "gold": 250,
                "items": ["Ring of Protection"]
            }
        },
        {
            "name": "Dragon's Lair",
            "type": "Kill",
            "difficulty": "Hard",
            "location": "Mountain Caves",
            "objective": "Slay the young dragon threatening the village",
            "challenges": ["Dragon's flame breath", "Narrow passages"],
            "rewards": {
                "gold": 1000,
                "items": ["Flametongue Sword"]
            }
        }
    ]
    
    # Select a random quest
    quest = random.choice(quest_templates)
    
    # Print quest details
    print(f"QUEST: {quest['name']}")
    print(f"TYPE: {quest['type']}")
    print(f"DIFFICULTY: {quest['difficulty']}")
    print(f"LOCATION: {quest['location']}")
    print(f"\nOBJECTIVE: {quest['objective']}")
    
    print("\nCHALLENGES:")
    for challenge in quest['challenges']:
        print(f"- {challenge}")
    
    print("\nREWARDS:")
    print(f"- {quest['rewards']['gold']} gold pieces")
    for item in quest['rewards']['items']:
        print(f"- {item}")

# Main demo function
def main():
    print("==================================")
    print("D&D AI ASSISTANT DEMONSTRATION")
    print("==================================")
    
    print("\nThis demo showcases the key functionalities of the D&D AI Assistant:")
    print("1. Combat Management")
    print("2. Quest Generation")
    
    while True:
        choice = input("\nSelect a demo to run (1-2) or 'q' to quit: ")
        
        if choice == '1':
            demo_combat()
        elif choice == '2':
            demo_quest_generation()
        elif choice.lower() == 'q':
            print("\nThank you for trying the D&D AI Assistant!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()