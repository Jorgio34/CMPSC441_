#!/usr/bin/env python3
"""
D&D AI Assistant

This script runs the D&D AI Assistant, which uses AI methods to generate
content and manage scenarios for Dungeons & Dragons games.
"""

import os
import sys
import argparse
import random
from typing import Dict, List, Any

# Local imports
from utils.logger import setup_logging
from scenarios.combat_scenario import create_combat_scenario
from scenarios.quest_generation import create_quest_scenario
from knowledge.retrieval import retrieve_lore, retrieve_monster
from core.llm_integration import LLMIntegration

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="D&D AI Assistant")
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo", 
                        help="AI model to use (default: gpt-3.5-turbo)")
    parser.add_argument("--scenario", type=str, default="tavern",
                        choices=["tavern", "combat", "quest"],
                        help="Scenario to run (default: tavern)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    parser.add_argument("--interactive", action="store_true",
                        help="Run in interactive mode")
    return parser.parse_args()

def initialize_system(args):
    """Initialize the D&D AI Assistant system"""
    # Set up logging
    logger = setup_logging(debug=args.debug)
    
    # Log initialization
    logger.info(f"Initializing D&D AI Assistant with {args.model}")
    
    # Initialize LLM
    llm = LLMIntegration(model_name=args.model, api_key=os.getenv("OPENAI_API_KEY"))
    
    # Initialize game state
    game_state = {
        "party": [
            {
                "name": "Tordek",
                "class": "Fighter",
                "level": 5,
                "strength": 18,
                "dexterity": 14,
                "constitution": 16,
                "intelligence": 10,
                "wisdom": 12,
                "charisma": 8,
                "hit_points": 45,
                "max_hit_points": 45,
                "armor_class": 18,
                "weapon_damage": "1d8+4",
                "weapon_type": "longsword"
            },
            {
                "name": "Mialee",
                "class": "Wizard",
                "level": 5,
                "strength": 8,
                "dexterity": 16,
                "constitution": 14,
                "intelligence": 18,
                "wisdom": 14,
                "charisma": 12,
                "hit_points": 28,
                "max_hit_points": 28,
                "armor_class": 13,
                "weapon_damage": "1d4",
                "weapon_type": "dagger"
            }
        ],
        "location": "Neverwinter",
        "quests": [],
        "inventory": [],
        "gold": 150,
        "world_context": "A classic fantasy world with elements of magic, monsters, and adventure."
    }
    
    # Create system object with all components
    system = {
        "llm": llm,
        "game_state": game_state,
        "party": game_state["party"],
        "logger": logger
    }
    
    return system

def tavern_scenario(system, args):
    """Run a tavern scenario"""
    logger = system["logger"]
    logger.info("Running tavern scenario")
    
    # Get LLM integration
    llm = system["llm"]
    
    print("=== TAVERN SCENARIO ===")
    
    # Generate tavern description with LLM
    tavern_description = "The Dragon's Rest tavern is bustling with activity. A warm fire crackles in the hearth, casting dancing shadows across the room. The air is thick with the smell of ale, roasted meat, and pipe smoke."
    
    # Generate game master narration
    game_master_response = llm.generate_game_master_response(tavern_description, temperature=0.5)
    print("Game Master:", game_master_response)
    
    # Process player input
    player_input = "What can you tell me about any interesting jobs in the area?"
    print("Player:", player_input)
    
    # Generate NPC response
    npc_name = "Durnan"
    npc_description = "Durnan is the gruff but fair barkeeper of the tavern. He's seen it all and has connections throughout the town. He speaks directly and values courage."
    
    npc_response = llm.generate_npc_dialogue(npc_name, npc_description, player_input, temperature=0.8)
    print(f"{npc_name}:", npc_response)
    
    # Perception check for lore
    lore = retrieve_lore("The Dragon's Rest")
    print(f"Game Master (Perception Check): With your exceptionally keen awareness, you notice: {lore}")
    
    # Generate a random event
    event_prompt = "Create a brief, unexpected event that happens in the tavern - someone entering, a small commotion, or an unusual sight."
    event = llm.generate_response(event_prompt, temperature=0.8)
    print(f"Game Master (Event):", event)

