# tools/simple_combat_tracker.py

class CombatTracker:
    """
    A simplified combat tracker designed to work with combat_scenario.py
    """
    
    def __init__(self):
        """Initialize the combat tracker"""
        self.combatants = []
        self.current_position = 0
    
    def add_combatant(self, name, initiative, is_player=False, combatant_data=None):
        """
        Add a combatant to the initiative order
        
        Args:
            name: The combatant's name
            initiative: The combatant's initiative roll
            is_player: Whether the combatant is a player character
            combatant_data: Additional data about the combatant
        """
        # Create combatant record
        combatant = {
            "name": name,
            "initiative": initiative,
            "is_player": is_player,
            "initiative_position": len(self.combatants),
            "combatant_data": combatant_data or {}
        }
        
        # Add to list
        self.combatants.append(combatant)
        
        # Sort combatants by initiative (highest first)
        self.combatants.sort(key=lambda x: x["initiative"], reverse=True)
        
        # Update initiative positions
        for i, c in enumerate(self.combatants):
            c["initiative_position"] = i
    
    def remove_combatant(self, name):
        """
        Remove a combatant from the initiative order
        
        Args:
            name: The name of the combatant to remove
        """
        # Find the combatant
        for i, combatant in enumerate(self.combatants):
            if combatant["name"] == name:
                # Remove the combatant
                self.combatants.pop(i)
                
                # Update initiative positions
                for j, c in enumerate(self.combatants):
                    c["initiative_position"] = j
                
                # Adjust current position if needed
                if self.current_position >= i and self.current_position > 0:
                    self.current_position -= 1
                elif self.current_position >= len(self.combatants):
                    self.current_position = 0
                
                return True
        
        return False
    
    def get_current_combatant(self):
        """
        Get the combatant whose turn it currently is
        
        Returns:
            The current combatant's data
        """
        if not self.combatants:
            return None
        
        return self.combatants[self.current_position]
    
    def next_turn(self):
        """
        Advance to the next turn in initiative order
        
        Returns:
            The next combatant's data
        """
        if not self.combatants:
            return None
        
        # Move to next position
        self.current_position = (self.current_position + 1) % len(self.combatants)
        
        return self.get_current_combatant()
    
    def get_initiative_order(self):
        """
        Get the full initiative order
        
        Returns:
            List of combatants in initiative order
        """
        return self.combatants
    
    def get_all_combatants(self):
        """
        Get all combatants
        
        Returns:
            List of all combatants
        """
        return self.combatants