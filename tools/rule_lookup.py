"""
Rule Lookup Utility

This module provides functions for looking up D&D 5e rules,
both from a local database and by searching online references.
"""

import re
import json
import os
from typing import Dict, List, Any, Optional, Union

# Import from the knowledge module to access monster data
from knowledge.retrieval import retrieve_monster

# In a real implementation, this would use an actual database or API
# For this demo, we'll use a simple dictionary of rules

RULES_DATABASE = {
    "ability_scores": {
        "strength": "Strength measures bodily power, athletic training, and the extent to which you can exert raw physical force.",
        "dexterity": "Dexterity measures agility, reflexes, and balance.",
        "constitution": "Constitution measures health, stamina, and vital force.",
        "intelligence": "Intelligence measures mental acuity, accuracy of recall, and the ability to reason.",
        "wisdom": "Wisdom reflects how attuned you are to the world around you and represents perceptiveness and intuition.",
        "charisma": "Charisma measures your ability to interact effectively with others. It includes such factors as confidence and eloquence."
    },
    
    "ability_checks": {
        "general": "To make an ability check, roll a d20 and add the relevant ability modifier. If you have proficiency in a skill, you can add your proficiency bonus.",
        "difficulty_classes": {
            "very_easy": "DC 5",
            "easy": "DC 10",
            "medium": "DC 15",
            "hard": "DC 20",
            "very_hard": "DC 25",
            "nearly_impossible": "DC 30"
        },
        "contest": "When your character's efforts are directly opposed by another character, you make a contest. Both participants make ability checks appropriate to their actions, and the higher check result wins."
    },
    
    "saving_throws": {
        "general": "A saving throw is a roll to avoid or reduce a threat. To make a saving throw, roll a d20 and add the relevant ability modifier. If you have proficiency in the saving throw, add your proficiency bonus.",
        "types": {
            "strength": "To break free from a grapple or resist being pushed",
            "dexterity": "To dodge area effects or avoid traps",
            "constitution": "To resist poison, disease, or similar threats",
            "intelligence": "To resist mental effects or illusions",
            "wisdom": "To resist charm effects or detect lies",
            "charisma": "To resist possession or banishment effects"
        }
    },
    
    "combat": {
        "initiative": "At the beginning of combat, each participant makes a Dexterity check to determine their place in the initiative order.",
        "actions": {
            "attack": "Make an attack against a creature or object within your reach.",
            "cast_spell": "Cast a spell with a casting time of 1 action.",
            "dash": "Gain extra movement equal to your speed for the current turn.",
            "disengage": "Your movement doesn't provoke opportunity attacks for the rest of the turn.",
            "dodge": "Until the start of your next turn, any attack roll made against you has disadvantage.",
            "help": "Grant advantage on the next ability check made by a creature you help, or grant advantage on the next attack roll against a creature you distract.",
            "hide": "Make a Dexterity (Stealth) check to hide.",
            "ready": "Prepare an action to trigger in response to a specific event.",
            "search": "Make a Wisdom (Perception) or Intelligence (Investigation) check to search for something.",
            "use_object": "Use an object that requires an action to use."
        },
        "bonus_actions": "Various class features, spells, and other abilities let you take an additional action called a bonus action. You can take only one bonus action on your turn.",
        "reactions": "A reaction is an instant response to a trigger of some kind. You can take only one reaction per round.",
        "movement": "On your turn, you can move a distance up to your speed. You can break up your movement before and after your action."
    },
    
    "spellcasting": {
        "general": "Casting a spell requires components (verbal, somatic, material) and typically uses an action.",
        "spell_slots": "Spellcasters have a limited number of spell slots they can use to cast spells. When a character casts a spell, they expend a slot of that spell's level or higher.",
        "concentration": "Some spells require you to maintain concentration to keep their effects active. If you take damage while concentrating on a spell, you must make a Constitution saving throw to maintain concentration.",
        "ritual_casting": "Some spells have the ritual tag. You can cast such a spell as a ritual if it has the ritual tag and you have the feature that allows you to do so. A ritual takes 10 minutes longer to cast than normal."
    },
    
    "conditions": {
        "blinded": "A blinded creature can't see and automatically fails any ability check that requires sight. Attack rolls against the creature have advantage, and the creature's attack rolls have disadvantage.",
        "charmed": "A charmed creature can't attack the charmer or target the charmer with harmful abilities or magical effects. The charmer has advantage on any ability check to interact socially with the creature.",
        "deafened": "A deafened creature can't hear and automatically fails any ability check that requires hearing.",
        "exhaustion": "Exhaustion has levels that accumulate, each with increasing penalties. A long rest reduces exhaustion by 1 level.",
        "frightened": "A frightened creature has disadvantage on ability checks and attack rolls while the source of its fear is within line of sight. The creature can't willingly move closer to the source of its fear.",
        "grappled": "A grappled creature's speed becomes 0, and it can't benefit from any bonus to its speed.",
        "incapacitated": "An incapacitated creature can't take actions or reactions.",
        "invisible": "An invisible creature is impossible to see without special senses. The creature has advantage on attack rolls, and attack rolls against the creature have disadvantage.",
        "paralyzed": "A paralyzed creature is incapacitated and can't move or speak. The creature automatically fails Strength and Dexterity saving throws. Attack rolls against the creature have advantage. Any attack that hits the creature is a critical hit if the attacker is within 5 feet of the creature.",
        "petrified": "A petrified creature is transformed, along with any nonmagical objects it is wearing or carrying, into a solid inanimate substance. Its weight increases by a factor of ten, and it ceases aging.",
        "poisoned": "A poisoned creature has disadvantage on attack rolls and ability checks.",
        "prone": "A prone creature's only movement option is to crawl. The creature has disadvantage on attack rolls. An attack roll against the creature has advantage if the attacker is within 5 feet of the creature. Otherwise, the attack roll has disadvantage.",
        "restrained": "A restrained creature's speed becomes 0, and it can't benefit from any bonus to its speed. Attack rolls against the creature have advantage, and the creature's attack rolls have disadvantage. The creature has disadvantage on Dexterity saving throws.",
        "stunned": "A stunned creature is incapacitated, can't move, and can speak only falteringly. The creature automatically fails Strength and Dexterity saving throws. Attack rolls against the creature have advantage.",
        "unconscious": "An unconscious creature is incapacitated, can't move or speak, and is unaware of its surroundings. The creature drops whatever it's holding and falls prone. The creature automatically fails Strength and Dexterity saving throws. Attack rolls against the creature have advantage. Any attack that hits the creature is a critical hit if the attacker is within 5 feet of the creature."
    },
    
    "resting": {
        "short_rest": "A short rest is a period of downtime, at least 1 hour long, during which a character does nothing more strenuous than eating, drinking, reading, and tending to wounds. A character can spend one or more Hit Dice at the end of a short rest, up to the character's maximum number of Hit Dice.",
        "long_rest": "A long rest is a period of extended downtime, at least 8 hours long, during which a character sleeps for at least 6 hours and performs no more than 2 hours of light activity. At the end of a long rest, a character regains all lost hit points and half their total Hit Dice (minimum of 1)."
    }
}

