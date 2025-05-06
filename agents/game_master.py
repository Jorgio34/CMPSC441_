"""
Game Master Agent

This module implements the Game Master agent, which is responsible for
narrative control, scene descriptions, NPC behavior, and rule adjudication.
It demonstrates advanced prompt engineering and chain-of-thought reasoning.
"""

import os
import logging
import random
from typing import Dict, List, Any, Optional, Tuple, Union

from agents.base_agent import BaseAgent, LLMInterface, Memory
from knowledge.retrieval import retrieve_rule, retrieve_lore, retrieve_monster
from tools.dice import roll_dice
from utils.text_processing import extract_entities
from config.prompts.system_prompts import GAME_MASTER_SYSTEM_PROMPT


class GameMasterAgent(BaseAgent):
    """
    Game Master agent that manages the narrative, NPCs, environment,
    and game rules for a D&D game session.
    """
    
    def __init__(self, 
                model_name: str = "gpt-4",
                model_params: Optional[Dict[str, Any]] = None,
                knowledge_base: Optional[Any] = None):
        """
        Initialize the Game Master agent.
        
        Args:
            model_name: The LLM model to use
            model_params: Model parameters for different functions
            knowledge_base: Reference to the knowledge retrieval system
        """
        # Initialize base agent
        super().__init__(
            name="GameMaster",
            system_prompt=GAME_MASTER_SYSTEM_PROMPT,
            llm=LLMInterface(model_name=model_name),
            tools={
                "roll_dice": roll_dice,
                "retrieve_rule": retrieve_rule,
                "retrieve_lore": retrieve_lore,
                "retrieve_monster": retrieve_monster
            },
            model_params=model_params or {}
        )
        
        self.knowledge_base = knowledge_base
        self.current_scene = None
        self.active_npcs = []
        self.campaign_state = {
            "party_level": 1,
            "location": "None",
            "active_quests": [],
            "completed_quests": [],
            "campaign_arc": "beginning"
        }
        
        self.logger = logging.getLogger("GameMaster")
        
    def describe_scene(self, location: str, 
                      time_of_day: str = "day", 
                      mood: str = "neutral", 
                      include_npcs: bool = True) -> str:
        """
        Generate a rich description of a scene.
        
        Args:
            location: The location to describe
            time_of_day: Time of day (e.g., "morning", "night")
            mood: The emotional tone of the description
            include_npcs: Whether to include NPCs in the description
            
        Returns:
            A narrative description of the scene
        """
        # Update current scene
        self.current_scene = {
            "location": location,
            "time_of_day": time_of_day,
            "mood": mood
        }
        
        # Retrieve relevant lore for the location
        location_lore = self.use_tool("retrieve_lore", location)
        
        # Create active NPCs for the scene if requested
        npc_descriptions = ""
        if include_npcs and not self.active_npcs:
            # Generate 1-3 NPCs appropriate for the location
            num_npcs = roll_dice("1d3")
            self._generate_npcs(location, num_npcs)
            
            # Format NPC descriptions
            npc_descriptions = "\n".join([
                f"- {npc['name']}: {npc['description']}" 
                for npc in self.active_npcs
            ])
        
        # Use different temperature for scene descriptions
        description_params = self.model_params.get("functions", {}).get("description", {})
        temp = description_params.get("temperature", self.model_params.get("temperature", 0.7))
        max_tokens = description_params.get("max_tokens", self.model_params.get("max_tokens", 300))
        
        # Use chain-of-thought prompting for scene construction
        scene_prompt = f"""
        You need to describe the {location} during {time_of_day} with a {mood} atmosphere.
        
        First, think about:
        1. What are the key visual elements of this location?
        2. What sounds would be present?
        3. What smells or other sensory details would be notable?
        4. How does the {time_of_day} affect the setting?
        5. How can you convey a {mood} mood through your description?
        
        Relevant lore about this location:
        {location_lore}
        
        {"NPCs present in this location:" if include_npcs and self.active_npcs else ""}
        {npc_descriptions if include_npcs and self.active_npcs else ""}
        
        Now, write a vivid, sensory-rich description of the {location} that brings the scene to life.
        Use second person ("you") perspective to immerse the players. Keep the description between 
        3-5 sentences for pacing.
        """
        
        # Generate the description with adjusted parameters
        description = self.llm.generate(
            prompt=scene_prompt,
            system_prompt=self.system_prompt,
            temperature=temp,
            max_tokens=max_tokens
        )
        
        # Add the scene description to memory
        self.add_memory(
            f"Scene description for {location} during {time_of_day}: {description[:100]}...",
            memory_type="scene"
        )
        
        return description
    
    def _generate_npcs(self, location: str, count: int) -> None:
        """Generate NPCs appropriate for the current location"""
        # Real implementation would use more sophisticated NPC generation
        # For now, we'll use a simplified approach
        
        # Common NPC templates by location type
        location_npcs = {
            "tavern": [
                {"name": "Barkeep", "type": "service", "attitude": "neutral"},
                {"name": "Bard", "type": "entertainment", "attitude": "friendly"},
                {"name": "Merchant", "type": "commerce", "attitude": "suspicious"},
                {"name": "Noble", "type": "patron", "attitude": "haughty"},
                {"name": "Mercenary", "type": "patron", "attitude": "gruff"}
            ],
            "market": [
                {"name": "Vendor", "type": "commerce", "attitude": "friendly"},
                {"name": "Guard", "type": "authority", "attitude": "stern"},
                {"name": "Pickpocket", "type": "criminal", "attitude": "deceptive"},
                {"name": "Crier", "type": "information", "attitude": "loud"},
                {"name": "Merchant", "type": "commerce", "attitude": "persuasive"}
            ],
            "temple": [
                {"name": "Priest", "type": "religious", "attitude": "serene"},
                {"name": "Acolyte", "type": "service", "attitude": "respectful"},
                {"name": "Worshipper", "type": "visitor", "attitude": "devout"},
                {"name": "Beggar", "type": "supplicant", "attitude": "humble"},
                {"name": "Pilgrim", "type": "visitor", "attitude": "reverent"}
            ],
            "wilderness": [
                {"name": "Hunter", "type": "local", "attitude": "wary"},
                {"name": "Hermit", "type": "resident", "attitude": "eccentric"},
                {"name": "Ranger", "type": "authority", "attitude": "vigilant"},
                {"name": "Traveler", "type": "visitor", "attitude": "curious"},
                {"name": "Bandit", "type": "threat", "attitude": "hostile"}
            ]
        }
        
        # Determine which NPC set to use
        npc_set = None
        for loc_type, npcs in location_npcs.items():
            if loc_type.lower() in location.lower():
                npc_set = npcs
                break
        
        # Use tavern as default if no match
        if npc_set is None:
            npc_set = location_npcs["tavern"]
            
        # Select random NPCs up to the count
        selected_templates = random.sample(npc_set, min(count, len(npc_set)))
        
        # Generate detailed NPCs from templates
        self.active_npcs = []
        for template in selected_templates:
            # Generate a more specific name
            names = {
                "Human": ["Jorah", "Eliza", "Thorne", "Meera", "Aldric"],
                "Elf": ["Thranduil", "Arwen", "Elrond", "Galadriel", "Legolas"],
                "Dwarf": ["Thorin", "Gimli", "Dain", "Balin", "Dwalin"],
                "Halfling": ["Bilbo", "Frodo", "Sam", "Merry", "Pippin"]
            }
            race = random.choice(list(names.keys()))
            name = random.choice(names[race])
            
            # Generate basic personality
            personalities = [
                "quiet and observant", "loud and boisterous", 
                "calculating and shrewd", "warm and generous",
                "nervous and fidgety", "stoic and reserved"
            ]
            personality = random.choice(personalities)
            
            # Create the NPC
            npc = {
                "name": name,
                "race": race,
                "occupation": template["name"],
                "type": template["type"],
                "attitude": template["attitude"],
                "personality": personality,
                "description": f"A {personality} {race} {template['name'].lower()} who appears {template['attitude']}",
                "secret": self._generate_npc_secret(template["type"])
            }
            
            self.active_npcs.append(npc)
            
            # Add NPC to memory
            self.add_memory(
                f"{npc['name']} is a {npc['race']} {npc['occupation']} in {location}. "
                f"They are {npc['personality']} and generally {npc['attitude']}.",
                memory_type="npc"
            )
            
    def _generate_npc_secret(self, npc_type: str) -> str:
        """Generate a secret for an NPC based on their type"""
        secrets = {
            "service": [
                "Is skimming money from their employer",
                "Is a spy for a rival establishment",
                "Has a forbidden romance with a noble",
                "Is addicted to a rare substance",
                "Used to be an adventurer until an injury"
            ],
            "entertainment": [
                "Is actually a famous bard in disguise",
                "Is using magic to enhance their performances",
                "Is gathering information for a thieves' guild",
                "Has lost their inspiration and is faking it",
                "Is possessed by a benign spirit"
            ],
            "commerce": [
                "Sells illegal goods on the side",
                "Is being blackmailed by a local gang",
                "Has magical items mixed in with normal wares",
                "Is actually much wealthier than they appear",
                "Is a fugitive using a false identity"
            ],
            "patron": [
                "Is hiding from assassins",
                "Is looking to hire for an illegal job",
                "Has gambled away their family fortune",
                "Is a shapeshifter in disguise",
                "Is investigating another patron"
            ],
            "authority": [
                "Is corrupt and taking bribes",
                "Is planning to overthrow their superior",
                "Knows about a coming disaster but is sworn to secrecy",
                "Is an imposter who killed the real authority figure",
                "Is actually working for a secret organization"
            ],
            "criminal": [
                "Is an undercover guard",
                "Is being forced into crime by threats to their family",
                "Is actually a noble slumming for thrills",
                "Has a magical item that helps them escape",
                "Is planning to betray their criminal organization"
            ],
            "religious": [
                "Has lost their faith but pretends otherwise",
                "Is actually worshipping a forbidden deity",
                "Has prophetic visions they don't understand",
                "Is hiding fugitives in their holy place",
                "Knows a dark secret about their religious order"
            ]
        }
        
        # Get secrets for this NPC type, or use a default set
        type_secrets = secrets.get(npc_type, secrets["service"])
        return random.choice(type_secrets)
    
    def handle_player_action(self, player_name: str, action: str) -> str:
        """
        Process a player's action and generate the outcome.
        
        Args:
            player_name: The name of the player
            action: The action being attempted
            
        Returns:
            Description of the action's outcome
        """
        # Extract key elements from the action
        action_elements = extract_entities(action)
        
        # Determine if a skill check is needed
        check_type, difficulty = self._determine_check_type(action)
        
        # If a check is needed, perform it
        check_result = None
        if check_type:
            # In a real implementation, we'd look up the player's skill bonus
            # For now, we'll use a simplified approach
            skill_bonus = 2  # Assume +2 bonus for demo purposes
            check_result = self.use_tool("roll_dice", "1d20") + skill_bonus
            
            # Add the check to memory
            self.add_memory(
                f"{player_name} attempted a {check_type} check for: {action}. "
                f"Result: {check_result} (needed {difficulty})",
                memory_type="game_mechanics"
            )
            
            # Determine success or failure
            success = check_result >= difficulty
        else:
            # No check needed, action automatically succeeds
            success = True
        
        # Use reasoning to determine the outcome
        outcome_prompt = f"""
        {player_name} attempts the following action:
        "{action}"
        
        Current scene: {self.current_scene["location"]} during {self.current_scene["time_of_day"]}
        
        {"A " + check_type + " check was required." if check_type else "No skill check was required for this action."}
        {"The result was " + str(check_result) + " against a difficulty of " + str(difficulty) + "." if check_type else ""}
        {"The action succeeds." if success else "The action fails."}
        
        Think through the following:
        1. What is the immediate outcome of this action?
        2. What consequences might result from this action?
        3. How does the environment or NPCs react?
        4. What new opportunities or challenges emerge?
        5. How should this be described to maintain narrative flow?
        
        Generate a vivid, detailed description of the outcome that flows naturally from the player's action.
        Use second person perspective ("you") and maintain the established tone and mood.
        """
        
        # Generate outcome with appropriate parameters
        outcome = self.llm.generate(
            prompt=outcome_prompt,
            system_prompt=self.system_prompt,
            temperature=0.7,
            max_tokens=250
        )
        
        # Add outcome to memory
        self.add_memory(
            f"{player_name}'s action: {action}. Outcome: {outcome[:100]}...",
            memory_type="player_actions"
        )
        
        return outcome
    
    def _determine_check_type(self, action: str) -> Tuple[Optional[str], int]:
        """
        Determine if a skill check is needed for an action and what type.
        
        Args:
            action: The action being attempted
            
        Returns:
            Tuple of (check_type, difficulty) or (None, 0) if no check needed
        """
        # Common action words that suggest specific checks
        skill_checks = {
            "sneak": ("Stealth", 15),
            "hide": ("Stealth", 15),
            "climb": ("Athletics", 12),
            "jump": ("Athletics", 10),
            "convince": ("Persuasion", 15),
            "persuade": ("Persuasion", 15),
            "intimidate": ("Intimidation", 15),
            "scare": ("Intimidation", 13),
            "lie": ("Deception", 15),
            "deceive": ("Deception", 15),
            "notice": ("Perception", 12),
            "spot": ("Perception", 12),
            "search": ("Investigation", 12),
            "investigate": ("Investigation", 13),
            "recall": ("History", 12),
            "remember": ("History", 12),
            "identify": ("Arcana", 15),
            "analyze": ("Investigation", 13),
            "heal": ("Medicine", 12),
            "treat": ("Medicine", 12),
            "handle": ("Animal Handling", 12),
            "tame": ("Animal Handling", 15),
            "entertain": ("Performance", 13),
            "perform": ("Performance", 13),
            "pick": ("Sleight of Hand", 15),
            "steal": ("Sleight of Hand", 15),
            "balance": ("Acrobatics", 12),
            "flip": ("Acrobatics", 13),
            "dodge": ("Acrobatics", 15)
        }
        
        # Check if the action contains any of the skill check triggers
        action_lower = action.lower()
        for keyword, (skill, dc) in skill_checks.items():
            if keyword in action_lower:
                return skill, dc
        
        # No skill check needed
        return None, 0
    
    def npc_interaction(self, 
                       npc_name: str, 
                       player_name: str, 
                       player_speech: str) -> str:
        """
        Handle dialogue interaction between a player and an NPC.
        
        Args:
            npc_name: Name of the NPC
            player_name: Name of the player
            player_speech: What the player says
            
        Returns:
            The NPC's response
        """
        # Find the specified NPC
        npc = next((n for n in self.active_npcs if n["name"].lower() == npc_name.lower()), None)
        if not npc:
            return f"There doesn't seem to be anyone named {npc_name} here."
        
        # Analyze the player's speech for intent
        speech_analysis = self._analyze_speech_intent(player_speech)
        
        # Determine NPC disposition modifier based on appropriateness of interaction
        disposition_mod = 0
        if speech_analysis["approach"] == "friendly" and npc["attitude"] in ["friendly", "neutral"]:
            disposition_mod = 2
        elif speech_analysis["approach"] == "hostile" and npc["attitude"] in ["suspicious", "hostile"]:
            disposition_mod = -2
            
        # Determine if persuasion/intimidation check is needed
        check_type = None
        if speech_analysis["intent"] == "persuade":
            check_type = "Persuasion"
        elif speech_analysis["intent"] == "intimidate":
            check_type = "Intimidation"
        elif speech_analysis["intent"] == "deceive":
            check_type = "Deception"
        
        # Perform check if needed
        check_result = None
        if check_type:
            # In a real implementation, we'd look up the player's skill bonus
            skill_bonus = 2  # Assume +2 bonus for demo purposes
            check_result = self.use_tool("roll_dice", "1d20") + skill_bonus
            
            # Add check result to memory
            self.add_memory(
                f"{player_name} made a {check_type} check when speaking to {npc_name}, "
                f"resulting in a {check_result}.",
                memory_type="game_mechanics"
            )
            
            # Apply check result to disposition modifier
            if check_result >= 20:  # Critical success
                disposition_mod += 5
            elif check_result >= 15:  # Success
                disposition_mod += 3
            elif check_result <= 5:  # Critical failure
                disposition_mod -= 5
            elif check_result < 10:  # Failure
                disposition_mod -= 2
                
        # Retrieve any relevant lore about topics mentioned
        lore_context = ""
        for topic in speech_analysis["topics"]:
            lore = self.use_tool("retrieve_lore", topic)
            if lore:
                lore_context += f"\nRelevant information about {topic}: {lore}\n"
        
        # Use different parameters for NPC dialogue
        dialogue_params = self.model_params.get("functions", {}).get("npc_dialogue", {})
        temp = dialogue_params.get("temperature", self.model_params.get("temperature", 0.8))
        max_tokens = dialogue_params.get("max_tokens", self.model_params.get("max_tokens", 250))
        
        # Generate NPC response with reasoning process
        response_prompt = f"""
        {player_name} speaks to {npc["name"]}, a {npc["race"]} {npc["occupation"]}, saying:
        
        "{player_speech}"
        
        Information about {npc["name"]}:
        - Personality: {npc["personality"]}
        - Attitude: {npc["attitude"]}
        - Secret: {npc["secret"]}
        
        Current disposition modifier: {disposition_mod} (positive is more favorable)
        
        {lore_context if lore_context else ""}
        
        Think through these steps before responding:
        1. How would {npc["name"]} feel about what was said?
        2. What knowledge does {npc["name"]} have that's relevant?
        3. What are {npc["name"]}'s goals in this conversation?
        4. Would {npc["name"]} reveal their secret? (Only if check result > 18 and relevant)
        5. How does {npc["name"]}'s race and occupation influence their response?
        
        Then respond as {npc["name"]} in first-person dialogue with mannerisms and speech patterns 
        appropriate to their personality and background. Include brief physical actions or gestures that
        convey their emotional state.
        """
        
        # Generate the response with adjusted parameters
        response = self.llm.generate(
            prompt=response_prompt,
            system_prompt=self.system_prompt,
            temperature=temp,
            max_tokens=max_tokens
        )
        
        # Add the interaction to memory
        self.add_memory(
            f"{player_name} spoke to {npc['name']} saying: '{player_speech}'. "
            f"The NPC responded: '{response[:100]}...'",
            memory_type="npc_interaction"
        )
        
        # Potentially update NPC state based on interaction
        if check_result and check_result >= 18 and "secret" in speech_analysis["topics"]:
            # NPC has revealed their secret
            self.add_memory(
                f"{npc['name']} has revealed their secret to {player_name}.",
                memory_type="plot_development"
            )
        
        return response
    
    def _analyze_speech_intent(self, speech: str) -> Dict[str, Any]:
        """
        Analyze player speech to determine intent, approach, and topics.
        
        Args:
            speech: What the player said
            
        Returns:
            Dictionary with analysis results
        """
        # In a full implementation, this would use more sophisticated NLP
        # For now, we'll use a simple keyword approach
        
        # Detect intent
        intent = "converse"  # Default intent
        if any(word in speech.lower() for word in ["convince", "persuade", "agree", "please"]):
            intent = "persuade"
        elif any(word in speech.lower() for word in ["threaten", "intimidate", "scare", "warn"]):
            intent = "intimidate"
        elif any(word in speech.lower() for word in ["lie", "deceive", "trick", "mislead"]):
            intent = "deceive"
        elif any(word in speech.lower() for word in ["buy", "sell", "trade", "purchase"]):
            intent = "commerce"
        elif any(word in speech.lower() for word in ["help", "quest", "mission", "task"]):
            intent = "request_help"
            
        # Detect approach
        approach = "neutral"  # Default approach
        if any(word in speech.lower() for word in ["please", "thank", "kind", "friend", "help"]):
            approach = "friendly"
        elif any(word in speech.lower() for word in ["stupid", "idiot", "hate", "damn", "curse"]):
            approach = "hostile"
            
        # Extract potential topics
        # In a real implementation, this would use named entity recognition
        # For now, we'll use a simplified approach
        topics = []
        
        # Common D&D topics
        topic_keywords = {
            "quest": ["quest", "mission", "job", "task", "adventure"],
            "monster": ["monster", "creature", "beast", "dragon", "undead"],
            "treasure": ["treasure", "gold", "coin", "wealth", "riches", "payment"],
            "magic": ["magic", "spell", "wizard", "sorcerer", "enchant", "arcane"],
            "weapon": ["sword", "axe", "bow", "weapon", "dagger", "armor"],
            "location": ["dungeon", "castle", "forest", "mountain", "cave", "temple"],
            "rumor": ["rumor", "gossip", "hear", "tale", "story", "legend"],
            "secret": ["secret", "hidden", "mystery", "discover", "reveal", "truth"]
        }
        
        # Check for topics in speech
        for topic, keywords in topic_keywords.items():
            if any(keyword in speech.lower() for keyword in keywords):
                topics.append(topic)
                
        return {
            "intent": intent,
            "approach": approach,
            "topics": topics
        }
    
    def generate_encounter(self, 
                          location: str, 
                          difficulty: str = "medium",
                          encounter_type: str = "combat") -> Dict[str, Any]:
        """
        Generate a random encounter appropriate for the location.
        
        Args:
            location: Where the encounter takes place
            difficulty: Difficulty level ("easy", "medium", "hard", "deadly")
            encounter_type: Type of encounter ("combat", "social", "trap", "puzzle")
            
        Returns:
            Dictionary with encounter details
        """
        # Determine party level from campaign state
        party_level = self.campaign_state["party_level"]
        
        # Generate appropriate monsters for combat encounters
        if encounter_type == "combat":
            # Determine number and CR of monsters based on difficulty and party level
            if difficulty == "easy":
                num_monsters = roll_dice("1d3+1")  # 2-4 monsters
                cr_modifier = -2  # CR lower than party level
            elif difficulty == "medium":
                num_monsters = roll_dice("1d4")  # 1-4 monsters
                cr_modifier = 0  # CR equal to party level
            elif difficulty == "hard":
                num_monsters = roll_dice("1d2+1")  # 2-3 monsters
                cr_modifier = 1  # CR slightly higher than party level
            else:  # deadly
                num_monsters = roll_dice("1d2")  # 1-2 monsters
                cr_modifier = 2  # CR higher than party level
                
            # Calculate target CR (minimum CR 1/8)
            target_cr = max(0.125, party_level + cr_modifier)
            
            # In a real implementation, we would query a monster database
            # For now, we'll use a simplified approach
            monsters = self._select_appropriate_monsters(location, target_cr, num_monsters)
            
            encounter = {
                "type": "combat",
                "location": location,
                "difficulty": difficulty,
                "monsters": monsters,
                "setup": self._generate_encounter_setup(location, monsters)
            }
            
        # Generate social encounters
        elif encounter_type == "social":
            # Generate NPCs for the encounter
            num_npcs = roll_dice("1d3")
            self._generate_npcs(location, num_npcs)
            
            # Select a social encounter type
            social_types = ["negotiation", "interrogation", "celebration", "dispute", "performance"]
            social_type = random.choice(social_types)
            
            encounter = {
                "type": "social",
                "subtype": social_type,
                "location": location,
                "difficulty": difficulty,
                "npcs": self.active_npcs,
                "setup": self._generate_social_setup(location, social_type)
            }
            
        # Generate trap encounters
        elif encounter_type == "trap":
            # Determine trap complexity and damage
            if difficulty == "easy":
                complexity = "simple"
                damage_dice = "2d6"
            elif difficulty == "medium":
                complexity = "moderate"
                damage_dice = "4d6"
            elif difficulty == "hard":
                complexity = "complex"
                damage_dice = "6d6"
            else:  # deadly
                complexity = "advanced"
                damage_dice = "10d6"
                
            # Determine detection and disarm DCs
            detect_dc = 10 + (party_level // 2) + (0 if difficulty == "easy" else 2 if difficulty == "medium" else 5 if difficulty == "hard" else 8)
            disarm_dc = detect_dc + 2
            
            # Generate trap details
            trap_types = ["pitfall", "poison dart", "crushing wall", "flame jet", "magic rune", "falling net"]
            trap_type = random.choice(trap_types)
            
            encounter = {
                "type": "trap",
                "trap_type": trap_type,
                "location": location,
                "difficulty": difficulty,
                "complexity": complexity,
                "detect_dc": detect_dc,
                "disarm_dc": disarm_dc,
                "damage": damage_dice,
                "setup": self._generate_trap_setup(location, trap_type)
            }
            
        # Generate puzzle encounters
        elif encounter_type == "puzzle":
            # Determine puzzle complexity
            if difficulty == "easy":
                complexity = "simple"
                hints = 3
            elif difficulty == "medium":
                complexity = "moderate"
                hints = 2
            elif difficulty == "hard":
                complexity = "complex"
                hints = 1
            else:  # deadly
                complexity = "devious"
                hints = 0
                
            # Generate puzzle details
            puzzle_types = ["riddle", "pattern matching", "symbol sequence", "mechanical device", "magical illusion", "element combination"]
            puzzle_type = random.choice(puzzle_types)
            
            encounter = {
                "type": "puzzle",
                "puzzle_type": puzzle_type,
                "location": location,
                "difficulty": difficulty,
                "complexity": complexity,
                "available_hints": hints,
                "solution_dc": 10 + (party_level // 2) + (0 if difficulty == "easy" else 3 if difficulty == "medium" else 6 if difficulty == "hard" else 9),
                "setup": self._generate_puzzle_setup(location, puzzle_type)
            }
            
        # Add encounter to memory
        self.add_memory(
            f"Generated a {difficulty} {encounter_type} encounter in {location}.",
            memory_type="encounter"
        )
        
        return encounter
    
    def _select_appropriate_monsters(self, location: str, target_cr: float, count: int) -> List[Dict[str, Any]]:
        """Select appropriate monsters for an encounter"""
        # In a real implementation, this would query a monster database
        # For now, we'll use a simplified approach with some common monsters by location
        
        # Very simplified monster data by environment
        location_monsters = {
            "forest": [
                {"name": "Wolf", "cr": 0.25, "type": "beast"},
                {"name": "Dire Wolf", "cr": 1, "type": "beast"},
                {"name": "Giant Spider", "cr": 1, "type": "beast"},
                {"name": "Brown Bear", "cr": 1, "type": "beast"},
                {"name": "Goblin", "cr": 0.25, "type": "humanoid"},
                {"name": "Bandit", "cr": 0.125, "type": "humanoid"},
                {"name": "Satyr", "cr": 0.5, "type": "fey"},
                {"name": "Dryad", "cr": 1, "type": "fey"},
                {"name": "Green Hag", "cr": 3, "type": "fey"},
                {"name": "Werewolf", "cr": 3, "type": "humanoid"}
            ],
            "dungeon": [
                {"name": "Skeleton", "cr": 0.25, "type": "undead"},
                {"name": "Zombie", "cr": 0.25, "type": "undead"},
                {"name": "Ghoul", "cr": 1, "type": "undead"},
                {"name": "Goblin", "cr": 0.25, "type": "humanoid"},
                {"name": "Kobold", "cr": 0.125, "type": "humanoid"},
                {"name": "Giant Rat", "cr": 0.125, "type": "beast"},
                {"name": "Ooze", "cr": 2, "type": "ooze"},
                {"name": "Mimic", "cr": 2, "type": "monstrosity"},
                {"name": "Grick", "cr": 2, "type": "monstrosity"},
                {"name": "Shadow", "cr": 0.5, "type": "undead"}
            ],
            "mountain": [
                {"name": "Eagle", "cr": 0, "type": "beast"},
                {"name": "Giant Eagle", "cr": 1, "type": "beast"},
                {"name": "Harpy", "cr": 1, "type": "monstrosity"},
                {"name": "Ogre", "cr": 2, "type": "giant"},
                {"name": "Hill Giant", "cr": 5, "type": "giant"},
                {"name": "Orc", "cr": 0.5, "type": "humanoid"},
                {"name": "Griffon", "cr": 2, "type": "monstrosity"},
                {"name": "Manticore", "cr": 3, "type": "monstrosity"},
                {"name": "Wyvern", "cr": 6, "type": "dragon"},
                {"name": "Young Dragon", "cr": 8, "type": "dragon"}
            ],
            "city": [
                {"name": "Bandit", "cr": 0.125, "type": "humanoid"},
                {"name": "Thug", "cr": 0.5, "type": "humanoid"},
                {"name": "Spy", "cr": 1, "type": "humanoid"},
                {"name": "Guard", "cr": 0.125, "type": "humanoid"},
                {"name": "Noble", "cr": 0.25, "type": "humanoid"},
                {"name": "Cult Fanatic", "cr": 2, "type": "humanoid"},
                {"name": "Priest", "cr": 2, "type": "humanoid"},
                {"name": "Wererat", "cr": 2, "type": "humanoid"},
                {"name": "Doppelganger", "cr": 3, "type": "monstrosity"},
                {"name": "Veteran", "cr": 3, "type": "humanoid"}
            ],
            "swamp": [
                {"name": "Crocodile", "cr": 0.5, "type": "beast"},
                {"name": "Giant Frog", "cr": 0.25, "type": "beast"},
                {"name": "Lizardfolk", "cr": 0.5, "type": "humanoid"},
                {"name": "Bullywug", "cr": 0.25, "type": "humanoid"},
                {"name": "Stirge", "cr": 0.125, "type": "beast"},
                {"name": "Giant Constrictor Snake", "cr": 2, "type": "beast"},
                {"name": "Green Hag", "cr": 3, "type": "fey"},
                {"name": "Black Dragon Wyrmling", "cr": 2, "type": "dragon"},
                {"name": "Shambling Mound", "cr": 5, "type": "plant"},
                {"name": "Will-o'-Wisp", "cr": 2, "type": "undead"}
            ]
        }
        
        # Determine which monster set to use
        monster_set = None
        for loc_type, monsters in location_monsters.items():
            if loc_type.lower() in location.lower():
                monster_set = monsters
                break
                
        # Use dungeon as default if no match
        if monster_set is None:
            monster_set = location_monsters["dungeon"]
            
        # Find monsters close to the target CR
        suitable_monsters = []
        for monster in monster_set:
            # Consider monsters within ±2 CR of the target
            if abs(monster["cr"] - target_cr) <= 2:
                suitable_monsters.append(monster)
                
        # If no suitable monsters found, take the closest ones
        if not suitable_monsters:
            # Sort by proximity to target CR
            monster_set.sort(key=lambda m: abs(m["cr"] - target_cr))
            suitable_monsters = monster_set[:5]  # Take the 5 closest
            
        # Select random monsters from suitable ones
        selected_monsters = []
        for _ in range(count):
            monster = random.choice(suitable_monsters).copy()
            # Retrieve additional details for the monster
            monster_details = self.use_tool("retrieve_monster", monster["name"])
            if monster_details:
                monster.update(monster_details)
            selected_monsters.append(monster)
            
        return selected_monsters
    
    def _generate_encounter_setup(self, location: str, monsters: List[Dict[str, Any]]) -> str:
        """Generate a setup description for a combat encounter"""
        # Use different parameters for encounter descriptions
        encounter_params = self.model_params.get("functions", {}).get("description", {})
        temp = encounter_params.get("temperature", self.model_params.get("temperature", 0.7))
        max_tokens = encounter_params.get("max_tokens", self.model_params.get("max_tokens", 300))
        
        # Create a list of monster descriptions
        monster_descriptions = []
        for monster in monsters:
            name = monster["name"]
            count = monsters.count(monster)
            if count > 1:
                monster_descriptions.append(f"{count} {name}s")
            else:
                monster_descriptions.append(f"a {name}")
                
        monster_text = ", ".join(monster_descriptions)
        
        # Use reasoning for encounter setup
        setup_prompt = f"""
        You need to create a combat encounter setup in {location} featuring {monster_text}.
        
        Think about:
        1. How are the monsters positioned in the environment?
        2. What are they doing when the players arrive?
        3. What environmental features could affect the combat?
        4. What tactics might these monsters employ?
        5. How can you make this encounter memorable and dynamic?
        
        Write a brief but vivid description of the encounter setup from the game master's perspective.
        Include practical details that help visualize the scene and suggest tactical possibilities.
        """
        
        # Generate the setup
        setup = self.llm.generate(
            prompt=setup_prompt,
            system_prompt=self.system_prompt,
            temperature=temp,
            max_tokens=max_tokens
        )
        
        return setup
    
    def _generate_social_setup(self, location: str, social_type: str) -> str:
        """Generate a setup description for a social encounter"""
        # Use different parameters for social encounters
        social_params = self.model_params.get("functions", {}).get("description", {})
        temp = social_params.get("temperature", self.model_params.get("temperature", 0.75))
        max_tokens = social_params.get("max_tokens", self.model_params.get("max_tokens", 300))
        
        # Create a list of NPC descriptions
        npc_descriptions = []
        for npc in self.active_npcs:
            npc_descriptions.append(f"{npc['name']} the {npc['race']} {npc['occupation']}")
                
        npc_text = ", ".join(npc_descriptions)
        
        # Use reasoning for social encounter setup
        setup_prompt = f"""
        You need to create a {social_type} social encounter in {location} featuring {npc_text}.
        
        Think about:
        1. What is the social dynamic between these NPCs?
        2. What is happening when the players arrive?
        3. What stakes or tensions exist in this encounter?
        4. What opportunities for roleplay does this present?
        5. How can players influence the outcome?
        
        Write a brief but vivid description of the social encounter from the game master's perspective.
        Include practical details about NPC motivations and potential player approaches.
        """
        
        # Generate the setup
        setup = self.llm.generate(
            prompt=setup_prompt,
            system_prompt=self.system_prompt,
            temperature=temp,
            max_tokens=max_tokens
        )
        
        return setup
    
    def _generate_trap_setup(self, location: str, trap_type: str) -> str:
        """Generate a setup description for a trap encounter"""
        # Use different parameters for trap descriptions
        trap_params = self.model_params.get("functions", {}).get("description", {})
        temp = trap_params.get("temperature", self.model_params.get("temperature", 0.6))
        max_tokens = trap_params.get("max_tokens", self.model_params.get("max_tokens", 250))
        
        # Use reasoning for trap setup
        setup_prompt = f"""
        You need to create a {trap_type} trap encounter in {location}.
        
        Think about:
        1. How is the trap concealed or triggered?
        2. What visual or environmental clues might hint at the trap?
        3. What effect does the trap have when triggered?
        4. How might players detect or disable the trap?
        5. What makes this trap interesting or challenging?
        
        Write a brief but detailed description of the trap from the game master's perspective.
        Include both narrative elements and practical mechanics.
        """
        
        # Generate the setup
        setup = self.llm.generate(
            prompt=setup_prompt,
            system_prompt=self.system_prompt,
            temperature=temp,
            max_tokens=max_tokens
        )
        
        return setup
    
    def _generate_puzzle_setup(self, location: str, puzzle_type: str) -> str:
        """Generate a setup description for a puzzle encounter"""
        # Use different parameters for puzzle descriptions
        puzzle_params = self.model_params.get("functions", {}).get("description", {})
        temp = puzzle_params.get("temperature", self.model_params.get("temperature", 0.8))
        max_tokens = puzzle_params.get("max_tokens", self.model_params.get("max_tokens", 350))
        
        # Use reasoning for puzzle setup
        setup_prompt = f"""
        You need to create a {puzzle_type} puzzle encounter in {location}.
        
        Think about:
        1. What is the core mechanic or challenge of this puzzle?
        2. How is the puzzle presented to the players?
        3. What clues are available to help solve it?
        4. What happens when the puzzle is solved?
        5. What makes this puzzle interesting or challenging?
        
        Write a detailed description of the puzzle from the game master's perspective.
        Include both the narrative presentation and the mechanical solution.
        """
        
        # Generate the setup
        setup = self.llm.generate(
            prompt=setup_prompt,
            system_prompt=self.system_prompt,
            temperature=temp,
            max_tokens=max_tokens
        )
        
        return setup
    
    def handle_scenario(self, scenario_type: str, scenario_data: Dict[str, Any]) -> str:
        """
        Handle a specific scenario type - implementation of abstract method.
        
        Args:
            scenario_type: Type of scenario to handle
            scenario_data: Data specific to the scenario
            
        Returns:
            Result of handling the scenario
        """
        if scenario_type == "scene_description":
            return self.describe_scene(
                location=scenario_data.get("location", "generic area"),
                time_of_day=scenario_data.get("time_of_day", "day"),
                mood=scenario_data.get("mood", "neutral"),
                include_npcs=scenario_data.get("include_npcs", True)
            )
        
        elif scenario_type == "npc_interaction":
            return self.npc_interaction(
                npc_name=scenario_data.get("npc_name", ""),
                player_name=scenario_data.get("player_name", "Player"),
                player_speech=scenario_data.get("player_speech", "")
            )
        
        elif scenario_type == "player_action":
            return self.handle_player_action(
                player_name=scenario_data.get("player_name", "Player"),
                action=scenario_data.get("action", "")
            )
        
        elif scenario_type == "encounter_generation":
            encounter = self.generate_encounter(
                location=scenario_data.get("location", "generic area"),
                difficulty=scenario_data.get("difficulty", "medium"),
                encounter_type=scenario_data.get("encounter_type", "combat")
            )
            return encounter.get("setup", "An encounter is prepared.")
        
        else:
            return f"Scenario type '{scenario_type}' not implemented."