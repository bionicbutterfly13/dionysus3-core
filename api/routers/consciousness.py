
"""
Consciousness Router
Feature: 040-designer-artifact-user
Exposes WebSocket endpoint for real-time visualization of the 
Triadic Active Inference loop (The "Ghost in the Machine").
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

from api.services.consciousness.triadic_inference_service import get_triadic_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/stream")
async def websocket_consciousness_stream(websocket: WebSocket):
    """
    Streams the internal state of the Triadic Inference Engine.
    Clients must send observation payloads:
    {
        "designer_obs": [..],
        "artifact_obs": [..],
        "user_obs": [..]
    }
    """
    await websocket.accept()
    service = get_triadic_service()
    
    try:
        while True:
            payload_in = await websocket.receive_json()
            designer_obs = payload_in.get("designer_obs")
            artifact_obs = payload_in.get("artifact_obs")
            user_obs = payload_in.get("user_obs")

            if not isinstance(designer_obs, list) or not isinstance(artifact_obs, list) or not isinstance(user_obs, list):
                await websocket.send_json({
                    "type": "error",
                    "detail": "designer_obs, artifact_obs, and user_obs must be lists of integers",
                })
                continue
            if (
                not all(isinstance(item, int) for item in designer_obs)
                or not all(isinstance(item, int) for item in artifact_obs)
                or not all(isinstance(item, int) for item in user_obs)
            ):
                await websocket.send_json({
                    "type": "error",
                    "detail": "Observation arrays must contain integers only",
                })
                continue

            state = service.step_simulation(designer_obs, artifact_obs, user_obs)
            artifact_energy = state.get("artifact", {}).get("free_energy", 0.0)
            thought_seed_activation = 1.0 / (1.0 + max(0.0, artifact_energy))

            if thought_seed_activation >= 0.7:
                archetype = "CREATOR"
            elif thought_seed_activation >= 0.4:
                archetype = "ANALYST"
            else:
                archetype = "SENTINEL"

            payload = {
                "type": "triadic_update",
                "state": state,
                "thought_seed_activation": thought_seed_activation,
                "active_archetype": archetype,
                "resonance_frequency": 20.0 + (40.0 * thought_seed_activation),
            }

            await websocket.send_json(payload)

    except WebSocketDisconnect:
        logger.info("Consciousness stream disconnected")
    except Exception as e:
        logger.error(f"Error in consciousness stream: {e}")
        await websocket.close()
