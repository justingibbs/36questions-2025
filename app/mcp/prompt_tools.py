from pathlib import Path
import json
from typing import Dict, List, Optional

from pydantic_ai import Tool

class PromptTools:
    def __init__(self):
        self.prompts_path = Path("data/prompts.json")

    @Tool
    async def get_system_prompt(self) -> Dict:
        """Get the system-level prompts for agent personality"""
        with open(self.prompts_path) as f:
            prompts = json.load(f)
            return prompts["system"]

    @Tool
    async def get_conversation_prompt(self, prompt_type: str) -> str:
        """Get a specific conversation prompt"""
        with open(self.prompts_path) as f:
            prompts = json.load(f)
            if prompt_type in prompts["conversation"]:
                return prompts["conversation"][prompt_type]
            
            # Handle arrays of prompts (like encouragement)
            if isinstance(prompts["conversation"][prompt_type], list):
                import random
                return random.choice(prompts["conversation"][prompt_type])
            
            raise ValueError(f"Unknown prompt type: {prompt_type}")

    @Tool
    async def format_question_prompt(self, question: Dict) -> str:
        """Format a question with its guidance for presentation"""
        with open(self.prompts_path) as f:
            prompts = json.load(f)
            
        return (f"{prompts['conversation']['question_intro']}\n\n"
                f"{question['question']}\n\n"
                f"{prompts['conversation']['guidance_intro']}\n"
                f"{question['guidance']}")