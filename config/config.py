"""
Configuration Module

This module handles loading and managing configuration settings
for the D&D AI Assistant.
"""

import os
import json
import yaml # type: ignore
from typing import Dict, Any, Optional


# Default configuration settings
DEFAULT_CONFIG = {
    "knowledge_paths": {
        "rules": "knowledge/data/rules",
        "monsters": "knowledge/data/monsters",
        "items": "knowledge/data/items",
        "spells": "knowledge/data/spells",
        "lore": "knowledge/data/lore"
    },
    "model_defaults": {
        "default_model": "gpt-4",
        "fallback_model": "gpt-3.5-turbo"
    },
    "scenario_defaults": {
        "tavern": {
            "default_tavern": "The Prancing Pony",
            "default_location": "Waterdeep",
            "use_random_events": True
        },
        "combat": {
            "initiative_mode": "automatic",
            "combat_narration_style": "cinematic",
            "auto_lookup_rules": True
        },
        "quest": {
            "difficulty_scale": "balanced",
            "quest_length": "medium",
            "theme_restrictions": []
        }
    },
    "tools": {
        "enable_dice_roller": True,
        "enable_rule_lookup": True,
        "enable_web_search": False,
        "enable_image_generation": False
    },
    "logging": {
        "log_level": "INFO",
        "log_file": "dnd_assistant.log",
        "enable_conversation_logging": True
    }
}


def load_config(profile: str = "default") -> Dict[str, Any]:
    """
    Load configuration from file or use defaults.
    
    Args:
        profile: Configuration profile to load
        
    Returns:
        Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    # Look for config file
    config_paths = [
        f"config/profiles/{profile}.json",
        f"config/profiles/{profile}.yaml",
        f"config/profiles/{profile}.yml",
        os.path.expanduser(f"~/.dnd_assistant/{profile}.json")
    ]
    
    # Try to load from each possible path
    for path in config_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    if path.endswith('.json'):
                        loaded_config = json.load(f)
                    else:
                        loaded_config = yaml.safe_load(f)
                        
                # Merge loaded config with defaults
                _deep_update(config, loaded_config)
                break
            except Exception as e:
                print(f"Error loading config from {path}: {str(e)}")
    
    return config


def save_config(config: Dict[str, Any], profile: str = "default") -> bool:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary to save
        profile: Profile name
        
    Returns:
        True if saved successfully, False otherwise
    """
    # Create directory if it doesn't exist
    os.makedirs("config/profiles", exist_ok=True)
    
    # Save to file
    path = f"config/profiles/{profile}.json"
    try:
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config to {path}: {str(e)}")
        return False


def get_scenario_config(config: Dict[str, Any], scenario: str) -> Dict[str, Any]:
    """
    Get configuration specific to a scenario.
    
    Args:
        config: Full configuration dictionary
        scenario: Scenario name
        
    Returns:
        Scenario-specific configuration
    """
    return config.get("scenario_defaults", {}).get(scenario, {})


def _deep_update(base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
    """
    Recursively update a dictionary with another dictionary.
    
    Args:
        base_dict: Dictionary to update
        update_dict: Dictionary with updates
    """
    for key, value in update_dict.items():
        if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
            _deep_update(base_dict[key], value)
        else:
            base_dict[key] = value