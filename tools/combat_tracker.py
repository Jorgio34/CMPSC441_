"""
Combat Tracker

This module provides tracking and management tools for D&D combat encounters,
including initiative tracking, status effect management, and turn handling.
"""

import random
import re  # Added missing import for regex
from typing import Dict, List, Any, Optional, Tuple
from tools.dice import roll_dice, roll_initiative


class Combatant:
    """Represents a combatant in an encounter (player or enemy)"""
    
    def __init__(self, name: str, ac: int, hp: int, max_hp: int, initiative_mod: int = 0,
                attack_bonus: int = 0, is_player: bool = False, dex_mod: int = 0):
        """Initialize a combatant"""
        self.name = name
        self.ac = ac
        self.hp = hp
        self.max_hp = max_hp
        self.initiative_mod = initiative_mod or dex_mod  # Use dex mod if no initiative mod specified
        self.initiative_roll = 0
        self.is_player = is_player
        self.conditions = []
        self.attack_bonus = attack_bonus
        self.dex_mod = dex_mod
        self.position = {"x": 0, "y": 0}
        self.active = True  # Is the combatant still in the fight?
    
    def roll_initiative(self) -> int:
        """Roll initiative for this combatant"""
        self.initiative_roll = roll_initiative(self.initiative_mod)
        return self.initiative_roll
    
    def take_damage(self, amount: int) -> int:
        """Apply damage to this combatant"""
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.active = False
        return self.hp
    
    def heal(self, amount: int) -> int:
        """Heal this combatant"""
        self.hp = min(self.max_hp, self.hp + amount)
        if self.hp > 0:
            self.active = True
        return self.hp
    
    def add_condition(self, condition: str, duration: int = 1) -> None:
        """Add a condition to this combatant"""
        self.conditions.append({"name": condition, "duration": duration})
    
    def remove_condition(self, condition: str) -> bool:
        """Remove a condition from this combatant"""
        for i, cond in enumerate(self.conditions):
            if cond["name"] == condition:
                self.conditions.pop(i)
                return True
        return False
    
    def update_conditions(self) -> List[Dict[str, Any]]:
        """Update conditions at the end of turn"""
        expired = []
        for i, condition in enumerate(self.conditions):
            if condition["duration"] > 0:
                condition["duration"] -= 1
                if condition["duration"] == 0:
                    expired.append(condition)
        
        # Remove expired conditions
        self.conditions = [c for c in self.conditions if c["duration"] > 0 or c["duration"] < 0]
        
        return expired
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of this combatant"""
        return {
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "hp_percentage": (self.hp / self.max_hp) * 100 if self.max_hp > 0 else 0,
            "conditions": [c["name"] for c in self.conditions],
            "active": self.active,
            "is_player": self.is_player,
            "position": self.position
        }


class CombatTracker:
    """Tracks and manages a combat encounter"""
    
    def __init__(self):
        """Initialize the combat tracker"""
        self.combatants = {}
        self.initiative_order = []
        self.current_turn = 0
        self.round_number = 0
        self.active = False
        self.log = []
    
    def add_combatant(self, combatant: Combatant) -> None:
        """Add a combatant to the encounter"""
        self.combatants[combatant.name] = combatant
    
    def add_player(self, name: str, ac: int, hp: int, initiative_mod: int = 0, dex_mod: int = 0) -> None:
        """Add a player character to the encounter"""
        player = Combatant(name, ac, hp, hp, initiative_mod, is_player=True, dex_mod=dex_mod)
        self.add_combatant(player)
    
    def add_enemy(self, name: str, ac: int, hp: int, initiative_mod: int = 0, attack_bonus: int = 0) -> None:
        """Add an enemy to the encounter"""
        enemy = Combatant(name, ac, hp, hp, initiative_mod, attack_bonus=attack_bonus)
        self.add_combatant(enemy)
    
    def roll_initiative(self) -> List[Tuple[str, int]]:
        """Roll initiative for all combatants"""
        initiative_results = []
        
        for name, combatant in self.combatants.items():
            initiative = combatant.roll_initiative()
            initiative_results.append((name, initiative))
        
        # Sort by initiative roll (high to low)
        initiative_results.sort(key=lambda x: (x[1], self.combatants[x[0]].is_player), reverse=True)
        
        # Update initiative order
        self.initiative_order = [name for name, _ in initiative_results]
        
        return initiative_results
    
    def start_combat(self) -> str:
        """Start the combat encounter"""
        if len(self.combatants) == 0:
            return "No combatants present. Add combatants before starting combat."
        
        # Roll initiative if not already rolled
        if not self.initiative_order:
            self.roll_initiative()
        
        self.active = True
        self.round_number = 1
        self.current_turn = 0
        
        # Add combat start to log
        self.log.append({
            "type": "combat_start",
            "round": self.round_number,
            "message": "Combat begins!"
        })
        
        current = self.get_current_combatant()
        
        return f"Combat begins! Round {self.round_number}\n" \
               f"Initiative order: {', '.join(self.initiative_order)}\n" \
               f"{current.name} is first to act."
    
    def get_current_combatant(self) -> Combatant:
        """Get the combatant whose turn it currently is"""
        if not self.active or not self.initiative_order:
            raise ValueError("Combat not active")
        
        return self.combatants[self.initiative_order[self.current_turn]]
    
    def next_turn(self) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Advance to the next turn"""
        if not self.active:
            return "Combat not active", None
        
        # Update conditions for current combatant
        current = self.get_current_combatant()
        expired_conditions = current.update_conditions()
        
        # Log expired conditions
        if expired_conditions:
            condition_names = [c["name"] for c in expired_conditions]
            self.log.append({
                "type": "condition_expired",
                "combatant": current.name,
                "conditions": condition_names,
                "round": self.round_number,
                "turn": self.current_turn
            })
        
        # Advance to next combatant
        self.current_turn = (self.current_turn + 1) % len(self.initiative_order)
        
        # If we've looped back to the first combatant, advance the round
        if self.current_turn == 0:
            self.round_number += 1
            self.log.append({
                "type": "round_start",
                "round": self.round_number,
                "message": f"Round {self.round_number} begins!"
            })
            
            round_info = {
                "round": self.round_number,
                "message": f"Round {self.round_number} begins!"
            }
        else:
            round_info = None
        
        # Skip defeated combatants
        while not self.combatants[self.initiative_order[self.current_turn]].active:
            self.current_turn = (self.current_turn + 1) % len(self.initiative_order)
            # If we've gone all the way around and found no active combatants, end combat
            if self.current_turn == 0:
                return self.end_combat()
        
        next_combatant = self.get_current_combatant()
        
        # Log turn change
        self.log.append({
            "type": "turn_change",
            "combatant": next_combatant.name,
            "round": self.round_number,
            "turn": self.current_turn
        })
        
        return f"{next_combatant.name}'s turn", round_info
    
    def apply_damage(self, target_name: str, amount: int) -> Dict[str, Any]:
        """Apply damage to a target"""
        if target_name not in self.combatants:
            return {"success": False, "message": f"Target '{target_name}' not found"}
        
        target = self.combatants[target_name]
        old_hp = target.hp
        new_hp = target.take_damage(amount)
        
        # Log damage
        self.log.append({
            "type": "damage",
            "target": target_name,
            "amount": amount,
            "old_hp": old_hp,
            "new_hp": new_hp,
            "round": self.round_number,
            "turn": self.current_turn
        })
        
        # Check if target was defeated
        if old_hp > 0 and new_hp == 0:
            self.log.append({
                "type": "defeat",
                "target": target_name,
                "round": self.round_number,
                "turn": self.current_turn
            })
            
            return {
                "success": True,
                "message": f"{target_name} takes {amount} damage and falls!",
                "old_hp": old_hp,
                "new_hp": new_hp,
                "defeated": True
            }
        
        return {
            "success": True,
            "message": f"{target_name} takes {amount} damage. HP: {new_hp}/{target.max_hp}",
            "old_hp": old_hp,
            "new_hp": new_hp,
            "defeated": False
        }
    
    def apply_healing(self, target_name: str, amount: int) -> Dict[str, Any]:
        """Apply healing to a target"""
        if target_name not in self.combatants:
            return {"success": False, "message": f"Target '{target_name}' not found"}
        
        target = self.combatants[target_name]
        old_hp = target.hp
        new_hp = target.heal(amount)
        
        # Log healing
        self.log.append({
            "type": "healing",
            "target": target_name,
            "amount": amount,
            "old_hp": old_hp,
            "new_hp": new_hp,
            "round": self.round_number,
            "turn": self.current_turn
        })
        
        # Check if target was revived
        if old_hp == 0 and new_hp > 0:
            self.log.append({
                "type": "revive",
                "target": target_name,
                "round": self.round_number,
                "turn": self.current_turn
            })
            
            return {
                "success": True,
                "message": f"{target_name} is healed for {amount} and regains consciousness!",
                "old_hp": old_hp,
                "new_hp": new_hp,
                "revived": True
            }
        
        return {
            "success": True,
            "message": f"{target_name} is healed for {amount}. HP: {new_hp}/{target.max_hp}",
            "old_hp": old_hp,
            "new_hp": new_hp,
            "revived": False
        }
    
    def add_condition(self, target_name: str, condition: str, duration: int = 1) -> Dict[str, Any]:
        """Add a condition to a target"""
        if target_name not in self.combatants:
            return {"success": False, "message": f"Target '{target_name}' not found"}
        
        target = self.combatants[target_name]
        target.add_condition(condition, duration)
        
        # Log condition
        self.log.append({
            "type": "condition_add",
            "target": target_name,
            "condition": condition,
            "duration": duration,
            "round": self.round_number,
            "turn": self.current_turn
        })
        
        if duration > 0:
            message = f"{target_name} is affected by {condition} for {duration} {'turns' if duration > 1 else 'turn'}."
        else:
            message = f"{target_name} is affected by {condition} until removed."
        
        return {
            "success": True,
            "message": message,
            "condition": condition,
            "duration": duration
        }
    
    def remove_condition(self, target_name: str, condition: str) -> Dict[str, Any]:
        """Remove a condition from a target"""
        if target_name not in self.combatants:
            return {"success": False, "message": f"Target '{target_name}' not found"}
        
        target = self.combatants[target_name]
        removed = target.remove_condition(condition)
        
        if removed:
            # Log condition removal
            self.log.append({
                "type": "condition_remove",
                "target": target_name,
                "condition": condition,
                "round": self.round_number,
                "turn": self.current_turn
            })
            
            return {
                "success": True,
                "message": f"{condition} condition removed from {target_name}."
            }
        else:
            return {
                "success": False,
                "message": f"{target_name} is not affected by {condition}."
            }
    
    def get_combat_status(self) -> Dict[str, Any]:
        """Get the current status of the combat encounter"""
        if not self.active:
            return {"active": False, "message": "No active combat"}
        
        combatant_status = []
        for name in self.initiative_order:
            combatant = self.combatants[name]
            status = combatant.get_status()
            status["current_turn"] = (name == self.initiative_order[self.current_turn])
            combatant_status.append(status)
        
        return {
            "active": True,
            "round": self.round_number,
            "current_turn": self.current_turn,
            "current_combatant": self.initiative_order[self.current_turn],
            "combatants": combatant_status
        }
    
    def check_combat_end(self) -> Tuple[bool, str]:
        """Check if combat should end"""
        if not self.active:
            return True, "Combat already ended"
        
        # Count active combatants on each side
        active_players = sum(1 for name, combatant in self.combatants.items() 
                           if combatant.is_player and combatant.active)
        active_enemies = sum(1 for name, combatant in self.combatants.items() 
                           if not combatant.is_player and combatant.active)
        
        if active_players == 0:
            return True, "All players have been defeated!"
        elif active_enemies == 0:
            return True, "All enemies have been defeated!"
        else:
            return False, "Combat continues"
    
    def end_combat(self) -> Tuple[str, Dict[str, Any]]:
        """End the combat encounter"""
        should_end, message = self.check_combat_end()
        
        if should_end or not self.active:
            self.active = False
            
            # Log combat end
            self.log.append({
                "type": "combat_end",
                "round": self.round_number,
                "message": message
            })
            
            # Generate summary
            summary = {
                "rounds": self.round_number,
                "result": message,
                "defeated_combatants": [name for name, combatant in self.combatants.items() if not combatant.active],
                "remaining_combatants": [name for name, combatant in self.combatants.items() if combatant.active]
            }
            
            return f"Combat ends after {self.round_number} rounds. {message}", summary
        
        return "Combat cannot end yet.", None
    
    def reset(self) -> None:
        """Reset the combat tracker for a new encounter"""
        self.combatants = {}
        self.initiative_order = []
        self.current_turn = 0
        self.round_number = 0
        self.active = False
        self.log = []


