import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.models.autobiographical import (
    ActiveInferenceState,
    DevelopmentEpisode,
    DevelopmentEvent,
    DevelopmentEventType,
)
from api.models.sync import MemoryType
from api.services.context_packaging import CellPriority, ContextCell, TokenBudgetManager
from api.services.nemori_river_flow import NemoriRiverFlow


@pytest.mark.asyncio
async def test_predict_and_calibrate_routes_facts_and_tracks_residue():
    mock_store = AsyncMock()
    mock_router = AsyncMock()
    mock_router.classify_memory_type.return_value = MemoryType.STRATEGIC
    mock_router.get_basin_for_type = MagicMock(return_value={
        "basin_name": "strategic-basin",
        "default_strength": 0.85,
    })
    mock_router.route_memory = AsyncMock()

    budget_manager = TokenBudgetManager(total_budget=10000)
    residue_tracker = MagicMock()

    episode = DevelopmentEpisode(
        episode_id="ep_456",
        journey_id="journey_2",
        title="Integration Episode",
        summary="Testing integration between routing and context packaging.",
        narrative="A short integration narrative.",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        events=["evt_456"],
    )

    active_state = ActiveInferenceState(twa_state={"focus": "integration"})

    event = DevelopmentEvent(
        event_id="evt_456",
        event_type=DevelopmentEventType.GENESIS,
        summary="Integration test event",
        rationale="Verify Nemori flow wiring",
        impact="None",
        active_inference_state=active_state,
    )

    residue_payload = {
        "active_goals": ["Align memory routing"],
        "active_entities": ["Nemori"],
        "stable_context": "Strategic memory distillation",
    }

    with patch("api.services.nemori_river_flow.get_consolidated_memory_store", return_value=mock_store), \
         patch("api.services.nemori_river_flow.get_memory_basin_router", return_value=mock_router), \
         patch("api.services.nemori_river_flow.get_token_budget_manager", return_value=budget_manager), \
         patch("api.services.nemori_river_flow.get_residue_tracker", return_value=residue_tracker), \
         patch("api.services.nemori_river_flow.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = [
            "- Fact one about strategy\n- Fact two about goals",
            json.dumps(
                {
                    "new_facts": ["Fact one about strategy", "Fact two about goals"],
                    "symbolic_residue": residue_payload,
                }
            ),
        ]

        nemori = NemoriRiverFlow()
        new_facts, residue = await nemori.predict_and_calibrate(episode, [event])

    assert new_facts == ["Fact one about strategy", "Fact two about goals"]
    assert residue == residue_payload

    assert mock_router.route_memory.await_count == 2
    for call in mock_router.route_memory.call_args_list:
        assert call.kwargs["memory_type"] == MemoryType.STRATEGIC
        assert call.kwargs["source_id"].startswith("nemori_distill:")

    fact_cells = [
        cell for cell_id, cell in budget_manager._cells.items()
        if cell_id.startswith("fact_")
    ]
    assert len(fact_cells) == 2
    for cell in fact_cells:
        assert isinstance(cell, ContextCell)
        assert cell.priority == CellPriority.MEDIUM
        assert cell.basin_id == "strategic-basin"
        assert cell.resonance_score == pytest.approx(0.85)
        assert cell.metadata.get("episode_id") == "ep_456"

    residue_cells = [
        cell for cell_id, cell in budget_manager._cells.items()
        if cell_id.startswith("residue_")
    ]
    assert len(residue_cells) == 1
    residue_cell = residue_cells[0]
    assert residue_cell.priority == CellPriority.HIGH
    assert residue_cell.basin_id == "strategic-basin"
    assert residue_cell.resonance_score == pytest.approx(0.95)

    residue_tracker.record_transformation.assert_called_once()
    call_kwargs = residue_tracker.record_transformation.call_args.kwargs
    source_cells = call_kwargs["source_cells"]
    derived_cell = call_kwargs["derived_cell"]
    assert len(source_cells) == 2
    assert all(isinstance(cell, ContextCell) for cell in source_cells)
    assert derived_cell.cell_id.startswith("residue_")
    assert call_kwargs["transformation_type"] == "residue_distillation"
