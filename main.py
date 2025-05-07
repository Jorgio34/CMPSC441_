"""
D&D AI Assistant - Main Entry Point

This is the main application entry point that initializes the system,
loads configurations, and provides the command-line interface.
"""

import argparse
import logging
from typing import Dict, Any

# Import core components
from config.config import load_config
from config.model_params import get_model_params
from agents.game_master import GameMasterAgent
from agents.combat_agent import CombatAgent
from agents.adventure_agent import AdventureAgent
from scenarios.tavern_encounter import create_tavern_scenario
from scenarios.combat_scenario import create_combat_scenario
from scenarios.quest_generation import create_quest_scenario
from knowledge.retrieval import initialize_knowledge_base
from utils.logger import setup_logging


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="D&D AI Assistant")
    parser.add_argument("--scenario", type=str, default="tavern",
                        choices=["tavern", "combat", "quest", "dungeon"],
                        help="Scenario to run")
    parser.add_argument("--model", type=str, default="gpt-4",
                        help="LLM model to use")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    parser.add_argument("--config", type=str, default="default",
                        help="Configuration profile to use")
    return parser.parse_args()


def initialize_system(args):
    """Initialize the system components"""
    # Setup logging and load config
    logger = setup_logging(debug=args.debug)
    logger.info(f"Initializing D&D AI Assistant with {args.model}")
    config = load_config(args.config)
    
    # Get model parameters and initialize knowledge base
    model_params = get_model_params(args.scenario, args.model)
    knowledge_base = initialize_knowledge_base(config.get("knowledge_paths", {}))
    
    # Initialize agents
    agents = {
        "game_master": GameMasterAgent(
            model_name=args.model,
            model_params=model_params.get("game_master", {}),
            knowledge_base=knowledge_base
        ),
        "combat": CombatAgent(
            model_name=args.model,
            model_params=model_params.get("combat", {}),
            knowledge_base=knowledge_base
        ),
        "adventure": AdventureAgent(
            model_name=args.model,
            model_params=model_params.get("adventure", {}),
            knowledge_base=knowledge_base
        )
    }
    
    # Return initialized components
    return {
        "logger": logger,
        "config": config,
        "knowledge_base": knowledge_base,
        "agents": agents
    }


def run_scenario(scenario_type: str, system: Dict[str, Any]):
    """Run the specified scenario"""
    logger = system["logger"]
    agents = system["agents"]
    logger.info(f"Running {scenario_type} scenario")
    
    # Run different scenarios based on type
    if scenario_type == "tavern":
        tavern = create_tavern_scenario(agents["game_master"])
        run_tavern_demo(tavern)
    
    elif scenario_type == "combat":
        combat = create_combat_scenario(agents["game_master"], agents["combat"])
        combat.run_demo_combat()
    
    elif scenario_type == "quest":
        quest = create_quest_scenario(agents["game_master"], agents["adventure"])
        agents["adventure"].run_demo_quest_generation()
    
    elif scenario_type == "dungeon":
        print("Dungeon exploration scenario coming soon!")
    
    else:
        print(f"Unknown scenario type: {scenario_type}")


def run_tavern_demo(tavern):
    """Run a demonstration of the tavern scenario"""
    print("\n=== TAVERN SCENARIO ===\n")
    
    # Enter the tavern
    description = tavern.enter_tavern()
    print(f"Game Master: {description}\n")
    
    # Interact with an NPC
    npc_name = "Durnan"
    player_query = "What can you tell me about any interesting jobs in the area?"
    response = tavern.interact_with_npc(npc_name, player_query)
    print(f"Player: {player_query}")
    print(f"{npc_name}: {response}\n")
    
    # Perception check
    perception = tavern.roll_perception_check(player_wisdom=14)
    print(f"Game Master (Perception Check): {perception}\n")
    
    # Random tavern event
    event = tavern.tavern_event()
    print(f"Game Master (Event): {event}\n")


def main():
    """Main application entry point"""
    # Parse arguments and initialize system
    args = parse_args()
    system = initialize_system(args)
    
    # Run the specified scenario
    run_scenario(args.scenario, system)
    
    print("\nD&D AI Assistant session complete.")


if __name__ == "__main__":
    main()