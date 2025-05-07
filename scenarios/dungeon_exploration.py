# scenarios/dungeon_exploration.py

import random
from utils.logger import logger
from tools.dice import roll_dice
from agents.adventure_agent import AdventureAgent
from tools.generators.map_gen import generate_dungeon_map
from knowledge.retrieval import retrieve_trap_descriptions, retrieve_treasure_descriptions

class DungeonExplorationScenario:
    def __init__(self, game_state, dungeon_type=None, difficulty=None, size=None):
        """
        Initialize a dungeon exploration scenario
        
        Args:
            game_state: Current game state
            dungeon_type: Optional dungeon type (e.g., "cave", "temple", "ruins")
            difficulty: Optional difficulty level (e.g., "easy", "medium", "hard")
            size: Optional size of the dungeon (e.g., "small", "medium", "large")
        """
        self.game_state = game_state
        self.dungeon_type = dungeon_type or self._select_random_dungeon_type()
        self.difficulty = difficulty or "medium"
        self.size = size or "medium"
        self.adventure_agent = AdventureAgent(
            world_context=game_state.get('world_context', {}),
            player_history=game_state.get('player_history', [])
        )
        self.dungeon_data = None
        self.current_room = None
        self.visited_rooms = set()
        
    def _select_random_dungeon_type(self):
        """Select a random dungeon type"""
        dungeon_types = ["cave", "temple", "ruins", "crypt", "mine", "castle", "wizard_tower"]
        return random.choice(dungeon_types)
    
    def generate_dungeon(self):
        """Generate a dungeon based on parameters"""
        # Generate basic dungeon structure
        dungeon_map = generate_dungeon_map(self.dungeon_type, self.size)
        
        # Use adventure agent to populate the dungeon
        self.dungeon_data = self.adventure_agent.create_dungeon(
            dungeon_type=self.dungeon_type,
            difficulty=self.difficulty,
            size=self.size,
            base_map=dungeon_map
        )
        
        # Set current room to entrance
        self.current_room = self.dungeon_data['entrance']
        self.visited_rooms.add(self.current_room['id'])
        
        # Add dungeon to game state
        if 'dungeons' not in self.game_state:
            self.game_state['dungeons'] = []
            
        self.game_state['dungeons'].append(self.dungeon_data)
        
        return self.dungeon_data
    
    def generate_dungeon_intro(self):
        """Generate introductory narrative for the dungeon"""
        if not self.dungeon_data:
            self.generate_dungeon()
            
        intro = self.adventure_agent.generate_dungeon_introduction(
            dungeon_data=self.dungeon_data
        )
        
        return intro
    
    def describe_current_room(self):
        """Describe the current room in detail"""
        if not self.current_room:
            if not self.dungeon_data:
                self.generate_dungeon()
            self.current_room = self.dungeon_data['entrance']
            
        # Check if room has been visited before
        first_visit = self.current_room['id'] not in self.visited_rooms
        self.visited_rooms.add(self.current_room['id'])
        
        room_description = self.adventure_agent.describe_dungeon_room(
            room=self.current_room,
            dungeon_type=self.dungeon_type,
            first_visit=first_visit
        )
        
        return room_description
    
    def move_to_room(self, direction):
        """Move to an adjacent room in the specified direction"""
        if not self.current_room:
            return "You haven't entered the dungeon yet."
            
        # Check if direction is valid
        if direction not in self.current_room['exits']:
            return f"There is no exit in the {direction} direction."
            
        # Get the ID of the next room
        next_room_id = self.current_room['exits'][direction]
        
        # Find the room with that ID
        next_room = None
        for room in self.dungeon_data['rooms']:
            if room['id'] == next_room_id:
                next_room = room
                break
                
        if not next_room:
            return f"Error: Room {next_room_id} not found."
            
        # Update current room
        self.current_room = next_room
        
        # Check for any encounters or events
        if 'encounter' in self.current_room and random.random() < self.current_room['encounter_chance']:
            # Handle encounter
            encounter_description = self.handle_room_encounter()
            room_description = self.describe_current_room()
            return f"{room_description}\n\n{encounter_description}"
        else:
            # Just describe the room
            return self.describe_current_room()
    
    def handle_room_encounter(self):
        """Handle any encounters in the current room"""
        if not self.current_room or 'encounter' not in self.current_room:
            return "No encounter in this room."
            
        encounter_type = self.current_room['encounter']['type']
        
        if encounter_type == 'monster':
            # Set up combat with the monsters in this room
            from scenarios.combat_scenario import CombatScenario
            
            monsters = self.current_room['encounter']['monsters']
            
            combat_scenario = CombatScenario(
                game_state=self.game_state,
                players=self.game_state.get('party', []),
                enemies=monsters,
                environment=self.current_room['description']
            )
            
            # Start combat but don't process turns yet
            combat_intro = combat_scenario.start_combat()
            
            # Store the combat scenario in the room for later reference
            self.current_room['active_combat'] = combat_scenario
            
            return f"As you enter the room, you encounter enemies!\n\n{combat_intro}"
        
        elif encounter_type == 'trap':
            # Handle trap encounter
            trap_type = self.current_room['encounter']['trap_type']
            trap_dc = self.current_room['encounter']['trap_dc']
            trap_description = retrieve_trap_descriptions(trap_type)
            
            # Default trap handling - in a real implementation, this would involve player skill checks
            detection_roll = roll_dice("1d20")
            detected = detection_roll >= trap_dc - 5  # Easier to detect than to disarm
            
            if detected:
                disarm_roll = roll_dice("1d20")
                disarmed = disarm_roll >= trap_dc
                
                if disarmed:
                    result = f"You notice {trap_description} You carefully disarm the trap."
                    # Mark trap as disarmed
                    self.current_room['encounter']['disarmed'] = True
                else:
                    # Calculate damage
                    damage_dice = self.current_room['encounter'].get('damage_dice', '2d6')
                    damage = roll_dice(damage_dice)
                    
                    result = f"You notice {trap_description} You try to disarm it but fail! The trap activates dealing {damage} damage."
                    # Mark trap as triggered
                    self.current_room['encounter']['triggered'] = True
            else:
                # Calculate damage
                damage_dice = self.current_room['encounter'].get('damage_dice', '2d6')
                damage = roll_dice(damage_dice)
                
                result = f"Too late! {trap_description} The trap activates dealing {damage} damage."
                # Mark trap as triggered
                self.current_room['encounter']['triggered'] = True
                
            return result
        
        elif encounter_type == 'treasure':
            # Handle treasure encounter
            treasure_type = self.current_room['encounter']['treasure_type']
            treasure_description = retrieve_treasure_descriptions(treasure_type)
            
            # Add treasure to inventory if applicable
            if 'items' in self.current_room['encounter']:
                if 'inventory' not in self.game_state:
                    self.game_state['inventory'] = []
                    
                self.game_state['inventory'].extend(self.current_room['encounter']['items'])
            
            # Add gold if applicable
            if 'gold' in self.current_room['encounter']:
                if 'gold' not in self.game_state:
                    self.game_state['gold'] = 0
                    
                self.game_state['gold'] += self.current_room['encounter']['gold']
                
            # Mark as looted
            self.current_room['encounter']['looted'] = True
                
            return f"You discover {treasure_description}"
        
        elif encounter_type == 'puzzle':
            # Handle puzzle encounter
            puzzle_description = self.current_room['encounter']['description']
            puzzle_solution = self.current_room['encounter']['solution']
            
            # Just return the puzzle description - solution will be checked elsewhere
            return f"You encounter a puzzle: {puzzle_description}"
        
        else:
            # Generic encounter
            return self.current_room['encounter'].get('description', 'You encounter something unexpected.')
    
    def check_puzzle_solution(self, solution_attempt):
        """Check if the provided solution solves the current room's puzzle"""
        if not self.current_room or 'encounter' not in self.current_room or self.current_room['encounter']['type'] != 'puzzle':
            return "There is no puzzle to solve in this room."
            
        correct_solution = self.current_room['encounter']['solution'].lower()
        
        if solution_attempt.lower() == correct_solution:
            # Puzzle solved!
            self.current_room['encounter']['solved'] = True
            
            # Check if solving unlocks anything
            if 'unlock' in self.current_room['encounter']:
                unlock_type = self.current_room['encounter']['unlock']['type']
                
                if unlock_type == 'door':
                    direction = self.current_room['encounter']['unlock']['direction']
                    room_id = self.current_room['encounter']['unlock']['room_id']
                    
                    # Add new exit
                    self.current_room['exits'][direction] = room_id
                    
                    return f"Correct! You solved the puzzle. A door opens to the {direction}."
                    
                elif unlock_type == 'treasure':
                    # Reveal hidden treasure
                    treasure_type = self.current_room['encounter']['unlock']['treasure_type']
                    treasure_description = retrieve_treasure_descriptions(treasure_type)
                    
                    # Add treasure to inventory if applicable
                    if 'items' in self.current_room['encounter']['unlock']:
                        if 'inventory' not in self.game_state:
                            self.game_state['inventory'] = []
                            
                        self.game_state['inventory'].extend(self.current_room['encounter']['unlock']['items'])
                    
                    # Add gold if applicable
                    if 'gold' in self.current_room['encounter']['unlock']:
                        if 'gold' not in self.game_state:
                            self.game_state['gold'] = 0
                            
                        self.game_state['gold'] += self.current_room['encounter']['unlock']['gold']
                        
                    return f"Correct! You solved the puzzle. A hidden compartment opens revealing {treasure_description}"
                    
                else:
                    return "Correct! You solved the puzzle."
            else:
                return "Correct! You solved the puzzle."
        else:
            # Wrong solution
            if 'failure_consequence' in self.current_room['encounter']:
                consequence = self.current_room['encounter']['failure_consequence']
                
                if consequence['type'] == 'damage':
                    damage = roll_dice(consequence['damage_dice'])
                    return f"Incorrect solution. The puzzle mechanism triggers, dealing {damage} damage."
                elif consequence['type'] == 'trap':
                    return f"Incorrect solution. {consequence['description']}"
                else:
                    return f"Incorrect solution. {consequence['description']}"
            else:
                return "That doesn't seem to be the correct solution. Try again."
    
    def search_room(self):
        """Search the current room for hidden features or items"""
        if not self.current_room:
            return "You haven't entered the dungeon yet."
            
        # Roll for search check
        search_roll = roll_dice("1d20")
        search_dc = self.current_room.get('search_dc', 12)
        
        if search_roll >= search_dc:
            # Successful search
            search_results = []
            
            # Check for hidden doors
            if 'hidden_exits' in self.current_room:
                for direction, room_id in self.current_room['hidden_exits'].items():
                    self.current_room['exits'][direction] = room_id
                    search_results.append(f"You discover a hidden passage leading {direction}.")
            
            # Check for hidden treasures
            if 'hidden_treasure' in self.current_room:
                treasure_description = retrieve_treasure_descriptions(self.current_room['hidden_treasure']['type'])
                
                # Add treasure to inventory if applicable
                if 'items' in self.current_room['hidden_treasure']:
                    if 'inventory' not in self.game_state:
                        self.game_state['inventory'] = []
                        
                    self.game_state['inventory'].extend(self.current_room['hidden_treasure']['items'])
                
                # Add gold if applicable
                if 'gold' in self.current_room['hidden_treasure']:
                    if 'gold' not in self.game_state:
                        self.game_state['gold'] = 0
                        
                    self.game_state['gold'] += self.current_room['hidden_treasure']['gold']
                    
                search_results.append(f"You discover hidden treasure: {treasure_description}")
                
                # Mark as found
                self.current_room['hidden_treasure']['found'] = True
            
            # Check for hidden traps
            if 'hidden_trap' in self.current_room and not self.current_room['hidden_trap'].get('detected', False):
                trap_description = retrieve_trap_descriptions(self.current_room['hidden_trap']['type'])
                search_results.append(f"You discover a hidden trap: {trap_description}")
                
                # Mark trap as detected
                self.current_room['hidden_trap']['detected'] = True
                
            # Check for hidden clues
            if 'hidden_clue' in self.current_room and not self.current_room['hidden_clue'].get('found', False):
                search_results.append(f"You discover a hidden clue: {self.current_room['hidden_clue']['description']}")
                
                # Mark clue as found
                self.current_room['hidden_clue']['found'] = True
                
            if search_results:
                return "\n".join(search_results)
            else:
                return "You search the room thoroughly but find nothing of interest."
        else:
            # Failed search
            return "You search the room but don't find anything noteworthy."
    
    def get_available_directions(self):
        """Get available movement directions from current room"""
        if not self.current_room:
            return []
            
        return list(self.current_room['exits'].keys())
    
    def get_dungeon_map(self, show_unexplored=False):
        """Get a representation of the dungeon map, showing explored areas"""
        if not self.dungeon_data:
            return "No dungeon has been generated yet."
            
        # In a real implementation, this would generate a visual map
        # For now, just return a text representation
        map_text = f"Map of {self.dungeon_data['name']} ({self.dungeon_type})\n"
        map_text += f"Difficulty: {self.difficulty}, Size: {self.size}\n\n"
        
        for room in self.dungeon_data['rooms']:
            # Only show rooms that have been visited
            if room['id'] in self.visited_rooms or show_unexplored:
                map_text += f"Room {room['id']}: {room['name']}\n"
                
                # Show exits
                if room['exits']:
                    map_text += "Exits: "
                    for direction, target_id in room['exits'].items():
                        target_visited = target_id in self.visited_rooms
                        if target_visited or show_unexplored:
                            map_text += f"{direction} (to Room {target_id}), "
                    map_text = map_text.rstrip(", ") + "\n"
                    
                # Mark current location
                if self.current_room and room['id'] == self.current_room['id']:
                    map_text += "** You are here **\n"
                    
                map_text += "\n"
                
        return map_text
        
    def get_dungeon_state(self):
        """Return the current state of dungeon exploration"""
        if not self.dungeon_data:
            return {
                "generated": False
            }
            
        return {
            "generated": True,
            "name": self.dungeon_data['name'],
            "type": self.dungeon_type,
            "difficulty": self.difficulty,
            "size": self.size,
            "current_room": self.current_room['id'] if self.current_room else None,
            "visited_rooms": list(self.visited_rooms),
            "rooms_total": len(self.dungeon_data['rooms']),
            "completion_percentage": len(self.visited_rooms) / len(self.dungeon_data['rooms']) * 100
        }