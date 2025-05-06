"""
D&D AI Assistant - Main Entry Point

This is the main application entry point that initializes the system,
loads configurations, and provides the command-line interface.
"""

import os
import argparse
import logging
from typing import Dict, Any, List, Optional

# Import core components
from config.config import load_config
from config.model_params import get_model_params # type: ignore
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
                        choices=["tavern", "combat", "quest", "dungeon", "npc"],
                        help="Scenario to run")
    parser.add_argument("--model", type=str, default="gpt-4",
                        help="LLM model to use")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    parser.add_argument("--config", type=str, default="default",
                        help="Configuration profile to use")
    return parser.parse_args()


def initialize_system(args) -> Dict[str, Any]:
    """Initialize the system components"""
    # Setup logging
    logger = setup_logging(debug=args.debug)
    logger.info(f"Initializing D&D AI Assistant with {args.model}")
    
    # Load configuration
    config = load_config(args.config)
    
    # Get model parameters based on scenario
    model_params = get_model_params(args.scenario, args.model)
    
    # Initialize knowledge base
    knowledge_base = initialize_knowledge_base(config.get("knowledge_paths", {}))
    
    # Initialize agents
    game_master = GameMasterAgent(
        model_name=args.model,
        model_params=model_params.get("game_master", {}),
        knowledge_base=knowledge_base
    )
    
    combat_agent = CombatAgent(
        model_name=args.model,
        model_params=model_params.get("combat", {}),
        knowledge_base=knowledge_base
    )
    
    adventure_agent = AdventureAgent(
        model_name=args.model,
        model_params=model_params.get("adventure", {}),
        knowledge_base=knowledge_base
    )
    
    # Return initialized components
    return {
        "logger": logger,
        "config": config,
        "game_master": game_master,
        "combat_agent": combat_agent,
        "adventure_agent": adventure_agent,
        "knowledge_base": knowledge_base
    }


def run_scenario(scenario_type: str, system_components: Dict[str, Any]) -> None:
    """Run the specified scenario"""
    logger = system_components["logger"]
    logger.info(f"Running {scenario_type} scenario")
    
    if scenario_type == "tavern":
        # Create and run tavern scenario
        tavern = create_tavern_scenario(system_components["game_master"])
        
        # Example interaction flow
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
    
    elif scenario_type == "combat":
        # Create and run combat scenario
        combat = create_combat_scenario(
            system_components["game_master"], 
            system_components["combat_agent"]
        )
        
        # Example combat flow
        print("\n=== COMBAT SCENARIO ===\n")
        combat.run_demo_combat()
    
    elif scenario_type == "quest":
        # Create and run quest generation scenario
        quest = create_quest_scenario(
            system_components["game_master"],
            system_components["adventure_agent"]
        )
        
        # Example quest generation
        print("\n=== QUEST GENERATION SCENARIO ===\n")
        quest.run_demo_quest_generation()
    
    else:
        print(f"Scenario '{scenario_type}' not implemented yet.")


def main():
    """Main application entry point"""
    # Parse command line arguments
    args = parse_args()
    
    # Initialize system components
    system = initialize_system(args)
    
    # Run the specified scenario
    run_scenario(args.scenario, system)
    
    print("\nD&D AI Assistant session complete.")


if __name__ == "__main__":
    main()