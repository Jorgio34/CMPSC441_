# core/llm_integration.py

import os
import openai
from typing import Dict, List, Any, Optional
from utils.logger import logger

class LLMIntegration:
    """Class to handle interactions with the language model API"""
    
    def __init__(self, model_name="gpt-3.5-turbo", api_key=None):
        """Initialize the LLM integration"""
        # Set API key from parameter or environment variable
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key provided. LLM functionality will not work.")
            
        self.model_name = model_name
        
        # Initialize OpenAI client if API key is available
        if self.api_key:
            openai.api_key = self.api_key
            logger.info(f"Initialized LLM integration with model: {model_name}")
        
    def generate_response(self, 
                         prompt: str, 
                         system_message: str = None,
                         temperature: float = 0.7,
                         max_tokens: int = 500,
                         conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Generate a response from the language model
        
        Args:
            prompt: The user's input or query
            system_message: Optional system message to guide the LLM's behavior
            temperature: Controls randomness (0.0-1.0)
            max_tokens: Maximum number of tokens to generate
            conversation_history: Previous messages in the conversation
            
        Returns:
            Generated text response
        """
        if not self.api_key:
            logger.warning("Cannot generate response: No API key provided")
            return "[LLM would generate a response here with temp={temperature}]"
            
        try:
            # Prepare messages for the LLM
            messages = []
            
            # Add system message if provided
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add the current prompt
            messages.append({"role": "user", "content": prompt})
            
            # Generate response using the OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract and return the generated content
            response_text = response.choices[0].message.content
            
            # Log usage for tracking
            tokens_used = response.usage.total_tokens
            logger.info(f"LLM generated response ({tokens_used} tokens used)")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return f"[Error generating response: {str(e)}]"
    
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
        # Construct the system message with D&D game master instructions
        system_message = """
        You are an expert Dungeons & Dragons Game Master with years of experience.
        Create immersive, atmospheric descriptions and engaging NPC interactions.
        Keep responses concise but vivid, focusing on elements that advance the story
        or provide meaningful choices to players. Use sensory details and appropriate
        fantasy language to make the world come alive.
        """
        
        # Add world context if provided
        prompt = scene_description
        if world_context:
            prompt = f"World Context: {world_context}\n\nCurrent Scene: {scene_description}"
        
        # Add player input if provided
        if player_input:
            prompt += f"\n\nPlayer: {player_input}\n\nYour response as Game Master:"
        
        # Generate the response
        return self.generate_response(
            prompt=prompt,
            system_message=system_message,
            temperature=temperature,
            max_tokens=750
        )
    
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
        # Create system message for the NPC
        system_message = f"""
        You are roleplaying as {npc_name}, a character in a Dungeons & Dragons game.
        {npc_description}
        
        Respond in character to the player's input. Keep your response concise
        but true to your character's personality. Don't narrate your actions,
        just provide your dialogue as if you were speaking directly to the player.
        """
        
        # Create the prompt
        prompt = f"The player says to you: {player_input}"
        
        # Generate the response
        npc_response = self.generate_response(
            prompt=prompt,
            system_message=system_message,
            temperature=temperature,
            max_tokens=300,
            conversation_history=conversation_history
        )
        
        return npc_response
    
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
        # Create system message for combat narration
        system_message = """
        You are narrating exciting combat in a Dungeons & Dragons game.
        Describe actions vividly with appropriate fantasy combat terminology.
        Focus on the impact and sensation of attacks, spells, and movements.
        Keep descriptions concise but evocative, emphasizing dramatic moments.
        """
        
        # Create the prompt
        environment = combat_state.get("environment", "the battlefield")
        
        prompt = f"""
        Combat environment: {environment}
        
        Action that occurred: {action_description}
        
        Narrate this combat action in an exciting way:
        """
        
        # Generate the response
        return self.generate_response(
            prompt=prompt,
            system_message=system_message,
            temperature=temperature,
            max_tokens=200
        )