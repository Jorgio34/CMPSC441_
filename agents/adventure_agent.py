"""
Adventure Generator Agent - Creates quests, NPCs, locations, and plot hooks
"""

import random
from typing import Dict, List, Any, Optional
import logging

from agents.base_agent import BaseAgent, LLMInterface
from knowledge.retrieval import retrieve_lore, retrieve_monster, retrieve_item, search_knowledge_base, add_knowledge_entry
from config.prompts.adventure_gen import QUEST_PROMPT, LOCATION_PROMPT, NPC_PROMPT, REWARD_PROMPT, HOOK_PROMPT # type: ignore
from config.prompts.system_prompts import ADVENTURE_GENERATOR_PROMPT


class AdventureAgent(BaseAgent):
    """Adventure Generator agent that creates quests, locations, NPCs, and plot hooks"""
    
    def __init__(self, model_name: str = "gpt-4", model_params: Optional[Dict[str, Any]] = None, 
                knowledge_base: Optional[Any] = None):
        # Initialize base agent
        super().__init__(
            name="AdventureGenerator",
            system_prompt=ADVENTURE_GENERATOR_PROMPT,
            llm=LLMInterface(model_name=model_name),
            tools={"retrieve_lore": retrieve_lore, "retrieve_monster": retrieve_monster, 
                   "retrieve_item": retrieve_item, "search_knowledge_base": search_knowledge_base, 
                   "add_knowledge_entry": add_knowledge_entry},
            model_params=model_params or {}
        )
        self.knowledge_base = knowledge_base
        self.logger = logging.getLogger("AdventureGenerator")
        
    def generate_quest(self, region: str = "Sword Coast", party_level: int = 1,
                      theme: Optional[str] = None, length: str = "medium",
                      hook_type: str = "tavern") -> Dict[str, Any]:
        """Generate a complete quest with NPCs, locations, and plot hooks"""
        # Get lore and theme
        region_lore = self.use_tool("retrieve_lore", region)
        theme = theme or random.choice(["undead", "bandits", "cult", "beasts", "fey", "elemental", 
                                      "intrigue", "mystery", "rescue", "heist", "exploration"])
        
        # Generate quest outline
        quest_outline = self._generate_with_params(
            "outline", QUEST_PROMPT.format(
                region=region, region_lore=region_lore, party_level=party_level,
                theme=theme, length=length, hook_type=hook_type
            )
        )
        
        # Parse outline
        quest_data = self._parse_outline(quest_outline)
        
        # Generate locations and encounters
        num_locations = 1 if length == "short" else 3 if length == "medium" else 5
        locations = [
            self._generate_location(
                region, theme, 
                "starting point" if i == 0 else 
                "final confrontation" if i == num_locations - 1 else
                random.choice(["challenge", "puzzle", "social encounter", "combat", "discovery"]),
                party_level
            )
            for i in range(num_locations)
        ]
        
        # Generate NPCs
        num_npcs = 2 if length == "short" else 4 if length == "medium" else 6
        npcs = self._generate_npcs(region, theme, party_level, num_npcs)
        
        # Generate rewards and hook
        rewards = self._generate_rewards(party_level, theme, length)
        hook = self._generate_hook(hook_type, quest_data["title"], quest_data["summary"], 
                                 npcs[0] if npcs else None)
        
        # Assemble quest
        quest = {
            **quest_data,
            "theme": theme,
            "level": party_level,
            "length": length,
            "hook": hook,
            "locations": locations,
            "npcs": npcs,
            "rewards": rewards
        }
        
        # Add to memory and knowledge base
        self.add_memory(f"Generated quest '{quest['title']}' with theme {theme} for level {party_level} party.")
        self.use_tool("add_knowledge_entry", "lore", f"Quest: {quest['title']}", 
                    f"A {length} adventure for level {party_level} characters set in {region}. {quest['summary']}")
        
        return quest
    
    def _generate_with_params(self, func_name: str, prompt: str) -> str:
        """Helper for generating content with the right parameters"""
        funcs = self.model_params.get("functions", {})
        params = funcs.get(func_name, {})
        temp = params.get("temperature", self.model_params.get("temperature", 0.7))
        max_tokens = params.get("max_tokens", self.model_params.get("max_tokens", 350))
        
        return self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=temp,
            max_tokens=max_tokens
        )
    
    def _parse_outline(self, outline: str) -> Dict[str, Any]:
        """Parse quest outline text into structured data"""
        parts = outline.split("\n\n")
        data = {"title": "", "summary": "", "objectives": []}
        
        for part in parts:
            if part.lower().startswith("title:"):
                data["title"] = part.split(":", 1)[1].strip()
            elif part.lower().startswith("summary:"):
                data["summary"] = part.split(":", 1)[1].strip()
            elif "objective" in part.lower() or "goal" in part.lower():
                data["objectives"] = [
                    obj.split(":", 1)[1].strip() for obj in part.split("\n")
                    if ":" in obj and not obj.lower().startswith("objectives")
                ]
        
        return data
    
    def _generate_location(self, region: str, theme: str, purpose: str, party_level: int) -> Dict[str, Any]:
        """Generate a detailed location for the quest"""
        # Get location type and lore
        region_locations = self.use_tool("search_knowledge_base", region, "lore")
        location_types = self._determine_location_types(theme, purpose)
        location_type = random.choice(location_types)
        location_lore = self.use_tool("retrieve_lore", location_type)
        
        # Generate location description
        description = self._generate_with_params(
            "locations", LOCATION_PROMPT.format(
                region=region, theme=theme, purpose=purpose, location_type=location_type,
                party_level=party_level, 
                region_locations="" if not region_locations else region_locations[0].get("content", ""),
                location_lore=location_lore
            )
        )
        
        # Parse the description
        location_data = self._parse_location(description)
        
        # Generate encounters
        encounters = self._generate_encounters(
            location_type, theme, party_level, 
            1 if purpose == "starting point" else 2
        )
        
        return {
            **location_data,
            "type": location_type,
            "purpose": purpose,
            "encounters": encounters
        }
    
    def _determine_location_types(self, theme: str, purpose: str) -> List[str]:
        """Determine location types based on theme and purpose"""
        # Define location types by theme
        theme_locations = {
            "undead": ["graveyard", "crypt", "abandoned temple", "haunted mansion", "forgotten battlefield"],
            "bandits": ["forest clearing", "mountain pass", "abandoned outpost", "hidden camp", "cave hideout"],
            "cult": ["underground temple", "abandoned tower", "secret chamber", "ritual site", "hidden shrine"],
            "beasts": ["dense forest", "monster lair", "hunting grounds", "natural cavern", "beast den"],
            "fey": ["enchanted grove", "fairy circle", "ancient tree", "mystical pond", "otherworldly glade"],
            "elemental": ["volcanic cavern", "storm-wracked peak", "frozen grotto", "underground river", "whispering canyon"],
            "intrigue": ["noble estate", "merchant guild", "royal gardens", "city streets", "council chambers"],
            "mystery": ["abandoned library", "sealed vault", "forgotten ruin", "strange monument", "ancient laboratory"],
            "rescue": ["prison cell", "monster lair", "slave camp", "fortress dungeon", "sacrificial altar"],
            "heist": ["noble vault", "merchant stronghold", "guarded archive", "wizard's tower", "temple treasury"],
            "exploration": ["ancient ruin", "lost temple", "unmapped cavern", "forgotten city", "magical anomaly"]
        }
        
        # Define location types by purpose
        purpose_locations = {
            "starting point": ["tavern", "village square", "town gate", "market", "campsite"],
            "final confrontation": ["throne room", "ritual chamber", "boss lair", "ancient altar", "command center"],
            "challenge": ["trapped hallway", "monster nest", "guard post", "dangerous terrain", "puzzle room"],
            "puzzle": ["library", "observatory", "ancient mechanism", "magical laboratory", "test chamber"],
            "social encounter": ["noble court", "marketplace", "local tavern", "festival grounds", "temple"],
            "combat": ["training grounds", "ambush site", "battle arena", "monster territory", "defensive position"],
            "discovery": ["hidden chamber", "vault", "ancient library", "forgotten shrine", "secret passage"]
        }
        
        # Combine and return
        t_locs = theme_locations.get(theme, ["dungeon", "forest", "cave"])
        p_locs = purpose_locations.get(purpose, ["chamber", "clearing", "room"])
        return t_locs + [p for p in p_locs if p not in t_locs]
    
    def _parse_location(self, description: str) -> Dict[str, Any]:
        """Parse location description into structured data"""
        parts = description.split("\n\n")
        data = {"name": "", "description": "", "features": []}
        
        for part in parts:
            if part.lower().startswith("name:"):
                data["name"] = part.split(":", 1)[1].strip()
            elif part.lower().startswith("description:"):
                data["description"] = part.split(":", 1)[1].strip()
            elif "feature" in part.lower() or "point of interest" in part.lower():
                data["features"] = [
                    f.split(":", 1)[1].strip() for f in part.split("\n")
                    if ":" in f and not f.lower().startswith("features")
                ]
        
        return data
    
    def _generate_encounters(self, location_type: str, theme: str, party_level: int, num_encounters: int) -> List[Dict[str, Any]]:
        """Generate encounters for a location"""
        # Define encounter types and weights
        types = ["combat", "social", "trap", "puzzle", "discovery"]
        weights = {"combat": 0.3, "social": 0.2, "trap": 0.15, "puzzle": 0.15, "discovery": 0.2}
        
        # Adjust weights based on location
        if "temple" in location_type or "tomb" in location_type:
            weights.update({"trap": weights["trap"] + 0.1, "puzzle": weights["puzzle"] + 0.1, 
                          "combat": weights["combat"] - 0.1, "social": weights["social"] - 0.1})
        elif "town" in location_type or "village" in location_type:
            weights.update({"social": weights["social"] + 0.2, "combat": weights["combat"] - 0.2})
        elif "forest" in location_type or "mountain" in location_type:
            weights.update({"discovery": weights["discovery"] + 0.1, "social": weights["social"] - 0.1})
        
        # Generate encounters
        encounters = []
        for _ in range(num_encounters):
            e_type = random.choices(types, weights=[weights[t] for t in types], k=1)[0]
            generator = getattr(self, f"_generate_{e_type}_encounter")
            encounters.append(generator(location_type, theme, party_level))
        
        return encounters
    
    def _generate_combat_encounter(self, location_type: str, theme: str, party_level: int) -> Dict[str, Any]:
        """Generate a combat encounter"""
        # Define monster types by theme
        monster_types = {
            "undead": ["skeleton", "zombie", "ghoul", "ghost", "wight"],
            "bandits": ["bandit", "thug", "scout", "archer", "captain"],
            "cult": ["cultist", "cult fanatic", "dark priest", "summoned demon", "corrupted warrior"],
            "beasts": ["wolf", "bear", "giant spider", "giant snake", "owlbear"],
            "fey": ["sprite", "satyr", "dryad", "harpy", "pixie"]
        }.get(theme, ["goblin", "orc", "kobold", "brigand", "mercenary"])
        
        # Adjust for party level
        if party_level >= 5:
            monster_types = [f"elite {m}" for m in monster_types]
        if party_level >= 10:
            monster_types = [f"veteran {m}" for m in monster_types]
        
        # Choose monster and determine count
        monster_type = random.choice(monster_types)
        num_monsters = random.randint(max(1, party_level-2), max(3, party_level+1))
        
        return {
            "type": "combat",
            "monsters": {"type": monster_type, "count": num_monsters},
            "setup": f"The party encounters {num_monsters} {monster_type}s in the {location_type}.",
            "tactics": f"The {monster_type}s will attempt to use the terrain to their advantage.",
            "difficulty": "medium"
        }
    
    def _generate_social_encounter(self, location_type: str, theme: str) -> Dict[str, Any]:
        """Generate a social encounter"""
        social_type = random.choice(["negotiation", "information", "deception", "assistance", "confrontation"])
        
        # Define NPC roles by social type
        npc_roles = {
            "negotiation": ["merchant", "noble", "criminal", "ambassador", "rival"],
            "information": ["sage", "scout", "informant", "witness", "scholar"],
            "deception": ["spy", "trickster", "double agent", "illusionist", "charlatan"],
            "assistance": ["healer", "guide", "craftsman", "refugee", "ally"],
            "confrontation": ["guard", "rival", "accuser", "official", "challenger"]
        }
        
        npc_role = random.choice(npc_roles.get(social_type, ["traveler"]))
        disposition = random.choice(["friendly", "neutral", "suspicious", "hostile"])
        
        return {
            "type": "social",
            "subtype": social_type,
            "npc": {"role": npc_role, "disposition": disposition},
            "goal": f"The {npc_role} wants to {social_type} with the party regarding {theme}.",
            "approach": f"The NPC will approach the situation with a {disposition} attitude."
        }
    
    def _generate_trap_encounter(self, location_type: str, theme: str, party_level: int) -> Dict[str, Any]:
        """Generate a trap encounter"""
        trap_type = random.choice([
            "pit trap", "poison dart", "rolling boulder", "flame jet", "collapsing ceiling",
            "magical rune", "animated object", "teleportation pad", "alarm trigger", "mind control"
        ])
        
        # Scale difficulty with party level
        dc_base = 10 + (party_level // 2)
        damage = f"{min(10, party_level*2)}d6" if party_level > 2 else "2d6"
        
        return {
            "type": "trap",
            "subtype": trap_type,
            "detect_dc": dc_base,
            "disarm_dc": dc_base + 2,
            "damage": damage,
            "description": f"A {trap_type} hidden in the {location_type}, triggered by {random.choice(['pressure plate', 'tripwire', 'magical sensor', 'timer', 'proximity'])}.",
            "effect": f"When triggered, the trap will deal {damage} damage and potentially cause {random.choice(['knockback', 'prone condition', 'restrained condition', 'poisoned condition', 'alert nearby enemies'])}."
        }
    
    def _generate_puzzle_encounter(self, location_type: str, theme: str) -> Dict[str, Any]:
        """Generate a puzzle encounter"""
        puzzle_type = random.choice([
            "riddle", "pattern matching", "symbol sequence", "weight distribution",
            "light and shadow", "water flow", "magical resonance", "statue arrangement",
            "key and lock", "musical sequence"
        ])
        
        return {
            "type": "puzzle",
            "subtype": puzzle_type,
            "description": f"A {puzzle_type} puzzle integrated into the {location_type}, themed around {theme}.",
            "solve_method": random.choice(["Intelligence check", "skill challenge", "combining items", "finding clues",
                                          "trial and error", "replicating pattern", "manipulating environment"]),
            "clues": [f"Clue hidden in {random.choice(['nearby wall carving', 'ancient text', 'pattern on the floor', 'mysterious symbols'])}"],
            "reward": f"When solved, the puzzle {random.choice(['reveals a secret passage', 'provides a valuable item', 'deactivates traps', 'strengthens the party temporarily', 'reveals crucial information'])}"
        }
    
    def _generate_discovery_encounter(self, location_type: str, theme: str) -> Dict[str, Any]:
        """Generate a discovery encounter"""
        discovery_type = random.choice([
            "hidden treasure", "ancient text", "magical phenomenon", "historical artifact",
            "natural wonder", "mysterious object", "forgotten technology", "prophetic vision",
            "secret passage", "living entity"
        ])
        
        return {
            "type": "discovery",
            "subtype": discovery_type,
            "description": f"The party discovers {discovery_type} in the {location_type} related to {theme}.",
            "significance": f"This discovery {random.choice(['reveals important plot information', 'provides historical context','offers a useful resource', 'poses a moral dilemma', 'connects to party backstory'])}.",
            "interaction": f"The party can {random.choice(['examine it closely', 'take it with them', 'activate its powers','learn from its contents', 'report it to authorities'])}"
        }
    
    def _generate_npcs(self, region: str, theme: str, party_level: int, num_npcs: int) -> List[Dict[str, Any]]:
        """Generate multiple NPCs with at least one ally and one adversary"""
        npcs = []
        has_ally = has_adversary = False
        
        for i in range(num_npcs):
            # Determine role
            if not has_ally and i == 0:
                role = "ally"
                has_ally = True
            elif not has_adversary and i == 1:
                role = "adversary"
                has_adversary = True
            else:
                role = random.choice(["ally", "adversary", "neutral", "contact", "victim", "bystander"])
                has_ally = has_ally or role == "ally"
                has_adversary = has_adversary or role == "adversary"
            
            # Generate NPC
            npc = self._generate_npc(region, theme, role, party_level)
            npcs.append(npc)
        
        return npcs
    
    def _generate_npc(self, region: str, theme: str, role: str, party_level: int) -> Dict[str, Any]:
        """Generate a detailed NPC"""
        # Get NPC type and regional info
        npc_types = self._determine_npc_types(theme, role)
        npc_type = random.choice(npc_types)
        regional_npcs = self.use_tool("search_knowledge_base", region + " notable personalities", "lore")
        
        # Generate NPC description
        description = self._generate_with_params(
            "npcs", NPC_PROMPT.format(
                region=region, theme=theme, role=role, npc_type=npc_type,
                party_level=party_level,
                regional_npcs="" if not regional_npcs else regional_npcs[0].get("content", "")
            )
        )
        
        # Parse and return NPC data
        return self._parse_npc(description, npc_type, role)
    
    def _determine_npc_types(self, theme: str, role: str) -> List[str]:
        """Determine NPC types based on theme and role"""
        # Define NPC types by theme
        theme_npcs = {
            "undead": ["necromancer", "grave digger", "ghost hunter", "cursed noble", "undead slayer"],
            "bandits": ["outlaw leader", "corrupt guard", "fence", "reformed thief", "bandit hunter"],
            "cult": ["cult leader", "acolyte", "cult escapee", "investigator", "demon hunter"],
            "beasts": ["beast tamer", "hunter", "druid", "ranger", "beast researcher"],
            "fey": ["fey touched", "fairy bargainer", "forest guardian", "changeling", "planar scholar"],
            "elemental": ["elementalist", "plane walker", "elemental binder", "mining foreman", "weather prophet"],
            "intrigue": ["noble", "spy", "diplomat", "blackmailer", "information broker"],
            "mystery": ["detective", "scholar", "witness", "sage", "conspiracy theorist"],
            "rescue": ["captive", "jailer", "rescue specialist", "kidnapper", "hostage negotiator"],
            "heist": ["security expert", "wealthy target", "fence", "insider", "rival thief"],
            "exploration": ["cartographer", "guide", "archaeologist", "treasure hunter", "lost expedition survivor"]
        }
        
        # Define NPC types by role
        role_npcs = {
            "ally": ["loyal friend", "guide", "mentor", "informant", "bodyguard"],
            "adversary": ["villain", "rival", "monster", "corrupt official", "enemy agent"],
            "neutral": ["merchant", "innkeeper", "farmer", "craftsman", "traveler"],
            "contact": ["messenger", "scout", "local expert", "fence", "old friend"],
            "victim": ["hostage", "target", "cursed individual", "possessed person", "missing person"],
            "bystander": ["witness", "local resident", "traveler", "refugee", "pilgrim"]
        }
        
        # Get types based on theme and role
        t_npcs = theme_npcs.get(theme, ["adventurer", "villager", "guard"])
        r_npcs = role_npcs.get(role, ["traveler", "villager", "merchant"])
        
        # Combine and return
        return r_npcs + [n for n in t_npcs if n not in r_npcs]
    
    def _parse_npc(self, description: str, npc_type: str, role: str) -> Dict[str, Any]:
        """Parse NPC description into structured data"""
        parts = description.split("\n\n")
        data = {
            "name": "", "description": "", "personality": [],
            "motivation": "", "secret": "", "type": npc_type, "role": role
        }
        
        for part in parts:
            if part.lower().startswith("name:"):
                data["name"] = part.split(":", 1)[1].strip()
            elif part.lower().startswith("description:"):
                data["description"] = part.split(":", 1)[1].strip()
            elif part.lower().startswith("personality:"):
                text = part.split(":", 1)[1].strip()
                data["personality"] = [t.strip() for t in text.split(",")]
            elif part.lower().startswith("motivation:"):
                data["motivation"] = part.split(":", 1)[1].strip()
            elif part.lower().startswith("secret:"):
                data["secret"] = part.split(":", 1)[1].strip()
        
        return data
    
    def _generate_rewards(self, party_level: int, theme: str, length: str) -> Dict[str, Any]:
        """Generate appropriate rewards for the quest"""
        # Calculate gold reward
        gold_multiplier = 1 if length == "short" else 2 if length == "medium" else 3
        base_gold = {
            1: 50, 2: 100, 3: 150, 4: 200, 5: 250,
            6: 500, 7: 750, 8: 1000, 9: 1250, 10: 1500,
            11: 2000, 12: 2500, 13: 3000, 14: 3500, 15: 4000,
            16: 5000, 17: 6000, 18: 7000, 19: 8000, 20: 10000
        }.get(party_level, 100 * party_level)
        
        gold_reward = base_gold * gold_multiplier
        
        # Generate item rewards
        num_items = 1 if length == "short" else 2 if length == "medium" else 3
        items_text = self._generate_with_params(
            "rewards", REWARD_PROMPT.format(
                party_level=party_level, theme=theme, num_items=num_items
            )
        )
        
        # Parse items
        items = []
        for line in items_text.split("\n"):
            if line.strip() and ":" in line:
                name, desc = line.split(":", 1)
                items.append({"name": name.strip(), "description": desc.strip()})
        
        # Calculate XP reward
        xp_multiplier = 1 if length == "short" else 2 if length == "medium" else 3
        xp_reward = {
            1: 300, 2: 600, 3: 900, 4: 1200, 5: 1800,
            6: 2100, 7: 2400, 8: 3000, 9: 3900, 10: 4500,
            11: 5100, 12: 5700, 13: 6300, 14: 6900, 15: 7500,
            16: 8100, 17: 8700, 18: 9300, 19: 9900, 20: 10500
        }.get(party_level, 300 * party_level) * xp_multiplier
        
        return {
            "gold": gold_reward,
            "xp": xp_reward,
            "items": items,
            "other": []  # For additional non-item rewards
        }
    
    def _generate_hook(self, hook_type: str, quest_title: str, quest_summary: str, 
                     key_npc: Optional[Dict[str, Any]] = None) -> str:
        """Generate a plot hook for the quest"""
        # Use a key NPC if available
        npc_name = key_npc.get("name", "a mysterious stranger") if key_npc else "a mysterious stranger"
        npc_type = key_npc.get("type", "informant") if key_npc else "informant"
        
        # Generate and return hook
        return self._generate_with_params(
            "hooks", HOOK_PROMPT.format(
                quest_title=quest_title, hook_type=hook_type, quest_summary=quest_summary,
                npc_name=npc_name, npc_type=npc_type
            )
        )
    
    def run_demo_quest_generation(self) -> None:
        """Run a demonstration of quest generation"""
        print("\n--- ADVENTURE GENERATOR DEMO ---\n")
        
        # Generate quest
        quest = self.generate_quest(region="Sword Coast", party_level=3, theme="cult", 
                                  length="medium", hook_type="tavern")
        
        # Display quest information
        print(f"QUEST: {quest['title']}")
        print(f"Summary: {quest['summary']}")
        print("\nObjectives:")
        for i, obj in enumerate(quest['objectives'], 1):
            print(f"  {i}. {obj}")
            
        print(f"\nHook ({quest['hook_type']}):")
        print(quest['hook'])
        
        print("\nLocations:")
        for i, loc in enumerate(quest['locations'], 1):
            print(f"  {i}. {loc['name']} ({loc['type']}) - {loc['purpose']}")
            print(f"     {loc['description'][:100]}...")
            
        print("\nNPCs:")
        for i, npc in enumerate(quest['npcs'], 1):
            print(f"  {i}. {npc['name']} - {npc['type']} ({npc['role']})")
            print(f"     Motivation: {npc['motivation']}")
            
        print("\nRewards:")
        print(f"  Gold: {quest['rewards']['gold']}")
        print(f"  XP: {quest['rewards']['xp']}")
        print("  Items:")
        for item in quest['rewards']['items']:
            print(f"    - {item['name']}: {item['description']}")
        
        print("\nQuest generation complete!")

    def handle_scenario(self, scenario_type: str, scenario_data: Dict[str, Any]) -> str:
        """Handle different scenario types"""
        handlers = {
            "quest_generation": lambda: self.generate_quest(
                region=scenario_data.get("region", "Sword Coast"),
                party_level=scenario_data.get("party_level", 1),
                theme=scenario_data.get("theme"),
                length=scenario_data.get("length", "medium"),
                hook_type=scenario_data.get("hook_type", "tavern")
            ),
            "npc_generation": lambda: self._generate_npc(
                region=scenario_data.get("region", "Sword Coast"),
                theme=scenario_data.get("theme", "adventure"),
                role=scenario_data.get("role", "ally"),
                party_level=scenario_data.get("party_level", 1)
            ),
            "location_generation": lambda: self._generate_location(
                region=scenario_data.get("region", "Sword Coast"),
                theme=scenario_data.get("theme", "adventure"),
                purpose=scenario_data.get("purpose", "challenge"),
                party_level=scenario_data.get("party_level", 1)
            ),
            "reward_generation": lambda: self._generate_rewards(
                party_level=scenario_data.get("party_level", 1),
                theme=scenario_data.get("theme", "adventure"),
                length=scenario_data.get("length", "medium")
            )
        }
        
        handler = handlers.get(scenario_type)
        if not handler:
            return f"Scenario type '{scenario_type}' not implemented."
            
        result = handler()
        
        # Format response based on scenario type
        if scenario_type == "quest_generation":
            return f"Generated quest: {result['title']} - {result['summary']}"
        elif scenario_type == "npc_generation":
            return f"Generated NPC: {result['name']} - {result['type']} ({result['role']})"
        elif scenario_type == "location_generation":
            return f"Generated location: {result['name']} - {result['type']} ({result['purpose']})"
        elif scenario_type == "reward_generation":
            return f"Generated rewards: {result['gold']} gold, {result['xp']} XP, and {len(result['items'])} items"
        
        return str(result)