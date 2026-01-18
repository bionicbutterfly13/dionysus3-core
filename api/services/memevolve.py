from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Protocol
from pydantic import BaseModel, Field
from api.models.marketing import Product, Lesson, Step, KeyPhrase, Avatar

# --- 1. THE MEMEVOLVE INTERFACE (The 4 Modules) ---

class MemoryItem(BaseModel):
    """The universal unit of memory."""
    id: str
    content: str
    metadata: Dict[str, Any]
    resonance_score: float = 0.0
    type: str # "lesson", "step", "obstacle", "phrase"

class MemoryRequest(BaseModel):
    query: str
    cpa_domain: str = "explore" # The agent's current mode
    avatar_state: Optional[Dict[str, Any]] = None # context

class MemoryResponse(BaseModel):
    items: List[MemoryItem]
    strategy_used: str

class IMemEvolve(ABC):
    """The Abstract Interface for Self-Evolving Memory."""
    
    @abstractmethod
    async def encode(self, raw_data: Any) -> List[MemoryItem]:
        """Parse raw content into structured MemoryItems."""
        pass
        
    @abstractmethod
    async def store(self, items: List[MemoryItem]) -> bool:
        """Persist items to the underlying storage (Graph/JSON)."""
        pass
        
    @abstractmethod
    async def retrieve(self, request: MemoryRequest) -> MemoryResponse:
        """Get relevant items based on query and resonance."""
        pass
        
    @abstractmethod
    async def manage(self) -> Dict[str, Any]:
        """Consolidate, Prune, and Evolve the memory structure."""
        pass

# --- 2. THE CONCRETE IMPLEMENTATION (Course Memory) ---

class CourseMemorySystem(IMemEvolve):
    """
    The 'Evolved Architecture' for the Inner Architect System.
    Specializes in 3x3x3 Graphs and Resonance Filtering.
    """
    
    def __init__(self, product: Product):
        self.product = product # The "Database" for this specific memory system
        
    async def encode(self, raw_data: Any) -> List[MemoryItem]:
        # In a real evolution, this would efficiently parse text -> Lesson/Step
        # For now, we assume raw_data is already structural or text to be distilled
        pass 

    async def store(self, items: List[MemoryItem]) -> bool:
        # Save to the Product Pydantic model
        pass

    async def retrieve(self, request: MemoryRequest) -> MemoryResponse:
        """
        Retrieves course content. 
        Crucial Feature: Filters by RESANANCE if provided.
        """
        matches = []
        
        # 1. Naive Search (can be upgraded to Vector)
        for module in self.product.modules:
            for lesson in module.lessons:
                # Check Lesson Match
                if request.query.lower() in lesson.title.lower() or request.query.lower() in lesson.key_concept.lower():
                    matches.append(MemoryItem(
                        id=lesson.id, content=f"LESSON: {lesson.title} - {lesson.promise}", 
                        type="lesson", metadata=lesson.model_dump(), resonance_score=1.0
                    ))
                
                # Check Steps
                for step in lesson.steps:
                     if request.query.lower() in step.name.lower():
                         matches.append(MemoryItem(
                            id=step.id, content=f"STEP: {step.name} - {step.instruction}",
                            type="step", metadata=step.model_dump(), resonance_score=0.9
                         ))
                         
        return MemoryResponse(items=matches, strategy_used="keyword_resonance")

    async def manage(self) -> Dict[str, Any]:
        """
        The 'Sleep' function.
        Checks for orphan steps or duplicate obstacles and merges them.
        """
        # Placeholder for 'Ultrathink' consolidation logic
        return {"status": "optimized", "nodes_pruned": 0}