# Simple monster database for the get_monster_stats function
MONSTER_DATABASE = {
    "goblin": {
        "name": "Goblin",
        "size": "Small",
        "type": "humanoid",
        "alignment": "neutral evil",
        "ac": 15,
        "hp": "7 (2d6)",
        "speed": "30 ft.",
        "abilities": {"str": 8, "dex": 14, "con": 10, "int": 10, "wis": 8, "cha": 8},
        "skills": "Stealth +6",
        "senses": "darkvision 60 ft.",
        "languages": "Common, Goblin",
        "cr": 0.25,
        "traits": ["Nimble Escape: The goblin can take the Disengage or Hide action as a bonus action on each of its turns."],
        "actions": ["Scimitar: Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 5 (1d6 + 2) slashing damage.",
                    "Shortbow: Ranged Weapon Attack: +4 to hit, range 80/320 ft., one target. Hit: 5 (1d6 + 2) piercing damage."],
        "description": "Goblins are small, black-hearted humanoids that lair in despoiled dungeons and other dismal settings. Individually weak, they gather in large numbers to torment other creatures."
    },
    "owlbear": {
        "name": "Owlbear",
        "size": "Large",
        "type": "monstrosity",
        "alignment": "unaligned",
        "ac": 13,
        "hp": "59 (7d10 + 21)",
        "speed": "40 ft.",
        "abilities": {"str": 20, "dex": 12, "con": 17, "int": 3, "wis": 12, "cha": 7},
        "skills": "Perception +3",
        "senses": "darkvision 60 ft.",
        "languages": "—",
        "cr": 3,
        "traits": ["Keen Sight and Smell: The owlbear has advantage on Wisdom (Perception) checks that rely on sight or smell."],
        "actions": ["Multiattack: The owlbear makes two attacks: one with its beak and one with its claws.",
                    "Beak: Melee Weapon Attack: +7 to hit, reach 5 ft., one creature. Hit: 10 (1d10 + 5) piercing damage.",
                    "Claws: Melee Weapon Attack: +7 to hit, reach 5 ft., one target. Hit: 14 (2d8 + 5) slashing damage."],
        "description": "An owlbear's screech echoes through dark valleys and benighted forests, piercing the quiet night to announce the death of its prey."
    },
    "dragon, red": {
        "name": "Red Dragon",
        "size": "Huge",
        "type": "dragon",
        "alignment": "chaotic evil",
        "ac": 19,
        "hp": "256 (19d12 + 133)",
        "speed": "40 ft., climb 40 ft., fly 80 ft.",
        "abilities": {"str": 27, "dex": 10, "con": 25, "int": 16, "wis": 13, "cha": 21},
        "saves": "Dex +6, Con +13, Wis +7, Cha +11",
        "skills": "Perception +13, Stealth +6",
        "immunities": "fire",
        "senses": "blindsight 60 ft., darkvision 120 ft.",
        "languages": "Common, Draconic",
        "cr": 17,
        "traits": ["Legendary Resistance (3/Day): If the dragon fails a saving throw, it can choose to succeed instead."],
        "actions": ["Multiattack: The dragon can use its Frightful Presence. It then makes three attacks: one with its bite and two with its claws.",
                    "Bite: Melee Weapon Attack: +14 to hit, reach 10 ft., one target. Hit: 19 (2d10 + 8) piercing damage plus 7 (2d6) fire damage.",
                    "Claw: Melee Weapon Attack: +14 to hit, reach 5 ft., one target. Hit: 15 (2d6 + 8) slashing damage.",
                    "Tail: Melee Weapon Attack: +14 to hit, reach 15 ft., one target. Hit: 17 (2d8 + 8) bludgeoning damage.",
                    "Frightful Presence: Each creature of the dragon's choice within 120 feet of it must succeed on a DC 19 Wisdom saving throw or be frightened for 1 minute.",
                    "Fire Breath (Recharge 5-6): The dragon exhales fire in a 60-foot cone. Each creature in that area must make a DC 21 Dexterity saving throw, taking 63 (18d6) fire damage on a failed save, or half as much damage on a successful one."]
    }
}


