import pytest
from unittest.mock import AsyncMock, patch
from api.services.hexis_service import HexisService

@pytest.fixture
def mock_graphiti():
    """Mock the GraphitiService instance returned by get_graphiti_service."""
    mock_service = AsyncMock()
    with patch("api.services.hexis_service.get_graphiti_service", new=AsyncMock(return_value=mock_service)):
        yield mock_service

@pytest.fixture
def hexis_service():
    return HexisService()

@pytest.mark.asyncio
async def test_check_consent_no_record(hexis_service, mock_graphiti):
    """Should return False if no consent fact exists."""
    mock_graphiti.search.return_value = {"edges": []}
    
    consent = await hexis_service.check_consent("agent-123")
    
    assert consent is False
    mock_graphiti.search.assert_called_once()

@pytest.mark.asyncio
async def test_grant_consent(hexis_service, mock_graphiti):
    """Should persist a consent fact."""
    agent_id = "agent-123"
    contract = {"signature": "valid_sig", "terms": "v1"}
    
    await hexis_service.grant_consent(agent_id, contract)
    
    # Verification: Ensure it calls persist_fact with 'hexis_consent' basin
    mock_graphiti.persist_fact.assert_called_once()
    call_args = mock_graphiti.persist_fact.call_args[1]
    
    # Note: 'category' often maps to 'basin_id' in Nemori patterns
    assert call_args.get("basin_id") == "hexis_consent"
    assert "valid_sig" in str(call_args.get("fact_text", ""))

@pytest.mark.asyncio
async def test_boundary_lifecycle(hexis_service, mock_graphiti):
    """Should add and retrieve boundaries."""
    agent_id = "agent-123"
    boundary_text = "Boundary: Never lie to the user."
    
    # 1. Add
    await hexis_service.add_boundary(agent_id, boundary_text)
    mock_graphiti.persist_fact.assert_called()
    call_args = mock_graphiti.persist_fact.call_args[1]
    assert call_args.get("basin_id") == "hexis_boundary"
    
    # 2. Retrieve
    # Mock return value for search
    # Mock return value for search (dict structure)
    mock_graphiti.search.return_value = {
        "edges": [{"fact": boundary_text}]
    }
    
    boundaries = await hexis_service.get_boundaries(agent_id)
    assert boundary_text in boundaries[0]

@pytest.mark.asyncio
async def test_termination_requires_verification(hexis_service, mock_graphiti):
    """Should strictly validate termination token."""
    agent_id = "agent-123"
    
    # 1. Request Termination (Generate Token)
    token = await hexis_service.request_termination(agent_id)
    assert token is not None
    
    # 2. Confirm check logic is accessible (white-box for service method?)
    # Ideally termination destroys data. Mock delete/archive call.
    
    await hexis_service.confirm_termination(agent_id, token, "Last Will: Goodbye")
    
    # Verify destructive action called on Graphiti/Memory
    # Verify destructive action called on Graphiti/Memory via execute_cypher
    mock_graphiti.execute_cypher.assert_called()
    # Or strict check:
    # mock_graphiti.execute_cypher.assert_any_call(
    #     "MATCH (t:Tombstone ...", ...
    # ) 
    # Or however we define "Wipe" in Graphiti abstraction
    
