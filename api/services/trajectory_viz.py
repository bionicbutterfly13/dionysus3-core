"""
Trajectory Visualization Service
Track: 062-document-ingestion-viz
Tasks: T062-019, T062-020

Generates visual representations of agent execution traces:
- Mermaid sequence diagrams
- OODA cycle visualization
- Basin transition markers
- Tool call annotations
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("dionysus.services.trajectory_viz")


class OODAPhase(str, Enum):
    """OODA loop phases."""
    OBSERVE = "observe"
    ORIENT = "orient"
    DECIDE = "decide"
    ACT = "act"


@dataclass
class AgentCall:
    """Record of an agent invocation."""
    agent_name: str
    step_number: int
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    duration_ms: int = 0
    ooda_phase: OODAPhase = OODAPhase.ACT


@dataclass
class BasinTransition:
    """Record of an attractor basin transition."""
    from_basin: Optional[str]
    to_basin: str
    trigger: str  # What caused the transition
    strength: float
    at_step: int


@dataclass
class TrajectoryTrace:
    """Complete trajectory trace for visualization."""
    trace_id: str
    session_id: str
    agent_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    calls: List[AgentCall] = field(default_factory=list)
    basin_transitions: List[BasinTransition] = field(default_factory=list)
    ooda_cycles: int = 0
    success: bool = True
    error_message: Optional[str] = None


class TrajectoryVisualizationService:
    """
    Service for generating trajectory visualizations.

    Supports:
    - Mermaid sequence diagrams
    - JSON export
    - HTML standalone viewer
    """

    def __init__(self):
        self._traces: Dict[str, TrajectoryTrace] = {}

    def generate_mermaid(self, trace: TrajectoryTrace) -> str:
        """
        Generate Mermaid sequence diagram from trace.

        Shows:
        - Agent hierarchy (HeartbeatAgent → ConsciousnessManager → sub-agents)
        - Tool calls with arguments
        - OODA phase transitions
        - Basin activations
        """
        lines = [
            "sequenceDiagram",
            "    autonumber",
            "",
            "    %% Participants",
            "    participant User",
            "    participant HA as HeartbeatAgent",
            "    participant CM as ConsciousnessManager",
            "    participant PA as PerceptionAgent",
            "    participant RA as ReasoningAgent",
            "    participant MA as MetacognitionAgent",
            "    participant Tools",
            "    participant Basins",
            "",
        ]

        # Add OODA cycle markers
        current_phase = None
        phase_colors = {
            OODAPhase.OBSERVE: "#e3f2fd",  # Light blue
            OODAPhase.ORIENT: "#fff3e0",   # Light orange
            OODAPhase.DECIDE: "#f3e5f5",   # Light purple
            OODAPhase.ACT: "#e8f5e9",      # Light green
        }

        for i, call in enumerate(trace.calls):
            # Add phase transition note
            if call.ooda_phase != current_phase:
                current_phase = call.ooda_phase
                phase_name = current_phase.value.upper()
                lines.append(f"    Note over HA,MA: 🔄 {phase_name} Phase")
                lines.append("")

            # Map agent to participant
            agent_map = {
                "heartbeat_agent": "HA",
                "consciousness_manager": "CM",
                "perception_agent": "PA",
                "reasoning_agent": "RA",
                "metacognition_agent": "MA",
            }
            agent_abbrev = agent_map.get(call.agent_name.lower(), "HA")

            # Add tool call
            if call.tool_name:
                # Truncate args for display
                args_str = str(call.tool_args)[:50] + "..." if call.tool_args else ""
                lines.append(f"    {agent_abbrev}->>Tools: {call.tool_name}({args_str})")

                # Add observation response
                if call.observation:
                    obs_short = call.observation[:40] + "..." if len(call.observation) > 40 else call.observation
                    lines.append(f"    Tools-->>+{agent_abbrev}: {obs_short}")

        # Add basin transitions as notes
        if trace.basin_transitions:
            lines.append("")
            lines.append("    %% Basin Transitions")
            for trans in trace.basin_transitions:
                from_str = trans.from_basin or "none"
                lines.append(f"    Note over Basins: {from_str} → {trans.to_basin} ({trans.strength:.2f})")

        # Add completion
        lines.append("")
        if trace.success:
            lines.append("    Note over User,MA: ✅ Complete")
        else:
            lines.append(f"    Note over User,MA: ❌ Failed: {trace.error_message or 'Unknown error'}")

        return "\n".join(lines)

    def generate_ooda_mermaid(self, trace: TrajectoryTrace) -> str:
        """
        Generate Mermaid flowchart showing OODA cycle.

        Visualizes the decision loop structure.
        """
        lines = [
            "flowchart TD",
            "",
            "    %% OODA Loop",
            '    O[("🔍 OBSERVE<br/>Perception Agent")] --> OR[("🧭 ORIENT<br/>Reasoning Agent")]',
            '    OR --> D[("🎯 DECIDE<br/>Metacognition Agent")]',
            '    D --> A[("⚡ ACT<br/>Tool Execution")]',
            "    A --> O",
            "",
            "    %% Style",
            "    style O fill:#e3f2fd,stroke:#1976d2",
            "    style OR fill:#fff3e0,stroke:#f57c00",
            "    style D fill:#f3e5f5,stroke:#7b1fa2",
            "    style A fill:#e8f5e9,stroke:#388e3c",
            "",
        ]

        # Add cycle count
        lines.append(f"    %% {trace.ooda_cycles} complete cycles")

        # Add basin nodes if present
        if trace.basin_transitions:
            lines.append("")
            lines.append("    %% Active Basins")
            unique_basins = set(t.to_basin for t in trace.basin_transitions)
            for i, basin in enumerate(unique_basins):
                basin_short = basin.replace("-basin", "")
                lines.append(f'    B{i}[("{basin_short}")] -.-> OR')
                lines.append(f"    style B{i} fill:#fce4ec,stroke:#c2185b")

        return "\n".join(lines)

    def generate_json(self, trace: TrajectoryTrace) -> Dict[str, Any]:
        """Export trace as JSON for external tools."""
        return {
            "trace_id": trace.trace_id,
            "session_id": trace.session_id,
            "agent_name": trace.agent_name,
            "start_time": trace.start_time.isoformat(),
            "end_time": trace.end_time.isoformat() if trace.end_time else None,
            "ooda_cycles": trace.ooda_cycles,
            "success": trace.success,
            "error_message": trace.error_message,
            "calls": [
                {
                    "agent_name": c.agent_name,
                    "step_number": c.step_number,
                    "tool_name": c.tool_name,
                    "tool_args": c.tool_args,
                    "observation": c.observation,
                    "duration_ms": c.duration_ms,
                    "ooda_phase": c.ooda_phase.value,
                }
                for c in trace.calls
            ],
            "basin_transitions": [
                {
                    "from_basin": t.from_basin,
                    "to_basin": t.to_basin,
                    "trigger": t.trigger,
                    "strength": t.strength,
                    "at_step": t.at_step,
                }
                for t in trace.basin_transitions
            ],
        }

    def generate_html(self, trace: TrajectoryTrace) -> str:
        """
        Generate standalone HTML viewer with Mermaid diagram.

        Includes Mermaid.js CDN for rendering.
        """
        mermaid_code = self.generate_mermaid(trace)
        ooda_code = self.generate_ooda_mermaid(trace)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trajectory Trace: {trace.trace_id}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #333;
        }}
        .metadata {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .metadata dt {{
            font-weight: bold;
            color: #666;
        }}
        .metadata dd {{
            margin: 0 0 10px 0;
        }}
        .diagram-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}
        h2 {{
            margin-top: 0;
            color: #555;
        }}
        .success {{
            color: #388e3c;
        }}
        .failure {{
            color: #d32f2f;
        }}
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }}
        .tab {{
            padding: 8px 16px;
            background: #e0e0e0;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        .tab.active {{
            background: #1976d2;
            color: white;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Trajectory Trace</h1>

        <div class="metadata">
            <dl>
                <dt>Trace ID</dt>
                <dd><code>{trace.trace_id}</code></dd>
                <dt>Agent</dt>
                <dd>{trace.agent_name}</dd>
                <dt>Start Time</dt>
                <dd>{trace.start_time.isoformat()}</dd>
                <dt>OODA Cycles</dt>
                <dd>{trace.ooda_cycles}</dd>
                <dt>Status</dt>
                <dd class="{'success' if trace.success else 'failure'}">
                    {'✅ Success' if trace.success else f'❌ Failed: {trace.error_message}'}
                </dd>
            </dl>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="showTab('sequence')">Sequence Diagram</button>
            <button class="tab" onclick="showTab('ooda')">OODA Loop</button>
        </div>

        <div id="sequence" class="diagram-container tab-content active">
            <h2>📊 Execution Sequence</h2>
            <pre class="mermaid">
{mermaid_code}
            </pre>
        </div>

        <div id="ooda" class="diagram-container tab-content">
            <h2>🔄 OODA Decision Loop</h2>
            <pre class="mermaid">
{ooda_code}
            </pre>
        </div>
    </div>

    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});

        function showTab(tabId) {{
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelector(`[onclick="showTab('${{tabId}}')"]`).classList.add('active');
            document.getElementById(tabId).classList.add('active');
            mermaid.init(undefined, document.querySelectorAll('.mermaid'));
        }}
    </script>
</body>
</html>"""
        return html

    async def get_trace_from_execution(self, trace_id: str) -> Optional[TrajectoryTrace]:
        """
        Load a trajectory trace from ExecutionTraceService.

        Converts execution trace to trajectory format.
        """
        try:
            from api.services.execution_trace_service import get_execution_trace_service

            service = get_execution_trace_service()
            exec_trace = await service.get_trace(trace_id)

            if not exec_trace:
                return None

            # Convert execution trace to trajectory trace
            trace = TrajectoryTrace(
                trace_id=trace_id,
                session_id=exec_trace.get("run_id", "unknown"),
                agent_name=exec_trace.get("agent_name", "unknown"),
                start_time=datetime.fromisoformat(exec_trace["start_time"]) if exec_trace.get("start_time") else datetime.utcnow(),
                end_time=datetime.fromisoformat(exec_trace["end_time"]) if exec_trace.get("end_time") else None,
                success=exec_trace.get("success", True),
                error_message=exec_trace.get("error_message"),
            )

            # Convert steps to calls
            steps = exec_trace.get("steps", [])
            for step in steps:
                call = AgentCall(
                    agent_name=exec_trace.get("agent_name", "unknown"),
                    step_number=step.get("step_number", 0),
                    tool_name=step.get("tool_name"),
                    tool_args=step.get("tool_arguments"),
                    observation=step.get("observation"),
                    ooda_phase=self._infer_ooda_phase(step),
                )
                trace.calls.append(call)

            # Convert basin links to transitions
            basins = exec_trace.get("basins", [])
            for i, basin in enumerate(basins):
                trans = BasinTransition(
                    from_basin=basins[i - 1]["basin_id"] if i > 0 else None,
                    to_basin=basin["basin_id"],
                    trigger="semantic_recall",
                    strength=basin.get("strength", 1.0),
                    at_step=basin.get("at_step", 0),
                )
                trace.basin_transitions.append(trans)

            # Count OODA cycles (4 phases = 1 cycle)
            trace.ooda_cycles = len(trace.calls) // 4

            return trace

        except Exception as e:
            logger.error(f"Failed to load trace {trace_id}: {e}")
            return None

    def _infer_ooda_phase(self, step: Dict[str, Any]) -> OODAPhase:
        """Infer OODA phase from step data."""
        tool_name = step.get("tool_name", "")
        step_type = step.get("step_type", "")

        if step_type == "PlanningStep":
            return OODAPhase.DECIDE

        # Map tools to phases
        observe_tools = ["semantic_recall", "get_context", "read_file"]
        orient_tools = ["analyze", "reason", "compare"]
        decide_tools = ["plan", "select", "choose"]

        if any(t in tool_name.lower() for t in observe_tools):
            return OODAPhase.OBSERVE
        elif any(t in tool_name.lower() for t in orient_tools):
            return OODAPhase.ORIENT
        elif any(t in tool_name.lower() for t in decide_tools):
            return OODAPhase.DECIDE
        else:
            return OODAPhase.ACT


# Singleton instance
_service: Optional[TrajectoryVisualizationService] = None


def get_trajectory_viz_service() -> TrajectoryVisualizationService:
    """Get or create the trajectory visualization service."""
    global _service
    if _service is None:
        _service = TrajectoryVisualizationService()
    return _service
