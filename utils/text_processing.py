"""
Text Processing Utility

This module provides text processing functions used throughout the system.
It includes entity extraction, intent recognition, and text formatting.
"""

import re
from typing import Dict, List, Any, Set, Optional, Tuple


def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract entities from text such as names, places, items, etc.
    
    Args:
        text: Input text to process
        
    Returns:
        Dictionary of entity types and their values
    """
    entities = {
        "names": [],
        "places": [],
        "items": [],
        "actions": [],
        "targets": []
    }
    
    # Extract names (capitalized words that aren't at the start of sentences)
    name_pattern = r'(?<!^)(?<![\.\?!]\s)([A-Z][a-z]+)'
    entities["names"] = re.findall(name_pattern, text)
    
    # Extract places (common place words)
    place_words = ["castle", "town", "village", "city", "forest", "mountain", 
                  "dungeon", "cave", "temple", "tavern", "inn", "shop", "store"]
    for word in place_words:
        if word in text.lower():
            # Try to get the full place name (e.g., "dark forest" instead of just "forest")
            place_pattern = r'(\w+\s+' + word + r'|\w+\s+\w+\s+' + word + r'|' + word + r')'
            matches = re.findall(place_pattern, text.lower())
            entities["places"].extend(matches)
    
    # Extract items (nouns that appear after "the", "a", "an", "my", "your", "his", "her")
    item_pattern = r'(the|a|an|my|your|his|her)\s+(\w+)'
    matches = re.findall(item_pattern, text.lower())
    entities["items"] = [match[1] for match in matches]
    
    # Extract actions (verbs)
    action_words = ["attack", "cast", "drink", "use", "open", "close", "break", "pick", 
                   "talk", "speak", "ask", "tell", "look", "search", "check", "investigate",
                   "move", "go", "run", "walk", "climb", "jump", "hide", "steal", "buy", "sell"]
    for word in action_words:
        if word in text.lower():
            # Get the action with potential object
            action_pattern = r'(' + word + r'\s+(?:the|a|an|my|your|his|her)?\s*\w+)'
            matches = re.findall(action_pattern, text.lower())
            entities["actions"].extend(matches)
    
    # Extract targets (words following prepositions like "at", "to", "on")
    target_pattern = r'(at|to|on|with)\s+(the\s+\w+|\w+)'
    matches = re.findall(target_pattern, text.lower())
    entities["targets"] = [match[1] for match in matches]
    
    # Remove duplicates and clean up
    for entity_type in entities:
        entities[entity_type] = list(set(entities[entity_type]))
    
    return entities


def get_text_sentiment(text: str) -> str:
    """
    Analyze the sentiment of a text (positive, negative, neutral).
    
    Args:
        text: Input text to analyze
        
    Returns:
        Sentiment category
    """
    # Simple keyword-based sentiment analysis
    positive_words = ["good", "great", "excellent", "wonderful", "happy", "pleased", 
                     "like", "love", "enjoy", "beautiful", "friend", "help", "thank",
                     "appreciate", "yes", "please"]
    
    negative_words = ["bad", "terrible", "awful", "horrible", "sad", "angry", "upset",
                     "hate", "dislike", "ugly", "enemy", "hurt", "annoyed", "no", "never"]
    
    # Count positive and negative words
    positive_count = sum(1 for word in positive_words if word in text.lower())
    negative_count = sum(1 for word in negative_words if word in text.lower())
    
    # Determine sentiment
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"


def identify_intent(text: str) -> Tuple[str, float]:
    """
    Identify the user's intent from text.
    
    Args:
        text: User input text
        
    Returns:
        Tuple of (intent_type, confidence)
    """
    # Intent categories with associated keywords
    intent_keywords = {
        "attack": ["attack", "fight", "kill", "hit", "strike", "slash", "stab", "shoot"],
        "explore": ["explore", "search", "look", "examine", "investigate", "check", "find"],
        "interact": ["talk", "speak", "ask", "tell", "persuade", "intimidate", "deceive", "bribe"],
        "move": ["go", "move", "walk", "run", "climb", "jump", "enter", "leave", "travel"],
        "use_item": ["use", "drink", "eat", "read", "open", "activate", "apply", "equip", "wear"],
        "cast_spell": ["cast", "spell", "magic", "ritual", "incantation"],
        "help": ["help", "explain", "what", "how", "who", "where", "when", "why"]
    }
    
    # Count matches for each intent
    intent_matches = {}
    for intent, keywords in intent_keywords.items():
        matches = sum(1 for keyword in keywords if keyword in text.lower())
        intent_matches[intent] = matches
    
    # Find the intent with the most matches
    best_intent = max(intent_matches.items(), key=lambda x: x[1])
    intent_type = best_intent[0]
    match_count = best_intent[1]
    
    # Calculate confidence (0-1)
    confidence = match_count / max(len(text.split()), 1) if match_count > 0 else 0
    
    # If no matches or very low confidence, use "unknown" intent
    if match_count == 0 or confidence < 0.1:
        return "unknown", 0.0
    
    return intent_type, min(1.0, confidence)


def format_list_for_display(items: List[str], style: str = "bullet") -> str:
    """
    Format a list of items for display with the specified style.
    
    Args:
        items: List of items to format
        style: Formatting style ("bullet", "numbered", "comma", "inline")
        
    Returns:
        Formatted string
    """
    if not items:
        return ""
    
    if style == "bullet":
        return "\n".join([f"• {item}" for item in items])
    elif style == "numbered":
        return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
    elif style == "comma":
        return ", ".join(items)
    elif style == "inline":
        if len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return f"{items[0]} and {items[1]}"
        else:
            return ", ".join(items[:-1]) + f", and {items[-1]}"
    else:
        return "\n".join(items)


def summarize_text(text: str, max_length: int = 200) -> str:
    """
    Create a shorter summary of a longer text.
    
    Args:
        text: Text to summarize
        max_length: Maximum length of the summary
        
    Returns:
        Summarized text
    """
    # If text is already short enough, return it
    if len(text) <= max_length:
        return text
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Very simple summarization: keep first few sentences
    summary = ""
    for sentence in sentences:
        if len(summary) + len(sentence) + 1 <= max_length:
            summary += " " + sentence if summary else sentence
        else:
            break
    
    return summary


def format_description(name: str, description: str, details: Optional[Dict[str, Any]] = None) -> str:
    """
    Format a description with name and optional details.
    
    Args:
        name: Name of the item/person/place
        description: Main description text
        details: Optional dictionary of additional details
        
    Returns:
        Formatted description
    """
    # Start with name as header and description
    formatted = f"**{name}**\n\n{description}"
    
    # Add details if provided
    if details:
        formatted += "\n\n"
        for key, value in details.items():
            # Format based on value type
            if isinstance(value, list):
                formatted += f"**{key.title()}**: {format_list_for_display(value, 'inline')}\n"
            else:
                formatted += f"**{key.title()}**: {value}\n"
    
    return formatted