class Attack:
    """Represents an attack action in combat"""
    
    @staticmethod
    def make_attack(attacker_name: str, target_name: str, tracker: CombatTracker, 
                  attack_bonus: Optional[int] = None, damage_dice: str = "1d8", 
                  damage_bonus: int = 0, advantage: bool = False, 
                  disadvantage: bool = False) -> Dict[str, Any]:
        """
        Make an attack against a target.
        
        Args:
            attacker_name: Name of the attacker
            target_name: Name of the target
            tracker: Combat tracker instance
            attack_bonus: Attack bonus (uses attacker's if None)
            damage_dice: Damage dice expression
            damage_bonus: Additional damage bonus
            advantage: Whether to roll with advantage
            disadvantage: Whether to roll with disadvantage
            
        Returns:
            Result of the attack
        """
        # Get attacker and target
        if attacker_name not in tracker.combatants:
            return {"success": False, "message": f"Attacker '{attacker_name}' not found"}
        
        if target_name not in tracker.combatants:
            return {"success": False, "message": f"Target '{target_name}' not found"}
        
        attacker = tracker.combatants[attacker_name]
        target = tracker.combatants[target_name]
        
        # Use attacker's attack bonus if not provided
        if attack_bonus is None:
            attack_bonus = attacker.attack_bonus
        
        # Roll attack
        if advantage and disadvantage:
            # They cancel each other out
            advantage = disadvantage = False
        
        # Roll the attack
        if advantage:
            roll1 = roll_dice("1d20")
            roll2 = roll_dice("1d20")
            natural_roll = max(roll1, roll2)
            roll_type = "advantage"
        elif disadvantage:
            roll1 = roll_dice("1d20")
            roll2 = roll_dice("1d20")
            natural_roll = min(roll1, roll2)
            roll_type = "disadvantage"
        else:
            natural_roll = roll_dice("1d20")
            roll1 = roll2 = natural_roll
            roll_type = "normal"
        
        # Calculate attack roll
        attack_roll = natural_roll + attack_bonus
        
        # Determine if critical
        is_critical = natural_roll == 20
        is_fumble = natural_roll == 1
        
        # Check if hit
        if is_fumble:
            # Critical miss
            # Log attack
            tracker.log.append({
                "type": "attack",
                "attacker": attacker_name,
                "target": target_name,
                "roll": natural_roll,
                "attack_roll": attack_roll,
                "hit": False,
                "critical_fumble": True,
                "round": tracker.round_number,
                "turn": tracker.current_turn
            })
            
            return {
                "success": True,
                "hit": False,
                "critical_fumble": True,
                "message": f"{attacker_name} critically misses {target_name}! (Rolled {natural_roll})",
                "roll_type": roll_type,
                "rolls": [roll1, roll2],
                "attack_roll": attack_roll
            }
        
        hit = is_critical or attack_roll >= target.ac
        
        if not hit:
            # Miss
            # Log attack
            tracker.log.append({
                "type": "attack",
                "attacker": attacker_name,
                "target": target_name,
                "roll": natural_roll,
                "attack_roll": attack_roll,
                "hit": False,
                "round": tracker.round_number,
                "turn": tracker.current_turn
            })
            
            return {
                "success": True,
                "hit": False,
                "message": f"{attacker_name} misses {target_name}. (Rolled {natural_roll} + {attack_bonus} = {attack_roll}, AC {target.ac})",
                "roll_type": roll_type,
                "rolls": [roll1, roll2],
                "attack_roll": attack_roll
            }
        
        # Hit! Calculate damage
        if is_critical:
            # Double dice on critical hit
            match = re.match(r'^(\d+)d(\d+)', damage_dice)  # Fixed regex pattern
            if match:
                num_dice = int(match.group(1)) * 2
                sides = match.group(2)
                damage_dice = f"{num_dice}d{sides}"
        
        damage = roll_dice(damage_dice) + damage_bonus
        
        # Apply damage
        damage_result = tracker.apply_damage(target_name, damage)
        
        # Log attack
        tracker.log.append({
            "type": "attack",
            "attacker": attacker_name,
            "target": target_name,
            "roll": natural_roll,
            "attack_roll": attack_roll,
            "hit": True,
            "critical": is_critical,
            "damage": damage,
            "damage_dice": damage_dice,
            "damage_bonus": damage_bonus,
            "round": tracker.round_number,
            "turn": tracker.current_turn
        })
        
        # Create result message
        if is_critical:
            hit_type = "critically hits"
        else:
            hit_type = "hits"
            
        message = f"{attacker_name} {hit_type} {target_name}! "
        message += f"(Rolled {natural_roll} + {attack_bonus} = {attack_roll}, AC {target.ac}) "
        message += f"Damage: {damage} ({damage_dice}+{damage_bonus})"
        
        if damage_result.get("defeated", False):
            message += f" {target_name} is defeated!"
        
        return {
            "success": True,
            "hit": True,
            "critical": is_critical,
            "damage": damage,
            "message": message,
            "roll_type": roll_type,
            "rolls": [roll1, roll2],
            "attack_roll": attack_roll,
            "defeated": damage_result.get("defeated", False)
        }


