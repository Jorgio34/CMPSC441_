"""
Knowledge Retrieval Module

This module implements the Retrieval Augmented Generation (RAG) functionality
for the D&D AI Assistant. It provides vector embedding and retrieval capabilities
for rules, lore, monsters, and other game data.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import random

# In a real implementation, this would use a vector database like FAISS or Pinecone
# For demo purposes, we'll use a simple in-memory approach

# Global knowledge store
KNOWLEDGE_BASE = {
    "rules": {},
    "monsters": {},
    "items": {},
    "spells": {},
    "lore": {}
}

# Logger
logger = logging.getLogger("knowledge")


def initialize_knowledge_base(data_paths: Dict[str, str]) -> Dict:
    """
    Initialize the knowledge base from data files.
    
    Args:
        data_paths: Dictionary mapping knowledge types to file paths
        
    Returns:
        The initialized knowledge base
    """
    global KNOWLEDGE_BASE
    
    # In a real implementation, this would load actual data files
    # For demo purposes, we'll populate with sample data
    
    # Sample rules data
    KNOWLEDGE_BASE["rules"] = {
        "ability_checks": "To make an ability check, roll a d20 and add the relevant ability modifier. " +
                         "Compare the total to the DC determined by the DM.",
        "attack_rolls": "To make an attack roll, roll a d20 and add your attack bonus. " +
                       "If the total equals or exceeds the target's AC, the attack hits.",
        "saving_throws": "To make a saving throw, roll a d20 and add the relevant ability modifier. " +
                        "If the total equals or exceeds the DC, the save succeeds.",
        "advantage_disadvantage": "Advantage: roll two d20s and take the higher result. " +
                                 "Disadvantage: roll two d20s and take the lower result.",
        "conditions": "Conditions like blinded, charmed, and frightened impose specific limitations " +
                     "on what a creature can do.",
        "grappling": "To grapple, make a Strength (Athletics) check contested by the target's " +
                    "Strength (Athletics) or Dexterity (Acrobatics) check.",
        "hiding": "To hide, make a Dexterity (Stealth) check contested by observers' " +
                 "Wisdom (Perception) checks.",
        "resting": "A short rest is at least 1 hour. A long rest is at least 8 hours. " +
                  "A character can benefit from only one long rest in a 24-hour period.",
        "concentration": "Concentration can be broken by taking damage (DC 10 or half the damage taken, " +
                        "whichever is higher), being incapacitated, or casting another spell that requires concentration."
    }
    
    # Sample monster data
    KNOWLEDGE_BASE["monsters"] = {
        "Goblin": {
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
        "Owlbear": {
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
            "description": "An owlbear's screech echoes through dark valleys and benighted forests, piercing the quiet night to announce the death of its prey. Feathers cover the thick, shaggy coat of its bearlike body, and the limpid pupils of its great round eyes stare furiously from its owlish head."
        },
        "Dragon, Red": {
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
    
    # Sample item data
    KNOWLEDGE_BASE["items"] = {
        "Potion of Healing": {
            "type": "Potion",
            "rarity": "Common",
            "attunement": False,
            "description": "You regain 2d4 + 2 hit points when you drink this potion.",
            "price": "50 gp"
        },
        "Ring of Protection": {
            "type": "Ring",
            "rarity": "Rare",
            "attunement": True,
            "description": "You gain a +1 bonus to AC and saving throws while wearing this ring.",
            "price": "3,500 gp"
        },
        "Bag of Holding": {
            "type": "Wondrous item",
            "rarity": "Uncommon",
            "attunement": False,
            "description": "This bag has an interior space considerably larger than its outside dimensions, roughly 2 feet in diameter at the mouth and 4 feet deep. The bag can hold up to 500 pounds, not exceeding a volume of 64 cubic feet. The bag weighs 15 pounds, regardless of its contents.",
            "price": "500 gp"
        }
    }
    
    # Sample spell data
    KNOWLEDGE_BASE["spells"] = {
        "Fireball": {
            "level": 3,
            "school": "Evocation",
            "casting_time": "1 action",
            "range": "150 feet",
            "components": "V, S, M (a tiny ball of bat guano and sulfur)",
            "duration": "Instantaneous",
            "description": "A bright streak flashes from your pointing finger to a point you choose within range and then blossoms with a low roar into an explosion of flame. Each creature in a 20-foot-radius sphere centered on that point must make a Dexterity saving throw. A target takes 8d6 fire damage on a failed save, or half as much damage on a successful one."
        },
        "Cure Wounds": {
            "level": 1,
            "school": "Evocation",
            "casting_time": "1 action",
            "range": "Touch",
            "components": "V, S",
            "duration": "Instantaneous",
            "description": "A creature you touch regains a number of hit points equal to 1d8 + your spellcasting ability modifier. This spell has no effect on undead or constructs."
        },
        "Shield": {
            "level": 1,
            "school": "Abjuration",
            "casting_time": "1 reaction, which you take when you are hit by an attack or targeted by the magic missile spell",
            "range": "Self",
            "components": "V, S",
            "duration": "1 round",
            "description": "An invisible barrier of magical force appears and protects you. Until the start of your next turn, you have a +5 bonus to AC, including against the triggering attack, and you take no damage from magic missile."
        }
    }
    
    # Sample lore data
    KNOWLEDGE_BASE["lore"] = {
        "Waterdeep": "Waterdeep, also known as the City of Splendors, is the most powerful and influential city in the North and perhaps in all Faerûn. It is a bustling city of commerce where coin rules, but also dedicated to maintaining peace and order through the Lords of Waterdeep and their masked agents, the Blackstaff, and the City Guard.",
        "Neverwinter": "Neverwinter is a city-state of artisans, craftspeople, and traders located on the northwestern coast of Faerûn, sitting along the High Road. The city is ruled by Lord Protector Dagult Neverember, who maintains order through his military forces.",
        "The Dragon's Rest": "The Dragon's Rest is a popular tavern in Neverwinter known for its warm hearth and exceptional dwarven ale. The establishment is owned by a retired adventurer named Grimm Ironheart, who claims to have once slain a young red dragon—a tale met with equal parts belief and skepticism by the regulars.",
        "The Prancing Pony": "The Prancing Pony is a cozy tavern in Waterdeep's Trade Ward known for its excellent food and diverse clientele. Travelers from across the Sword Coast often gather here to exchange stories and information, making it a valuable spot for adventurers seeking work.",
        "Undermountain": "Undermountain is a vast dungeon complex beneath the city of Waterdeep, created by the mad wizard Halaster Blackcloak. It is said to be the largest dungeon in Faerûn and contains countless dangers and treasures spread across many different levels.",
        "Sword Coast": "The Sword Coast is the region of coastline along the Sea of Swords, stretching from Waterdeep in the north to Baldur's Gate in the south. The area is home to several prominent city-states and is known for trade, piracy, and adventure.",
        "Harper's guild": "The Harpers are a semi-secret organization dedicated to promoting good, preserving knowledge, and maintaining the balance between civilization and nature. Their operatives use the harp-and-moon symbol to identify themselves to allies and often work independently to gather information and thwart threats to the realms.",
        "Green Hag": "Green hags are malevolent fey creatures that dwell in forests, swamps, and other wilderness locations. They delight in corrupting the innocent and bringing ruin to the lives of mortals through manipulation and deceit. Green hags possess innate spellcasting abilities and can disguise themselves as beautiful women to lure victims."
    }
    
    logger.info("Knowledge base initialized with sample data")
    return KNOWLEDGE_BASE


def retrieve_rule(rule_name: str) -> str:
    """
    Retrieve information about a specific game rule.
    
    Args:
        rule_name: The name of the rule to retrieve
        
    Returns:
        The rule information as a string
    """
    # Convert the rule name to lowercase for case-insensitive matching
    rule_lower = rule_name.lower()
    
    # In a real implementation, this would use vector similarity search
    # For demo purposes, we'll use simple keyword matching
    for rule_key, rule_text in KNOWLEDGE_BASE["rules"].items():
        if rule_lower in rule_key.lower():
            logger.info(f"Rule found for '{rule_name}': {rule_key}")
            return rule_text
    
    # Check for partial matches if no exact match found
    partial_matches = []
    for rule_key, rule_text in KNOWLEDGE_BASE["rules"].items():
        for word in rule_lower.split():
            if word in rule_key.lower() and len(word) > 3:  # Only match significant words
                partial_matches.append((rule_key, rule_text))
                break
    
    if partial_matches:
        # Return the first partial match
        logger.info(f"Partial rule match found for '{rule_name}': {partial_matches[0][0]}")
        return partial_matches[0][1]
    
    logger.warning(f"No rule found for '{rule_name}'")
    return f"No specific rule found for '{rule_name}'. Please try a different query."


def retrieve_monster(monster_name: str) -> Dict[str, Any]:
    """
    Retrieve information about a specific monster.
    
    Args:
        monster_name: The name of the monster to retrieve
        
    Returns:
        The monster information as a dictionary
    """
    # Convert the monster name to lowercase for case-insensitive matching
    monster_lower = monster_name.lower()
    
    # Try direct lookup first
    for monster_key, monster_data in KNOWLEDGE_BASE["monsters"].items():
        if monster_lower == monster_key.lower():
            logger.info(f"Monster found: {monster_key}")
            return monster_data
    
    # Try partial matches
    partial_matches = []
    for monster_key, monster_data in KNOWLEDGE_BASE["monsters"].items():
        if monster_lower in monster_key.lower():
            partial_matches.append((monster_key, monster_data))
    
    if partial_matches:
        # Return the first partial match
        logger.info(f"Partial monster match found: {partial_matches[0][0]}")
        return partial_matches[0][1]
    
    logger.warning(f"No monster found for '{monster_name}'")
    return {}

def retrieve_combat_descriptions(description_type: str, weapon_type: str = None, monster_type: str = None) -> str:
    """
    Retrieve combat descriptions for hits, misses, etc.
    
    Args:
        description_type: Type of description ("hit", "miss", "enemy_hit", "enemy_miss", etc.)
        weapon_type: Type of weapon used (optional)
        monster_type: Type of monster (optional)
        
    Returns:
        Combat description as a string
    """
    # Dictionary of combat descriptions
    combat_descriptions = {
        "hit": {
            "generic": [
                "The attack lands with devastating force",
                "The attack strikes true, hitting its mark",
                "A powerful blow connects with the target",
                "The attack finds a gap in the target's defenses"
            ],
            "sword": [
                "The sword slices through the enemy's defenses",
                "The blade cleaves into the target with a satisfying impact",
                "The sword carves a gash across the enemy",
                "The blade strikes with precision"
            ],
            "axe": [
                "The axe crashes down with brutal force",
                "The axe bites deeply into the target",
                "The heavy axe head connects with a solid thud",
                "The axe cleaves through armor with ease"
            ],
            "mace": [
                "The mace crushes against the target with a dull crunch",
                "The heavy mace smashes into the enemy",
                "The mace connects with bone-crushing force",
                "The mace delivers a stunning blow"
            ],
            "bow": [
                "The arrow pierces the target with precision",
                "The shot finds a vulnerable spot",
                "The arrow flies true to its mark",
                "The arrow sinks deep into the target"
            ],
            "dagger": [
                "The dagger slips between the gaps in armor",
                "The blade strikes a vulnerable point",
                "The dagger finds its mark with surgical precision",
                "The quick strike catches the enemy by surprise"
            ]
        },
        "miss": {
            "generic": [
                "The attack narrowly misses its target",
                "The enemy deftly evades the attack",
                "The attack is deflected at the last moment",
                "The attack fails to connect"
            ],
            "sword": [
                "The sword swings wide, missing the target",
                "The blade is parried aside",
                "The sword strike is anticipated and avoided",
                "The sword meets only air as the enemy dodges"
            ],
            "axe": [
                "The axe embeds into the ground as the enemy steps aside",
                "The heavy axe swing is too slow to connect",
                "The axe crashes down but the enemy is no longer there",
                "The enemy blocks the axe with their shield"
            ],
            "mace": [
                "The mace swings harmlessly past",
                "The enemy sidesteps the heavy mace blow",
                "The mace connects only with the ground, sending up dust",
                "The unwieldy mace is easily avoided"
            ],
            "bow": [
                "The arrow flies wide of its mark",
                "The target shifts at the last moment, avoiding the shot",
                "The arrow deflects off armor without causing harm",
                "The shot misses by inches"
            ],
            "dagger": [
                "The quick strike is anticipated and blocked",
                "The dagger finds only empty air",
                "The target twists away from the blade",
                "The dagger's point is turned aside"
            ]
        },
        "enemy_hit": {
            "generic": [
                "The creature strikes with frightening precision",
                "The attack tears into you painfully",
                "The blow lands with unexpected force",
                "The attack catches you off-guard"
            ],
            "humanoid": [
                "The enemy's weapon finds a gap in your armor",
                "The attack slips past your defenses",
                "The foe's strike is surprisingly effective",
                "The blow lands exactly where you're most vulnerable"
            ],
            "beast": [
                "The creature's claws tear through your defenses",
                "Its fangs sink into you painfully",
                "The beast's attack is wild but effective",
                "The creature's natural weapons find their mark"
            ],
            "undead": [
                "The undead's cold touch drains warmth where it strikes",
                "The rotting limb delivers a surprisingly powerful blow",
                "The creature's unearthly strength drives the attack home",
                "The undead's attack brings a momentary chill of the grave"
            ],
            "dragon": [
                "The dragon's attack is devastatingly powerful",
                "The massive claws tear through defenses like paper",
                "The dragon's precisely aimed attack finds its mark",
                "The creature's ancient might is brought to bear"
            ]
        },
        "enemy_miss": {
            "generic": [
                "You manage to avoid the attack at the last moment",
                "The creature's attack misses by inches",
                "You deflect the attack skillfully",
                "Your defensive maneuver prevents the attack from landing"
            ],
            "humanoid": [
                "You parry the enemy's weapon aside",
                "The foe's attack is anticipated and avoided",
                "You sidestep the clumsy strike",
                "Your armor deflects the worst of the blow"
            ],
            "beast": [
                "The beast's attack is wild and easy to avoid",
                "You dodge the creature's lunge",
                "The beast's claws find only air as you move",
                "The creature's attack is powerful but poorly aimed"
            ],
            "undead": [
                "The shambling attack is slow enough to evade",
                "The undead's deteriorated form fails in its attack",
                "You recoil from the grotesque limb as it swings past",
                "The creature's attack lacks the coordination to connect"
            ],
            "dragon": [
                "Even the dragon's speed isn't enough to catch you",
                "You narrowly avoid being crushed by the massive attack",
                "Through luck or skill, you avoid the deadly attack",
                "The dragon's confidence made its attack predictable"
            ]
        }
    }
    
    # Select the appropriate description type
    descriptions = combat_descriptions.get(description_type, {})
    
    # For player attacks, use weapon type if provided
    if description_type in ["hit", "miss"] and weapon_type:
        weapon_specific = descriptions.get(weapon_type.lower(), [])
        if weapon_specific:
            return random.choice(weapon_specific)
    
    # For enemy attacks, use monster type if provided
    if description_type in ["enemy_hit", "enemy_miss"] and monster_type:
        monster_specific = descriptions.get(monster_type.lower(), [])
        if monster_specific:
            return random.choice(monster_specific)
    
    # Default to generic descriptions
    generic = descriptions.get("generic", ["The attack is made."])
    return random.choice(generic)


def retrieve_item(item_name: str) -> Dict[str, Any]:
    """
    Retrieve information about a specific item.
    
    Args:
        item_name: The name of the item to retrieve
        
    Returns:
        The item information as a dictionary
    """
    # Convert the item name to lowercase for case-insensitive matching
    item_lower = item_name.lower()
    
    # Try direct lookup first
    for item_key, item_data in KNOWLEDGE_BASE["items"].items():
        if item_lower == item_key.lower():
            logger.info(f"Item found: {item_key}")
            return item_data
    
    # Try partial matches
    partial_matches = []
    for item_key, item_data in KNOWLEDGE_BASE["items"].items():
        if item_lower in item_key.lower():
            partial_matches.append((item_key, item_data))
    
    if partial_matches:
        # Return the first partial match
        logger.info(f"Partial item match found: {partial_matches[0][0]}")
        return partial_matches[0][1]
    
    logger.warning(f"No item found for '{item_name}'")
    return {}


def retrieve_spell(spell_name: str) -> Dict[str, Any]:
    """
    Retrieve information about a specific spell.
    
    Args:
        spell_name: The name of the spell to retrieve
        
    Returns:
        The spell information as a dictionary
    """
    # Convert the spell name to lowercase for case-insensitive matching
    spell_lower = spell_name.lower()
    
    # Try direct lookup first
    for spell_key, spell_data in KNOWLEDGE_BASE["spells"].items():
        if spell_lower == spell_key.lower():
            logger.info(f"Spell found: {spell_key}")
            return spell_data
    
    # Try partial matches
    partial_matches = []
    for spell_key, spell_data in KNOWLEDGE_BASE["spells"].items():
        if spell_lower in spell_key.lower():
            partial_matches.append((spell_key, spell_data))
    
    if partial_matches:
        # Return the first partial match
        logger.info(f"Partial spell match found: {partial_matches[0][0]}")
        return partial_matches[0][1]
    
    logger.warning(f"No spell found for '{spell_name}'")
    return {}


def retrieve_lore(topic: str) -> str:
    """
    Retrieve lore information about a specific topic.
    
    Args:
        topic: The topic to retrieve lore about
        
    Returns:
        The lore information as a string
    """
    # Convert the topic to lowercase for case-insensitive matching
    topic_lower = topic.lower()
    
    # Try direct lookup first
    for lore_key, lore_text in KNOWLEDGE_BASE["lore"].items():
        if topic_lower == lore_key.lower():
            logger.info(f"Lore found for '{topic}': {lore_key}")
            return lore_text
    
    # Try partial matches
    partial_matches = []
    for lore_key, lore_text in KNOWLEDGE_BASE["lore"].items():
        if topic_lower in lore_key.lower():
            partial_matches.append((lore_key, lore_text))
            
    # Also check for topics mentioned within lore entries
    content_matches = []
    for lore_key, lore_text in KNOWLEDGE_BASE["lore"].items():
        if topic_lower in lore_text.lower():
            content_matches.append((lore_key, lore_text))
    
    # Return a partial match if found
    if partial_matches:
        logger.info(f"Partial lore match found for '{topic}': {partial_matches[0][0]}")
        return partial_matches[0][1]
    
    # Return a content match if found
    if content_matches:
        logger.info(f"Content lore match found for '{topic}' in entry: {content_matches[0][0]}")
        return content_matches[0][1]
    
    # If no direct match, try to generate some plausible lore
    generated_lore = _generate_plausible_lore(topic)
    if generated_lore:
        logger.info(f"Generated plausible lore for '{topic}'")
        # Store the generated lore for future reference
        KNOWLEDGE_BASE["lore"][topic] = generated_lore
        return generated_lore
    
    logger.warning(f"No lore found for '{topic}'")
    return f"No specific lore found for '{topic}'."


def _generate_plausible_lore(topic: str) -> str:
    """
    Generate plausible lore for a topic not in the knowledge base.
    This demonstrates a more creative approach to RAG when exact matches aren't found.
    
    Args:
        topic: The topic to generate lore about
        
    Returns:
        Generated lore as a string
    """
    # Extract potential subtopics from the main topic
    subtopics = topic.split()
    
    # Check if any of the subtopics match known categories
    is_location = any(word in topic.lower() for word in ["tavern", "inn", "city", "town", "village", "castle", "dungeon", "forest", "mountain", "cave", "temple"])
    is_person = any(word in topic.lower() for word in ["king", "queen", "lord", "lady", "wizard", "witch", "knight", "warrior", "merchant", "prince", "princess", "hero"])
    is_object = any(word in topic.lower() for word in ["sword", "artifact", "tome", "book", "scroll", "jewel", "crown", "orb", "staff", "wand", "amulet", "ring"])
    is_creature = any(word in topic.lower() for word in ["dragon", "beast", "monster", "demon", "devil", "spirit", "undead", "giant", "elemental", "fey"])
    is_faction = any(word in topic.lower() for word in ["guild", "order", "cult", "coven", "clan", "tribe", "kingdom", "empire", "circle", "society", "brotherhood"])
    
    # Generate appropriate lore based on category
    if is_location:
        return _generate_location_lore(topic)
    elif is_person:
        return _generate_person_lore(topic)
    elif is_object:
        return _generate_object_lore(topic)
    elif is_creature:
        return _generate_creature_lore(topic)
    elif is_faction:
        return _generate_faction_lore(topic)
    else:
        # Generic lore generation for uncategorized topics
        return _generate_generic_lore(topic)


def _generate_location_lore(location: str) -> str:
    """Generate lore for a location"""
    location_types = {
        "tavern": [
            f"The {location} is a popular establishment known for its {random.choice(['excellent ale', 'hearty food', 'rowdy patrons', 'mysterious clientele'])}. Located in {random.choice(['the heart of town', 'the seedy district', 'the merchant quarter', 'the outskirts'])}, it's run by {random.choice(['a retired adventurer', 'a jovial halfling', 'a stern dwarf', 'a secretive elf'])}.",
            f"Travelers speak of {location} as a place where {random.choice(['deals are made', 'information is traded', 'adventurers meet', 'secrets are kept'])}. The tavern's distinctive {random.choice(['thatched roof', 'stone architecture', 'wooden beams', 'stained glass windows'])} makes it a landmark in the area."
        ],
        "city": [
            f"{location} stands as one of the {random.choice(['oldest', 'wealthiest', 'most fortified', 'most diverse'])} cities in the region. Known for its {random.choice(['towering spires', 'extensive marketplaces', 'skilled artisans', 'magical academies'])}, the city is ruled by {random.choice(['a council of merchants', 'a noble family', 'an elected mayor', 'a mysterious figure'])}.",
            f"The city of {location} was founded {random.choice(['centuries ago by refugees', 'on the ruins of an ancient civilization', 'as a trading post', 'as a military outpost'])}. Its strategic location makes it {random.choice(['a hub for trade', 'a cultural center', 'a military stronghold', 'a center of learning'])}."
        ],
        "dungeon": [
            f"The {location} is a notorious dungeon said to be filled with {random.choice(['ancient treasures', 'deadly traps', 'forgotten magic', 'terrible monsters'])}. Few who enter have returned to tell tales of its {random.choice(['labyrinthine corridors', 'multiple levels', 'strange phenomena', 'undead guardians'])}.",
            f"Legends claim {location} was once {random.choice(['a dwarf fortress', 'a wizard laboratory', 'a temple to dark gods', 'a prison for magical creatures'])}. Adventurers are drawn to its depths by rumors of {random.choice(['untold riches', 'powerful artifacts', 'forgotten knowledge', 'a gateway to other planes'])}."
        ],
        "forest": [
            f"The {location} stretches for many leagues, its ancient trees home to {random.choice(['elven communities', 'fey creatures', 'territorial druids', 'reclusive beasts'])}. Travelers tell of {random.choice(['paths that shift', 'strange lights at night', 'enchanted clearings', 'trees that whisper secrets'])}.",
            f"Few dare to venture deep into {location}, for its {random.choice(['twisted paths', 'dense canopy', 'magical mists', 'territorial guardians'])} have claimed many unwary travelers. Those who respect the forest speak of its {random.choice(['natural bounty', 'healing springs', 'ancient wisdom', 'protective spirits'])}."
        ]
    }
    
    # Determine location type
    location_type = None
    for loc_type in location_types.keys():
        if loc_type in location.lower():
            location_type = loc_type
            break
    
    # Use tavern as default if no match
    if location_type is None:
        location_type = "tavern"
        
    # Select a random lore entry for this location type
    return random.choice(location_types[location_type])


def _generate_person_lore(person: str) -> str:
    """Generate lore for a person"""
    person_types = {
        "wizard": [
            f"{person} is a {random.choice(['reclusive', 'eccentric', 'renowned', 'mysterious'])} wizard known for {random.choice(['mastery of elemental magic', 'controversial magical experiments', 'prophetic visions', 'collecting rare magical artifacts'])}. Those who have met the wizard speak of {random.choice(['piercing eyes that see beyond the veil', 'hands marked with arcane symbols', 'the ability to speak with spirits', 'peculiar familiars that follow everywhere'])}.",
            f"The wizard {person} has lived for {random.choice(['centuries', 'longer than anyone remembers', 'three human lifetimes', 'an unnaturally long time'])}, leading to rumors of {random.choice(['a pact with otherworldly beings', 'the discovery of immortality elixirs', 'being trapped between life and death', 'secretly being a dragon in human form'])}."
        ],
        "king": [
            f"King {person} rules with {random.choice(['an iron fist', 'wisdom and compassion', 'cunning and guile', 'divine authority'])}. The kingdom has {random.choice(['prospered under his reign', 'suffered from his tyranny', 'expanded its borders aggressively', 'maintained peace with neighboring realms'])} for {random.choice(['decades', 'a generation', 'only a few years', 'longer than expected'])}.",
            f"The lineage of King {person} traces back to {random.choice(['ancient heroes', 'the first human kingdoms', 'divine blessing', 'a magical bloodline'])}. His court is known for {random.choice(['lavish celebrations', 'strict protocol', 'political intrigue', 'magical advisors'])}."
        ],
        "merchant": [
            f"{person} is a {random.choice(['shrewd', 'generous', 'well-connected', 'mysterious'])} merchant who deals in {random.choice(['exotic goods from distant lands', 'rare magical components', 'information as often as wares', 'items with curious histories'])}. Their {random.choice(['network of contacts', 'fleet of ships', 'chain of trading posts', 'guild connections'])} makes them a valuable ally—or a dangerous enemy.",
            f"The merchant known as {person} rose from {random.choice(['humble beginnings', 'the ashes of tragedy', 'a life of crime', 'foreign shores'])} to become one of the wealthiest individuals in the region. Rumors suggest that their success comes from {random.choice(['a magical ledger that predicts market changes', 'deals with supernatural entities', 'blackmail of noble families', 'discovery of ancient treasure'])}."
        ],
        "hero": [
            f"Tales of {person}'s heroic deeds include {random.choice(['slaying a legendary monster', 'breaking an ancient curse', 'saving a noble family', 'uncovering a sinister plot'])}. Bards sing of their {random.choice(['unmatched combat prowess', 'clever tactics', 'inspiring leadership', 'selfless sacrifice'])} in the face of overwhelming odds.",
            f"The hero known as {person} carries {random.choice(['an ancestral weapon of great power', 'scars from countless battles', 'tokens from those they have saved', 'a mysterious legacy'])}. Some say they were {random.choice(['chosen by destiny', 'born under a special star', 'blessed by the gods', 'the subject of an ancient prophecy'])}."
        ]
    }
    
    # Determine person type
    person_type = None
    for p_type in person_types.keys():
        if p_type in person.lower():
            person_type = p_type
            break
    
    # Use hero as default if no match
    if person_type is None:
        person_type = "hero"
        
    # Select a random lore entry for this person type
    return random.choice(person_types[person_type])


def _generate_object_lore(object_name: str) -> str:
    """Generate lore for an object"""
    object_types = {
        "sword": [
            f"The {object_name} is a legendary blade said to have been {random.choice(['forged in dragon fire', 'crafted by master dwarven smiths', 'blessed by forgotten gods', 'quenched in the blood of a demon'])}. Its wielder gains {random.choice(['supernatural speed', 'the ability to sense danger', 'resistance to magical attacks', 'visions of past wielders'])}.",
            f"Warriors speak in hushed tones of {object_name}, a sword that {random.choice(['glows in the presence of specific enemies', 'cuts through magical barriers', 'never dulls or breaks', 'whispers secrets to its wielder'])}. Its last known owner was {random.choice(['a famous hero who disappeared mysteriously', 'a tyrant who met a fitting end', 'a noble house now fallen into obscurity', 'a temple guardian sworn to eternal vigilance'])}."
        ],
        "artifact": [
            f"The {object_name} is an ancient artifact dating back to {random.choice(['the Age of Dragons', 'before humans walked the world', 'a forgotten empire', 'the creation of the world'])}. Scholars believe it can {random.choice(['reveal hidden truths', 'open doorways between worlds', 'bind powerful entities', 'alter the flow of time'])} when activated properly.",
            f"Few know the true origins of the {object_name}, though many have sought to {random.choice(['unlock its power', 'study its inscriptions', 'claim it for themselves', 'return it to its rightful place'])}. What is known is that it {random.choice(['appears in ancient texts', 'radiates a strange energy', 'changes its appearance subtly', 'calls to those with certain bloodlines'])}."
        ],
        "tome": [
            f"The {object_name} contains knowledge of {random.choice(['forgotten magical traditions', 'realms beyond mortal understanding', 'rituals of immense power', 'secrets that mortal minds were not meant to comprehend'])}. Those who have read from its pages speak of {random.choice(['visions that haunt their dreams', 'insights that changed their understanding', 'voices that whisper from the text', 'symbols that burn themselves into memory'])}.",
            f"Written in {random.choice(['a language thought lost to time', 'ink that seems to shift and move', 'blood of an unknown creature', 'cipher that reveals different text to different readers'])}, the {object_name} has passed through the hands of {random.choice(['many powerful spellcasters', 'secret societies', 'collectors of forbidden knowledge', 'those marked by prophecy'])} throughout history."
        ],
        "amulet": [
            f"The {object_name} is said to protect its wearer from {random.choice(['certain types of magic', 'the influence of specific entities', 'curses and hexes', 'scrying and magical detection'])}. Crafted by {random.choice(['an ancient order of mages', 'a forgotten civilization', 'a being from another plane', 'a deity for their champion'])}, its symbols and materials suggest connections to {random.choice(['elemental forces', 'celestial bodies', 'life and death', 'fate and destiny'])}.",
            f"Legends say the {object_name} can {random.choice(['reveal invisible beings', 'open sealed doorways', 'commune with the departed', 'store spells for later use'])} in the hands of one who knows its secrets. It has appeared throughout history at {random.choice(['moments of great crisis', 'the rise and fall of empires', 'the birth of important figures', 'the discovery of new magic'])}."
        ]
    }
    
    # Determine object type
    object_type = None
    for o_type in object_types.keys():
        if o_type in object_name.lower():
            object_type = o_type
            break
    
    # Use artifact as default if no match
    if object_type is None:
        object_type = "artifact"
        
    # Select a random lore entry for this object type
    return random.choice(object_types[object_type])


def _generate_creature_lore(creature: str) -> str:
    """Generate lore for a creature"""
    creature_types = {
        "dragon": [
            f"{creature}s are among the most {random.choice(['feared', 'respected', 'ancient', 'intelligent'])} creatures in existence, known for their {random.choice(['immense hoards of treasure', 'mastery of arcane magic', 'territorial nature', 'long memories'])}. They can live for {random.choice(['thousands of years', 'millennia', 'countless generations', 'epochs'])}, growing ever larger and more powerful.",
            f"Legends speak of {creature}s that can {random.choice(['take humanoid form', 'control the weather', 'speak all languages', 'see into the future'])}. Their lairs are typically {random.choice(['hidden in remote mountains', 'deep within ancient forests', 'on islands surrounded by treacherous waters', 'in caverns beneath the earth'])} and filled with traps and servants to protect their treasures."
        ],
        "undead": [
            f"The {creature} arises from {random.choice(['violent death', 'unfinished business', 'dark magic', 'ancient curses'])}. Unlike mindless zombies, these entities retain {random.choice(['fragments of memory', 'twisted personalities', 'malevolent intelligence', 'specific obsessions'])} from their living days.",
            f"Those who encounter a {creature} often report {random.choice(['bone-chilling cold', 'overwhelming dread', 'whispers of the damned', 'distortions in reality'])} before the entity appears. Folklore suggests they can be {random.choice(['repelled by specific herbs', 'trapped in mirrors', 'bound by their true name', 'destroyed only by addressing their unfinished business'])}."
        ],
        "fey": [
            f"The {creature} hails from the Feywild, a realm where {random.choice(['emotion becomes reality', 'time flows differently', 'beauty and danger intertwine', 'promises have power'])}. These beings are known for their {random.choice(['capricious nature', 'love of bargains and pacts', 'hatred of iron', 'fascination with mortals'])}.",
            f"Encounters with a {creature} often leave mortals {random.choice(['missing time', 'speaking in riddles', 'unable to lie', 'with memories that fade like dreams'])}. They are bound by {random.choice(['ancient rules of hospitality', 'the power of true names', 'inability to break their word', 'cycles of debt and repayment'])} that mortals would do well to understand before dealing with them."
        ],
        "elemental": [
            f"The {creature} embodies the essence of {random.choice(['primordial fire', 'eternal earth', 'endless air', 'depthless water'])}, existing as {random.choice(['raw energy given form', 'living manifestation of a fundamental force', 'sentience born from elemental chaos', 'an aspect of nature itself'])}.",
            f"When a {creature} appears in the material plane, it often {random.choice(['heralds natural disasters', 'signals a weakening between worlds', 'has been summoned for a purpose', 'seeks to return to its native plane'])}. Those with knowledge of elemental binding may {random.choice(['compel it to service', 'communicate with its alien mind', 'redirect its power', 'send it back to its home plane'])}."
        ]
    }
    
    # Determine creature type
    creature_type = None
    for c_type in creature_types.keys():
        if c_type in creature.lower():
            creature_type = c_type
            break
    
    # Use dragon as default if no match
    if creature_type is None:
        creature_type = "dragon"
        
    # Select a random lore entry for this creature type
    return random.choice(creature_types[creature_type])


def _generate_faction_lore(faction: str) -> str:
    """Generate lore for a faction"""
    faction_types = {
        "guild": [
            f"The {faction} unites practitioners of {random.choice(['a specific trade', 'various crafts', 'merchants and traders', 'specialized skills'])} under a hierarchy of {random.choice(['masters and apprentices', 'elected officials', 'merit-based ranks', 'secretive leadership'])}. Members benefit from {random.choice(['shared resources', 'collective bargaining power', 'protection from competition', 'access to rare materials'])}.",
            f"Founded {random.choice(['centuries ago', 'in response to oppression', 'by a visionary master', 'through a merger of smaller groups'])}, the {faction} maintains {random.choice(['strict quality standards', 'elaborate initiation rituals', 'a network of guild houses', 'influence over local politics'])} to ensure its continued prosperity."
        ],
        "order": [
            f"The {faction} is a disciplined organization dedicated to {random.choice(['martial excellence', 'specific religious ideals', 'arcane study', 'protecting an ancient secret'])}. Members undergo {random.choice(['years of rigorous training', 'tests of faith and character', 'magical binding rituals', 'oaths of loyalty and service'])} before being fully accepted.",
            f"Throughout its history, the {faction} has {random.choice(['served kings and queens', 'operated from the shadows', 'accumulated vast knowledge', 'guarded against specific threats'])}. Their distinctive {random.choice(['regalia', 'fighting style', 'philosophies', 'artifacts'])} mark them as part of a tradition that stretches back to {random.choice(['legendary founders', 'a divine mandate', 'a historic crisis', 'an ancient pact'])}."
        ],
        "cult": [
            f"The {faction} venerates {random.choice(['a forgotten deity', 'an elder entity', 'forbidden knowledge', 'apocalyptic prophecies'])} through {random.choice(['secretive rituals', 'public displays of devotion', 'sacrifice and offerings', 'the collection of specific artifacts'])}. Leaders maintain control through {random.choice(['promises of power', 'fear and intimidation', 'genuine charisma', 'supernatural abilities'])}.",
            f"Those who have investigated the {faction} report {random.choice(['disturbing transformations among members', 'communities infiltrated at all levels', 'connections to unexplained phenomena', 'more influence than their numbers would suggest'])}. Their true goals may include {random.choice(['bringing about a specific event', 'opening a gateway', 'resurrecting an ancient power', 'transforming reality itself'])}."
        ],
        "kingdom": [
            f"The {faction} spans {random.choice(['fertile valleys and plains', 'mountain strongholds', 'coastal trading ports', 'dense forests and wild frontiers'])}, unified under the rule of {random.choice(['a dynasty centuries old', 'recently established conquerors', 'an elected monarchy', 'a regent council'])}. Its people are known for {random.choice(['craftsmanship', 'military tradition', 'magical aptitude', 'religious devotion'])}.",
            f"Relations between the {faction} and neighboring realms are {random.choice(['tense with frequent border disputes', 'peaceful but wary', 'built on strong trade alliances', 'defined by ancient treaties'])}. Within its borders, {random.choice(['strict class divisions', 'relative equality', 'regional autonomy', 'competing noble houses'])} shape daily life and politics."
        ]
    }
    
    # Determine faction type
    faction_type = None
    for f_type in faction_types.keys():
        if f_type in faction.lower():
            faction_type = f_type
            break
    
    # Use guild as default if no match
    if faction_type is None:
        faction_type = "guild"
        
    # Select a random lore entry for this faction type
    return random.choice(faction_types[faction_type])


def _generate_generic_lore(topic: str) -> str:
    """Generate generic lore for uncategorized topics"""
    generic_templates = [
        f"Scholars debate the significance of {topic}, with some claiming it {random.choice(['dates back to forgotten ages', 'holds a key role in ancient prophecies', 'appears in myths across different cultures', 'was mentioned in texts predating current civilizations'])}.",
        
        f"Legends surrounding {topic} vary widely across regions, though most agree it is connected to {random.choice(['powerful magic', 'historical turning points', 'the influence of otherworldly beings', 'cycles of fate that shape the world'])}.",
        
        f"Those who have studied {topic} often note its connection to {random.choice(['celestial movements', 'elemental forces', 'the boundary between planes', 'patterns that repeat throughout history'])}. Such knowledge is typically preserved by {random.choice(['secretive orders', 'scholarly institutions', 'oral traditions', 'encoded in ancient monuments'])}.",
        
        f"Mention of {topic} appears in {random.choice(['dusty tomes of forgotten lore', 'songs passed down through generations', 'cryptic prophecies', 'the teachings of esoteric traditions'])}, suggesting it may be {random.choice(['older than currently believed', 'more significant than commonly recognized', 'misunderstood by modern scholars', 'tied to events yet to unfold'])}."
    ]
    
    return random.choice(generic_templates)


def search_knowledge_base(query: str, knowledge_type: str = None) -> List[Dict[str, Any]]:
    """
    Search the knowledge base for relevant information.
    
    Args:
        query: The search query
        knowledge_type: Optional type of knowledge to search ("rules", "monsters", etc.)
        
    Returns:
        List of dictionaries with matching information
    """
    # Convert query to lowercase for case-insensitive matching
    query_lower = query.lower()
    
    results = []
    
    # If knowledge_type is specified, only search that type
    if knowledge_type:
        if knowledge_type == "rules":
            for rule_key, rule_text in KNOWLEDGE_BASE["rules"].items():
                if query_lower in rule_key.lower() or query_lower in rule_text.lower():
                    results.append({
                        "type": "rule",
                        "name": rule_key,
                        "content": rule_text
                    })
        elif knowledge_type == "monsters":
            for monster_key, monster_data in KNOWLEDGE_BASE["monsters"].items():
                if query_lower in monster_key.lower() or query_lower in monster_data.get("description", "").lower():
                    results.append({
                        "type": "monster",
                        "name": monster_key,
                        "content": monster_data
                    })
        elif knowledge_type == "items":
            for item_key, item_data in KNOWLEDGE_BASE["items"].items():
                if query_lower in item_key.lower() or query_lower in item_data.get("description", "").lower():
                    results.append({
                        "type": "item",
                        "name": item_key,
                        "content": item_data
                    })
        elif knowledge_type == "spells":
            for spell_key, spell_data in KNOWLEDGE_BASE["spells"].items():
                if query_lower in spell_key.lower() or query_lower in spell_data.get("description", "").lower():
                    results.append({
                        "type": "spell",
                        "name": spell_key,
                        "content": spell_data
                    })
        elif knowledge_type == "lore":
            for lore_key, lore_text in KNOWLEDGE_BASE["lore"].items():
                if query_lower in lore_key.lower() or query_lower in lore_text.lower():
                    results.append({
                        "type": "lore",
                        "name": lore_key,
                        "content": lore_text
                    })
    else:
        # Search all knowledge types if not specified
        # Search rules
        for rule_key, rule_text in KNOWLEDGE_BASE["rules"].items():
            if query_lower in rule_key.lower() or query_lower in rule_text.lower():
                results.append({
                    "type": "rule",
                    "name": rule_key,
                    "content": rule_text
                })
                
        # Search monsters
        for monster_key, monster_data in KNOWLEDGE_BASE["monsters"].items():
            if query_lower in monster_key.lower() or query_lower in monster_data.get("description", "").lower():
                results.append({
                    "type": "monster",
                    "name": monster_key,
                    "content": monster_data
                })
                
        # Search items
        for item_key, item_data in KNOWLEDGE_BASE["items"].items():
            if query_lower in item_key.lower() or query_lower in item_data.get("description", "").lower():
                results.append({
                    "type": "item",
                    "name": item_key,
                    "content": item_data
                })
                
        # Search spells
        for spell_key, spell_data in KNOWLEDGE_BASE["spells"].items():
            if query_lower in spell_key.lower() or query_lower in spell_data.get("description", "").lower():
                results.append({
                    "type": "spell",
                    "name": spell_key,
                    "content": spell_data
                })
                
        # Search lore
        for lore_key, lore_text in KNOWLEDGE_BASE["lore"].items():
            if query_lower in lore_key.lower() or query_lower in lore_text.lower():
                results.append({
                    "type": "lore",
                    "name": lore_key,
                    "content": lore_text
                })
    
    logger.info(f"Search for '{query}' returned {len(results)} results")
    return results


def list_all_knowledge_entries(knowledge_type: str) -> List[str]:
    """
    List all entries in a specific knowledge type.
    
    Args:
        knowledge_type: Type of knowledge to list ("rules", "monsters", etc.)
        
    Returns:
        List of entry names
    """
    if knowledge_type not in KNOWLEDGE_BASE:
        return []
        
    return sorted(list(KNOWLEDGE_BASE[knowledge_type].keys()))


# Function to add new knowledge to the knowledge base
def add_knowledge_entry(knowledge_type: str, name: str, content: Union[str, Dict[str, Any]]) -> bool:
    """
    Add a new entry to the knowledge base.
    
    Args:
        knowledge_type: Type of knowledge to add ("rules", "monsters", etc.)
        name: Name/key for the new entry
        content: Content of the entry (string or dictionary)
        
    Returns:
        True if added successfully, False otherwise
    """
    if knowledge_type not in KNOWLEDGE_BASE:
        logger.error(f"Invalid knowledge type: {knowledge_type}")
        return False
        
    if name in KNOWLEDGE_BASE[knowledge_type]:
        logger.warning(f"Entry '{name}' already exists in {knowledge_type}")
        return False
        
    KNOWLEDGE_BASE[knowledge_type][name] = content
    logger.info(f"Added new {knowledge_type} entry: {name}")
    return True


# Function to update an existing knowledge entry
def update_knowledge_entry(knowledge_type: str, name: str, content: Union[str, Dict[str, Any]]) -> bool:
    """
    Update an existing entry in the knowledge base.
    
    Args:
        knowledge_type: Type of knowledge to update ("rules", "monsters", etc.)
        name: Name/key of the entry to update
        content: New content for the entry (string or dictionary)
        
    Returns:
        True if updated successfully, False otherwise
    """
    if knowledge_type not in KNOWLEDGE_BASE:
        logger.error(f"Invalid knowledge type: {knowledge_type}")
        return False
        
    if name not in KNOWLEDGE_BASE[knowledge_type]:
        logger.warning(f"Entry '{name}' not found in {knowledge_type}")
        return False
        
    KNOWLEDGE_BASE[knowledge_type][name] = content
    logger.info(f"Updated {knowledge_type} entry: {name}")
    return True


# Function to delete a knowledge entry
def delete_knowledge_entry(knowledge_type: str, name: str) -> bool:
    """
    Delete an entry from the knowledge base.
    
    Args:
        knowledge_type: Type of knowledge to delete from ("rules", "monsters", etc.)
        name: Name/key of the entry to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    if knowledge_type not in KNOWLEDGE_BASE:
        logger.error(f"Invalid knowledge type: {knowledge_type}")
        return False
        
    if name not in KNOWLEDGE_BASE[knowledge_type]:
        logger.warning(f"Entry '{name}' not found in {knowledge_type}")
        return False
        
    del KNOWLEDGE_BASE[knowledge_type][name]
    logger.info(f"Deleted {knowledge_type} entry: {name}")
    return True

