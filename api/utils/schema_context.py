import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from pydantic import BaseModel, ValidationError
from api.services.llm_service import chat_completion

logger = logging.getLogger("dionysus.schema_context")

class SchemaContext:
    """
    Ensures LLM outputs conform to a specific Pydantic model/JSON Schema.
    Implements retry logic and error injection.
    """
    
    def __init__(
        self,
        model_class: Type[BaseModel],
        max_retries: int = 3,
        timeout_seconds: int = 5
    ):
        self.model_class = model_class
        # Extract JSON Schema from Pydantic
        self.schema_dict = model_class.model_json_schema()
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extracts JSON from text, handling markdown blocks."""
        try:
            # Try direct parse
            return json.loads(text)
        except json.JSONDecodeError:
            # Try extraction via regex
            json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
            matches = re.findall(json_pattern, text)
            if matches:
                try:
                    return json.loads(matches[0])
                except json.JSONDecodeError:
                    pass
            
            # Fallback: try finding first { and last }
            try:
                start = text.find('{')
                end = text.rfind('}')
                if start != -1 and end != -1:
                    return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
                
        return None

    def _generate_schema_prompt(self, base_prompt: str) -> str:
        """Appends schema instructions to the prompt."""
        schema_json = json.dumps(self.schema_dict, indent=2)
        return f"""{base_prompt}

Your response MUST be a valid JSON object conforming to this schema:
```json
{schema_json}
```
Respond ONLY with the JSON object."""

    async def query(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the query loop with validation and retries.
        """
        current_prompt = self._generate_schema_prompt(prompt)
        attempts = 0
        last_error = None

        while attempts <= self.max_retries:
            attempts += 1
            logger.info(f"Query attempt {attempts}/{self.max_retries + 1}")
            
            try:
                # Use the fast GPT-5 Nano for the schema validation loop
                response_text = await chat_completion(
                    messages=[{"role": "user", "content": current_prompt}],
                    system_prompt=system_prompt or "You are a precise JSON assistant.",
                )
                
                parsed = self._extract_json(response_text)
                if parsed is None:
                    last_error = "Could not parse JSON from response."
                else:
                    # Validate against Pydantic model
                    try:
                        # This ensures the data matches our model
                        validated = self.model_class.model_validate(parsed)
                        return validated.model_dump()
                    except ValidationError as e:
                        last_error = f"Validation Error: {str(e)}"
                
            except Exception as e:
                last_error = f"LLM Call Error: {str(e)}"
            
            if attempts <= self.max_retries:
                logger.warning(f"Attempt {attempts} failed: {last_error}. Retrying...")
                # Inject error into prompt for next attempt
                error_info = f"\n\nYour previous response was invalid.\nError: {last_error}\nPlease try again and ensure strict schema compliance."
                current_prompt = f"{current_prompt}{error_info}"
            else:
                logger.error(f"All {attempts} attempts failed. Last error: {last_error}")

        return {"error": f"Failed after {attempts} attempts. Last error: {last_error}"}