class Spell:
    """Represents a spell casting action in combat"""
    
    @staticmethod
    def cast_damage_spell(caster_name: str, spell_name: str, targets: List[str], 
                        tracker: CombatTracker, damage_dice: str = "2d6", 
                        damage_type: str = "fire", save_type: Optional[str] = None, 
                        save_dc: int = 15, half_on_save: bool = True) -> Dict[str, Any]:
        """
        Cast a damage-dealing spell.
        
        Args:
            caster_name: Name of the spellcaster
            spell_name: Name of the spell
            targets: List of target names
            tracker: Combat tracker instance
            damage_dice: Damage dice expression
            damage_type: Type of damage (e.g., "fire", "cold")
            save_type: Type of saving throw (e.g., "dexterity"), or None for no save
            save_dc: Save DC
            half_on_save: Whether targets take half damage on a successful save
            
        Returns:
            Result of the spell casting
        """
        # Get caster
        if caster_name not in tracker.combatants:
            return {"success": False, "message": f"Caster '{caster_name}' not found"}
        
        # Process each target
        target_results = []
        for target_name in targets:
            if target_name not in tracker.combatants:
                target_results.append({
                    "target": target_name,
                    "hit": False,
                    "message": f"Target '{target_name}' not found"
                })
                continue
            
            target = tracker.combatants[target_name]
            
            # Roll save if applicable
            save_result = None
            if save_type:
                # Roll saving throw (using a simple d20 roll for demo)
                save_roll = roll_dice("1d20")
                save_result = save_roll >= save_dc
            
            # Roll damage
            base_damage = roll_dice(damage_dice)
            
            # Adjust damage based on save
            if save_result and half_on_save:
                damage = base_damage // 2
            else:
                damage = base_damage
            
            # Apply damage
            damage_result = tracker.apply_damage(target_name, damage)
            
            # Create result message
            if save_type:
                if save_result:
                    save_msg = f"{target_name} succeeds on a {save_type} save"
                    if half_on_save:
                        save_msg += f" and takes {damage} {damage_type} damage (half damage)."
                    else:
                        save_msg += "."
                else:
                    save_msg = f"{target_name} fails a {save_type} save and takes {damage} {damage_type} damage."
            else:
                save_msg = f"{target_name} takes {damage} {damage_type} damage."
                
            if damage_result.get("defeated", False):
                save_msg += f" {target_name} is defeated!"
            
            # Log spell effect
            tracker.log.append({
                "type": "spell_effect",
                "caster": caster_name,
                "spell": spell_name,
                "target": target_name,
                "damage_type": damage_type,
                "damage": damage,
                "base_damage": base_damage,
                "save_type": save_type,
                "save_result": save_result,
                "round": tracker.round_number,
                "turn": tracker.current_turn
            })
            
            target_results.append({
                "target": target_name,
                "hit": True,
                "damage": damage,
                "save_type": save_type,
                "save_result": save_result,
                "message": save_msg,
                "defeated": damage_result.get("defeated", False)
            })
        
        # Log spell cast
        tracker.log.append({
            "type": "spell_cast",
            "caster": caster_name,
            "spell": spell_name,
            "targets": targets,
            "damage_dice": damage_dice,
            "damage_type": damage_type,
            "save_type": save_type,
            "save_dc": save_dc,
            "round": tracker.round_number,
            "turn": tracker.current_turn
        })
        
        # Create overall result
        target_msgs = [result["message"] for result in target_results if "message" in result]
        
        return {
            "success": True,
            "message": f"{caster_name} casts {spell_name}!",
            "target_results": target_results,
            "details": "\n".join(target_msgs)
        }
    
    @staticmethod
    def cast_healing_spell(caster_name: str, spell_name: str, targets: List[str],
                         tracker: CombatTracker, healing_dice: str = "1d8+4") -> Dict[str, Any]:
        """
        Cast a healing spell.
        
        Args:
            caster_name: Name of the spellcaster
            spell_name: Name of the spell
            targets: List of target names
            tracker: Combat tracker instance
            healing_dice: Healing dice expression
            
        Returns:
            Result of the spell casting
        """
        # Get caster
        if caster_name not in tracker.combatants:
            return {"success": False, "message": f"Caster '{caster_name}' not found"}
        
        # Process each target
        target_results = []
        for target_name in targets:
            if target_name not in tracker.combatants:
                target_results.append({
                    "target": target_name,
                    "success": False,
                    "message": f"Target '{target_name}' not found"
                })
                continue
            
            # Roll healing
            healing = roll_dice(healing_dice)
            
            # Apply healing
            healing_result = tracker.apply_healing(target_name, healing)
            
            # Create result message
            heal_msg = f"{target_name} regains {healing} hit points."
            if healing_result.get("revived", False):
                heal_msg += f" {target_name} regains consciousness!"
            
            # Log spell effect
            tracker.log.append({
                "type": "healing_effect",
                "caster": caster_name,
                "spell": spell_name,
                "target": target_name,
                "healing": healing,
                "round": tracker.round_number,
                "turn": tracker.current_turn
            })
            
            target_results.append({
                "target": target_name,
                "success": True,
                "healing": healing,
                "message": heal_msg,
                "revived": healing_result.get("revived", False)
            })
        
        # Log spell cast
        tracker.log.append({
            "type": "spell_cast",
            "caster": caster_name,
            "spell": spell_name,
            "targets": targets,
            "healing_dice": healing_dice,
            "round": tracker.round_number,
            "turn": tracker.current_turn
        })
        
        # Create overall result
        target_msgs = [result["message"] for result in target_results if "message" in result]
        
        return {
            "success": True,
            "message": f"{caster_name} casts {spell_name}!",
            "target_results": target_results,
            "details": "\n".join(target_msgs)
        }
    
    @staticmethod
    def cast_condition_spell(caster_name: str, spell_name: str, targets: List[str],
                           tracker: CombatTracker, condition: str, duration: int = 1,
                           save_type: Optional[str] = None, save_dc: int = 15) -> Dict[str, Any]:
        """
        Cast a spell that applies a condition.
        
        Args:
            caster_name: Name of the spellcaster
            spell_name: Name of the spell
            targets: List of target names
            tracker: Combat tracker instance
            condition: Condition to apply (e.g., "frightened", "stunned")
            duration: Duration of the condition in rounds (-1 for until removed)
            save_type: Type of saving throw (e.g., "wisdom"), or None for no save
            save_dc: Save DC
            
        Returns:
            Result of the spell casting
        """
        # Get caster
        if caster_name not in tracker.combatants:
            return {"success": False, "message": f"Caster '{caster_name}' not found"}
        
        # Process each target
        target_results = []
        for target_name in targets:
            if target_name not in tracker.combatants:
                target_results.append({
                    "target": target_name,
                    "success": False,
                    "message": f"Target '{target_name}' not found"
                })
                continue
            
            # Roll save if applicable
            save_result = None
            if save_type:
                # Roll saving throw (using a simple d20 roll for demo)
                save_roll = roll_dice("1d20")
                save_result = save_roll >= save_dc
            
            # Apply condition if no save or failed save
            if not save_type or not save_result:
                condition_result = tracker.add_condition(target_name, condition, duration)
                affected = True
            else:
                affected = False
            
            # Create result message
            if save_type:
                if save_result:
                    condition_msg = f"{target_name} succeeds on a {save_type} save and resists the {condition} condition."
                else:
                    if duration > 0:
                        condition_msg = f"{target_name} fails a {save_type} save and is {condition} for {duration} {'turns' if duration > 1 else 'turn'}."
                    else:
                        condition_msg = f"{target_name} fails a {save_type} save and is {condition} until the condition is removed."
            else:
                if duration > 0:
                    condition_msg = f"{target_name} is {condition} for {duration} {'turns' if duration > 1 else 'turn'}."
                else:
                    condition_msg = f"{target_name} is {condition} until the condition is removed."
            
            # Log spell effect
            tracker.log.append({
                "type": "condition_effect",
                "caster": caster_name,
                "spell": spell_name,
                "target": target_name,
                "condition": condition,
                "duration": duration,
                "save_type": save_type,
                "save_result": save_result,
                "affected": affected,
                "round": tracker.round_number,
                "turn": tracker.current_turn
            })
            
            target_results.append({
                "target": target_name,
                "success": True,
                "affected": affected,
                "save_type": save_type,
                "save_result": save_result,
                "message": condition_msg
            })
        
        # Log spell cast
        tracker.log.append({
            "type": "spell_cast",
            "caster": caster_name,
            "spell": spell_name,
            "targets": targets,
            "condition": condition,
            "duration": duration,
            "save_type": save_type,
            "save_dc": save_dc,
            "round": tracker.round_number,
            "turn": tracker.current_turn
        })
        
        # Create overall result
        target_msgs = [result["message"] for result in target_results if "message" in result]
        
        return {
            "success": True,
            "message": f"{caster_name} casts {spell_name}!",
            "target_results": target_results,
            "details": "\n".join(target_msgs)
        }
    
    

