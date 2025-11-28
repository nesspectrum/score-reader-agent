"""
Validation Agent - Sub-agent for validating and improving music data extraction
Can be used as a sub-agent or standalone tool
"""

import os
from typing import Optional, Dict, Any
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from tools.agent_tools import (
    validate_music_data,
    get_music_statistics,
    suggest_corrections
)


class ValidationAgent(Agent):
    """
    A specialized agent for validating and improving extracted music data.
    Can be used as a sub-agent of ExtractionAgent.
    """
    
    def __init__(
        self,
        project_id=None,
        location="us-central1",
        library_agent=None
    ):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        model_name = os.getenv("GOOGLE_CLOUD_MODEL", "gemini-2.5-flash-lite")
        self.library_agent = library_agent
        
        instruction = """You are a music data validation expert. Your task is to:
        1. Validate extracted music data structure and format
        2. Identify missing or incorrect fields
        3. Suggest improvements based on music theory and common patterns
        4. Calculate statistics about the music data
        
        Use the available tools to validate and analyze music data."""
        
        # Create wrapper for suggest_corrections with library_agent
        def suggest_corrections_wrapper(music_data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
            preferences = None
            if self.library_agent and user_id:
                preferences = self.library_agent.get_user_preferences(user_id)
            return suggest_corrections(music_data, preferences)
        
        tools = [
            FunctionTool(func=validate_music_data),
            FunctionTool(func=get_music_statistics),
            FunctionTool(func=suggest_corrections_wrapper),
        ]
        
        # Initialize parent Agent (Pydantic model)
        super().__init__(
            name="MusicDataValidator",
            model=model_name,
            instruction=instruction,
            tools=tools
        )
        
        # Store additional attributes using object.__setattr__
        object.__setattr__(self, 'project_id', project_id)
        object.__setattr__(self, 'location', location)
        object.__setattr__(self, 'library_agent', library_agent)
    
    async def validate(self, music_data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate music data and return validation results.
        
        Args:
            music_data: Extracted music data to validate
            user_id: Optional user ID for preference-based suggestions
            
        Returns:
            Dictionary with validation results and suggestions
        """
        # Use tools to validate
        validation_result = validate_music_data(music_data)
        stats_result = get_music_statistics(music_data)
        
        # Get suggestions
        preferences = None
        if self.library_agent and user_id:
            preferences = self.library_agent.get_user_preferences(user_id)
        suggestions_result = suggest_corrections(music_data, preferences)
        
        return {
            "validation": validation_result,
            "statistics": stats_result.get("statistics", {}),
            "suggestions": suggestions_result.get("suggestions", {}),
            "is_valid": validation_result.get("valid", False)
        }

