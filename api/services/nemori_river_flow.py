import logging
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict, Tuple
from uuid import uuid4

from api.models.autobiographical import (
    DevelopmentEvent,
    DevelopmentEpisode,
    RiverStage,
    RiverStage,
    DevelopmentArchetype
)
from api.models.memevolve import TrajectoryData
from api.models.beautiful_loop import ResonanceSignal, ResonanceMode
from api.agents.consolidated_memory_stores import get_consolidated_memory_store
from api.services.llm_service import chat_completion, GPT5_NANO
from api.services.memory_basin_router import get_memory_basin_router
from api.services.graphiti_service import get_graphiti_service
from api.services.context_packaging import (
    get_token_budget_manager,
    get_residue_tracker,
    ContextCell,
    CellPriority,
)
from api.services.memevolve_adapter import get_memevolve_adapter
from api.models.memevolve import MemoryIngestRequest, TrajectoryData, TrajectoryStep, TrajectoryMetadata

logger = logging.getLogger("dionysus.nemori_river_flow")


class NemoriRiverFlow:
    """
    Service for managing the episodic 'River' flow.
    Implements Boundary Alignment, Predict-Calibrate, and Neuronal Packet Quantization.
    """
    def __init__(self):
        self.store = get_consolidated_memory_store()
        self.token_budget = get_token_budget_manager()

    async def create_packet_train(
        self, 
        content: str, 
        source_id: str = "user_input",
        event_type: str = "cognitive_stream"
    ) -> List[DevelopmentEvent]:
        """
        QUANTIZATION LAYER (The Axon):
        Splits a continuous stream of content into discrete 'Neuronal Packets' (DevelopmentEvents).
        
        Mandate:
        - Max duration ~200ms (simulated).
        - Each packet has independent dynamics (spike density).
        - Packets are chained via parent_episode_id or sequence metadata.
        """
        # 1. Tokenize (Approximate)
        words = content.split()
        total_tokens = len(words)
        
        # 2. Determine Quantum Size (Packet Window)
        # 50 tokens ~ 200ms processing time (heuristic)
        PACKET_SIZE = 50 
        
        packets = []
        chunks = [words[i:i + PACKET_SIZE] for i in range(0, len(words), PACKET_SIZE)]
        
        parent_packet_id = None
        basin_router = get_memory_basin_router()
        
        for i, chunk in enumerate(chunks):
            chunk_text = " ".join(chunk)
            
            # Calculate Dynamics
            dynamics = self._calculate_packet_dynamics(chunk_text)
            
            # Determine Basin Context (Manifold Constraint)
            # Only do full classification for the first packet to set the trajectory
            linked_basin_id = None
            basin_score = 0.0
            if i == 0: 
                try:
                    mem_type = await basin_router.classify_memory_type(chunk_text)
                    basin_config = basin_router.get_basin_for_type(mem_type)
                    linked_basin_id = basin_config.get("basin_name")
                    basin_score = basin_config.get("default_strength", 0.5)
                    # Update dynamics with manifold position if possible (placeholder)
                    dynamics.manifold_position = [0.1, 0.5] # Symbolic
                except Exception:
                    pass

            event_id = f"pkt_{uuid4().hex[:8]}"
            
            packet = DevelopmentEvent(
                event_id=event_id,
                timestamp=datetime.now(timezone.utc),
                event_type=event_type,
                summary=chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text,
                rationale=chunk_text, # The full content is the rationale
                impact="neuronal_flow",
                packet_dynamics=dynamics,
                linked_basin_id=linked_basin_id,
                basin_r_score=basin_score,
                metadata={
                    "sequence_index": i,
                    "total_packets": len(chunks),
                    "source_id": source_id,
                    "parent_packet_id": parent_packet_id 
                }
            )
            
            # Store immediately (Fire the neuron)
            await self.store.store_event(packet)
            packets.append(packet)
            parent_packet_id = event_id
            
        return packets

    def _calculate_packet_dynamics(self, text: str) -> "PacketDynamics":
        """
        Calculate the simulated neuro-dynamics of a text chunk.
        """
        from api.models.autobiographical import PacketDynamics
        
        token_count = len(text.split())
        
        # Duration: ~10ms per token + 50ms base overhead
        # Max cap at 500ms (slow wave) per physics constraints
        estimated_duration = min(500, 50 + (token_count * 10))
        
        # Spike Density: Tokens / Duration
        # Higher density = More information per ms
        spike_density = token_count / estimated_duration if estimated_duration > 0 else 0
        
        # Phase Ratio: 
        # Short packets are mostly structural (Early Phase)
        # Long packets are mostly content (Late Phase)
        phase_ratio = 0.5 if token_count < 10 else 0.25
        
        return PacketDynamics(
            duration_ms=estimated_duration,
            spike_density=spike_density,
            phase_ratio=phase_ratio,
            manifold_position=[] # populated by router if active
        )

    async def check_boundary(self, events: List[DevelopmentEvent], resonance_signal: Optional[ResonanceSignal] = None) -> bool:
        """
        Reflective boundary detection using Predict-Calibrate logic.
        Detects if current events represent a phase shift (Attractor transition).
        Incorporates Richmond/Zacks Event Segmentation Theory (EST).
        """
        logger.debug(f"Checking boundary for {len(events)} events...")
        if not events:
            return False

        # Prepare context with surprisal/uncertainty if available
        context_lines = []
        max_surprisal = 0.0
        for e in events:
            line = f"- {e.event_type.value}: {e.summary}"
            surprisal = 0.0
            if e.active_inference_state:
                surprisal = e.active_inference_state.surprisal
                line += f" [Surprisal: {surprisal:.2f}, Uncertainty: {e.active_inference_state.uncertainty:.2f}]"
            elif e.prediction_error:
                surprisal = e.prediction_error
                line += f" [PredErr: {surprisal:.2f}]"
            
            max_surprisal = max(max_surprisal, surprisal)
            context_lines.append(line)
        
        # Computational Trigger: High surprisal immediately triggers boundary
        if max_surprisal > 0.8: # Threshold could be dynamic
            logger.info(f"Computational EST Trigger: High surprisal detected ({max_surprisal:.2f})")
            return True

        # ULTRATHINK Trigger: Dissonance forces segmentation to protect Worldview
        if resonance_signal:
            if resonance_signal.mode == ResonanceMode.DISSONANT:
                logger.info(f"ULTRATHINK Trigger: Dissonance detected (Score: {resonance_signal.resonance_score:.2f}). Forcing boundary.")
                return True
            if resonance_signal.mode == ResonanceMode.TURBULENT and max_surprisal > 0.6:
                logger.info("ULTRATHINK Trigger: Turbulence + High Surprisal. Forcing boundary.")
                return True

        context = "\n".join(context_lines)
        
        prompt = f"""
        Analyze the following stream of development events (Nemori River SOURCE flow).
        Determine if the latest event represents an 'Episode Boundary' (a transition between attractor basins).
        
        Based on Richmond/Zacks EST (Event Segmentation Theory), a boundary occurs when:
        1. Prediction error (Surprisal) spikes significantly.
        2. The 'smooth dynamics' of the current activity are interrupted.
        3. A shift in thematic 'Strand' occurs (Character, Goal, Location).
        4. A goal has been achieved or abandoned.

        Events:
        {context}

        Respond ONLY with a JSON object:
        {{
            "boundary_detected": true/false,
            "confidence": 0.0-1.0,
            "surprisal_estimate": 0.0-1.0,
            "rationale": "Detailed explanation using EST principles"
        }}
        """
        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a Nemori Memory Architect, detecting phase shifts in cognitive flow using EST.",
                model=GPT5_NANO
            )
            result = json.loads(response.strip().strip("`").replace("json", "").strip())
            detected = result.get("boundary_detected", False)
            
            # Record the surprisal estimate back into the event if detected
            # (In a real flow, this would be computed by the agent during prediction)
            
            logger.info(f"Boundary check: {detected} (Confidence: {result.get('confidence')}) - {result.get('rationale')}")
            return detected
        except Exception as e:
            logger.error(f"Error in check_boundary: {e}")
            return False

    async def construct_episode(self, events: List[DevelopmentEvent], journey_id: str, parent_episode_id: Optional[str] = None) -> Optional[DevelopmentEpisode]:
        """
        Consolidates TRIBUTARY events into a coherent Episode (Stable Attractor).
        Supports Richmond/Zacks 'Strands' and Hierarchical structure.
        """
        logger.info(f"Constructing episode from {len(events)} events for journey {journey_id}")
        if not events:
            return None
            
        context = "\n".join([f"- {e.summary} (Impact: {e.impact})" for e in events])
        
        prompt = f"""
        Synthesize these development events into a coherent 'Development Episode'.
        Identify the 'Stabilizing Attractor' (the core theme/goal) and the thematic 'Strand'.

        Events:
        {context}

        Respond ONLY with a JSON object:
        {{
            "title": "Short descriptive title",
            "summary": "Brief summary",
            "narrative": "Coherent story of what happened",
            "archetype": "one of: innocent, orphan, warrior, caregiver, explorer, rebel, lover, creator, jester, sage, magician, ruler",
            "stabilizing_attractor": "The core theme",
            "strand_id": "One-word thematic strand (e.g. 'coding', 'research', 'ops')"
        }}
        """
        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a Narrative Architect, distilling experience into hierarchical attractor basins.",
                model=GPT5_NANO
            )
            data = json.loads(response.strip().strip("`").replace("json", "").strip())
            
            # Aggregate Mosaic Metrics
            c_levels = [e.consciousness_level for e in events]
            peak_c = max(c_levels) if c_levels else 0.5
            avg_c = sum(c_levels) / len(c_levels) if c_levels else 0.5
            
            episode = DevelopmentEpisode(
                episode_id=str(uuid4()),
                journey_id=journey_id,
                title=data.get("title", "Untitled Episode"),
                summary=data.get("summary", ""),
                narrative=data.get("narrative", ""),
                start_time=events[0].timestamp,
                end_time=events[-1].timestamp,
                events=[e.event_id for e in events],
                dominant_archetype=DevelopmentArchetype(data.get("archetype", "sage")) if data.get("archetype") else None,
                river_stage=RiverStage.MAIN_RIVER,
                stabilizing_attractor=data.get("stabilizing_attractor", None),
                parent_episode_id=parent_episode_id,
                strand_id=data.get("strand_id", "general"),
                peak_consciousness_level=peak_c,
                avg_consciousness_level=avg_c
            )
            
            # Hippocampal Binding: Sharpen the narrative before storing
            episode.narrative = await self._sharpen_episode_narrative(episode, events)
            
            await self.store.create_episode(episode)
            
            # T041-029: Episode-to-Trajectory Bridge
            # Promote Hierarchical Episode to MemEvolve Retrieval System
            # This ensures the narrative is entity-extracted and vector-indexed via the standard pipeline.
            try:
                adapter = get_memevolve_adapter()
                traj_data = TrajectoryData(
                    query=f"Episode: {episode.title}",
                    steps=[
                        TrajectoryStep(
                            observation=f"Summary: {episode.summary}", 
                            thought=f"Narrative: {episode.narrative}",
                            action=f"Archetype: {episode.dominant_archetype.value if episode.dominant_archetype else 'None'}, Strand: {episode.strand_id}"
                        )
                    ],
                    metadata=TrajectoryMetadata(
                        agent_id="nemori_architect",
                        session_id=None, # System level
                        project_id="dionysus_core",
                        timestamp=episode.start_time,
                        tags=["episode", episode.strand_id, "nemori"]
                    )
                )
                
                await adapter.ingest_trajectory(MemoryIngestRequest(
                   trajectory=traj_data,
                   session_id=None,
                   project_id="dionysus_core",
                   memory_type="episodic"  
                ))
                logger.info(f"Bridged episode {episode.episode_id} to MemEvolve trajectory.")
            except Exception as bridge_err:
                logger.warning(f"Episode-to-Trajectory bridge failed: {bridge_err}")

            return episode
        except Exception as e:
            logger.error(f"Error in episode construction: {e}")
            # Fallback
            return DevelopmentEpisode(
                episode_id=str(uuid4()),
                journey_id=journey_id,
                title="Consolidated Episode (Fallback)",
                summary="An error occurred during episode construction.",
                narrative="No detailed narrative due to error.",
                start_time=events[0].timestamp if events else datetime.now(timezone.utc),
                end_time=events[-1].timestamp if events else datetime.now(timezone.utc),
                events=[e.event_id for e in events],
                dominant_archetype=DevelopmentArchetype.SAGE,
                river_stage=RiverStage.MAIN_RIVER
            )

    async def predict_and_calibrate(
        self, 
        episode: DevelopmentEpisode, 
        original_events: List[DevelopmentEvent],
        basin_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], Dict[str, Any]]:
        """
        Implements the Predict-Calibrate Principle (Nemori 3.2 for DELTA).
        Returns distilled facts AND 'Symbolic Residue' for incremental continuity.
        Now context-aware via Attractor Basins.
        """
        # 1. Prediction Stage with Basin Context
        basin_prompt = ""
        if basin_context:
            basin_prompt = f"\nContext from Attractor Basin ({basin_context.get('name')}): {basin_context.get('description')}"

        prediction_prompt = (
            f"Based on the episode title '{episode.title}' and summary '{episode.summary}', "
            f"{basin_prompt}\n"
            "predict what semantic facts or architectural lessons should be confirmed by this experience. "
            "Respond ONLY with a bulleted list of predictions."
        )
        
        # 2. Calibration Stage
        calibration_prompt = (
            "You are a knowledge distiller. Identify the 'Prediction Gap' and 'Symbolic Residue'.\n"
            "Prediction Gap: What new standalone semantic facts were learned?\n"
            "Symbolic Residue: What specific situational features (actors, goals, location) remain ACTIVE and should carry over to the next episode?\n"
            "Surprisal: A score from 0.0 to 1.0 representing how unexpected the actual experience was compared to the prediction.\n"
            "Respond ONLY with a JSON object:\n"
            "{\n"
            "  \"new_facts\": [\"fact1\", \"fact2\"],\n"
            "  \"symbolic_residue\": {\"active_goals\": [], \"active_entities\": [], \"stable_context\": \"\"},\n"
            "  \"surprisal\": 0.5\n"
            "}"
        )
        
        raw_logs = "\n".join([f"{e.summary}: {e.rationale}" for e in original_events])
        
        try:
            # Predict
            predictions = await chat_completion([{"role": "user", "content": "Generate predictions."}], prediction_prompt, model=GPT5_NANO)
            
            # Calibrate
            messages = [{"role": "user", "content": f"Predictions:\n{predictions}\n\nActual Logs:\n{raw_logs}"}]
            response = await chat_completion(messages, calibration_prompt, model=GPT5_NANO)
            data = json.loads(response.strip().strip("`").replace("json", "").strip())
            new_facts = data.get("new_facts", [])
            residue = data.get("symbolic_residue", {})
            surprisal = float(data.get("surprisal", 0.0))
            
            # T041-030: Predict-Calibrate -> Meta-Evolution loop
            # If surprisal exceeds threshold, trigger meta-evolution
            if surprisal > 0.6:
                try:
                    adapter = get_memevolve_adapter()
                    await adapter.trigger_evolution()
                    logger.info(f"High surprisal ({surprisal:.2f}) triggered Meta-Evolution.")
                except Exception as evo_err:
                    logger.warning(f"Failed to trigger meta-evolution: {evo_err}")

            # Record semantic distillation event with Basin Linkage
            distill_id = f"distill_{uuid4().hex[:6]}"
            metadata = {"new_facts": new_facts, "residue": residue}
            if basin_context:
                metadata["linked_basin_id"] = basin_context.get("id")
                metadata["basin_r_score"] = basin_context.get("resonance_score", 0.0)

            # Basin Classification and Routing
            linked_basin_id = None
            basin_score = 0.0
            if basin_context:
                linked_basin_id = basin_context.get("id")
                basin_score = basin_context.get("resonance_score", 0.0)
            else:
                try:
                    router = get_memory_basin_router()
                    # 1. Classify
                    mem_type = await router.classify_memory_type(f"{episode.title}: {episode.summary}")
                    # 2. Get Basin Config
                    basin_config = router.get_basin_for_type(mem_type)
                    # 3. Use Basin Name (and default strength)
                    linked_basin_id = basin_config.get("basin_name")
                    basin_score = basin_config.get("default_strength", 0.5)

                    logger.info(f"Classified episode as {mem_type} -> Basin: {linked_basin_id}")

                    # 4. Route each new fact through the basin for proper extraction and storage
                    # MEMORY CLUSTER INTEGRATION:
                    # Step 4a: route_memory() → extracts entities/relationships → stores in graph
                    # Step 4b: persist_fact() → creates Fact nodes with bi-temporal tracking
                    # Both steps are complementary: entities for graph traversal, facts for temporal queries
                    for fact in new_facts:
                        if fact and len(fact) > 10:  # Skip trivial facts
                            # 4a. Basin Router: classify → activate → extract entities/relationships
                            try:
                                await router.route_memory(
                                    content=fact,
                                    memory_type=mem_type,
                                    source_id=f"nemori_distill:{episode.episode_id}"
                                )
                            except Exception as route_err:
                                logger.warning(f"Failed to route fact through basin: {route_err}")

                            # 4b. Graphiti: persist Fact node with bi-temporal tracking
                            # Links to episode via DISTILLED_FROM, cross-refs basin classification
                            try:
                                graphiti = await get_graphiti_service()
                                await graphiti.persist_fact(
                                    fact_text=fact,
                                    source_episode_id=episode.episode_id,
                                    valid_at=datetime.now(timezone.utc),
                                    basin_id=linked_basin_id,
                                    confidence=0.8,
                                )
                            except Exception as persist_err:
                                logger.warning(f"Failed to persist fact to Graphiti: {persist_err}")

                except Exception as e:
                    logger.warning(f"Basin classification failed: {e}")

            # Markov Blanket ID Calculation
            blanket_id = None
            # Aggregating TWA states from events to form a stable blanket ID for the distillation
            # Simple approach: hash of sorted event IDs + episode ID to represent this specific blanket configuration context
            # Or use the last event's blanket state if available
            last_valid_state = next((e.active_inference_state for e in reversed(original_events) if e.active_inference_state), None)
            if last_valid_state and last_valid_state.twa_state:
                # Deterministic hash of TWA state keys/values (session-stable)
                state_str = json.dumps(last_valid_state.twa_state, sort_keys=True)
                state_hash = hashlib.sha256(state_str.encode()).hexdigest()[:16]
                blanket_id = f"mb_{state_hash}"

            distill_event = DevelopmentEvent(
                event_id=distill_id,
                timestamp=datetime.now(timezone.utc),
                event_type="semantic_distillation",
                summary=f"Distilled {len(new_facts)} facts from episode {episode.title}",
                rationale=f"Predict-Calibrate on {episode.episode_id}",
                impact="Semantic knowledge enrichment",
                metadata=metadata,
                river_stage=RiverStage.DELTA,
                parent_episode_id=episode.episode_id,
                linked_basin_id=linked_basin_id, # If we had it
                basin_r_score=basin_score,
                markov_blanket_id=blanket_id 
            )
            await self.store.store_event(distill_event)

            # Wire symbolic residue to context packaging system
            try:
                budget_manager = get_token_budget_manager()
                residue_tracker = get_residue_tracker()

                # Create context cells from distilled facts (SEMANTIC memory)
                fact_cells: List[ContextCell] = []
                for i, fact in enumerate(new_facts):
                    if fact and len(fact) > 5:
                        cell = ContextCell(
                            cell_id=f"fact_{distill_id}_{i}",
                            content=fact,
                            priority=CellPriority.MEDIUM,
                            token_count=len(fact.split()) * 2,  # Rough estimate
                            resonance_score=basin_score,
                            basin_id=linked_basin_id,
                            metadata={"episode_id": episode.episode_id, "fact_index": i}
                        )
                        if budget_manager.add_cell(cell):
                            fact_cells.append(cell)

                # Store symbolic residue for retrieval cue integration
                if residue.get("active_goals") or residue.get("active_entities"):
                    # Create a HIGH priority cell for active residue
                    residue_content = []
                    if residue.get("active_goals"):
                        residue_content.append(f"Active Goals: {', '.join(residue['active_goals'])}")
                    if residue.get("active_entities"):
                        residue_content.append(f"Active Entities: {', '.join(residue['active_entities'])}")
                    if residue.get("stable_context"):
                        residue_content.append(f"Context: {residue['stable_context']}")

                    residue_cell = ContextCell(
                        cell_id=f"residue_{distill_id}",
                        content="\n".join(residue_content),
                        priority=CellPriority.HIGH,
                        token_count=len(" ".join(residue_content).split()) * 2,
                        resonance_score=basin_score + 0.1,  # Boost for active residue
                        basin_id=linked_basin_id,
                        metadata={"type": "symbolic_residue", "episode_id": episode.episode_id}
                    )
                    residue_added = budget_manager.add_cell(residue_cell)
                    if residue_added and fact_cells and hasattr(residue_tracker, "record_transformation"):
                        residue_tracker.record_transformation(
                            source_cells=fact_cells,
                            derived_cell=residue_cell,
                            transformation_type="residue_distillation",
                            lost_details=[],
                        )

                logger.info(f"Context packaging: {len(new_facts)} fact cells + 1 residue cell added")
            except Exception as ctx_err:
                logger.warning(f"Context packaging integration failed: {ctx_err}")

            return new_facts, residue
        except Exception as e:
            logger.error(f"Error in predict-calibrate cycle: {e}")
            return [], {}

    async def check_boundary_for_trajectories(self, trajectories: List[TrajectoryData]) -> bool:
        """
        Check for boundary condition in a stream of Trajectories (Protocol 060).
        """
        if not trajectories:
            return False
            
        context_lines = []
        for t in trajectories:
            line = f"- Trajectory {t.id or 'unknown'}: {t.summary or 'No summary'}"
            if t.metadata and t.metadata.agent_id:
                line += f" [Agent: {t.metadata.agent_id}]"
            context_lines.append(line)
            
        context = "\n".join(context_lines)
        
        prompt = f"""
        Analyze the following sequence of MemEvolve Trajectories.
        Determine if the latest trajectory represents a SIGNIFICANT shift in focus, goal, or context (Episode Boundary).
        
        Trajectories:
        {context}

        Respond ONLY with a JSON object:
        {{
            "boundary_detected": true/false,
            "confidence": 0.0-1.0,
            "rationale": "Explanation"
        }}
        """
        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a Nemori Memory Architect, detecting phase shifts in trajectory flows.",
                model=GPT5_NANO
            )
            result = json.loads(response.strip().strip("`").replace("json", "").strip())
            return result.get("boundary_detected", False)
        except Exception as e:
            logger.error(f"Error in check_boundary_for_trajectories: {e}")
            return False

    async def construct_episode_from_trajectories(self, trajectories: List[TrajectoryData], journey_id: str, parent_episode_id: Optional[str] = None) -> Optional[DevelopmentEpisode]:
        """
        Constructs a DevelopmentEpisode from a sequence of Trajectories (Protocol 060).
        Promotes Level 1 (Trajectory) to Level 3 (Episode) via linking.
        """
        logger.info(f"Constructing episode from {len(trajectories)} trajectories for journey {journey_id}")
        if not trajectories:
            return None
        
        context = "\n".join([f"- {t.summary or 'No summary'} (ID: {t.id})" for t in trajectories])
        
        prompt = f"""
        Synthesize these Trajectories into a coherent 'Development Episode'.
        Identify the overarching goal or theme that unites these execution traces.

        Trajectories:
        {context}

        Respond ONLY with a JSON object:
        {{
            "title": "Short descriptive title",
            "summary": "Brief summary",
            "narrative": "Coherent story of what happened",
            "archetype": "one of: innocent, orphan, warrior, caregiver, explorer, rebel, lover, creator, jester, sage, magician, ruler",
            "stabilizing_attractor": "The core theme",
            "strand_id": "One-word thematic strand"
        }}
        """
        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a Narrative Architect, distilling execution traces into hierarchical episodes.",
                model=GPT5_NANO
            )
            data = json.loads(response.strip().strip("`").replace("json", "").strip())
            
            # Map Trajectory IDs
            traj_ids = [t.id for t in trajectories if t.id]
            
            episode = DevelopmentEpisode(
                episode_id=str(uuid4()),
                journey_id=journey_id,
                title=data.get("title", "Untitled Episode"),
                summary=data.get("summary", ""),
                narrative=data.get("narrative", ""),
                start_time=trajectories[0].metadata.timestamp if trajectories[0].metadata and trajectories[0].metadata.timestamp else datetime.now(timezone.utc),
                end_time=trajectories[-1].metadata.timestamp if trajectories[-1].metadata and trajectories[-1].metadata.timestamp else datetime.now(timezone.utc),
                events=[], # Empty: we rely on source_trajectory_ids
                source_trajectory_ids=traj_ids, # Protocol 060 Link
                dominant_archetype=DevelopmentArchetype(data.get("archetype", "sage")) if data.get("archetype") else None,
                river_stage=RiverStage.MAIN_RIVER,
                stabilizing_attractor=data.get("stabilizing_attractor", None),
                parent_episode_id=parent_episode_id,
                strand_id=data.get("strand_id", "general"),
                peak_consciousness_level=0.5, # Default, as trajectories lack this metric typically
                avg_consciousness_level=0.5
            )
            
            # Hippocampal Binding
            episode.narrative = await self._sharpen_episode_narrative(episode, trajectories)
            
            await self.store.create_episode(episode)
            return episode
        except Exception as e:
            logger.error(f"Error in trajectory episode construction: {e}")
            return None

    async def _sharpen_episode_narrative(self, episode: DevelopmentEpisode, context_items: List[Any]) -> str:
        """
        Hippocampal Binding (Now Print) function.
        Sharps the narrative by reinforcing key situational features and goals.
        Supports both DevelopmentEvent and TrajectoryData input.
        """
        logger.debug(f"Sharpening narrative for episode {episode.title}")
        
        context_str = ""
        if not context_items:
            return episode.narrative
            
        if isinstance(context_items[0], TrajectoryData):
             context_str = ", ".join([t.summary or "No summary" for t in context_items])
        elif hasattr(context_items[0], 'summary'): # Duck typing for DevelopmentEvent
             context_str = ", ".join([e.summary for e in context_items])
        
        prompt = f"""
        Refine and 'Sharpen' the following episode narrative. 
        Focus on the 'Hippocampal Binding' of situational features:
        - Key Entities (Objects, Actors)
        - Goal Trajectories (What was achieved)
        - Symbolic Residue (What remains for the next episode)
        
        Original Narrative: {episode.narrative}
        Events/Trajectories: {context_str}
        
        Produce a more vivid, high-fidelity narrative that captures the essence of this cognitive scene.
        """
        try:
            sharpened = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a Hippocampal Architect, sharpening situational bindings into long-term memory.",
                model=GPT5_NANO
            )
            return sharpened.strip()
        except Exception as e:
            logger.error(f"Error sharpening narrative: {e}")
            return episode.narrative

_instance: Optional[NemoriRiverFlow] = None

def get_nemori_river_flow() -> NemoriRiverFlow:
    global _instance
    if _instance is None:
        _instance = NemoriRiverFlow()
    return _instance