def lookup_rule(rule_query: str) -> str:
    """
    Look up a rule in the local database.
    
    Args:
        rule_query: The rule to look up
        
    Returns:
        Rule information
    """
    rule_query = rule_query.lower()
    
    # Check for direct rule category matches
    for category, rules in RULES_DATABASE.items():
        if rule_query == category or rule_query in category:
            if isinstance(rules, str):
                return f"{category.title()}: {rules}"
            elif isinstance(rules, dict):
                # Format nested dictionary as a string
                result = f"{category.title()}:\n"
                for key, value in rules.items():
                    if isinstance(value, dict):
                        result += f"  {key.replace('_', ' ').title()}:\n"
                        for subkey, subvalue in value.items():
                            result += f"    {subkey.replace('_', ' ').title()}: {subvalue}\n"
                    else:
                        result += f"  {key.replace('_', ' ').title()}: {value}\n"
                return result
    
    # Look for specific rule matches
    for category, rules in RULES_DATABASE.items():
        if isinstance(rules, dict):
            for key, value in rules.items():
                if rule_query == key or rule_query in key:
                    if isinstance(value, dict):
                        result = f"{key.replace('_', ' ').title()}:\n"
                        for subkey, subvalue in value.items():
                            result += f"  {subkey.replace('_', ' ').title()}: {subvalue}\n"
                        return result
                    else:
                        return f"{key.replace('_', ' ').title()}: {value}"
                
                # Check one level deeper if needed
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        if rule_query == subkey or rule_query in subkey:
                            return f"{subkey.replace('_', ' ').title()}: {subvalue}"
    
    # If no direct match, look for partial matches
    matches = []
    for category, rules in RULES_DATABASE.items():
        if rule_query in category:
            matches.append((category, "category"))
        
        if isinstance(rules, dict):
            for key, value in rules.items():
                if rule_query in key:
                    matches.append((f"{category}.{key}", "rule"))
                
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        if rule_query in subkey:
                            matches.append((f"{category}.{key}.{subkey}", "subrule"))
    
    if matches:
        # Return the closest match
        closest_match = matches[0]
        path_parts = closest_match[0].split(".")
        
        if len(path_parts) == 1:
            return f"Closest match: {path_parts[0].replace('_', ' ').title()} category"
        elif len(path_parts) == 2:
            category, key = path_parts
            value = RULES_DATABASE[category][key]
            if isinstance(value, dict):
                return f"Closest match - {key.replace('_', ' ').title()}:\n" + "\n".join(
                    f"  {subkey.replace('_', ' ').title()}: {subvalue}" 
                    for subkey, subvalue in value.items()
                )
            else:
                return f"Closest match - {key.replace('_', ' ').title()}: {value}"
        elif len(path_parts) == 3:
            category, key, subkey = path_parts
            return f"Closest match - {subkey.replace('_', ' ').title()}: {RULES_DATABASE[category][key][subkey]}"
    
    return f"No rule found for '{rule_query}'. Try a more general term like 'combat', 'spellcasting', or 'conditions'."