def retrieve_quest_templates(quest_type: str = None) -> List[Dict[str, Any]]:
    """
    Retrieve quest templates based on quest type.
    
    Args:
        quest_type: Optional type of quest (rescue, fetch, kill, etc.)
        
    Returns:
        List of quest templates
    """
    # Quest template database
    quest_templates = {
        "rescue": [
            {
                "title": "The Missing Villager",
                "hook": "A local villager has gone missing in the nearby {location}. Their family fears the worst.",
                "objective": "Rescue the missing villager from {enemy_group} that have taken them captive.",
                "challenges": ["Navigate through dangerous territory", "Defeat or avoid the captors", "Escort the villager safely home"],
                "rewards": {"gold": "250", "items": ["Potion of Healing", "Local favor"]}
            },
            {
                "title": "Noble in Distress",
                "hook": "The son/daughter of a prominent noble family has been kidnapped by {enemy_group}.",
                "objective": "Rescue the noble from their kidnappers in the {location}.",
                "challenges": ["Track down the kidnappers' hideout", "Deal with the ransom exchange", "Ensure the noble's safety"],
                "rewards": {"gold": "500", "items": ["Letter of recommendation", "Fine jewelry"]}
            }
        ],
        "fetch": [
            {
                "title": "The Lost Artifact",
                "hook": "A valuable artifact has been lost in the {location}. It must be recovered before it falls into the wrong hands.",
                "objective": "Find and retrieve the artifact from the {location}.",
                "challenges": ["Solve ancient puzzles", "Avoid traps", "Compete with rival treasure hunters"],
                "rewards": {"gold": "300", "items": ["Magic scroll", "Historical knowledge"]}
            },
            {
                "title": "Rare Ingredients",
                "hook": "A local alchemist needs rare ingredients that can only be found in the {location}.",
                "objective": "Collect the rare ingredients and return them safely.",
                "challenges": ["Identify the correct specimens", "Brave hazardous terrain", "Preserve the fragile ingredients"],
                "rewards": {"gold": "200", "items": ["Potion of your choice", "Alchemist's favor"]}
            }
        ],
        "kill": [
            {
                "title": "Beast Hunt",
                "hook": "A dangerous beast has been terrorizing the countryside around {location}.",
                "objective": "Track and kill the beast that's threatening the area.",
                "challenges": ["Track the elusive creature", "Prepare for its special abilities", "Deliver proof of the kill"],
                "rewards": {"gold": "400", "items": ["Trophy from the beast", "Local renown"]}
            },
            {
                "title": "Bandit Leader",
                "hook": "A notorious bandit leader and their gang have set up in the {location}.",
                "objective": "Eliminate the bandit leader to restore safety to the region.",
                "challenges": ["Find the hidden bandit camp", "Deal with the leader's bodyguards", "Decide the fate of surrendering bandits"],
                "rewards": {"gold": "350", "items": ["Bandit's weapon", "Recovered stolen goods"]}
            }
        ],
        "escort": [
            {
                "title": "Merchant Caravan",
                "hook": "A merchant needs protection for their caravan traveling through {location}.",
                "objective": "Safely escort the merchant caravan to its destination.",
                "challenges": ["Defend against bandit attacks", "Navigate difficult terrain", "Manage resources for the journey"],
                "rewards": {"gold": "300", "items": ["Trade discount", "Exotic goods"]}
            },
            {
                "title": "Pilgrim's Journey",
                "hook": "A pilgrim wishes to visit a sacred site in the dangerous {location}.",
                "objective": "Escort the pilgrim safely to the sacred site and back.",
                "challenges": ["Protect the vulnerable pilgrim", "Respect religious customs", "Deal with hostile locals"],
                "rewards": {"gold": "250", "items": ["Religious blessing", "Ancient wisdom"]}
            }
        ],
        "investigate": [
            {
                "title": "Strange Occurrences",
                "hook": "Unusual events have been happening in {location}, causing concern among locals.",
                "objective": "Investigate the strange occurrences and discover their cause.",
                "challenges": ["Gather witness testimonies", "Connect seemingly unrelated events", "Confront the truth"],
                "rewards": {"gold": "350", "items": ["Mysterious clue", "Local gratitude"]}
            },
            {
                "title": "Missing Shipment",
                "hook": "A valuable shipment has disappeared on its way to {location}.",
                "objective": "Discover what happened to the missing shipment.",
                "challenges": ["Follow the trail of evidence", "Question suspects", "Determine if theft or accident"],
                "rewards": {"gold": "400", "items": ["Finder's fee", "Merchant guild favor"]}
            }
        ],
        "defend": [
            {
                "title": "Village Under Siege",
                "hook": "A small village near {location} is threatened by an imminent attack.",
                "objective": "Help the villagers prepare defenses and repel the attack.",
                "challenges": ["Organize villagers", "Set up defensive positions", "Lead the defense"],
                "rewards": {"gold": "350", "items": ["Village elder's heirloom", "Safe haven"]}
            },
            {
                "title": "Last Stand",
                "hook": "An important location in {location} must be held against overwhelming odds.",
                "objective": "Defend the position until reinforcements arrive.",
                "challenges": ["Manage limited resources", "Maintain morale", "Strategic positioning"],
                "rewards": {"gold": "500", "items": ["Military commendation", "Tactical advantage"]}
            }
        ]
    }
    
    # If quest type is specified, return templates of that type
    if quest_type and quest_type.lower() in quest_templates:
        return quest_templates[quest_type.lower()]
    
    # If no quest type specified or not found, return a random selection
    all_templates = []
    for templates in quest_templates.values():
        all_templates.extend(templates)
    
    # Return all templates or a random subset
    if not quest_type:
        return all_templates
    else:
        # Return a random selection if the specific type wasn't found
        return random.sample(all_templates, min(3, len(all_templates)))

