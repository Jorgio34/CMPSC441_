"""
Dice Rolling Utility

This module provides dice rolling functionality for D&D game mechanics.
It supports standard dice notation (e.g., "2d6+3") and various rolling options.
"""

import random
import re
from typing import Union, List, Dict, Tuple, Optional


def roll_dice(dice_notation: str, advantage: bool = False, 
              disadvantage: bool = False, verbose: bool = False) -> Union[int, Dict]:
    """
    Roll dice based on standard D&D notation.
    
    Args:
        dice_notation: String in format "XdY+Z" where:
                       X = number of dice
                       Y = sides per die
                       Z = modifier (optional)
        advantage: If True, roll twice and take the higher result
        disadvantage: If True, roll twice and take the lower result
        verbose: If True, return detailed roll information
        
    Returns:
        If verbose=False: Total of the dice roll as an integer
        If verbose=True: Dictionary containing roll details
    """
    # Parse the dice notation
    match = re.match(r'^(\d+)d(\d+)([+-]\d+)?$', dice_notation)
    if not match:
        raise ValueError(f"Invalid dice notation: {dice_notation}. Expected format: XdY+Z")
    
    # Extract components
    num_dice = int(match.group(1))
    sides = int(match.group(2))
    modifier_str = match.group(3) or "+0"
    modifier = int(modifier_str)
    
    # Validate inputs
    if num_dice <= 0 or sides <= 0:
        raise ValueError("Number of dice and sides must be positive integers")
    if num_dice > 100:
        raise ValueError("Too many dice requested. Maximum is 100.")
    
    # Perform the roll(s)
    if advantage or disadvantage:
        # Roll twice for advantage/disadvantage
        roll1 = _roll_single_set(num_dice, sides)
        roll2 = _roll_single_set(num_dice, sides)
        
        # Determine which to use
        if advantage:
            dice_rolls = roll1 if sum(roll1) > sum(roll2) else roll2
            other_roll = roll2 if sum(roll1) > sum(roll2) else roll1
            advantage_type = "advantage"
        else:  # disadvantage
            dice_rolls = roll1 if sum(roll1) < sum(roll2) else roll2
            other_roll = roll2 if sum(roll1) < sum(roll2) else roll1
            advantage_type = "disadvantage"
    else:
        # Standard roll
        dice_rolls = _roll_single_set(num_dice, sides)
        other_roll = None
        advantage_type = None
    
    # Calculate total
    total = sum(dice_rolls) + modifier
    
    # Return appropriate result based on verbose flag
    if verbose:
        result = {
            "notation": dice_notation,
            "dice_rolled": num_dice,
            "sides": sides,
            "modifier": modifier,
            "individual_rolls": dice_rolls,
            "raw_total": sum(dice_rolls),
            "total": total
        }
        
        # Add advantage/disadvantage info if applicable
        if advantage_type:
            result["advantage_type"] = advantage_type
            result["other_roll"] = other_roll
            result["other_roll_total"] = sum(other_roll)
            
        return result
    else:
        return total


def _roll_single_set(num_dice: int, sides: int) -> List[int]:
    """Roll a set of dice with the same number of sides"""
    return [random.randint(1, sides) for _ in range(num_dice)]


