# agents/tactical_agent.py

import random
from typing import Dict, List, Any, Optional, Tuple

class TacticalAgent:
    """Agent that makes tactical decisions for enemies in combat"""
    
    def __init__(self, creature: Dict[str, Any], allies: List[Dict[str, Any]], 
                 enemies: List[Dict[str, Any]], environment: str = None):
        """
        Initialize a tactical agent for an enemy creature
        
        Args:
            creature: Stats and data for the creature this agent controls
            allies: List of other friendly creatures
            enemies: List of enemy creatures (typically the players)
            environment: Optional description of the combat environment
        """
        self.creature = creature
        self.allies = allies
        self.enemies = enemies
        self.environment = environment
        
    def determine_action(self) -> Tuple[str, str]:
        """
        Determine the best action for this creature based on tactical considerations
        
        Returns:
            Tuple of (action_type, target_name)
        """
        # Ensure there are valid enemies to target
        valid_enemies = [e for e in self.enemies if e and isinstance(e, dict) and "name" in e]
        
        if not valid_enemies:
            return "idle", ""
            
        # Simple tactical decision-making
        
        # If creature has very low health (< 25%), consider fleeing
        if "hit_points" in self.creature and "max_hit_points" in self.creature:
            max_hp = self.creature.get("max_hit_points", 0)
            if max_hp > 0 and self.creature["hit_points"] / max_hp < 0.25:
                # 50% chance to flee if badly injured
                if random.random() < 0.5:
                    return "flee", ""
        
        # Determine if creature has spells
        has_spells = self.creature.get("spell_name") is not None
        
        # If creature has spells, decide whether to use them
        if has_spells and random.random() < 0.3:  # 30% chance to cast a spell
            # Pick a random enemy as the target for the spell
            target = random.choice(valid_enemies)
            return "spell", target["name"]
        
        # Default: basic attack against a random enemy
        target = random.choice(valid_enemies)
        return "attack", target["name"]