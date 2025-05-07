# scenarios/quest_generation.py

import random
from knowledge.retrieval import retrieve_quest_templates, retrieve_location_info
from agents.adventure_agent import AdventureAgent
from utils.logger import logger

class QuestGenerationScenario:
    def __init__(self, game_state, location=None, quest_type=None, difficulty=None):
        """
        Initialize a quest generation scenario
        
        Args:
            game_state: Current game state
            location: Optional location for the quest
            quest_type: Optional quest type (e.g., "rescue", "fetch", "kill")
            difficulty: Optional difficulty level (e.g., "easy", "medium", "hard")
        """
        self.game_state = game_state
        self.location = location or self._select_random_location(game_state)
        self.quest_type = quest_type or self._select_random_quest_type()
        self.difficulty = difficulty or "medium"
        self.adventure_agent = AdventureAgent(
            world_context=game_state.get('world_context', {}),
            player_history=game_state.get('player_history', [])
        )
        self.quest_data = None
        
    def _select_random_location(self, game_state):
        """Select a random location from available locations"""
        available_locations = game_state.get('known_locations', [])
        if not available_locations:
            return "nearby village"
        return random.choice(available_locations)
    
    def _select_random_quest_type(self):
        """Select a random quest type"""
        quest_types = ["rescue", "fetch", "kill", "escort", "investigate", "defend", "heist"]
        return random.choice(quest_types)
    
    def generate_quest(self):
        """Generate a quest based on parameters"""
        # Get location information for context
        location_info = retrieve_location_info(self.location)
        
        # Retrieve quest templates based on quest type
        quest_templates = retrieve_quest_templates(self.quest_type)
        
        # Use adventure agent to create a detailed quest
        self.quest_data = self.adventure_agent.create_quest(
            location=self.location,
            location_info=location_info,
            quest_type=self.quest_type,
            difficulty=self.difficulty,
            templates=quest_templates
        )
        
        # Add quest to game state
        if 'active_quests' not in self.game_state:
            self.game_state['active_quests'] = []
            
        quest_id = f"quest_{len(self.game_state['active_quests']) + 1}"
        self.quest_data['id'] = quest_id
        self.quest_data['status'] = 'active'
        self.quest_data['progress'] = 0
        self.game_state['active_quests'].append(self.quest_data)
        
        return self.quest_data
    
    def generate_quest_intro(self):
        """Generate introductory narrative for the quest"""
        if not self.quest_data:
            self.generate_quest()
            
        intro = self.adventure_agent.generate_quest_introduction(
            quest_data=self.quest_data,
            location=self.location
        )
        
        return intro
    
    def generate_quest_giver_npc(self):
        """Generate an NPC that gives the quest"""
        if not self.quest_data:
            self.generate_quest()
            
        quest_giver = self.adventure_agent.generate_quest_giver(
            quest_data=self.quest_data,
            location=self.location
        )
        
        # Add quest giver to game state
        if 'npcs' not in self.game_state:
            self.game_state['npcs'] = []
            
        self.game_state['npcs'].append(quest_giver)
        self.quest_data['quest_giver'] = quest_giver['name']
        
        return quest_giver
    
    def update_quest_progress(self, quest_id, progress_update, completed=False):
        """Update the progress of a quest"""
        for quest in self.game_state.get('active_quests', []):
            if quest['id'] == quest_id:
                prev_progress = quest['progress']
                quest['progress'] = min(100, prev_progress + progress_update)
                
                if completed or quest['progress'] >= 100:
                    quest['status'] = 'completed'
                    
                    # Move quest to completed quests
                    if 'completed_quests' not in self.game_state:
                        self.game_state['completed_quests'] = []
                        
                    self.game_state['completed_quests'].append(quest)
                    self.game_state['active_quests'].remove(quest)
                    
                    # Generate completion narrative
                    completion_narrative = self.adventure_agent.generate_quest_completion(quest)
                    return completion_narrative
                else:
                    # Generate progress update narrative
                    progress_narrative = self.adventure_agent.generate_quest_progress_update(
                        quest, 
                        prev_progress, 
                        quest['progress']
                    )
                    return progress_narrative
                    
        return f"Quest {quest_id} not found."
    
    def get_active_quests(self):
        """Get all active quests"""
        return self.game_state.get('active_quests', [])
    
    def get_completed_quests(self):
        """Get all completed quests"""
        return self.game_state.get('completed_quests', [])
    
    def get_quest_details(self, quest_id):
        """Get details of a specific quest"""
        for quest in self.game_state.get('active_quests', []):
            if quest['id'] == quest_id:
                return quest
                
        for quest in self.game_state.get('completed_quests', []):
            if quest['id'] == quest_id:
                return quest
                
        return None
    
    def generate_quest_stage(self, quest_id, stage_number):
        """Generate a specific stage of a quest"""
        quest = self.get_quest_details(quest_id)
        if not quest:
            return f"Quest {quest_id} not found."
            
        # Generate stage description based on quest data
        stage = self.adventure_agent.generate_quest_stage(
            quest=quest,
            stage_number=stage_number
        )
        
        # Add stage to quest data if not exists
        if 'stages' not in quest:
            quest['stages'] = []
            
        # Add or update stage
        if stage_number <= len(quest['stages']):
            quest['stages'][stage_number - 1] = stage
        else:
            quest['stages'].append(stage)
            
        return stage
    
    def generate_quest_rewards(self, quest_id):
        """Generate rewards for completing a quest"""
        quest = self.get_quest_details(quest_id)
        if not quest:
            return f"Quest {quest_id} not found."
            
        # Generate rewards based on quest difficulty and type
        rewards = self.adventure_agent.generate_quest_rewards(
            quest=quest,
            difficulty=self.difficulty
        )
        
        quest['rewards'] = rewards
        return rewards
    
    def generate_quest_challenge(self, quest_id, challenge_type=None):
        """Generate a specific challenge for a quest"""
        quest = self.get_quest_details(quest_id)
        if not quest:
            return f"Quest {quest_id} not found."
            
        # If challenge type not specified, choose appropriate one based on quest type
        if not challenge_type:
            if quest['quest_type'] == 'rescue':
                challenge_type = random.choice(['combat', 'trap', 'puzzle'])
            elif quest['quest_type'] == 'fetch':
                challenge_type = random.choice(['trap', 'puzzle', 'negotiation'])
            elif quest['quest_type'] == 'kill':
                challenge_type = 'combat'
            elif quest['quest_type'] == 'escort':
                challenge_type = random.choice(['ambush', 'obstacle', 'combat'])
            elif quest['quest_type'] == 'investigate':
                challenge_type = random.choice(['puzzle', 'hidden_clue', 'interrogation'])
            elif quest['quest_type'] == 'defend':
                challenge_type = random.choice(['combat', 'preparation', 'strategy'])
            elif quest['quest_type'] == 'heist':
                challenge_type = random.choice(['trap', 'stealth', 'puzzle'])
            else:
                challenge_type = random.choice(['combat', 'puzzle', 'trap', 'negotiation'])
        
        # Generate challenge using adventure agent
        challenge = self.adventure_agent.generate_quest_challenge(
            quest=quest,
            challenge_type=challenge_type
        )
        
        # Add challenge to quest data
        if 'challenges' not in quest:
            quest['challenges'] = []
            
        quest['challenges'].append(challenge)
        return challenge
    
    def generate_quest_location(self, quest_id):
        """Generate a specific location for a quest"""
        quest = self.get_quest_details(quest_id)
        if not quest:
            return f"Quest {quest_id} not found."
            
        # Generate location details
        location = self.adventure_agent.generate_quest_location(
            quest=quest,
            world_context=self.game_state.get('world_context', {})
        )
        
        # Add location to game state if not exists
        if 'locations' not in self.game_state:
            self.game_state['locations'] = []
            
        self.game_state['locations'].append(location)
        
        # Update quest with location reference
        quest['location'] = location['name']
        
        return location

def create_quest_scenario(game_state, location=None, quest_type=None, difficulty=None):
    """
    Factory function to create and initialize a quest generation scenario.
    
    Args:
        game_state: Current game state
        location: Optional location for the quest
        quest_type: Optional quest type (e.g., "rescue", "fetch", "kill")
        difficulty: Optional difficulty level (e.g., "easy", "medium", "hard")
        
    Returns:
        Initialized QuestGenerationScenario instance
    """
    scenario = QuestGenerationScenario(game_state, location, quest_type, difficulty)
    # Generate the quest immediately
    scenario.generate_quest()
    return scenario