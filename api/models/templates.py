from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SalesTemplateSection(BaseModel):
    name: str
    fields: Dict[str, str] = Field(description="Key-value pairs for the section content")

class SalesTemplate(BaseModel):
    """
    Abstract representation of a Sales Page Template (e.g. GrowthWorks MVMO).
    """
    name: str = "Generic Template"
    headline: str
    promise: str
    mechanism: str
    
    # Context
    program_name: str
    core_benefit: str
    pain_points: List[str]
    the_shift: str # Old Way -> New Way
    
    # Process
    process_steps: List[Dict[str, str]] # {"step": "1", "title": "Map", "desc": "..."}
    
    # Deliverables
    modules: List[Dict[str, str]] # {"title": "Module 1", "desc": "..."}
    bonuses: List[Dict[str, str]]
    
    # Offer
    price: str
    guarantee: str
    upsell_hint: Optional[str] = None
    
    def render_markdown(self) -> str:
        """Simple markdown rendering of the filled template."""
        md = f"# {self.headline}\n\n"
        md += f"**Promise:** {self.promise}\n"
        md += f"**Mechanism:** {self.mechanism}\n\n"
        md += f"## {self.program_name}\n"
        md += f"**Benefit:** {self.core_benefit}\n\n"
        md += "### The Shift\n" + self.the_shift + "\n\n"
        md += "### The Process\n"
        for step in self.process_steps:
            md += f"- **Step {step.get('step')}:** {step.get('title')} - {step.get('desc')}\n"
        md += "\n### What You Get\n"
        for mod in self.modules:
            md += f"- **{mod.get('title')}:** {mod.get('desc')}\n"
        md += "\n### Bonuses\n"
        for bonus in self.bonuses:
            md += f"- **{bonus.get('title')}:** {bonus.get('desc')}\n"
        md += f"\n**Price:** {self.price}\n"
        md += f"**Guarantee:** {self.guarantee}\n"
        return md