def get_condition_effects(condition: str) -> str:
    """
    Get the effects of a specific condition.
    
    Args:
        condition: The condition name
        
    Returns:
        Effects of the condition
    """
    condition = condition.lower()
    conditions = RULES_DATABASE.get("conditions", {})
    
    if condition in conditions:
        return f"{condition.title()}: {conditions[condition]}"
    
    # Try partial matches
    for cond_name, cond_effects in conditions.items():
        if condition in cond_name:
            return f"{cond_name.title()}: {cond_effects}"
    
    return f"Condition '{condition}' not found. Available conditions: {', '.join(conditions.keys())}"


def get_action_description(action: str) -> str:
    """
    Get the description of a specific action in combat.
    
    Args:
        action: The action name
        
    Returns:
        Description of the action
    """
    action = action.lower()
    actions = RULES_DATABASE.get("combat", {}).get("actions", {})
    
    if action in actions:
        return f"{action.title()}: {actions[action]}"
    
    # Check other combat sections
    for section in ["bonus_actions", "reactions", "movement"]:
        if section in RULES_DATABASE.get("combat", {}):
            if action == section or action in section:
                return f"{section.title()}: {RULES_DATABASE['combat'][section]}"
    
    # Try partial matches
    for act_name, act_desc in actions.items():
        if action in act_name:
            return f"{act_name.title()}: {act_desc}"
    
    return f"Action '{action}' not found. Available actions: {', '.join(actions.keys())}"


def get_difficulty_class(difficulty: str) -> str:
    """
    Get the DC for a specific difficulty level.
    
    Args:
        difficulty: The difficulty level
        
    Returns:
        The corresponding Difficulty Class (DC)
    """
    difficulty = difficulty.lower()
    dcs = RULES_DATABASE.get("ability_checks", {}).get("difficulty_classes", {})
    
    if difficulty in dcs:
        return f"{difficulty.replace('_', ' ').title()}: {dcs[difficulty]}"
    
    # Try partial matches
    for dc_name, dc_value in dcs.items():
        if difficulty in dc_name:
            return f"{dc_name.replace('_', ' ').title()}: {dc_value}"
    
    return f"Difficulty level '{difficulty}' not found. Available levels: {', '.join(dcs.keys())}"


def get_monster_stats(monster_name: str) -> Dict[str, Any]:
    """
    Retrieve stats for a specific monster.
    
    Args:
        monster_name: The name of the monster to retrieve stats for
        
    Returns:
        Dictionary containing monster stats or an empty dict if not found
    """
    # Convert the monster name to lowercase for case-insensitive matching
    monster_lower = monster_name.lower()
    
    # First try to retrieve from our local database
    for key, monster_data in MONSTER_DATABASE.items():
        if monster_lower == key.lower() or monster_lower == monster_data.get("name", "").lower():
            return monster_data
    
    # If not found in local database, try to retrieve from the knowledge retrieval system
    try:
        # Try to use the retrieve_monster function if it's available
        monster_data = retrieve_monster(monster_name)
        if monster_data:
            return monster_data
    except (ImportError, NameError):
        # If the import failed or the function doesn't exist, we'll fall back to defaults
        pass
    
    # If not found, return a minimal default stat block
    return {
        "name": monster_name,
        "size": "Medium",
        "type": "unknown",
        "alignment": "unaligned",
        "ac": 10,
        "hp": "10 (1d8+2)",
        "speed": "30 ft.",
        "abilities": {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10},
        "senses": "passive Perception 10",
        "languages": "Common",
        "cr": 0.5,
        "actions": [f"{monster_name} Attack: Melee Weapon Attack: +2 to hit, reach 5 ft., one target. Hit: 3 (1d6) damage."],
        "description": f"A mysterious creature known as {monster_name}."
    }


def get_ability_modifier(ability_score: int) -> int:
    """
    Calculate the ability modifier for a given ability score.
    
    Args:
        ability_score: The ability score (1-30)
        
    Returns:
        The ability modifier
    """
    # Standard D&D 5e formula: (score - 10) / 2, rounded down
    return (ability_score - 10) // 2


def get_proficiency_bonus(level: int) -> int:
    """
    Calculate the proficiency bonus for a given character level.
    
    Args:
        level: The character level (1-20)
        
    Returns:
        The proficiency bonus
    """
    # Standard D&D 5e formula: 2 + (level - 1) // 4
    return 2 + (level - 1) // 4