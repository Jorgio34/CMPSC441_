# scenarios/combat_scenario.py

import random
from utils.logger import logger
from tools.dice import roll_dice
from tools.combat_tracker import CombatTracker
from tools.rule_lookup import get_monster_stats, get_ability_modifier
from knowledge.retrieval import retrieve_combat_descriptions

class CombatScenario:
    def __init__(self, game_state, players, enemies, environment=None):
        """
        Initialize a combat scenario
        
        Args:
            game_state: Current game state
            players: List of player character dictionaries
            enemies: List of enemy dictionaries or monster names
            environment: Optional description of combat environment
        """
        self.game_state = game_state
        self.players = players
        self.enemies = self._prepare_enemies(enemies)
        self.environment = environment or "a nondescript battlefield"
        self.combat_tracker = CombatTracker()
        self.round_number = 0
        self.is_active = False
        self.combat_log = []
        
    def _prepare_enemies(self, enemies):
        """Convert enemy names to full stat blocks if needed"""
        prepared_enemies = []
        for enemy in enemies:
            if isinstance(enemy, str):
                # If just a name is provided, retrieve stats
                stats = get_monster_stats(enemy)
                if stats:
                    prepared_enemies.append(stats)
                else:
                    logger.warning(f"Stats for enemy {enemy} not found")
            else:
                # Already a full enemy definition
                prepared_enemies.append(enemy)
        return prepared_enemies
    
    def start_combat(self):
        """Initialize combat by rolling initiative for all participants"""
        self.is_active = True
        self.round_number = 1
        
        # Roll initiative for all combatants
        all_combatants = self.players + self.enemies
        for combatant in all_combatants:
            initiative_mod = get_ability_modifier(combatant.get('dexterity', 10))
            initiative_roll = roll_dice("1d20") + initiative_mod
            self.combat_tracker.add_combatant(
                combatant['name'], 
                initiative_roll, 
                is_player=combatant in self.players,
                combatant_data=combatant
            )
            
        initiative_order = self.combat_tracker.get_initiative_order()
        
        # Log the start of combat
        start_message = f"Combat begins in {self.environment}!\n"
        start_message += "Initiative order:\n"
        for i, combatant in enumerate(initiative_order):
            start_message += f"{i+1}. {combatant['name']} ({combatant['initiative']})\n"
        
        self.combat_log.append(start_message)
        return start_message
    
    def process_turn(self, action_description=None):
        """Process a single turn in combat"""
        if not self.is_active:
            return "Combat has not been started yet. Call start_combat() first."
            
        current_combatant = self.combat_tracker.get_current_combatant()
        
        # Handle player turns vs NPC turns differently
        if current_combatant['is_player']:
            if not action_description:
                return f"It's {current_combatant['name']}'s turn. What would they like to do?"
            
            # Process player action based on description
            result = self._resolve_player_action(current_combatant, action_description)
        else:
            # For NPCs/enemies, automatically determine and execute their action
            result = self._execute_enemy_action(current_combatant)
        
        # Move to next combatant
        next_combatant = self.combat_tracker.next_turn()
        
        # Check if we've completed a round
        if next_combatant['initiative_position'] == 0:
            self.round_number += 1
            result += f"\n\nRound {self.round_number} begins!"
        
        # Check for end of combat conditions
        if self._check_combat_end():
            self.is_active = False
            result += "\n\nCombat has ended!"
        
        self.combat_log.append(result)
        return result
    
    def _resolve_player_action(self, player, action_description):
        """Resolve a player's described action"""
        # Parse action to determine type (attack, spell, movement, etc.)
        action_type = self._determine_action_type(action_description)
        
        if action_type == "attack":
            target_name = self._extract_target(action_description)
            target = self._find_combatant(target_name)
            
            if not target:
                return f"{player['name']} tries to attack {target_name}, but they can't find their target!"
            
            # Roll attack
            attack_mod = get_ability_modifier(player['combatant_data'].get('strength', 10))
            attack_roll = roll_dice("1d20") + attack_mod
            
            # Determine hit/miss
            target_ac = target['combatant_data'].get('armor_class', 10)
            hit = attack_roll >= target_ac
            
            if hit:
                # Roll damage
                weapon_dmg = player['combatant_data'].get('weapon_damage', '1d6')
                damage = roll_dice(weapon_dmg) + attack_mod
                
                # Apply damage
                target['combatant_data']['hit_points'] -= damage
                
                # Get a narrative description of the hit
                hit_description = retrieve_combat_descriptions("hit", weapon_type=player['combatant_data'].get('weapon_type', 'generic'))
                result = f"{player['name']} attacks {target['name']} and hits (rolled {attack_roll} vs AC {target_ac})! {hit_description} dealing {damage} damage."
                
                # Check if target is defeated
                if target['combatant_data']['hit_points'] <= 0:
                    result += f"\n{target['name']} has been defeated!"
                    self.combat_tracker.remove_combatant(target['name'])
            else:
                miss_description = retrieve_combat_descriptions("miss", weapon_type=player['combatant_data'].get('weapon_type', 'generic'))
                result = f"{player['name']} attacks {target['name']} and misses (rolled {attack_roll} vs AC {target_ac}). {miss_description}"
                
            return result
        
        elif action_type == "spell":
            # Implement spell casting
            spell_name = self._extract_spell_name(action_description)
            target_name = self._extract_target(action_description)
            target = self._find_combatant(target_name) if target_name else None
            
            # Get spell details (in a real implementation, retrieve from a spell database)
            spell_damage = "2d6"  # Default damage
            spell_save_dc = 13    # Default save DC
            
            if target:
                # For damaging spells with a target
                save_ability = "dexterity"  # Default save ability
                save_mod = get_ability_modifier(target['combatant_data'].get(save_ability, 10))
                save_roll = roll_dice("1d20") + save_mod
                save_success = save_roll >= spell_save_dc
                
                damage = roll_dice(spell_damage)
                if save_success:
                    damage = damage // 2  # Half damage on successful save
                    target['combatant_data']['hit_points'] -= damage
                    result = f"{player['name']} casts {spell_name} at {target['name']}! {target['name']} makes a successful save (rolled {save_roll} vs DC {spell_save_dc}) but still takes {damage} damage."
                else:
                    target['combatant_data']['hit_points'] -= damage
                    result = f"{player['name']} casts {spell_name} at {target['name']}! {target['name']} fails to save (rolled {save_roll} vs DC {spell_save_dc}) and takes {damage} damage."
                
                # Check if target is defeated
                if target['combatant_data']['hit_points'] <= 0:
                    result += f"\n{target['name']} has been defeated!"
                    self.combat_tracker.remove_combatant(target['name'])
            else:
                # For utility or area effect spells without a specific target
                result = f"{player['name']} casts {spell_name}. The spell takes effect in the area."
                
            return result
        
        elif action_type == "move":
            # Simple movement handling
            return f"{player['name']} moves {action_description.replace('move', '').strip()}."
        
        else:
            # Handle other actions
            return f"{player['name']} {action_description}."
    
    def _execute_enemy_action(self, enemy):
        """Determine and execute an enemy's action"""
        # Use tactical agent to determine best action
        from agents.tactical_agent import TacticalAgent
        
        tactical_agent = TacticalAgent(
            creature=enemy['combatant_data'],
            allies=[e['combatant_data'] for e in self.combat_tracker.get_all_combatants() if not e['is_player']],
            enemies=[p['combatant_data'] for p in self.combat_tracker.get_all_combatants() if p['is_player']],
            environment=self.environment
        )
        
        action, target_name = tactical_agent.determine_action()
        
        if action == "attack":
            target = self._find_combatant(target_name)
            
            # Roll attack
            attack_mod = get_ability_modifier(enemy['combatant_data'].get('strength', 10))
            attack_roll = roll_dice("1d20") + attack_mod
            
            # Determine hit/miss
            target_ac = target['combatant_data'].get('armor_class', 10)
            hit = attack_roll >= target_ac
            
            if hit:
                # Roll damage
                weapon_dmg = enemy['combatant_data'].get('weapon_damage', '1d6')
                damage = roll_dice(weapon_dmg) + attack_mod
                
                # Apply damage
                target['combatant_data']['hit_points'] -= damage
                
                # Get a narrative description
                hit_description = retrieve_combat_descriptions("enemy_hit", monster_type=enemy['combatant_data'].get('type', 'generic'))
                result = f"{enemy['name']} attacks {target['name']} and hits (rolled {attack_roll} vs AC {target_ac})! {hit_description} dealing {damage} damage."
                
                # Check if target is defeated
                if target['combatant_data']['hit_points'] <= 0:
                    result += f"\n{target['name']} has been defeated!"
                    self.combat_tracker.remove_combatant(target['name'])
            else:
                miss_description = retrieve_combat_descriptions("enemy_miss", monster_type=enemy['combatant_data'].get('type', 'generic'))
                result = f"{enemy['name']} attacks {target['name']} and misses (rolled {attack_roll} vs AC {target_ac}). {miss_description}"
                
            return result
        
        elif action == "spell":
            # Similar to player spell casting but for enemies
            spell_name = enemy['combatant_data'].get('spell_name', 'an unknown spell')
            spell_damage = enemy['combatant_data'].get('spell_damage', '2d6')
            spell_save_dc = enemy['combatant_data'].get('spell_save_dc', 12)
            
            target = self._find_combatant(target_name)
            
            save_ability = enemy['combatant_data'].get('spell_save_ability', 'dexterity')
            save_mod = get_ability_modifier(target['combatant_data'].get(save_ability, 10))
            save_roll = roll_dice("1d20") + save_mod
            save_success = save_roll >= spell_save_dc
            
            damage = roll_dice(spell_damage)
            if save_success:
                damage = damage // 2
                target['combatant_data']['hit_points'] -= damage
                result = f"{enemy['name']} casts {spell_name} at {target['name']}! {target['name']} makes a successful save (rolled {save_roll} vs DC {spell_save_dc}) but still takes {damage} damage."
            else:
                target['combatant_data']['hit_points'] -= damage
                result = f"{enemy['name']} casts {spell_name} at {target['name']}! {target['name']} fails to save (rolled {save_roll} vs DC {spell_save_dc}) and takes {damage} damage."
            
            # Check if target is defeated
            if target['combatant_data']['hit_points'] <= 0:
                result += f"\n{target['name']} has been defeated!"
                self.combat_tracker.remove_combatant(target['name'])
                
            return result
        
        elif action == "flee":
            self.combat_tracker.remove_combatant(enemy['name'])
            return f"{enemy['name']} flees from the battle!"
        
        else:
            return f"{enemy['name']} {action}."
    
    def _determine_action_type(self, action_description):
        """Determine the type of action from description"""
        action_description = action_description.lower()
        
        if any(term in action_description for term in ["attack", "strike", "slash", "stab", "shoot", "hit"]):
            return "attack"
        elif any(term in action_description for term in ["cast", "spell", "magic"]):
            return "spell"
        elif any(term in action_description for term in ["move", "walk", "run", "jump"]):
            return "move"
        else:
            return "other"
    
    def _extract_target(self, action_description):
        """Extract target name from action description"""
        # Simple extraction - in real implementation, use NLP or pattern matching
        action_words = action_description.lower().split()
        
        # Look for patterns like "attack [target]" or "at [target]"
        if "attack" in action_words and len(action_words) > action_words.index("attack") + 1:
            return action_words[action_words.index("attack") + 1]
        elif "at" in action_words and len(action_words) > action_words.index("at") + 1:
            return action_words[action_words.index("at") + 1]
        
        return None
    
    def _extract_spell_name(self, action_description):
        """Extract spell name from action description"""
        # Simple extraction - in real implementation, use NLP or pattern matching
        action_words = action_description.lower().split()
        if "cast" in action_words and len(action_words) > action_words.index("cast") + 1:
            return action_words[action_words.index("cast") + 1]
        return "a spell"  # Default return if no specific spell is detected
    
    def _find_combatant(self, name):
        """Find a combatant by name"""
        if not name:
            return None
            
        all_combatants = self.combat_tracker.get_all_combatants()
        for combatant in all_combatants:
            if name in combatant['name'].lower():
                return combatant
        return None
    
    def _check_combat_end(self):
        """Check if combat should end"""
        all_combatants = self.combat_tracker.get_all_combatants()
        players_alive = any(c['is_player'] for c in all_combatants)
        enemies_alive = any(not c['is_player'] for c in all_combatants)
        
        return not (players_alive and enemies_alive)
    
    def get_combat_state(self):
        """Return the current state of combat"""
        return {
            "active": self.is_active,
            "round": self.round_number,
            "combatants": self.combat_tracker.get_all_combatants(),
            "current_turn": self.combat_tracker.get_current_combatant()['name'] if self.is_active else None,
            "environment": self.environment,
            "log": self.combat_log
        }