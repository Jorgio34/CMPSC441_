"""
Adventure Generation Prompts

This module contains the prompts used by the AdventureAgent for generating
quest content, locations, NPCs, and other adventure elements.
"""

# Quest generation prompt
QUEST_PROMPT = """
Generate a detailed D&D quest with the following specifications:
- Quest Type: {quest_type}
- Difficulty: {difficulty}
- Location: {location}

The quest should include:
1. A compelling title
2. A brief background/hook
3. Clear objectives
4. 2-3 interesting challenges or obstacles
5. Appropriate rewards for the party level
6. At least one interesting NPC involved in the quest

Make the quest feel authentic to the D&D world and setting, with appropriate
fantasy elements and themes. Incorporate any provided world context
or player history where relevant.
"""

# Location generation prompt
LOCATION_PROMPT = """
Create a detailed D&D location with the following specifications:
- Location Type: {location_type}
- Setting: {setting}
- Purpose: {purpose}

The location description should include:
1. Physical appearance and layout
2. Atmosphere and sensory details
3. Notable features or points of interest
4. Any inhabitants or regular visitors
5. History or lore associated with the location
6. At least one secret or hidden element

Make the location feel authentic to the D&D world, with appropriate
fantasy elements and themes that fit the specified setting.
"""

# NPC generation prompt
NPC_PROMPT = """
Create a detailed D&D NPC with the following specifications:
- Role: {role}
- Race: {race}
- Alignment: {alignment}

The NPC description should include:
1. Name and basic physical description
2. Personality traits and mannerisms
3. Motivations and goals
4. Special abilities or skills
5. Connections to other NPCs or organizations
6. A secret or hidden aspect

Make the NPC feel authentic to the D&D world, with appropriate
fantasy elements and characteristics that make them memorable and interesting.
"""

# Reward generation prompt
REWARD_PROMPT = """
Generate appropriate rewards for a D&D party completing a {difficulty} quest.
Party Level: {level}
Quest Type: {quest_type}

The rewards should include:
1. Appropriate gold amount
2. Possible magical items (if any)
3. Other valuables (gems, art objects, etc.)
4. Potential non-material rewards (favors, information, reputation)

Balance the rewards to be satisfying but not overpowered for the party level.
Consider the difficulty and nature of the quest when determining rewards.
"""

# Adventure hook prompt
HOOK_PROMPT = """
Create an engaging adventure hook for a D&D party with the following specifications:
- Party Level: {level}
- Theme: {theme}
- Location: {location}

The hook should:
1. Provide a compelling reason for the party to engage
2. Hint at potential rewards or consequences
3. Introduce an interesting NPC or situation
4. Contain an element of mystery or intrigue

Make the hook concise but evocative, with enough detail to spark interest
but leaving room for development during play.
"""

# Combat encounter prompt
COMBAT_PROMPT = """
Design a balanced combat encounter for a D&D party with the following specifications:
- Party Level: {level}
- Party Size: {party_size}
- Environment: {environment}
- Difficulty: {difficulty}

The encounter should include:
1. Appropriate enemy types and numbers
2. Tactical positioning and terrain features
3. Potential special conditions or complications
4. At least one interesting combat mechanic or twist
5. Options for both combat and non-combat resolution where appropriate

Balance the encounter to provide a suitable challenge without being overwhelming.
Consider the party composition and environment in your design.
"""

# Puzzle prompt
PUZZLE_PROMPT = """
Create an engaging D&D puzzle with the following specifications:
- Difficulty: {difficulty}
- Theme: {theme}
- Environment: {environment}

The puzzle should include:
1. Clear description of what the players encounter
2. The mechanism of the puzzle
3. Clues that players might discover
4. The solution or possible solutions
5. Consequences for success or failure
6. Any narrative integration with the adventure

Make the puzzle interesting and fair, with multiple ways for players to engage with it.
Avoid puzzles that rely entirely on a single skill check or that punish failure too severely.
"""

# Treasure prompt
TREASURE_PROMPT = """
Generate appropriate treasure for a D&D party of level {level} in a {difficulty} 
adventure with a {theme} theme.

The treasure should include:
1. Coin amount and distribution (copper, silver, gold, platinum if applicable)
2. Appropriate magical items for the party level (if any)
3. Valuable goods (gems, art objects, trade goods)
4. Any unique or thematic items related to the adventure
5. Appropriate distribution between immediate and potential future rewards

Consider the setting, opposition faced, and adventure theme when determining treasure.
Balance the rewards to enhance gameplay without disrupting game balance.
"""

# Dungeon generation prompt
DUNGEON_PROMPT = """
Design a detailed D&D dungeon with the following specifications:
- Dungeon Type: {dungeon_type}
- Size: {size}
- Theme: {theme}
- Difficulty: {difficulty}

The dungeon design should include:
1. Overall layout and structure
2. Purpose and history
3. Key areas and features
4. Inhabitants and their motivations
5. Traps and hazards
6. Treasures and rewards
7. At least one unique or memorable element

Create a cohesive dungeon that feels like a real place with internal logic.
Consider how different inhabitants might interact with each other and with the environment.
"""

# Trap generation prompt
TRAP_PROMPT = """
Design a D&D trap with the following specifications:
- Trap Type: {trap_type}
- Difficulty: {difficulty}
- Environment: {environment}

The trap description should include:
1. Trigger mechanism
2. Effect when triggered
3. Detection methods
4. Disarming methods
5. Damage or consequences
6. Any special components or magical elements

Make the trap reasonable to detect and disarm with appropriate skills,
but dangerous enough to be a meaningful challenge. Consider the 
environment and context when designing the trap's appearance and mechanism.
"""

# Social encounter prompt
SOCIAL_PROMPT = """
Create a detailed D&D social encounter with the following specifications:
- Encounter Type: {encounter_type}
- Setting: {setting}
- Stakes: {stakes}

The social encounter should include:
1. Key NPCs and their motivations
2. Initial situation and tension
3. Possible approaches for the players
4. Consequences for success or failure
5. Potential complications or twists
6. Integration with the larger adventure

Design the encounter to allow for multiple approaches (intimidation, persuasion, 
deception, etc.) and to reward creative player engagement. Consider how different 
character types might contribute to the resolution.
"""