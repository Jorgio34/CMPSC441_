"""
Model Parameters Configuration

This module provides parameter configurations for different LLM models
and scenarios, optimizing for different interaction types.
"""

from typing import Dict, Any, Optional


# Base parameter sets for different models
MODEL_BASE_PARAMS = {
    "gpt-4": {
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    },
    "gpt-3.5-turbo": {
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    },
    "claude-3-opus": {
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 1.0
    },
    "claude-3-sonnet": {
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 1.0
    }
}

# Scenario-specific parameter adjustments
SCENARIO_PARAMS = {
    "tavern": {
        # For tavern scenarios, we want more creativity in descriptions and NPC responses
        "game_master": {
            # Higher temperature for more creative and varied descriptions
            "temperature": 0.8,
            # Different parameters for different aspects of tavern interaction
            "description": {
                "temperature": 0.75,  # Vivid but coherent descriptions
                "max_tokens": 350     # Longer descriptions
            },
            "npc_dialogue": {
                "temperature": 0.85,  # More personality variation
                "max_tokens": 250     # Medium length responses
            },
            "perception": {
                "temperature": 0.6,   # More factual for perception checks
                "max_tokens": 200     # Shorter but informative
            },
            "events": {
                "temperature": 0.9,   # More creative for random events
                "max_tokens": 300     # Medium-long event descriptions
            }
        }
    },
    "combat": {
        # For combat scenarios, we want more precision and rule adherence
        "game_master": {
            "temperature": 0.5,       # More consistent for rules
            "max_tokens": 250,        # Shorter responses for game flow
            "frequency_penalty": 0.2  # Avoid repetitive combat descriptions
        },
        "combat": {
            "tactical": {
                "temperature": 0.4,   # More predictable for tactical decisions
                "max_tokens": 150     # Brief tactical explanations
            },
            "narration": {
                "temperature": 0.75,  # Creative for combat descriptions
                "max_tokens": 200     # Descriptive but concise
            },
            "rules": {
                "temperature": 0.2,   # Very precise for rule explanations
                "max_tokens": 300     # Detailed rule explanations
            }
        }
    },
    "quest": {
        # For quest generation, we want high creativity but logical consistency
        "game_master": {
            "temperature": 0.7,  # Balanced for quest presentation
            "max_tokens": 400    # Longer responses for quest details
        },
        "adventure": {
            "outline": {
                "temperature": 0.8,   # Creative for quest structure
                "max_tokens": 500     # Detailed quest outlines
            },
            "npcs": {
                "temperature": 0.85,  # Very creative for NPCs
                "max_tokens": 300     # Detailed NPC descriptions
            },
            "locations": {
                "temperature": 0.8,   # Creative for locations
                "max_tokens": 350     # Detailed location descriptions
            },
            "hooks": {
                "temperature": 0.9,   # Most creative for quest hooks
                "max_tokens": 250     # Engaging but concise hooks
            }
        }
    },
    "dungeon": {
        # For dungeon exploration, we want environmental detail and tension
        "game_master": {
            "temperature": 0.65,      # Balanced for exploration
            "max_tokens": 300,        # Medium length responses
            "frequency_penalty": 0.1  # Slight variation in descriptions
        }
    },
    "npc": {
        # For detailed NPC interactions, we want consistent personality
        "game_master": {
            "temperature": 0.7,       # Balanced for NPC consistency
            "max_tokens": 300,        # Medium length responses
            "frequency_penalty": 0.2  # Avoid repetitive speech patterns
        }
    }
}


