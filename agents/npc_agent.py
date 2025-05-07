"""
NPC Agent

Manages NPC behavior, dialogue, and decision-making for consistent
and realistic non-player characters in the D&D AI Assistant.
"""

import random
from typing import Dict, List, Any, Optional

from agents.base_agent import BaseAgent, LLMInterface
from config.prompts.system_prompts import NPC_AGENT_PROMPT


class NPCAgent(BaseAgent):
    """
    NPC Agent that manages NPC behavior, dialogue, and decision-making
    for consistent and realistic non-player characters.
    """
    
    def __init__(self, 
                npc_data: Dict[str, Any],
                model_name: str = "gpt-4",
                model_params: Optional[Dict[str, Any]] = None):
        """
        Initialize the NPC agent with data for a specific NPC.
        
        Args:
            npc_data: Dictionary with NPC information
            model_name: LLM model to use
            model_params: Model parameters
        """
        # Store NPC data
        self.npc_data = npc_data
        
        # Construct a tailored system prompt for this NPC
        npc_system_prompt = self._construct_npc_prompt(npc_data)
        
        # Initialize base agent
        super().__init__(
            name=f"NPC_{npc_data.get('name', 'Unknown')}",
            system_prompt=npc_system_prompt,
            llm=LLMInterface(model_name=model_name),
            model_params=model_params or {}
        )
        
        # Initialize interaction history
        self.interaction_history = []
    
    def _construct_npc_prompt(self, npc_data: Dict[str, Any]) -> str:
        """
        Construct a tailored system prompt for this NPC.
        
        Args:
            npc_data: Dictionary with NPC information
            
        Returns:
            System prompt for this NPC
        """
        # Start with general NPC prompt
        npc_prompt = NPC_AGENT_PROMPT
        
        # Add NPC-specific details
        npc_details = f"""
        You are roleplaying as {npc_data.get('name', 'an NPC')}, a {npc_data.get('race', '')} 
        {npc_data.get('occupation', '')} in the world of Dungeons & Dragons.
        
        Character details:
        - Personality: {', '.join(npc_data.get('personality', ['No personality defined']))}
        - Motivation: {npc_data.get('motivation', 'Unknown')}
        - Background: {npc_data.get('background', 'Unknown')}
        - Secret: {npc_data.get('secret', 'Unknown')}
        - Disposition: {npc_data.get('disposition', 'neutral')}
        
        Always respond in character as {npc_data.get('name', 'this NPC')}, using first-person 
        perspective and speech patterns appropriate for your character. Include brief descriptions 
        of your body language, tone, and emotional reactions where appropriate.
        
        Your goal is to create a consistent, believable character that reacts naturally to player 
        interactions based on your personality, background, and motivations.
        """
        
        return npc_prompt + npc_details
    
    def respond_to_player(self, 
                         player_name: str, 
                         player_speech: str, 
                         context: Optional[str] = None) -> str:
        """
        Generate an in-character response to player speech.
        
        Args:
            player_name: Name of the player character
            player_speech: What the player said to the NPC
            context: Optional additional context
            
        Returns:
            NPC's response
        """
        # Add to interaction history
        self.interaction_history.append({
            "speaker": "player",
            "name": player_name,
            "text": player_speech
        })
        
        # Format recent interaction history
        history_text = self._format_interaction_history(3)  # Last 3 interactions
        
        # Create prompt for response
        response_prompt = f"""
        {player_name} says to you: "{player_speech}"
        
        {f"Context: {context}" if context else ""}
        
        Recent conversation:
        {history_text}
        
        Respond in character as {self.npc_data.get('name', 'yourself')}, considering:
        1. Your personality and background
        2. Your current disposition and mood
        3. Your goals and motivations
        4. The current context and history of this conversation
        5. Any secrets you might be keeping
        
        Your response:
        """
        
        # Adjust model parameters based on NPC personality
        temp_adjustment = 0
        # More erratic personalities get higher temperature
        if any(trait in str(self.npc_data.get('personality', [])).lower() 
               for trait in ['unpredictable', 'chaotic', 'erratic', 'unstable']):
            temp_adjustment = 0.15
        # More methodical personalities get lower temperature
        elif any(trait in str(self.npc_data.get('personality', [])).lower() 
                for trait in ['logical', 'methodical', 'calculating', 'precise']):
            temp_adjustment = -0.15
            
        base_temp = self.model_params.get("temperature", 0.7)
        adjusted_temp = max(0.1, min(1.0, base_temp + temp_adjustment))
        
        # Generate response
        response = self.llm.generate(
            prompt=response_prompt,
            system_prompt=self.system_prompt,
            temperature=adjusted_temp,
            max_tokens=250
        )
        
        # Add response to interaction history
        self.interaction_history.append({
            "speaker": "npc",
            "name": self.npc_data.get('name', 'NPC'),
            "text": response
        })
        
        return response
    
    def _format_interaction_history(self, limit: int = 5) -> str:
        """
        Format recent interaction history for context.
        
        Args:
            limit: Maximum number of interactions to include
            
        Returns:
            Formatted interaction history
        """
        if not self.interaction_history:
            return "No previous interactions."
            
        # Get last N interactions
        recent = self.interaction_history[-limit:] if len(self.interaction_history) > limit else self.interaction_history
        
        # Format interactions
        formatted = []
        for interaction in recent:
            if interaction["speaker"] == "player":
                formatted.append(f"{interaction['name']}: \"{interaction['text']}\"")
            else:
                formatted.append(f"{interaction['name']}: \"{interaction['text']}\"")
                
        return "\n".join(formatted)
    
    def get_opinion_of(self, target_name: str, context: Optional[str] = None) -> str:
        """
        Get the NPC's opinion about a specific person, place, or thing.
        
        Args:
            target_name: Name of the target
            context: Optional additional context
            
        Returns:
            NPC's opinion
        """
        opinion_prompt = f"""
        What is your opinion of {target_name}?
        
        {f"Context: {context}" if context else ""}
        
        Consider:
        1. Your past experiences with {target_name} (if any)
        2. Your personality and values
        3. Your current goals and motivations
        4. Rumors or information you've heard
        
        Express your honest opinion in character, including your emotional reaction.
        """
        
        opinion = self.llm.generate(
            prompt=opinion_prompt,
            system_prompt=self.system_prompt,
            temperature=0.7,
            max_tokens=150
        )
        
        return opinion
    
    def make_decision(self, 
                     situation: str, 
                     options: List[str] = None,
                     context: Optional[str] = None) -> str:
        """
        Have the NPC make a decision based on their character.
        
        Args:
            situation: Description of the situation requiring a decision
            options: Optional list of specific options to choose from
            context: Optional additional context
            
        Returns:
            NPC's decision and reasoning
        """
        options_text = ""
        if options:
            options_text = "Your options are:\n" + "\n".join([f"- {option}" for option in options])
        
        decision_prompt = f"""
        You face a situation that requires a decision:
        
        {situation}
        
        {options_text}
        
        {f"Context: {context}" if context else ""}
        
        Think through this decision based on:
        1. Your personality traits and values
        2. Your goals and motivations
        3. Your relationship with those involved
        4. The potential consequences of each option
        5. Your secrets and hidden agendas
        
        Make a decision in character, explaining your thought process and reasoning.
        """
        
        decision = self.llm.generate(
            prompt=decision_prompt,
            system_prompt=self.system_prompt,
            temperature=0.7,
            max_tokens=200
        )
        
        return decision
    
    def handle_scenario(self, scenario_type: str, scenario_data: Dict[str, Any]) -> str:
        """
        Handle a specific scenario type.
        
        Args:
            scenario_type: Type of scenario to handle
            scenario_data: Data specific to the scenario
            
        Returns:
            Result of handling the scenario
        """
        if scenario_type == "dialogue":
            return self.respond_to_player(
                player_name=scenario_data.get("player_name", "Player"),
                player_speech=scenario_data.get("player_speech", ""),
                context=scenario_data.get("context")
            )
        
        elif scenario_type == "opinion":
            return self.get_opinion_of(
                target_name=scenario_data.get("target_name", ""),
                context=scenario_data.get("context")
            )
        
        elif scenario_type == "decision":
            return self.make_decision(
                situation=scenario_data.get("situation", ""),
                options=scenario_data.get("options"),
                context=scenario_data.get("context")
            )
        
        else:
            return f"Scenario type '{scenario_type}' not implemented for NPCs."