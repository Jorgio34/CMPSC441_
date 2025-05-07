# core/llm_integration.py

import os
import random
from typing import Dict, List, Any, Optional
from utils.logger import logger

class LLMIntegration:
    """Mock class to handle interactions with language models without requiring OpenAI package"""
    
    def __init__(self, model_name="gpt-3.5-turbo", api_key=None):
        """Initialize the LLM integration"""
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            logger.warning("No API key provided. Using mock responses.")
        
        logger.info(f"Initialized LLM integration with model: {model_name}")
        
    def generate_response(self, 
                         prompt: str, 
                         system_message: str = None,
                         temperature: float = 0.7,
                         max_tokens: int = 500,
                         conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Generate a mock response that simulates what a language model would produce
        
        Args:
            prompt: The user's input or query
            system_message: Optional system message to guide the LLM's behavior
            temperature: Controls randomness (0.0-1.0)
            max_tokens: Maximum number of tokens to generate
            conversation_history: Previous messages in the conversation
            
        Returns:
            Generated text response
        """
        # Log the request
        logger.info(f"Generating response for prompt: {prompt[:50]}...")
        
        # Create mock responses based on the prompt content
        if "tavern" in prompt.lower():
            responses = [
                "The tavern is filled with the lively chatter of adventurers sharing tales of their exploits. A bard plays a cheerful tune in the corner while patrons clink mugs and laugh heartily.",
                "You notice several patrons giving you curious glances. The tavern has a cozy atmosphere with a crackling fireplace and the aroma of fresh bread and stew fills the air.",
                "The tavern keeper nods in your direction as you enter. The establishment is moderately busy, with a mix of locals and travelers enjoying drinks and meals."
            ]
        elif "combat" in prompt.lower() or "attack" in prompt.lower():
            responses = [
                "The sword slices through the air with deadly precision, catching the enemy off guard. Blood sprays as the blade makes contact, and the creature howls in pain.",
                "With impressive agility, the fighter dodges the incoming attack before countering with a powerful thrust. The sound of steel meeting flesh echoes in the chamber.",
                "Magic crackles through the air as the spell takes effect. The enemy is engulfed in arcane energy, their screams muffled by the roaring flames."
            ]
        elif "quest" in prompt.lower():
            responses = [
                "A wealthy merchant requires brave adventurers to recover a shipment stolen by bandits. The goods are believed to be hidden in a camp to the north.",
                "Mysterious disappearances have plagued the village for weeks. The mayor suspects a cult operating from the nearby caves and seeks heroes to investigate.",
                "An ancient artifact of great power has been discovered in ruins to the east. You are tasked with retrieving it before it falls into the wrong hands."
            ]
        else:
            responses = [
                "Your request has been processed, and I've generated a response appropriate to the context.",
                "I've considered your input carefully and created a narrative that fits the scenario.",
                "Based on your prompt, I've crafted a response that should meet your expectations for this D&D scenario."
            ]
            
        # Randomize response selection based on temperature
        randomness = min(max(temperature, 0.1), 1.0)  # Keep between 0.1 and 1.0
        weighted_idx = int(random.random() / randomness) % len(responses)
        return responses[weighted_idx]
    
    def generate_game_master_response(self, 
                                     scene_description: str, 
                                     player_input: str = None,
                                     world_context: str = None,
                                     temperature: float = 0.7) -> str:
        """
        Generate a game master response for a D&D scenario
        
        Args:
            scene_description: Description of the current scene
            player_input: Optional player's input to respond to
            world_context: Optional world-building context
            temperature: Controls randomness (0.0-1.0)
            
        Returns:
            Generated game master response
        """
        # Create a prompt based on the inputs
        prompt = f"Scene: {scene_description}"
        if world_context:
            prompt += f"\nWorld Context: {world_context}"
        if player_input:
            prompt += f"\nPlayer Input: {player_input}"
            
        # Generate response with tavern context
        prompt += "\nTavern scenario"
        return self.generate_response(prompt, temperature=temperature)
    
    def generate_npc_dialogue(self,
                             npc_name: str,
                             npc_description: str,
                             player_input: str,
                             conversation_history: List[Dict[str, str]] = None,
                             temperature: float = 0.8) -> str:
        """
        Generate dialogue for an NPC responding to a player
        
        Args:
            npc_name: Name of the NPC
            npc_description: Description of the NPC's personality and role
            player_input: What the player said to the NPC
            conversation_history: Previous exchanges in the conversation
            temperature: Controls randomness (0.0-1.0)
            
        Returns:
            Generated NPC dialogue response
        """
        # NPC dialogue responses based on innkeeper/tavern owner archetype
        if "job" in player_input.lower() or "quest" in player_input.lower() or "work" in player_input.lower():
            responses = [
                f"Aye, there's talk of bandits in the hills. The merchant's guild is offering a bounty for anyone brave enough to clear the roads.",
                f"*lowers voice* If you're looking for work, I heard the local mage is seeking adventurers for a delicate matter. Pays well, but could be dangerous.",
                f"The town guard is stretched thin these days. Captain Harlow was in here yesterday, saying they might hire swords for a special task."
            ]
        elif "rumor" in player_input.lower() or "news" in player_input.lower():
            responses = [
                f"*wipes a mug clean* Strange lights have been seen in the old ruins to the north. Some say treasure hunters disturbed something ancient.",
                f"Word is the baron's son hasn't been seen in a fortnight. Official story is he's visiting relatives, but that's not what the servants say.",
                f"*leans in closer* Between you and me, there's something odd about those traveling merchants that arrived yesterday. They ask too many questions."
            ]
        else:
            responses = [
                f"*nods curtly* What can I help you with? The stew is fresh and the ale is cold, if you're interested.",
                f"You're not from around here, are ya? Well, make yourself comfortable. Just keep the peace or you'll answer to me.",
                f"*eyes you carefully* We don't get many adventurers these days. Something I can help you with?"
            ]
            
        # Randomize response
        randomness = min(max(temperature, 0.1), 1.0)
        weighted_idx = int(random.random() / randomness) % len(responses)
        return responses[weighted_idx]
    
    def generate_combat_narration(self,
                                 action_description: str,
                                 combat_state: Dict[str, Any],
                                 temperature: float = 0.6) -> str:
        """
        Generate narration for combat actions
        
        Args:
            action_description: Description of what happened mechanically
            combat_state: Current state of the combat (participants, environment, etc.)
            temperature: Controls randomness (0.0-1.0)
            
        Returns:
            Generated combat narration
        """
        prompt = f"Combat: {action_description}"
        return self.generate_response(prompt, temperature=temperature)
        
    def generate_quest(self,
                      location: str,
                      quest_type: str,
                      difficulty: str,
                      temperature: float = 0.7) -> Dict[str, Any]:
        """
        Generate a D&D quest
        
        Args:
            location: The location where the quest takes place
            quest_type: Type of quest (rescue, fetch, kill, etc.)
            difficulty: Difficulty level of the quest
            temperature: Controls randomness (0.0-1.0)
            
        Returns:
            Dictionary containing quest details
        """
        prompt = f"Generate quest: {quest_type} in {location}, {difficulty} difficulty"
        quest_description = self.generate_response(prompt, temperature=temperature)
        
        if quest_type == "rescue":
            title = "The Captive's Plea"
        elif quest_type == "fetch":
            title = "The Lost Artifact"
        elif quest_type == "kill":
            title = "Beast Hunter"
        else:
            title = "Adventure Awaits"
            
        return {
            "title": title,
            "description": quest_description,
            "type": quest_type,
            "difficulty": difficulty,
            "location": location
        }