import os
import asyncio
import logging
from litellm import acompletion
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_litellm")

async def test_gpt5():
    api_key = os.getenv("OPENAI_API_KEY")
    model = "openai/gpt-5-nano"
    
    print(f"Testing {model} via LiteLLM...")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "say hello"}
    ]
    
    try:
        response = await acompletion(
            model=model,
            messages=messages,
            api_key=api_key
        )
        content = response.choices[0].message.content
        print(f"Response: '{content}'")
        print(f"Finish Reason: {response.choices[0].finish_reason}")
        print(f"Full Response Object: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_gpt5())