def combat_scenario(system, args):
    """Run a combat scenario"""
    logger = system["logger"]
    logger.info("Running combat scenario")
    
    # Get LLM integration
    llm = system["llm"]
    
    print("=== COMBAT SCENARIO ===")
    
    # Create enemies
    enemies = ["Goblin", "Goblin Archer"]
    
    # Create combat scenario
    combat = create_combat_scenario(system["game_state"], system["party"], enemies)
    
    # Start combat
    start_message = combat.start_combat()
    print(start_message)
    
    # First player action
    player_action = "I attack the goblin with my sword"
    print(f"\nPlayer (Tordek): {player_action}")
    
    # Process turn and get result
    turn_result = combat.process_turn(player_action)
    
    # Use LLM to enhance combat narration
    enhanced_narration = llm.generate_combat_narration(turn_result, combat.get_combat_state())
    print(f"Game Master (Enhanced): {enhanced_narration}")
    
    # Process enemy turn
    enemy_turn = combat.process_turn()
    print(f"\nEnemy Turn: {enemy_turn}")
    
    # Second player action
    player2_action = "I cast Magic Missile at the goblin archer"
    print(f"\nPlayer (Mialee): {player2_action}")
    
    # Process turn
    turn_result2 = combat.process_turn(player2_action)
    
    # Enhanced narration
    enhanced_narration2 = llm.generate_combat_narration(turn_result2, combat.get_combat_state())
    print(f"Game Master (Enhanced): {enhanced_narration2}")

def quest_scenario(system, args):
    """Run a quest generation scenario"""
    logger = system["logger"]
    logger.info("Running quest generation scenario")
    
    # Get LLM integration
    llm = system["llm"]
    
    print("=== QUEST GENERATION SCENARIO ===")
    
    # Create quest scenario
    quest_location = "ancient ruins"
    quest_type = "rescue"
    difficulty = "medium"
    
    # Use LLM to generate a quest
    quest = llm.generate_quest(quest_location, quest_type, difficulty)
    
    # Display quest details
    print(f"Generated Quest: {quest['title']}\n")
    print(quest['description'])
    
    # Generate quest giver NPC dialogue
    quest_giver_name = "Elminster the Sage"
    quest_giver_description = "An elderly wizard with twinkling eyes and a long white beard. He speaks with authority and wisdom earned through decades of adventure."
    
    quest_offer = f"The sage {quest_giver_name} approaches you with an urgent quest:"
    print(f"\n{quest_offer}")
    
    quest_dialogue = llm.generate_npc_dialogue(
        quest_giver_name,
        quest_giver_description,
        f"I need brave adventurers to undertake a {difficulty} {quest_type} mission in the {quest_location}."
    )
    
    print(f"{quest_giver_name}: {quest_dialogue}")
    
    # Generate player response options
    options_prompt = f"Generate 3 different ways the players might respond to this {quest_type} quest offer, from accepting enthusiastically to being reluctant or asking for more details."
    options = llm.generate_response(options_prompt)
    
    print("\nPossible Player Responses:")
    print(options)

def main():
    """Main function"""
    # Parse arguments
    args = parse_arguments()
    
    # Initialize system
    system = initialize_system(args)
    
    # Run the requested scenario
    if args.scenario == "tavern":
        tavern_scenario(system, args)
    elif args.scenario == "combat":
        combat_scenario(system, args)
    elif args.scenario == "quest":
        quest_scenario(system, args)
    else:
        print(f"Unknown scenario: {args.scenario}")
        sys.exit(1)
    
    print("\nD&D AI Assistant session complete.")

if __name__ == "__main__":
    main()