def roll_ability_scores(method: str = "4d6_drop_lowest") -> List[int]:
    """
    Generate a set of D&D ability scores using different standard methods.
    
    Args:
        method: The method to use for rolling:
                - "4d6_drop_lowest": Roll 4d6 and drop the lowest die (standard)
                - "3d6": Simply roll 3d6 for each ability
                - "standard_array": Use the standard array [15, 14, 13, 12, 10, 8]
                - "point_buy": Generate a valid point buy set
    
    Returns:
        List of 6 ability scores
    """
    if method == "4d6_drop_lowest":
        scores = []
        for _ in range(6):
            # Roll 4d6
            rolls = [random.randint(1, 6) for _ in range(4)]
            # Drop the lowest die
            rolls.remove(min(rolls))
            # Sum the remaining dice
            scores.append(sum(rolls))
        return scores
    
    elif method == "3d6":
        return [sum(random.randint(1, 6) for _ in range(3)) for _ in range(6)]
    
    elif method == "standard_array":
        return [15, 14, 13, 12, 10, 8]
    
    elif method == "point_buy":
        # Generate a valid point buy based on 5e rules
        # (27 points, costs: 8=0, 9=1, 10=2, 11=3, 12=4, 13=5, 14=7, 15=9)
        scores = [8, 8, 8, 8, 8, 8]  # Start with all 8s
        
        point_costs = {9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
        points_left = 27
        
        # Randomly distribute points
        while points_left > 0:
            # Pick a random ability to increase
            ability_index = random.randint(0, 5)
            current_score = scores[ability_index]
            
            # Can't go above 15
            if current_score >= 15:
                continue
                
            # Calculate cost to increase
            cost = point_costs.get(current_score + 1, 0)
            
            # Check if we can afford it
            if cost <= points_left:
                scores[ability_index] += 1
                points_left -= cost
            else:
                # If we can't increase any scores, break out
                break_counter = 0
                can_increase = False
                for i, score in enumerate(scores):
                    if score < 15 and point_costs.get(score + 1, 0) <= points_left:
                        can_increase = True
                        break
                
                if not can_increase:
                    break
        
        return scores
    
    else:
        raise ValueError(f"Unknown ability score method: {method}")


def roll_initiative(dexterity_modifier: int = 0, advantage: bool = False) -> int:
    """
    Roll initiative for combat.
    
    Args:
        dexterity_modifier: Dexterity modifier to add to the roll
        advantage: Whether to roll with advantage
        
    Returns:
        Initiative roll result
    """
    return roll_dice("1d20", advantage=advantage) + dexterity_modifier


def roll_attack(attack_bonus: int = 0, advantage: bool = False, 
               disadvantage: bool = False, critical_on: int = 20) -> Tuple[int, bool]:
    """
    Roll an attack and determine if it's a critical hit.
    
    Args:
        attack_bonus: Attack bonus to add to the roll
        advantage: Whether to roll with advantage
        disadvantage: Whether to roll with disadvantage
        critical_on: Number needed for a critical hit (usually 20)
        
    Returns:
        Tuple of (attack roll result, whether it's a critical hit)
    """
    if advantage and disadvantage:
        # They cancel each other out
        advantage = disadvantage = False
    
    # Roll the attack
    if advantage or disadvantage:
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        
        if advantage:
            natural_roll = max(roll1, roll2)
        else:  # disadvantage
            natural_roll = min(roll1, roll2)
    else:
        natural_roll = random.randint(1, 20)
    
    # Determine if critical
    is_critical = natural_roll >= critical_on
    
    # Calculate final result
    attack_roll = natural_roll + attack_bonus
    
    return attack_roll, is_critical


def roll_damage(damage_dice: str, damage_bonus: int = 0, critical: bool = False) -> int:
    """
    Roll damage for an attack.
    
    Args:
        damage_dice: Damage dice in standard notation (e.g., "2d6")
        damage_bonus: Additional damage modifier
        critical: Whether this is a critical hit (doubles dice)
        
    Returns:
        Damage amount
    """
    # Parse the damage dice
    match = re.match(r'^(\d+)d(\d+)$', damage_dice)
    if not match:
        raise ValueError(f"Invalid damage dice notation: {damage_dice}. Expected format: XdY")
    
    num_dice = int(match.group(1))
    sides = int(match.group(2))
    
    # Double dice on critical hit
    if critical:
        num_dice *= 2
    
    # Roll damage
    damage_rolls = [random.randint(1, sides) for _ in range(num_dice)]
    total_damage = sum(damage_rolls) + damage_bonus
    
    return max(0, total_damage)  # Damage can't be negative


def roll_saving_throw(ability_modifier: int = 0, proficient: bool = False, 
                    proficiency_bonus: int = 2, advantage: bool = False, 
                    disadvantage: bool = False) -> int:
    """
    Roll a saving throw.
    
    Args:
        ability_modifier: Ability modifier for the save
        proficient: Whether the character is proficient in this save
        proficiency_bonus: Character's proficiency bonus
        advantage: Whether to roll with advantage
        disadvantage: Whether to roll with disadvantage
        
    Returns:
        Saving throw result
    """
    total_modifier = ability_modifier
    if proficient:
        total_modifier += proficiency_bonus
    
    return roll_dice("1d20", advantage=advantage, disadvantage=disadvantage) + total_modifier