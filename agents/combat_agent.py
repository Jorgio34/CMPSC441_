"""
Combat Agent

This module implements the Combat Agent, which manages tactical encounters,
initiative tracking, damage calculations, and narrative combat descriptions.
"""

import os
import logging
import random
from typing import Dict, List, Any, Optional, Tuple, Union

from agents.base_agent import BaseAgent, LLMInterface, Memory
from knowledge.retrieval import retrieve_monster, retrieve_rule
from tools.dice import roll_dice
from config.prompts.system_prompts import COMBAT_AGENT_PROMPT


class CombatAgent(BaseAgent):
    """
    Combat Agent that manages combat encounters, tracking initiative,
    calculating damage, and generating narrative descriptions.
    """
    
    def __init__(self, 
                model_name: str = "gpt-4",
                model_params: Optional[Dict[str, Any]] = None,
                knowledge_base: Optional[Any] = None):
        # Initialize base agent
        super().__init__(
            name="CombatAgent",
            system_prompt=COMBAT_AGENT_PROMPT,
            llm=LLMInterface(model_name=model_name),
            tools={
                "roll_dice": roll_dice,
                "retrieve_monster": retrieve_monster,
                "retrieve_rule": retrieve_rule
            },
            model_params=model_params or {}
        )
        
        self.knowledge_base = knowledge_base
        self.logger = logging.getLogger("CombatAgent")
        
        # Combat state tracking
        self.active_combat = False
        self.initiative_order = []
        self.current_turn = 0
        self.round_number = 0
        self.combatants = {}
        self.environment = {}
        
    def initialize_combat(self, 
                         players: List[Dict[str, Any]], 
                         enemies: List[Dict[str, Any]], 
                         environment: Dict[str, Any]) -> str:
        """
        Initialize a new combat encounter with players, enemies, and environment.
        
        Args:
            players: List of player character data dictionaries
            enemies: List of enemy data dictionaries
            environment: Dictionary with environment details
            
        Returns:
            Combat initialization description
        """
        # Reset combat state
        self.active_combat = True
        self.initiative_order = []
        self.current_turn = 0
        self.round_number = 0
        self.combatants = {}
        self.environment = environment
        
        # Process player characters
        for player in players:
            player_id = player.get("name", f"Player_{len(self.combatants)}")
            
            # Create combatant entry
            self.combatants[player_id] = {
                "name": player.get("name", player_id),
                "type": "player",
                "hp": player.get("hp", 10),
                "max_hp": player.get("hp", 10),
                "ac": player.get("ac", 10),
                "initiative_bonus": player.get("initiative_bonus", 0),
                "initiative_roll": 0,  # Will be set during initiative rolling
                "conditions": [],
                "position": player.get("position", {"x": 0, "y": 0}),
                "stats": player.get("stats", {}),
                "abilities": player.get("abilities", [])
            }
        
        # Process enemies
        for enemy in enemies:
            enemy_id = enemy.get("name", f"Enemy_{len(self.combatants)}")
            
            # If the enemy is a monster type, retrieve monster data
            monster_data = {}
            if "monster_type" in enemy:
                monster_data = self.use_tool("retrieve_monster", enemy["monster_type"])
            
            # Determine HP (use provided, or calculate from monster data, or default)
            hp = enemy.get("hp", 0)
            if hp == 0 and "hp" in monster_data:
                # Parse monster HP value (e.g., "59 (7d10 + 21)")
                hp_str = monster_data["hp"]
                hp = int(hp_str.split(" ")[0]) if " " in hp_str else int(hp_str)
            
            if hp == 0:
                # Default HP based on CR if available
                cr = enemy.get("cr", 0)
                if "cr" in monster_data:
                    cr = monster_data["cr"]
                hp = max(1, int(cr) * 15)
            
            # Create combatant entry
            self.combatants[enemy_id] = {
                "name": enemy.get("name", enemy_id),
                "type": "enemy",
                "hp": hp,
                "max_hp": hp,
                "ac": enemy.get("ac", monster_data.get("ac", 10)),
                "initiative_bonus": enemy.get("initiative_bonus", 0),
                "initiative_roll": 0,  # Will be set during initiative rolling
                "conditions": [],
                "position": enemy.get("position", {"x": 0, "y": 0}),
                "stats": enemy.get("stats", monster_data.get("abilities", {})),
                "abilities": enemy.get("abilities", monster_data.get("actions", []))
            }
        
        # Roll initiative for all combatants
        initiative_description = self._roll_initiative()
        
        # Create combat start description
        environment_desc = (
            f"The combat takes place in {environment.get('name', 'an area')}. "
            f"{environment.get('description', '')}"
        )
        
        enemies_desc = self._format_combatant_list([self.combatants[eid] for eid in self.combatants if self.combatants[eid]["type"] == "enemy"])
        
        combat_start = (
            f"Combat begins!\n\n"
            f"{environment_desc}\n\n"
            f"The party faces: {enemies_desc}\n\n"
            f"{initiative_description}\n\n"
            f"Round 1 begins! {self._get_current_combatant()['name']} is up first."
        )
        
        # Add the combat start to memory
        self.add_memory(
            f"Combat initialized with {len(players)} players and {len(enemies)} enemies in {environment.get('name', 'an area')}.",
            memory_type="combat_start"
        )
        
        return combat_start
    
    def _roll_initiative(self) -> str:
        """
        Roll initiative for all combatants and determine turn order.
        
        Returns:
            Initiative order description
        """
        # Roll initiative for each combatant
        for combatant_id, combatant in self.combatants.items():
            initiative_bonus = combatant["initiative_bonus"]
            initiative_roll = self.use_tool("roll_dice", "1d20") + initiative_bonus
            combatant["initiative_roll"] = initiative_roll
        
        # Sort combatants by initiative roll (higher first)
        self.initiative_order = sorted(
            self.combatants.keys(),
            key=lambda cid: (self.combatants[cid]["initiative_roll"], 
                            # Tiebreaker: player characters go before enemies
                            0 if self.combatants[cid]["type"] == "player" else 1),
            reverse=True
        )
        
        # Create initiative description
        initiative_rolls = []
        for cid in self.initiative_order:
            combatant = self.combatants[cid]
            initiative_rolls.append(f"{combatant['name']}: {combatant['initiative_roll']}")
        
        return "Initiative order:\n" + "\n".join(initiative_rolls)
    
    def process_turn(self, action: Dict[str, Any]) -> str:
        """
        Process a combat turn based on the provided action.
        
        Args:
            action: Dictionary with action details
            
        Returns:
            Turn results description
        """
        if not self.active_combat:
            return "No active combat in progress."
        
        # Get the current combatant
        current_combatant = self._get_current_combatant()
        
        # Verify it's the correct combatant's turn
        if action.get("actor") != current_combatant["name"]:
            return f"It's not {action.get('actor')}'s turn. {current_combatant['name']} is currently acting."
        
        # Process different action types
        action_type = action.get("type", "attack")
        
        if action_type == "attack":
            result = self._process_attack_action(action)
        elif action_type == "spell":
            result = self._process_spell_action(action)
        elif action_type == "ability":
            result = self._process_ability_action(action)
        elif action_type == "move":
            result = self._process_move_action(action)
        elif action_type == "dash":
            result = self._process_dash_action(action)
        elif action_type == "disengage":
            result = self._process_disengage_action(action)
        elif action_type == "dodge":
            result = self._process_dodge_action(action)
        elif action_type == "help":
            result = self._process_help_action(action)
        elif action_type == "hide":
            result = self._process_hide_action(action)
        elif action_type == "custom":
            result = self._process_custom_action(action)
        else:
            result = f"{current_combatant['name']} attempts an unknown action type: {action_type}."
        
        # Check for combat end conditions
        if self._check_combat_end():
            self.active_combat = False
            result += "\n\n" + self._generate_combat_end()
            return result
        
        # Advance to the next turn
        self._advance_turn()
        
        # Add turn results to memory
        self.add_memory(
            f"{current_combatant['name']} used {action_type} action. " +
            f"Result: {result[:100]}...",
            memory_type="combat_turn"
        )
        
        next_combatant = self._get_current_combatant()
        result += f"\n\nIt's now {next_combatant['name']}'s turn."
        
        return result
    
    def _process_attack_action(self, action: Dict[str, Any]) -> str:
        """Process an attack action"""
        actor_id = self._get_combatant_id(action.get("actor"))
        target_id = self._get_combatant_id(action.get("target"))
        
        if not actor_id or not target_id:
            return "Invalid actor or target."
        
        actor = self.combatants[actor_id]
        target = self.combatants[target_id]
        
        # Extract attack details
        attack_bonus = action.get("attack_bonus", 0)
        damage_dice = action.get("damage_dice", "1d6")
        damage_bonus = action.get("damage_bonus", 0)
        damage_type = action.get("damage_type", "slashing")
        
        # Roll attack
        attack_roll = self.use_tool("roll_dice", "1d20") + attack_bonus
        critical_hit = attack_roll - attack_bonus == 20
        critical_miss = attack_roll - attack_bonus == 1
        
        # Determine hit or miss
        if critical_miss:
            return self._generate_attack_miss_description(actor, target, action, critical=True)
        
        if attack_roll >= target["ac"] or critical_hit:
            # Hit! Calculate damage
            damage_dice_count = "2" + damage_dice[1:] if critical_hit else damage_dice
            damage = self.use_tool("roll_dice", damage_dice_count) + damage_bonus
            
            # Apply damage to target
            self._apply_damage(target_id, damage)
            
            # Generate hit description
            return self._generate_attack_hit_description(
                actor, target, action, attack_roll, damage, damage_type, critical_hit
            )
        else:
            # Miss
            return self._generate_attack_miss_description(actor, target, action)
    
    def _process_spell_action(self, action: Dict[str, Any]) -> str:
        """Process a spell casting action"""
        actor_id = self._get_combatant_id(action.get("actor"))
        
        if not actor_id:
            return "Invalid actor."
        
        actor = self.combatants[actor_id]
        spell_name = action.get("spell_name", "unknown spell")
        spell_level = action.get("spell_level", 1)
        
        # Handle different spell types
        spell_type = action.get("spell_type", "damage")
        
        if spell_type == "damage":
            return self._process_damage_spell(actor, action)
        elif spell_type == "heal":
            return self._process_healing_spell(actor, action)
        elif spell_type == "buff":
            return self._process_buff_spell(actor, action)
        elif spell_type == "debuff":
            return self._process_debuff_spell(actor, action)
        elif spell_type == "control":
            return self._process_control_spell(actor, action)
        else:
            return f"{actor['name']} casts {spell_name} (level {spell_level}), but the spell's effects are unclear."
    
    def _process_damage_spell(self, actor: Dict[str, Any], action: Dict[str, Any]) -> str:
        """Process a damage-dealing spell"""
        spell_name = action.get("spell_name", "unknown spell")
        targets = action.get("targets", [])
        
        if not targets:
            return f"{actor['name']} casts {spell_name}, but there are no targets."
        
        # Get spell parameters
        damage_dice = action.get("damage_dice", "2d6")
        damage_type = action.get("damage_type", "fire")
        save_type = action.get("save_type", "dexterity")
        save_dc = action.get("save_dc", 13)
        half_on_save = action.get("half_on_save", True)
        
        # Process each target
        target_results = []
        
        for target_name in targets:
            target_id = self._get_combatant_id(target_name)
            if not target_id:
                target_results.append(f"Invalid target: {target_name}")
                continue
                
            target = self.combatants[target_id]
            
            # Roll save if applicable
            save_result = None
            if save_type:
                # Get save bonus (0 by default)
                save_bonus = 0
                if "stats" in target and save_type.lower() in target["stats"]:
                    stat_value = target["stats"][save_type.lower()]
                    save_bonus = (stat_value - 10) // 2
                
                save_roll = self.use_tool("roll_dice", "1d20") + save_bonus
                save_result = save_roll >= save_dc
            
            # Roll damage
            base_damage = self.use_tool("roll_dice", damage_dice)
            
            # Adjust damage based on save
            if save_result and half_on_save:
                damage = base_damage // 2
            else:
                damage = base_damage
            
            # Apply damage
            self._apply_damage(target_id, damage)
            
            # Create result description
            if save_type:
                if save_result:
                    target_results.append(
                        f"{target['name']} makes a {save_type} save and takes {damage} {damage_type} damage."
                    )
                else:
                    target_results.append(
                        f"{target['name']} fails a {save_type} save and takes {damage} {damage_type} damage."
                    )
            else:
                target_results.append(
                    f"{target['name']} takes {damage} {damage_type} damage."
                )
        
        # Combine results
        area_desc = action.get("area_desc", "")
        return (
            f"{actor['name']} casts {spell_name}. {area_desc}\n" +
            "\n".join(target_results)
        )
    
    def _process_healing_spell(self, actor: Dict[str, Any], action: Dict[str, Any]) -> str:
        """Process a healing spell"""
        spell_name = action.get("spell_name", "healing spell")
        targets = action.get("targets", [])
        
        if not targets:
            return f"{actor['name']} casts {spell_name}, but there are no targets."
        
        # Get spell parameters
        healing_dice = action.get("healing_dice", "1d8")
        healing_bonus = action.get("healing_bonus", 0)
        
        # Process each target
        target_results = []
        
        for target_name in targets:
            target_id = self._get_combatant_id(target_name)
            if not target_id:
                target_results.append(f"Invalid target: {target_name}")
                continue
                
            target = self.combatants[target_id]
            
            # Roll healing
            healing = self.use_tool("roll_dice", healing_dice) + healing_bonus
            
            # Apply healing
            self._apply_healing(target_id, healing)
            
            # Create result description
            target_results.append(
                f"{target['name']} regains {healing} hit points."
            )
        
        # Combine results
        return (
            f"{actor['name']} casts {spell_name}.\n" +
            "\n".join(target_results)
        )
    
    def _process_buff_spell(self, actor: Dict[str, Any], action: Dict[str, Any]) -> str:
        """Process a buff spell"""
        spell_name = action.get("spell_name", "buff spell")
        targets = action.get("targets", [])
        
        if not targets:
            return f"{actor['name']} casts {spell_name}, but there are no targets."
        
        # Get spell parameters
        buff_type = action.get("buff_type", "condition")
        buff_value = action.get("buff_value", "blessed")
        duration = action.get("duration", "1 minute")
        
        # Process each target
        target_results = []
        
        for target_name in targets:
            target_id = self._get_combatant_id(target_name)
            if not target_id:
                target_results.append(f"Invalid target: {target_name}")
                continue
                
            target = self.combatants[target_id]
            
            # Apply buff
            if buff_type == "condition":
                if buff_value not in target["conditions"]:
                    target["conditions"].append(buff_value)
            
            # Create result description
            target_results.append(
                f"{target['name']} is affected by {spell_name} and gains {buff_value} for {duration}."
            )
        
        # Combine results
        return (
            f"{actor['name']} casts {spell_name}.\n" +
            "\n".join(target_results)
        )
    
    def _process_debuff_spell(self, actor: Dict[str, Any], action: Dict[str, Any]) -> str:
        """Process a debuff spell"""
        spell_name = action.get("spell_name", "debuff spell")
        targets = action.get("targets", [])
        
        if not targets:
            return f"{actor['name']} casts {spell_name}, but there are no targets."
        
        # Get spell parameters
        debuff_type = action.get("debuff_type", "condition")
        debuff_value = action.get("debuff_value", "frightened")
        save_type = action.get("save_type", "wisdom")
        save_dc = action.get("save_dc", 13)
        duration = action.get("duration", "1 minute")
        
        # Process each target
        target_results = []
        
        for target_name in targets:
            target_id = self._get_combatant_id(target_name)
            if not target_id:
                target_results.append(f"Invalid target: {target_name}")
                continue
                
            target = self.combatants[target_id]
            
            # Roll save if applicable
            save_result = None
            if save_type:
                # Get save bonus (0 by default)
                save_bonus = 0
                if "stats" in target and save_type.lower() in target["stats"]:
                    stat_value = target["stats"][save_type.lower()]
                    save_bonus = (stat_value - 10) // 2
                
                save_roll = self.use_tool("roll_dice", "1d20") + save_bonus
                save_result = save_roll >= save_dc
            
            # Apply debuff if save failed or no save required
            if not save_type or not save_result:
                if debuff_type == "condition" and debuff_value not in target["conditions"]:
                    target["conditions"].append(debuff_value)
                
                if save_type:
                    target_results.append(
                        f"{target['name']} fails a {save_type} save and is afflicted with {debuff_value} for {duration}."
                    )
                else:
                    target_results.append(
                        f"{target['name']} is afflicted with {debuff_value} for {duration}."
                    )
            else:
                target_results.append(
                    f"{target['name']} succeeds on a {save_type} save and resists {spell_name}."
                )
        
        # Combine results
        return (
            f"{actor['name']} casts {spell_name}.\n" +
            "\n".join(target_results)
        )
    
    def _process_control_spell(self, actor: Dict[str, Any], action: Dict[str, Any]) -> str:
        """Process an area control or battlefield manipulation spell"""
        spell_name = action.get("spell_name", "control spell")
        area_desc = action.get("area_desc", "an area")
        effect_desc = action.get("effect_desc", "is magically altered")
        
        return f"{actor['name']} casts {spell_name}. {area_desc} {effect_desc}."
    
    def _process_ability_action(self, action: Dict[str, Any]) -> str:
        """Process a special ability action"""
        actor_id = self._get_combatant_id(action.get("actor"))
        
        if not actor_id:
            return "Invalid actor."
        
        actor = self.combatants[actor_id]
        ability_name = action.get("ability_name", "special ability")
        
        # Get ability details - could be improved to look up from abilities list
        ability_desc = action.get("description", f"uses {ability_name}")
        targets = action.get("targets", [])
        
        # Process effects if any
        effects = []
        
        if "damage" in action:
            # Process damage effect
            for target_name in targets:
                target_id = self._get_combatant_id(target_name)
                if not target_id:
                    effects.append(f"Invalid target: {target_name}")
                    continue
                    
                target = self.combatants[target_id]
                
                # Get damage parameters
                damage_dice = action.get("damage_dice", "1d6")
                damage_bonus = action.get("damage_bonus", 0)
                damage_type = action.get("damage_type", "piercing")
                
                # Roll damage
                damage = self.use_tool("roll_dice", damage_dice) + damage_bonus
                
                # Apply damage
                self._apply_damage(target_id, damage)
                
                # Add effect description
                effects.append(
                    f"{target['name']} takes {damage} {damage_type} damage."
                )
        
        if "condition" in action:
            # Process condition effect
            condition = action.get("condition", "stunned")
            save_type = action.get("save_type", "constitution")
            save_dc = action.get("save_dc", 13)
            
            for target_name in targets:
                target_id = self._get_combatant_id(target_name)
                if not target_id:
                    effects.append(f"Invalid target: {target_name}")
                    continue
                    
                target = self.combatants[target_id]
                
                # Roll save
                save_bonus = 0
                if "stats" in target and save_type.lower() in target["stats"]:
                    stat_value = target["stats"][save_type.lower()]
                    save_bonus = (stat_value - 10) // 2
                
                save_roll = self.use_tool("roll_dice", "1d20") + save_bonus
                save_result = save_roll >= save_dc
                
                if not save_result:
                    # Add condition to target
                    if condition not in target["conditions"]:
                        target["conditions"].append(condition)
                    
                    # Add effect description
                    effects.append(
                        f"{target['name']} fails a {save_type} save and is {condition}."
                    )
                else:
                    effects.append(
                        f"{target['name']} succeeds on a {save_type} save and resists the effect."
                    )
        
        # Combine ability description and effects
        if effects:
            return f"{actor['name']} {ability_desc}.\n" + "\n".join(effects)
        else:
            return f"{actor['name']} {ability_desc}."
    
    def _process_move_action(self, action: Dict[str, Any]) -> str:
        """Process a movement action"""
        actor_id = self._get_combatant_id(action.get("actor"))
        
        if not actor_id:
            return "Invalid actor."
        
        actor = self.combatants[actor_id]
        
        # Update position
        if "position" in action:
            actor["position"] = action["position"]
        
        # Create movement description
        destination = action.get("destination", "a new position")
        movement_desc = action.get("description", f"moves to {destination}")
        
        return f"{actor['name']} {movement_desc}."
    
    def _process_dash_action(self, action: Dict[str, Any]) -> str:
        """Process a dash action"""
        actor_id = self._get_combatant_id(action.get("actor"))
        
        if not actor_id:
            return "Invalid actor."
        
        actor = self.combatants[actor_id]
        
        # Update position if included
        if "position" in action:
            actor["position"] = action["position"]
        
        # Create dash description
        destination = action.get("destination", "rapidly across the battlefield")
        
        return f"{actor['name']} takes the Dash action and moves {destination}."
    
    def _process_disengage_action(self, action: Dict[str, Any]) -> str:
        """Process a disengage action"""
        actor_id = self._get_combatant_id(action.get("actor"))
        
        if not actor_id:
            return "Invalid actor."
        
        actor = self.combatants[actor_id]
        
        # Update position if included
        if "position" in action:
            actor["position"] = action["position"]
        
        # Create disengage description
        destination = action.get("destination", "away")
        
        return f"{actor['name']} takes the Disengage action, carefully moving {destination} without provoking opportunity attacks."
    
    def _process_dodge_action(self, action: Dict[str, Any]) -> str:
        """Process a dodge action"""
        actor_id = self._get_combatant_id(action.get("actor"))
        
        if not actor_id:
            return "Invalid actor."
        
        actor = self.combatants[actor_id]
        
        # Add dodging condition
        if "dodging" not in actor["conditions"]:
            actor["conditions"].append("dodging")
        
        return f"{actor['name']} takes the Dodge action, focusing entirely on avoiding attacks until their next turn."
    
    def _process_help_action(self, action: Dict[str, Any]) -> str:
        """Process a help action"""
        actor_id = self._get_combatant_id(action.get("actor"))
        target_id = self._get_combatant_id(action.get("target"))
        
        if not actor_id:
            return "Invalid actor."
        
        actor = self.combatants[actor_id]
        
        if not target_id:
            return f"{actor['name']} tries to help, but the target is invalid."
        
        target = self.combatants[target_id]
        
        # Add helped condition to target
        if "helped" not in target["conditions"]:
            target["conditions"].append("helped")
        
        # Create help description
        task = action.get("task", "their next task")
        
        return f"{actor['name']} takes the Help action, assisting {target['name']} with {task}."
    
    def _process_hide_action(self, action: Dict[str, Any]) -> str:
        """Process a hide action"""
        actor_id = self._get_combatant_id(action.get("actor"))
        
        if not actor_id:
            return "Invalid actor."
        
        actor = self.combatants[actor_id]
        
        # Roll stealth check
        stealth_bonus = action.get("stealth_bonus", 0)
        stealth_roll = self.use_tool("roll_dice", "1d20") + stealth_bonus
        
        # Add hidden condition if roll seems good enough
        # In a real implementation, would compare against perception of enemies
        if stealth_roll >= 10:
            if "hidden" not in actor["conditions"]:
                actor["conditions"].append("hidden")
            return f"{actor['name']} takes the Hide action and successfully conceals themselves with a stealth check of {stealth_roll}."
        else:
            return f"{actor['name']} attempts to hide, but their stealth check of {stealth_roll} isn't enough to remain concealed."
    
    def _process_custom_action(self, action: Dict[str, Any]) -> str:
        """Process a custom/creative action"""
        actor_id = self._get_combatant_id(action.get("actor"))
        
        if not actor_id:
            return "Invalid actor."
        
        actor = self.combatants[actor_id]
        
        # Get custom action description
        description = action.get("description", "does something unexpected")
        
        # Process any skill checks
        if "skill_check" in action:
            skill = action.get("skill", "dexterity")
            dc = action.get("dc", 15)
            bonus = action.get("bonus", 0)
            
            # Roll check
            check_roll = self.use_tool("roll_dice", "1d20") + bonus
            success = check_roll >= dc
            
            if success:
                success_desc = action.get("success_desc", "succeeds in their attempt")
                return f"{actor['name']} {description}. They roll a {check_roll} on their {skill} check and {success_desc}."
            else:
                failure_desc = action.get("failure_desc", "fails in their attempt")
                return f"{actor['name']} {description}. They roll a {check_roll} on their {skill} check and {failure_desc}."
        
        # If no skill check, just return the description
        return f"{actor['name']} {description}."
    
    def _apply_damage(self, target_id: str, damage: int) -> None:
        """Apply damage to a target"""
        target = self.combatants[target_id]
        target["hp"] = max(0, target["hp"] - damage)
    
    def _apply_healing(self, target_id: str, healing: int) -> None:
        """Apply healing to a target"""
        target = self.combatants[target_id]
        target["hp"] = min(target["max_hp"], target["hp"] + healing)
    
    def _get_combatant_id(self, name: str) -> Optional[str]:
        """Get combatant ID from name"""
        for cid, combatant in self.combatants.items():
            if combatant["name"].lower() == name.lower():
                return cid
        return None
    
    def _get_current_combatant(self) -> Dict[str, Any]:
        """Get the combatant whose turn it is"""
        if not self.initiative_order:
            return {}
        
        combatant_id = self.initiative_order[self.current_turn]
        return self.combatants[combatant_id]
    
    def _advance_turn(self) -> None:
        """Advance to the next turn in initiative order"""
        self.current_turn = (self.current_turn + 1) % len(self.initiative_order)
        
        # If we've gone through all combatants, increase the round number
        if self.current_turn == 0:
            self.round_number += 1
    
    def _check_combat_end(self) -> bool:
        """Check if combat should end"""
        # Count alive players and enemies
        alive_players = sum(1 for cid in self.combatants 
                          if self.combatants[cid]["type"] == "player" and self.combatants[cid]["hp"] > 0)
        alive_enemies = sum(1 for cid in self.combatants 
                          if self.combatants[cid]["type"] == "enemy" and self.combatants[cid]["hp"] > 0)
        
        # Combat ends if all players or all enemies are defeated
        return alive_players == 0 or alive_enemies == 0
    
    def _generate_combat_end(self) -> str:
        """Generate a description of the combat ending"""
        # Determine victor
        alive_players = sum(1 for cid in self.combatants 
                          if self.combatants[cid]["type"] == "player" and self.combatants[cid]["hp"] > 0)
        
        if alive_players > 0:
            # Players win
            return "The party emerges victorious from the battle!"
        else:
            # Enemies win
            return "The party has been defeated!"
    
    def get_combat_summary(self) -> str:
        """Get a summary of the current combat state"""
        if not self.active_combat:
            return "No active combat in progress."
        
        # Create current status of all combatants
        combatant_status = []
        
        for combatant_id in self.initiative_order:
            combatant = self.combatants[combatant_id]
            
            # Format HP and conditions
            hp_status = f"{combatant['hp']}/{combatant['max_hp']} HP"
            conditions = f"Conditions: {', '.join(combatant['conditions'])}" if combatant['conditions'] else "No conditions"
            
            # Mark current turn
            current = " (Current Turn)" if self.initiative_order[self.current_turn] == combatant_id else ""
            
            combatant_status.append(
                f"{combatant['name']}{current}: {hp_status}. {conditions}"
            )
        
        # Create the summary
        summary = (
            f"Combat Status - Round {self.round_number}\n\n" +
            "\n".join(combatant_status)
        )
        
        return summary
    
    def _generate_attack_hit_description(self, 
                                       actor: Dict[str, Any], 
                                       target: Dict[str, Any],
                                       action: Dict[str, Any],
                                       attack_roll: int,
                                       damage: int,
                                       damage_type: str,
                                       critical: bool) -> str:
        """Generate a description of a successful attack"""
        # Get weapon/attack name
        attack_name = action.get("attack_name", "attack")
        
        # Generate appropriate description based on critical and damage
        if critical:
            if damage > target["max_hp"] // 2:
                return f"{actor['name']} scores a devastating critical hit with their {attack_name}! The attack strikes {target['name']} with tremendous force ({attack_roll} to hit), dealing {damage} {damage_type} damage!"
            else:
                return f"{actor['name']} lands a critical hit with their {attack_name} on {target['name']} ({attack_roll} to hit), dealing {damage} {damage_type} damage!"
        else:
            if damage > target["max_hp"] // 3:
                return f"{actor['name']}'s {attack_name} connects solidly with {target['name']} ({attack_roll} to hit), inflicting a serious wound for {damage} {damage_type} damage!"
            else:
                return f"{actor['name']} hits {target['name']} with their {attack_name} ({attack_roll} to hit), dealing {damage} {damage_type} damage."
    
    def _generate_attack_miss_description(self, 
                                        actor: Dict[str, Any], 
                                        target: Dict[str, Any],
                                        action: Dict[str, Any],
                                        critical: bool = False) -> str:
        """Generate a description of a missed attack"""
        # Get weapon/attack name
        attack_name = action.get("attack_name", "attack")
        
        if critical:
            return f"{actor['name']}'s {attack_name} goes horribly wrong, missing {target['name']} completely."
        else:
            # Randomly select a miss description
            miss_descriptions = [
                f"{actor['name']}'s {attack_name} misses {target['name']}.",
                f"{target['name']} dodges {actor['name']}'s {attack_name}.",
                f"{target['name']} blocks {actor['name']}'s {attack_name}.",
                f"{actor['name']}'s {attack_name} narrowly misses {target['name']}."
            ]
            return random.choice(miss_descriptions)
    
    def _format_combatant_list(self, combatants: List[Dict[str, Any]]) -> str:
        """Format a list of combatants for display"""
        if not combatants:
            return "none"
            
        # Group identical enemy types
        enemy_counts = {}
        for combatant in combatants:
            name = combatant["name"]
            if name in enemy_counts:
                enemy_counts[name] += 1
            else:
                enemy_counts[name] = 1
        
        # Format the list
        enemy_list = []
        for name, count in enemy_counts.items():
            if count > 1:
                enemy_list.append(f"{count} {name}s")
            else:
                enemy_list.append(name)
        
        # Join with appropriate grammar
        if len(enemy_list) == 1:
            return enemy_list[0]
        elif len(enemy_list) == 2:
            return f"{enemy_list[0]} and {enemy_list[1]}"
        else:
            return ", ".join(enemy_list[:-1]) + f", and {enemy_list[-1]}"
    
    def run_demo_combat(self) -> None:
        """Run a demonstration of a simple combat encounter"""
        print("\n--- COMBAT SYSTEM DEMO ---\n")
        
        # Create sample players
        players = [
            {
                "name": "Thorin",
                "hp": 30,
                "ac": 16,
                "initiative_bonus": 2,
                "stats": {"str": 16, "dex": 14, "con": 16, "int": 10, "wis": 12, "cha": 8}
            },
            {
                "name": "Elara",
                "hp": 24,
                "ac": 13,
                "initiative_bonus": 3,
                "stats": {"str": 10, "dex": 16, "con": 14, "int": 16, "wis": 12, "cha": 14}
            }
        ]
        
        # Create sample enemies
        enemies = [
            {
                "name": "Goblin Scout",
                "hp": 7,
                "ac": 14,
                "initiative_bonus": 2,
                "monster_type": "Goblin"
            },
            {
                "name": "Goblin Scout",
                "hp": 7,
                "ac": 14,
                "initiative_bonus": 2,
                "monster_type": "Goblin"
            },
            {
                "name": "Goblin Leader",
                "hp": 12,
                "ac": 15,
                "initiative_bonus": 2,
                "monster_type": "Goblin"
            }
        ]
        
        # Create sample environment
        environment = {
            "name": "Forest Clearing",
            "description": "A small clearing in the forest with dense trees surrounding it. A fallen log lies across the eastern edge."
        }
        
        # Initialize combat
        combat_start = self.initialize_combat(players, enemies, environment)
        print(combat_start)
        
        # Sample combat turns
        turns = [
            {
                "actor": "Elara",
                "type": "spell",
                "spell_name": "Fire Bolt",
                "spell_type": "damage",
                "targets": ["Goblin Leader"],
                "damage_dice": "2d10"
            },
            {
                "actor": "Goblin Scout",
                "type": "attack",
                "attack_name": "shortbow",
                "target": "Thorin",
                "attack_bonus": 4,
                "damage_dice": "1d6",
                "damage_bonus": 2,
                "damage_type": "piercing"
            },
            {
                "actor": "Thorin",
                "type": "attack",
                "attack_name": "battleaxe",
                "target": "Goblin Scout",
                "attack_bonus": 5,
                "damage_dice": "1d8",
                "damage_bonus": 3,
                "damage_type": "slashing"
            },
            {
                "actor": "Goblin Leader",
                "type": "ability",
                "ability_name": "Rally",
                "description": "shouts commands to its allies",
                "targets": ["Goblin Scout"],
                "condition": "inspired"
            },
            {
                "actor": "Goblin Scout",
                "type": "attack",
                "attack_name": "shortbow",
                "target": "Elara",
                "attack_bonus": 4,
                "damage_dice": "1d6",
                "damage_bonus": 2,
                "damage_type": "piercing"
            },
            {
                "actor": "Elara",
                "type": "spell",
                "spell_name": "Thunderwave",
                "spell_type": "damage",
                "area_desc": "A wave of thunderous force sweeps out from Elara.",
                "targets": ["Goblin Scout", "Goblin Leader"],
                "damage_dice": "2d8",
                "damage_type": "thunder",
                "save_type": "constitution",
                "save_dc": 14,
                "half_on_save": True
            }
        ]
        
        # Process each turn
        for i, turn in enumerate(turns):
            print(f"\n--- Turn {i+1} ---")
            result = self.process_turn(turn)
            print(result)
            
            # Print combat summary every 2 turns
            if (i + 1) % 2 == 0:
                print("\n" + self.get_combat_summary())
        
        print("\nDemo combat complete!")

    def handle_scenario(self, scenario_type: str, scenario_data: Dict[str, Any]) -> str:
        """
        Handle a specific scenario type - implementation of abstract method.
        
        Args:
            scenario_type: Type of scenario to handle
            scenario_data: Data specific to the scenario
            
        Returns:
            Result of handling the scenario
        """
        if scenario_type == "combat_initialization":
            players = scenario_data.get("players", [])
            enemies = scenario_data.get("enemies", [])
            environment = scenario_data.get("environment", {})
            
            return self.initialize_combat(players, enemies, environment)
        
        elif scenario_type == "combat_turn":
            action = scenario_data.get("action", {})
            
            return self.process_turn(action)
        
        elif scenario_type == "combat_summary":
            return self.get_combat_summary()
        
        else:
            return f"Scenario type '{scenario_type}' not implemented."