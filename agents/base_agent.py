"""
Base Agent Architecture for D&D AI Assistant

This module defines the core agent architecture that serves as the foundation
for all specialized agents in the system.
"""

import uuid
import logging
from typing import Dict, List, Any, Optional, Callable


class LLMInterface:
    """Simplified interface for LLM interactions"""
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
        
    def generate(self, prompt: str, system_prompt: str = "", 
                temperature: Optional[float] = None, max_tokens: int = 1000) -> str:
        """Generate a response from the LLM"""
        # In a real implementation, this would call an LLM API
        # For now, we'll return a placeholder
        return f"[LLM would generate a response here with temp={temperature or self.temperature}]"


class Memory:
    """Memory system for agents with short and long-term storage"""
    
    def __init__(self, capacity: int = 20):
        self.short_term = []
        self.capacity = capacity
        self.long_term = {}
        
    def add(self, content: str, memory_type: str = "observation") -> None:
        """Add a memory entry"""
        # Create memory entry
        entry = {
            "id": str(uuid.uuid4()),
            "type": memory_type,
            "content": content,
            "timestamp": 0  # Would be actual timestamp in real implementation
        }
        
        # Add to short-term memory
        self.short_term.append(entry)
        
        # If over capacity, move oldest to long-term
        if len(self.short_term) > self.capacity:
            self.long_term[self.short_term[0]["id"]] = self.short_term.pop(0)
            
    def retrieve_relevant(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant memories based on query"""
        # In a real implementation, would use vector similarity search
        # For now, return most recent memories
        return self.short_term[-limit:] if self.short_term else []
    
    def format_context(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories for context window"""
        return "\n".join([f"[Memory: {m['type']}] {m['content']}" for m in memories])


class BaseAgent:
    """Base agent class that specialized agents inherit from"""
    
    def __init__(self, name: str, system_prompt: str, llm: Optional[LLMInterface] = None,
                tools: Optional[Dict[str, Callable]] = None, 
                model_params: Optional[Dict[str, Any]] = None,
                memory: Optional[Memory] = None):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = llm or LLMInterface()
        self.tools = tools or {}
        self.model_params = model_params or {"temperature": 0.7, "max_tokens": 1000}
        self.memory = memory or Memory()
        self.conversation_history = []
        
    def use_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """Use a tool from the agent's toolset"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not available to this agent")
        
        # Execute tool
        result = self.tools[tool_name](*args, **kwargs)
        
        # Log tool usage
        self.memory.add(
            f"Used tool '{tool_name}' with args: {args}, kwargs: {kwargs}. Result: {str(result)[:50]}...",
            memory_type="tool_usage"
        )
        
        return result
    
    def add_memory(self, content: str, memory_type: str = "observation") -> None:
        """Add a new memory entry"""
        self.memory.add(content, memory_type)
    
    def process(self, query: str) -> str:
        """Process a query and generate a response"""
        # Build context with relevant memories
        relevant_memories = self.memory.retrieve_relevant(query)
        memory_text = self.memory.format_context(relevant_memories)
        
        # Format conversation history (last 10 messages)
        history = "\n".join([
            f"{'User' if i % 2 == 0 else 'Assistant'}: {msg}"
            for i, msg in enumerate(self.conversation_history[-10:])
        ]) if self.conversation_history else ""
        
        # Construct full prompt context
        context = f"""
SYSTEM: {self.system_prompt}

CONVERSATION HISTORY:
{history}

RELEVANT MEMORIES:
{memory_text}

USER QUERY: {query}
"""
        
        # Add query to history and generate response
        self.conversation_history.append(query)
        response = self._generate_response(context)
        self.conversation_history.append(response)
        
        # Add interaction to memory
        self.add_memory(
            f"User asked: {query}\nAgent responded: {response[:100]}...",
            memory_type="interaction"
        )
        
        return response
    
    def _generate_response(self, context: str) -> str:
        """Generate response using the LLM"""
        return self.llm.generate(
            prompt=context,
            system_prompt=self.system_prompt,
            temperature=self.model_params.get("temperature"),
            max_tokens=self.model_params.get("max_tokens")
        )
    
    def handle_scenario(self, scenario_type: str, scenario_data: Dict[str, Any]) -> str:
        """Handle a specific scenario type - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement handle_scenario()")