from smolagents import Tool
import os
import litellm
import json

class SynthesizeTool(Tool):
    name = "synthesize_information"
    description = """
    Synthesize multiple pieces of information (memories, observations, goals) into a coherent analysis or plan.
    Use this to connect the dots between different data points and determine the 'big picture'.
    """
    inputs = {
        "data_points": {
            "type": "string",
            "description": "The data to synthesize (can be a JSON string of multiple items or a combined text block)."
        },
        "objective": {
            "type": "string",
            "description": "What you want to achieve with this synthesis (e.g., 'create a 3-step plan', 'identify contradictions')."
        }
    }
    output_type = "string"

    def forward(self, data_points: str, objective: str) -> str:
        """
        Perform synthesis using GPT-5.
        """
        model_id = os.getenv("OPENAI_MODEL", "openai/gpt-5-nano-2025-08-07")
        
        system_prompt = """You are Dionysus's synthesis faculty. 
        Your task is to take disparate data points and weave them into a high-level, actionable, and coherent narrative or plan.
        Focus on emergence—what new insights arise when these specific pieces of information are combined?
        """
        
        user_content = f"Objective: {objective}\n\nData Points:\n{data_points}"
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        try:
            response = litellm.completion(
                model=model_id,
                messages=messages,
                api_key=os.getenv("OPENAI_API_KEY")
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Synthesis failed: {str(e)}"
