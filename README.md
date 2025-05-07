# D&D AI Assistant

An AI-powered assistant for Dungeons & Dragons that helps with game mastering, adventure generation, combat management, and NPC interactions. This system uses advanced AI methods including prompt engineering, RAG implementation, and multi-step reasoning to create an immersive and helpful D&D companion.

## Features

- **Game Master Assistant**: Generates rich scene descriptions, manages NPCs, and handles player actions
- **Adventure Generator**: Creates complete quests with locations, NPCs, plot hooks, and rewards
- **Combat Manager**: Tracks initiative, calculates damage, and provides narrative combat descriptions
- **NPC Simulator**: Creates realistic NPCs with consistent personalities and motivations
- **Knowledge Base**: Uses RAG (Retrieval Augmented Generation) to incorporate D&D lore and rules

## Running the D&D AI Assistant

This project demonstrates AI methods for Dungeons & Dragons assistance through several scenarios.

### Setup

1. Clone the repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
   Note: The project uses a mock LLM integration that doesn't require an OpenAI API key.

### Available Commands

Run any of the following commands from the project root directory:

1. Tavern Scenario (default):
   ```
   python main.py
   ```

2. Combat Scenario:
   ```
   python main.py --scenario combat
   ```

3. Quest Generation:
   ```
   python main.py --scenario quest
   ```

4. Run with debug logging:
   ```
   python main.py --debug
   ```

### Expected Output

Each scenario demonstrates different AI methods:
- The tavern scenario shows NPC interactions and world-building
- The combat scenario demonstrates the tactical combat system
- The quest scenario shows dynamic quest generation

For detailed information about the implementation and AI methods used, see the Project.md report.

## System Architecture

The system is designed with a modular architecture:

- **Agents**: Specialized AI agents for different aspects of the game
  - `GameMasterAgent`: Handles narrative, NPCs, and environment
  - `AdventureAgent`: Generates quests and adventures
  - `CombatAgent`: Manages combat mechanics and narration
  - `NPCAgent`: Simulates realistic NPC behavior and dialogue

- **Knowledge Retrieval**: RAG implementation for accessing D&D lore and rules
  - Vector-based retrieval for monsters, items, spells, and world lore
  - Fallback to procedural generation when information is not in the database

- **Tools**: Utility functions for game mechanics
  - Dice rolling with support for standard D&D notation
  - Rule lookups for quick reference
  - Combat state tracking

- **Scenarios**: Pre-defined interactions for common D&D situations
  - Tavern encounters with NPCs
  - Combat scenarios with various enemies
  - Dungeon exploration with descriptions and encounters
  - Quest generation for campaign development

## Key AI Methods Used

### Prompt Engineering

The system uses carefully crafted prompts to guide the AI's behavior for different functions:

- **System Prompts**: Define the role and behavior of agents
- **Scenario Prompts**: Structure the generation of specific content types
- **Parameter Tuning**: Different temperature settings for creative vs. rule-based content

Example: Temperature settings are higher (0.8-0.9) for creative content like NPC dialogue and scene descriptions, but lower (0.3-0.5) for rule interpretations and combat calculations.

### RAG Implementation

Retrieval Augmented Generation is used to incorporate D&D knowledge into responses:

- **Knowledge Base**: Structured data for rules, monsters, items, spells, and lore
- **Contextual Retrieval**: Using location, theme, and other context to find relevant information
- **Fallback Generation**: Creating plausible content when exact information isn't available

Example: When generating a location description, the system retrieves relevant lore and integrates it with the location type and purpose to create a cohesive and lore-consistent environment.

### Planning & Reasoning

Multi-step reasoning is used for complex tasks:

- **Chain-of-Thought**: Breaking complex tasks into reasoning steps
- **Goal-Oriented Planning**: Creating structured adventures with coherent elements
- **Decision Making**: NPC behavior based on personality, goals, and context

Example: NPCs make decisions based on their personality traits, motivations, and past interactions with players, maintaining consistent behavior over time.

## Usage Examples

### Running a Tavern Encounter

```python
from agents.game_master import GameMasterAgent
from scenarios.tavern_encounter import create_tavern_scenario

# Initialize Game Master
game_master = GameMasterAgent()

# Create tavern scenario
tavern = create_tavern_scenario(game_master)

# Enter the tavern
tavern_description = tavern.enter_tavern()
print(tavern_description)

# Interact with an NPC
npc_response = tavern.interact_with_npc("Durnan", "What rumors have you heard lately?")
print(f"Durnan: {npc_response}")

# Make a perception check
perception_result = tavern.roll_perception_check(player_wisdom=14)
print(perception_result)
```

### Generating a Quest

```python
from agents.adventure_agent import AdventureAgent

# Initialize Adventure Generator
adventure_gen = AdventureAgent()

# Generate a quest
quest = adventure_gen.generate_quest(
    region="Sword Coast",
    party_level=5,
    theme="cult",
    length="medium",
    hook_type="tavern"
)

# Display quest information
print(f"Quest: {quest['title']}")
print(f"Summary: {quest['summary']}")
print("\nObjectives:")
for objective in quest['objectives']:
    print(f"- {objective}")
```

### Managing Combat

```python
from agents.combat_agent import CombatAgent

# Initialize Combat Manager
combat_manager = CombatAgent()

# Set up players and enemies
players = [
    {"name": "Thorin", "hp": 45, "ac": 18, "initiative_bonus": 2},
    {"name": "Elara", "hp": 30, "ac": 15, "initiative_bonus": 4}
]

enemies = [
    {"name": "Orc Warrior", "hp": 15, "ac": 13, "initiative_bonus": 1},
    {"name": "Orc Warrior", "hp": 15, "ac": 13, "initiative_bonus": 1},
    {"name": "Orc Shaman", "hp": 22, "ac": 11, "initiative_bonus": 0}
]

environment = {
    "name": "Forest Clearing",
    "description": "A small clearing in the forest with dense trees surrounding it."
}

# Initialize combat
combat_start = combat_manager.initialize_combat(players, enemies, environment)
print(combat_start)

# Process a combat turn
attack_action = {
    "actor": "Thorin",
    "type": "attack",
    "attack_name": "warhammer",
    "target": "Orc Warrior",
    "attack_bonus": 6,
    "damage_dice": "1d8",
    "damage_bonus": 4,
    "damage_type": "bludgeoning"
}

turn_result = combat_manager.process_turn(attack_action)
print(turn_result)
```

## Project Structure

```
dnd_ai_assistant/
├── agents/                    # AI agent implementations
├── config/                    # Configuration settings
│   └── prompts/               # Prompt templates
├── knowledge/                 # Knowledge retrieval system
│   └── data/                  # D&D data (rules, monsters, etc.)
├── scenarios/                 # Pre-defined scenario types
├── tools/                     # Utility tools (dice, combat tracker, etc.)
├── utils/                     # Utility functions
├── main.py                    # Main entry point
└── requirements.txt           # Project dependencies
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Wizards of the Coast for creating Dungeons & Dragons
- The Python, LangChain, and LLM communities for their excellent tools and libraries