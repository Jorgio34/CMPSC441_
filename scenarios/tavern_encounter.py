"""
Tavern Encounter Scenario

This module implements the tavern encounter scenario, which demonstrates:
1. NPC interactions with memory
2. Dice-based skill checks
3. RAG for lore retrieval
4. Multi-step reasoning for NPC responses
"""

import random
from typing import Dict, List, Any, Optional

from agents.base_agent import BaseAgent
from tools.dice import roll_dice
from knowledge.retrieval import retrieve_lore


class TavernScenario:
    """Tavern encounter scenario handler for NPC interactions, dice rolls, and narrative progression"""
    
    def __init__(self, 
                 game_master_agent: BaseAgent,
                 tavern_name: str = "The Prancing Pony",
                 location: str = "Waterdeep"):
        """Initialize the tavern scenario with a game master agent and setting details"""
        self.game_master = game_master_agent
        self.tavern_name = tavern_name
        self.location = location
        self.mood = "lively"  # Initial tavern mood
        self.current_interlocutor = None  # Currently speaking NPC
        
        # Add tavern to game master's memory
        self.game_master.add_memory(
            f"The party is currently in {self.tavern_name}, a tavern in {self.location}. "
            f"The tavern is {self.mood}.",
            memory_type="setting"
        )
        
        # Generate default NPCs
        self.npcs = self._generate_default_npcs()
        
        # Add NPCs to game master's memory
        for npc in self.npcs:
            self.game_master.add_memory(
                f"{npc['name']} is a {npc['race']} {npc['occupation']} in the tavern. "
                f"They are {npc['disposition']} toward the party.",
                memory_type="npc"
            )
    
    def _generate_default_npcs(self) -> List[Dict[str, Any]]:
        """Generate a default set of NPCs for the tavern"""
        return [
            {
                "name": "Durnan",
                "race": "Human",
                "occupation": "Barkeep",
                "disposition": "neutral",
                "knowledge": "Knows rumors about local dungeons",
                "personality": "Gruff but fair",
                "secret": "Former adventurer who explored Undermountain"
            },
            {
                "name": "Elaria",
                "race": "Half-Elf",
                "occupation": "Bard",
                "disposition": "friendly",
                "knowledge": "Knows songs and tales from across the realm",
                "personality": "Outgoing and curious",
                "secret": "Working as a spy for the Harper's guild"
            },
            {
                "name": "Grum",
                "race": "Dwarf",
                "occupation": "Merchant",
                "disposition": "suspicious",
                "knowledge": "Information about rare items and their sources",
                "personality": "Greedy but reliable",
                "secret": "Sells contraband magical items under the table"
            }
        ]
    
    def enter_tavern(self) -> str:
        """Handle the initial tavern entry"""
        # Retrieve relevant lore about the tavern and location
        tavern_lore = self.game_master.use_tool("retrieve_lore", f"{self.tavern_name} {self.location}")
        
        # Use the RAG approach to incorporate lore into the description
        self.game_master.add_memory(
            f"Relevant lore about {self.tavern_name}: {tavern_lore}",
            memory_type="lore"
        )
        
        # Prompt engineering: Specific prompt for tavern description
        tavern_prompt = f"""
        The party enters {self.tavern_name} in {self.location}. 
        The tavern is {self.mood} at this time of day.
        
        Describe the tavern in vivid detail, including:
        - The atmosphere and ambiance
        - Sounds, smells, and sights
        - Notable patrons (including {', '.join([npc['name'] for npc in self.npcs])})
        - Any immediate hooks or points of interest
        
        Make the description immersive and evocative, setting the stage for roleplay.
        """
        
        # Use a lower temperature for descriptive text to ensure coherence
        temp = self.game_master.model_params.get("temperature", 0.7)
        self.game_master.model_params["temperature"] = 0.5
        description = self.game_master.process(tavern_prompt)
        # Reset temperature to default
        self.game_master.model_params["temperature"] = temp
        
        return description
    
    def interact_with_npc(self, npc_name: str, player_query: str, player_charisma: int = 10) -> str:
        """Handle player interaction with a specific NPC"""
        # Find the requested NPC
        npc = next((n for n in self.npcs if n["name"].lower() == npc_name.lower()), None)
        if not npc:
            return f"There doesn't seem to be anyone named {npc_name} in the tavern."
        
        # Set as current interlocutor
        self.current_interlocutor = npc
        
        # Determine if a skill check is needed based on the query content
        requires_check = any(word in player_query.lower() for word 
                            in ["secret", "truth", "persuade", "convince", "intimidate", "lie"])
        
        # If persuasion/deception is being attempted, perform a charisma check
        check_result = None
        if requires_check:
            # Use the dice tool to roll a charisma check
            check_result = self.game_master.use_tool("roll_dice", "1d20") + (player_charisma - 10) // 2
            
            # Add the check result to memory
            self.game_master.add_memory(
                f"Player made a charisma check when speaking to {npc['name']}, "
                f"resulting in a {check_result}.",
                memory_type="game_mechanics"
            )
            
            # Determine disposition modifier based on check
            if check_result >= 15:
                # Success
                disposition_mod = "more favorably than usual"
            elif check_result <= 5:
                # Critical failure
                disposition_mod = "more suspiciously than usual"
            else:
                # Neutral
                disposition_mod = "with typical demeanor"
                
            # Update NPC's temporary disposition
            npc["temp_disposition"] = disposition_mod
        else:
            npc["temp_disposition"] = "with typical demeanor"
        
        # Retrieve any additional lore relevant to this NPC
        npc_lore = self.game_master.use_tool("retrieve_lore", f"{npc['name']} {npc['occupation']} {self.location}")
        if npc_lore:
            self.game_master.add_memory(
                f"Additional lore about {npc['name']}: {npc_lore}",
                memory_type="lore"
            )
        
        # Use chain of thought prompting to generate NPC response
        # This demonstrates the planning & reasoning requirement
        npc_response_prompt = f"""
        The player speaks to {npc['name']}, the {npc['race']} {npc['occupation']}.
        
        Player says: "{player_query}"
        
        {npc['name']} is {npc['disposition']} toward the party generally, but is responding {npc['temp_disposition']} right now.
        
        Personality: {npc['personality']}
        Knowledge: {npc['knowledge']}
        Secret: {npc['secret']}
        
        Before responding, think through:
        1. How would this character feel about this query?
        2. What knowledge do they have that's relevant?
        3. Would they reveal their secret? (Only if check result > 18)
        4. What are their goals and motivations in this interaction?
        5. How does their race and occupation influence their perspective?
        
        Then respond as {npc['name']}, using first-person speech and mannerisms appropriate to their personality.
        """
        
        # Use a higher temperature for NPC responses to allow for personality
        temp = self.game_master.model_params.get("temperature", 0.7)
        self.game_master.model_params["temperature"] = 0.8
        response = self.game_master.process(npc_response_prompt)
        # Reset temperature to default
        self.game_master.model_params["temperature"] = temp
        
        # Add interaction to memory
        self.game_master.add_memory(
            f"Player spoke to {npc['name']} saying: '{player_query}'. "
            f"The NPC responded: '{response[:100]}...'",
            memory_type="interaction"
        )
        
        # If check was very successful and secret was relevant, update NPC state
        if check_result and check_result > 18 and "secret" in player_query.lower():
            self.game_master.add_memory(
                f"{npc['name']} has revealed their secret to the party.",
                memory_type="plot_development"
            )
        
        return response
    
    def roll_perception_check(self, player_wisdom: int = 10) -> str:
        """Perform a perception check to notice something in the tavern"""
        # Roll perception check
        check_result = self.game_master.use_tool("roll_dice", "1d20") + (player_wisdom - 10) // 2
        
        # Determine what is noticed based on result
        # This demonstrates the RAG implementation by pulling different information
        if check_result >= 18:
            # Critical success - notice something very subtle
            # Use RAG to retrieve "secrets" about the tavern
            secret_detail = self.game_master.use_tool("retrieve_lore", f"{self.tavern_name} secret")
            perception_detail = f"With your exceptionally keen awareness, you notice: {secret_detail}"
        elif check_result >= 15:
            # Success - notice something interesting
            interesting_detail = self.game_master.use_tool("retrieve_lore", f"{self.tavern_name} interesting detail")
            perception_detail = f"Your sharp eyes catch: {interesting_detail}"
        elif check_result >= 10:
            # Average - notice normal elements
            normal_detail = self.game_master.use_tool("retrieve_lore", f"{self.tavern_name} common sight")
            perception_detail = f"You observe: {normal_detail}"
        else:
            # Failure - notice nothing or get distracted
            perception_detail = "You look around, but nothing in particular catches your attention."
        
        # Add the perception result to memory
        self.game_master.add_memory(
            f"Player made a perception check in the tavern, resulting in a {check_result}. "
            f"They noticed: {perception_detail[:100]}...",
            memory_type="game_mechanics"
        )
        
        return perception_detail
    
    def tavern_event(self) -> str:
        """Generate a random event that occurs in the tavern"""
        # List of possible tavern events
        events = [
            "A bar fight breaks out between two patrons",
            "A messenger bursts in with urgent news",
            "A group of musicians starts playing a lively tune",
            "A hooded stranger enters and surveys the room",
            "Someone spills their drink on a temperamental warrior",
            "The lights flicker and dim momentarily",
            "A local noble arrives with their entourage",
            "A drunken patron starts telling improbable stories",
            "A fortune teller offers to read someone's future",
            "The barkeep announces a special discount"
        ]
        
        # Select random event
        event = random.choice(events)
        
        # Use planning & reasoning to determine consequences
        event_prompt = f"""
        The following event occurs in {self.tavern_name}:
        
        {event}
        
        Think about:
        1. How do the various NPCs react?
        2. What opportunities does this create for the players?
        3. How might this event develop if left unaddressed?
        4. What subtle details set the mood?
        
        Describe the event unfolding in vivid detail, including NPC reactions and opportunities for player interaction.
        """
        
        # Generate event description
        event_description = self.game_master.process(event_prompt)
        
        # Add event to memory
        self.game_master.add_memory(
            f"A tavern event occurred: {event}",
            memory_type="plot_development"
        )
        
        return event_description


def create_tavern_scenario(game_master_agent: BaseAgent) -> TavernScenario:
    """Create and return a tavern scenario instance"""
    # Make sure the game master has the dice rolling tool
    if "roll_dice" not in game_master_agent.tools:
        game_master_agent.tools["roll_dice"] = roll_dice
    
    # Create the scenario
    tavern = TavernScenario(
        game_master_agent=game_master_agent,
        tavern_name="The Dragon's Rest",
        location="Neverwinter"
    )
    
    return tavern