def retrieve_location_info(location_name: str) -> Dict[str, Any]:
    """
    Retrieve information about a specific location.
    
    Args:
        location_name: The name of the location
        
    Returns:
        Dictionary containing location information
    """
    # Location database
    locations = {
        "dark forest": {
            "type": "wilderness",
            "description": "A dense forest where sunlight struggles to reach the ground. Ancient trees tower overhead, their gnarled branches creating a canopy that blocks the sky. The forest floor is covered in twisted roots, fallen logs, and patches of phosphorescent fungi.",
            "inhabitants": ["Wolves", "Forest Goblins", "Giant Spiders", "Fey Creatures"],
            "features": ["Ancient ruins", "Twisted trees", "Mysterious shrines", "Fog-filled clearings"],
            "dangers": ["Getting lost in the shifting paths", "Predatory beasts", "Territorial fey", "Poisonous plants"],
            "atmosphere": "Eerie and primeval, with strange sounds echoing through the trees and shadows that seem to move of their own accord."
        },
        "ancient ruins": {
            "type": "dungeon",
            "description": "The crumbling remains of a once-great civilization, now reclaimed by nature and darker forces. Fallen columns, shattered statues, and walls covered in mysterious carvings create a labyrinth of stone and shadow.",
            "inhabitants": ["Undead", "Cultists", "Treasure Hunters", "Ancient Guardians"],
            "features": ["Hidden chambers", "Trapped passages", "Forgotten treasures", "Ancient magic"],
            "dangers": ["Collapsing structures", "Magical anomalies", "Awakened guardians", "Cursed artifacts"],
            "atmosphere": "A heavy sense of history and decay, with the weight of forgotten ages pressing down on all who enter."
        },
        "mountain pass": {
            "type": "wilderness",
            "description": "A narrow route winding between towering peaks, offering the only safe passage through the treacherous mountain range. Sheer cliffs rise on either side, and the path frequently narrows to barely the width of a cart.",
            "inhabitants": ["Mountain Goblins", "Griffons", "Rock Trolls", "Dwarf Patrols"],
            "features": ["Breathtaking vistas", "Precarious bridges", "Hidden caves", "Avalanche-prone slopes"],
            "dangers": ["Falling rocks", "Sudden storms", "Ambush points", "Treacherous footing"],
            "atmosphere": "Exposed and vulnerable, with howling winds that carry echoes for miles and the constant awareness of being watched from above."
        },
        "coastal caves": {
            "type": "dungeon",
            "description": "A network of sea caves carved by centuries of relentless waves. The lower chambers flood with the rising tide, while the upper passages wind deep into the coastal cliffs. Salt crystals glitter on the walls, and the constant sound of dripping water and distant surf creates an otherworldly melody.",
            "inhabitants": ["Smugglers", "Sahuagin", "Pirates", "Cave Fisher"],
            "features": ["Underwater passages", "Hidden smuggler caches", "Natural bridges", "Bioluminescent fungi"],
            "dangers": ["Rising tides", "Slippery rocks", "Cave-ins", "Territorial sea creatures"],
            "atmosphere": "Damp and echoing, with the rhythmic sound of waves a constant reminder of the sea's power and the taste of salt on every breath."
        },
        "desert oasis": {
            "type": "settlement",
            "description": "A lush pocket of greenery amid the vast, merciless desert. Fed by an ancient spring, the oasis supports a small settlement that serves as a vital waypoint for caravans. Palm trees provide precious shade, and the contrast between the verdant growth and surrounding sands is striking.",
            "inhabitants": ["Merchants", "Nomads", "Desert Druids", "Travelers from distant lands"],
            "features": ["Crystal-clear pools", "Date palm groves", "Colorful market tents", "Ancient well"],
            "dangers": ["Water disputes", "Bandits", "Desert predators", "Heat sickness"],
            "atmosphere": "A haven of life and color in the barren wastes, with the constant bustle of travelers and traders creating a multicultural melting pot."
        }
    }
    
    # Convert location name to lowercase for case-insensitive matching
    location_lower = location_name.lower()
    
    # Try direct lookup first
    if location_lower in locations:
        return locations[location_lower]
    
    # Try partial matches
    for loc_key, loc_data in locations.items():
        if location_lower in loc_key or loc_key in location_lower:
            return loc_data
    
    # If no match found, generate a basic location template
    location_types = ["wilderness", "dungeon", "settlement", "sacred site", "battlefield"]
    
    # Generate a basic location description
    if "forest" in location_lower:
        loc_type = "wilderness"
        inhabitants = ["Forest Animals", "Bandits", "Fey Creatures"]
        features = ["Tall trees", "Clearings", "Streams", "Wildlife"]
    elif "ruins" in location_lower or "dungeon" in location_lower or "cave" in location_lower:
        loc_type = "dungeon"
        inhabitants = ["Monsters", "Undead", "Treasure Hunters"]
        features = ["Crumbling walls", "Dark passages", "Ancient artifacts", "Traps"]
    elif "town" in location_lower or "village" in location_lower or "city" in location_lower:
        loc_type = "settlement"
        inhabitants = ["Townspeople", "Merchants", "Guards", "Travelers"]
        features = ["Buildings", "Market", "Inn", "Temple"]
    else:
        loc_type = random.choice(location_types)
        inhabitants = ["Local creatures", "Wandering monsters", "Travelers"]
        features = ["Distinctive landmarks", "Natural features", "Signs of past events"]
    
    return {
        "type": loc_type,
        "description": f"A {loc_type} known as {location_name}.",
        "inhabitants": inhabitants,
        "features": features,
        "dangers": ["Unknown threats", "Natural hazards", "Hostile inhabitants"],
        "atmosphere": "A place of mystery and adventure, waiting to be explored."
    }