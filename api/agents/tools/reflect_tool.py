from smolagents import Tool
import asyncio
import os
import litellm

class ReflectTool(Tool):
    name = "reflect_on_topic"
    description = """
    Engage in deep reflection on a specific topic or recent events to gain new insights.
    Useful for analyzing patterns, understanding failures, or synthesizing complex information.
    """
    inputs = {
        "topic": {
            "type": "string",
            "description": "The specific topic, question, or experience to reflect upon."
        },
        "context": {
            "type": "string",
            "description": "Additional context or background information to inform the reflection.",
            "nullable": True
        }
    }
    output_type = "string"

    def forward(self, topic: str, context: str = "") -> str:
        """
        Perform reflection using LiteLLM.
        """
        model_id = os.getenv("OPENAI_MODEL", "openai/gpt-5-nano-2025-08-07")
        
        system_prompt = """You are Dionysus's reflective faculty. 
        Your goal is to think deeply about the provided topic, connecting it to broader patterns, 
        values, and potential future actions. 
        
        Avoid superficial summaries. Dig for root causes, hidden implications, and systemic connections.
        """
        
        user_content = f"Topic to reflect on: {topic}"
        if context:
            user_content += f"\n\nContext:\n{context}"
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        # litellm.completion is sync by default unless using acompletion
        try:
            response = litellm.completion(
                model=model_id,
                messages=messages,
                api_key=os.getenv("OPENAI_API_KEY")
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Reflection failed: {str(e)}"
