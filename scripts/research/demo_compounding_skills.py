
import os
import json
from smolagents import CodeAgent, LiteLLMModel, tool

# 1. Define atomic skills as tools

@tool
def generate_headline(topic: str, audience: str) -> str:
    """
    Generates a high-converting headline for a given topic and audience.
    
    Args:
        topic: The subject of the content.
        audience: The target demographic.
    """
    # In a real scenario, this would call an LLM or use a template
    return f"How {audience} Can Master {topic} Without Burnout"

@tool
def analyze_copy(text: str) -> str:
    """
    Analyzes copy and returns a JSON string with quality metrics.
    
    Args:
        text: The copy to analyze.
    """
    # Mock analysis result
    metrics = {
        "readability": 0.85,
        "emotional_resonance": 0.92,
        "urgency": 0.75,
        "word_count": len(text.split())
    }
    return json.dumps(metrics)

@tool
def build_landing_page(headline: str, metrics_json: str) -> str:
    """
    Assembles a landing page asset using a headline and analysis metrics.
    
    Args:
        headline: The main headline for the page.
        metrics_json: JSON string of analysis metrics to display as proof.
    """
    metrics = json.loads(metrics_json)
    page = {
        "layout": "modern-minimalist",
        "header": headline,
        "proof_section": f"Our analysis shows an emotional resonance of {metrics['emotional_resonance']*100}%",
        "cta": "Start Your Journey"
    }
    return json.dumps(page, indent=2)

# 2. Setup the agent with gpt-5-nano
model = LiteLLMModel(model_id="openai/gpt-5-nano")

agent = CodeAgent(
    tools=[generate_headline, analyze_copy, build_landing_page],
    model=model,
    name="CompoundingAgent",
    description="An agent specialized in chaining copy skills into complete assets."
)

# 3. Task that requires chaining
task = """
I need you to create a landing page asset for 'Quantum Meditation' targeting 'Hustle Culture Entrepreneurs'.
Follow these steps:
1. Generate a powerful headline.
2. Analyze the quality of that headline.
3. Use the headline and the analysis metrics to build the final landing page asset.
Ensure you pass the actual output objects between the tools.
"""

if __name__ == "__main__":
    print("🚀 Running Compounding Skills Demo...")
    result = agent.run(task)
    print("\n--- FINAL ASSET ---")
    print(result)