def get_model_params(scenario: str, model_name: str) -> Dict[str, Dict[str, Any]]:
    """
    Get the optimized parameters for a specific scenario and model.
    
    Args:
        scenario: The scenario type (e.g., "tavern", "combat")
        model_name: The name of the LLM model
        
    Returns:
        Dictionary of parameter configurations for different agents
    """
    # Get base parameters for the model
    base_params = MODEL_BASE_PARAMS.get(model_name, MODEL_BASE_PARAMS["gpt-4"])
    
    # Get scenario-specific parameters
    scenario_params = SCENARIO_PARAMS.get(scenario, {})
    
    # Combine the parameters
    result = {}
    
    # Process each agent type
    for agent_type, agent_params in scenario_params.items():
        if isinstance(agent_params, dict) and not any(isinstance(v, dict) for v in agent_params.values()):
            # Agent has simple parameters, merge with base
            result[agent_type] = {**base_params, **agent_params}
        elif isinstance(agent_params, dict):
            # Agent has nested parameters for different functions
            result[agent_type] = {
                # Base parameters for the agent
                **{k: v for k, v in agent_params.items() if not isinstance(v, dict)},
                # Function-specific parameters
                "functions": {
                    func_name: {**base_params, **func_params}
                    for func_name, func_params in agent_params.items()
                    if isinstance(func_params, dict)
                }
            }
            # Add any base parameters not overridden
            for k, v in base_params.items():
                if k not in result[agent_type]:
                    result[agent_type][k] = v
    
    return result


def explain_parameter_choice(scenario: str, function: str) -> str:
    """
    Generate an explanation of parameter choices for a specific scenario and function.
    
    Args:
        scenario: The scenario type
        function: The specific function within the scenario
        
    Returns:
        A textual explanation of the parameter choices
    """
    explanations = {
        "tavern": {
            "description": (
                "We use a moderately high temperature (0.75) for tavern descriptions to create "
                "vivid and engaging environments while maintaining coherence. The higher max_tokens "
                "value (350) allows for detailed sensory descriptions that immerse players in the "
                "setting."
            ),
            "npc_dialogue": (
                "For NPC dialogues, we increase temperature to 0.85 to enhance personality variation "
                "and make each character feel distinct. This helps NPCs respond with appropriate "
                "emotion and personal quirks while keeping responses at a conversational length."
            ),
            "perception": (
                "Perception checks use a lower temperature (0.6) to ensure factual consistency "
                "when revealing details. This makes discoveries feel fair and objective rather "
                "than arbitrary, maintaining player trust in the game mechanics."
            ),
            "events": (
                "Random tavern events use the highest temperature (0.9) to generate surprising "
                "and creative scenarios that add dynamism to what could otherwise be static "
                "social encounters."
            )
        },
        "combat": {
            "tactical": (
                "Enemy tactical decisions use a low temperature (0.4) to ensure consistent, "
                "logical behavior that players can understand and strategize against. This makes "
                "combat feel fair rather than random."
            ),
            "narration": (
                "Combat narration uses a higher temperature (0.75) to create vivid, varied "
                "descriptions of attacks, dodges, and spells that prevent combat from feeling "
                "repetitive."
            ),
            "rules": (
                "Rule explanations use a very low temperature (0.2) to maximize accuracy and "
                "consistency, ensuring that game mechanics are applied fairly and predictably."
            )
        },
        "quest": {
            "outline": (
                "Quest outlines use a high temperature (0.8) to generate creative and unexpected "
                "adventure structures while maintaining enough coherence to create a sensible "
                "narrative arc."
            ),
            "npcs": (
                "NPC generation uses an even higher temperature (0.85) to create memorable "
                "characters with distinctive personalities, motivations, and quirks that make "
                "them feel alive in the game world."
            ),
            "locations": (
                "Location descriptions use a high temperature (0.8) to create imaginative "
                "environments with distinctive features, atmosphere, and points of interest."
            ),
            "hooks": (
                "Quest hooks use the highest temperature (0.9) to create compelling and unusual "
                "inciting incidents that motivate player engagement with the adventure."
            )
        }
    }
    
    # Get the explanation for the specific scenario and function
    scenario_explanations = explanations.get(scenario, {})
    function_explanation = scenario_explanations.get(function, 
        "Parameter choices balance creativity with consistency, adjusting based on the specific "
        "needs of this interaction type.")
    
    return function_explanation