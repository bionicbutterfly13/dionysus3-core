
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from api.services.context_packaging import (
    ContextCell, 
    SchemaContextCell, 
    TokenBudgetManager, 
    fetch_schema_context
)
from api.services.consciousness.autoschemakg_integration import (
    AutoSchemaKGIntegration, 
    InferredConcept, 
    ConceptType
)

@pytest.mark.asyncio
async def test_schema_context_cell_generation():
    """Test that SchemaContextCell generates valid XML content."""
    cell = SchemaContextCell(
        cell_id="test_1",
        content="",
        priority="high",
        token_count=100,
        schema_domain="testing",
        constraints=["UnitTesting (Activity)", "Mocking (Technique)"]
    )
    
    assert '<active_schema domain="testing">' in cell.content
    assert '<constraint>UnitTesting (Activity)</constraint>' in cell.content
    assert '<constraint>Mocking (Technique)</constraint>' in cell.content

@pytest.mark.asyncio
async def test_fetch_schema_context_integration():
    """Test the fetch_schema_context orchestration."""
    
    # 1. Mock AutoSchemaKG Retrieval
    mock_svc = MagicMock(spec=AutoSchemaKGIntegration)
    mock_svc.retrieve_relevant_concepts = AsyncMock(return_value=[
        InferredConcept(name="TestConcept", concept_type=ConceptType.ENTITY, confidence=0.9),
        InferredConcept(name="TestRelation", concept_type=ConceptType.RELATION, confidence=0.8)
    ])
    
    # 2. Mock Dependency Injection
    with patch('api.services.consciousness.autoschemakg_integration.get_autoschemakg_service', return_value=mock_svc):
        
        # 3. Setup Budget Manager
        budget = TokenBudgetManager(total_budget=1000)
        
        # 4. Execute Retrieval
        cell = await fetch_schema_context("test query", budget)
        
        # 5. Verify Results
        assert cell is not None
        assert isinstance(cell, SchemaContextCell)
        assert cell.schema_domain == "inferred_ontology"
        assert len(cell.constraints) == 2
        assert "TestConcept (entity)" in cell.constraints[0]
        assert "TestRelation (relation)" in cell.constraints[1]
        
        # 6. Verify Budget Injection
        stored_cell = budget.get_cell(cell.cell_id)
        assert stored_cell == cell
        assert budget.used_tokens > 0

@pytest.mark.asyncio
async def test_fetch_schema_context_empty():
    """Test graceful handling of empty results."""
    
    mock_svc = MagicMock(spec=AutoSchemaKGIntegration)
    mock_svc.retrieve_relevant_concepts = AsyncMock(return_value=[])
    
    with patch('api.services.consciousness.autoschemakg_integration.get_autoschemakg_service', return_value=mock_svc):
        budget = TokenBudgetManager(total_budget=1000)
        cell = await fetch_schema_context("nonexistent", budget)
        
        assert cell is None
        assert budget.used_tokens == 0
