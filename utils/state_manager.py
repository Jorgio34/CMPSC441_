"""
State Manager

Handles persistence of game state in the D&D AI Assistant.
Uses JSON files to store and retrieve game state.
"""

import os
import json
import time
from typing import Dict, Any, Optional, List


class StateManager:
    """Manages game state persistence"""
    
    def __init__(self, save_dir: str = "saves"):
        """Initialize state manager with save directory"""
        self.save_dir = save_dir
        
        # Create save directory if it doesn't exist
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    
    def save_game_state(self, state: Dict[str, Any], save_name: Optional[str] = None) -> str:
        """
        Save game state to file
        
        Args:
            state: Game state dictionary
            save_name: Optional name for save file
            
        Returns:
            Path to saved file
        """
        # Generate save name if not provided
        if not save_name:
            timestamp = int(time.time())
            save_name = f"save_{timestamp}"
        
        # Add .json extension if not present
        if not save_name.endswith('.json'):
            save_name += '.json'
            
        # Create full path
        save_path = os.path.join(self.save_dir, save_name)
        
        # Add timestamp to state
        state['_save_timestamp'] = int(time.time())
        
        # Save state to file
        with open(save_path, 'w') as f:
            json.dump(state, f, indent=2)
            
        return save_path
    
    def load_game_state(self, save_name: str) -> Dict[str, Any]:
        """
        Load game state from file
        
        Args:
            save_name: Save file name
            
        Returns:
            Game state dictionary
        """
        # Add .json extension if not present
        if not save_name.endswith('.json'):
            save_name += '.json'
            
        # Create full path
        save_path = os.path.join(self.save_dir, save_name)
        
        # Load state from file
        try:
            with open(save_path, 'r') as f:
                state = json.load(f)
            return state
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to load save file: {e}")
    
    def list_saved_games(self) -> List[Dict[str, Any]]:
        """
        List all saved games
        
        Returns:
            List of save file info dictionaries
        """
        saves = []
        
        for filename in os.listdir(self.save_dir):
            if filename.endswith('.json'):
                path = os.path.join(self.save_dir, filename)
                try:
                    # Get basic file info
                    stats = os.stat(path)
                    
                    # Try to load state to get name and timestamp
                    with open(path, 'r') as f:
                        state = json.load(f)
                        
                    # Create save info
                    save_info = {
                        'filename': filename,
                        'path': path,
                        'size': stats.st_size,
                        'modified': stats.st_mtime,
                        'name': state.get('campaign_name', 'Unnamed Campaign'),
                        'timestamp': state.get('_save_timestamp', 0),
                        'party_level': state.get('party_level', 1)
                    }
                    
                    saves.append(save_info)
                except:
                    # Skip this file if there's an error
                    continue
                    
        # Sort by timestamp (newest first)
        saves.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return saves
    
    def delete_saved_game(self, save_name: str) -> bool:
        """
        Delete a saved game
        
        Args:
            save_name: Save file name
            
        Returns:
            True if deleted successfully
        """
        # Add .json extension if not present
        if not save_name.endswith('.json'):
            save_name += '.json'
            
        # Create full path
        save_path = os.path.join(self.save_dir, save_name)
        
        # Delete file
        try:
            os.remove(save_path)
            return True
        except FileNotFoundError:
            return False