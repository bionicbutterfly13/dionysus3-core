"""
Journal Service

Automates the creation and updating of the 'Daily Pulse' journal entry.
Runs as a background task within the API.
"""

import logging
import asyncio
from datetime import datetime
from pathlib import Path

from api.routers.monitoring_pulse import get_daily_pulse, PulseResponse
from api.services.graphiti_service import get_graphiti_dependency

logger = logging.getLogger(__name__)

JOURNAL_DIR = Path("/app/docs/journal")
MARKER_START = "<!-- DIONYSUS-PULSE-START -->"
MARKER_END = "<!-- DIONYSUS-PULSE-END -->"

def _format_pulse_markdown(pulse: PulseResponse) -> str:
    """Format the pulse data into a SilverBullet-compatible markdown section."""
    
    # Git Section
    git_section = ""
    if pulse.git_commits:
        git_section = "\n".join([
            f"*   **{c.message}** (__{c.author}__)\n    *   Files: `{', '.join(c.files_changed[:3])}{'...' if len(c.files_changed)>3 else ''}`"
            for c in pulse.git_commits
        ])
    else:
        git_section = "*   _No recent commits._"

    # Entities Section
    entities_section = ""
    if pulse.recent_entities:
        entities_section = "\n".join([
            f"*   **[[{e.name}]]** ({e.type}): {e.summary or 'No summary'}"
            for e in pulse.recent_entities
        ])
    else:
        entities_section = "*   _No new knowledge entities detected._"

    return f"""{MARKER_START}
# ⚡ System Pulse (Updated: {pulse.timestamp.strftime('%H:%M:%S UTC')})

## 🚀 Status
*   **API:** {pulse.system_status.get('api', 'Unknown')}
*   **Neo4j:** {pulse.system_status.get('neo4j', 'Unknown')}
*   **n8n:** {pulse.system_status.get('n8n', 'Unknown')}

## 💻 Code Activity
{git_section}

## 🧠 Knowledge Evolution
{entities_section}

---
## 📝 Narrative & Impact
> {pulse.narrative_summary or "System operating normally."}
{MARKER_END}"""

async def update_daily_journal():
    """
    Main entry point: Generates pulse and updates today's journal file.
    """
    try:
        logger.info("Starting Daily Journal update...")
        
        # 1. Ensure directory exists
        if not JOURNAL_DIR.exists():
            logger.warning(f"Journal directory {JOURNAL_DIR} not found. Creating...")
            JOURNAL_DIR.mkdir(parents=True, exist_ok=True)

        # 2. Get Data
        # We need to manually inject dependencies since we aren't in a request context
        try:
            graphiti = await get_graphiti_dependency()
            pulse = await get_daily_pulse(graphiti)
        except Exception as e:
            logger.error(f"Failed to fetch pulse data: {e}")
            return

        # 3. Format Content
        new_content_block = _format_pulse_markdown(pulse)
        
        # 4. Read/Update File
        today_str = datetime.now().strftime("%Y-%m-%d")
        journal_file = JOURNAL_DIR / f"{today_str}.md"
        
        file_content = ""
        if journal_file.exists():
            with open(journal_file, "r") as f:
                file_content = f.read()
        else:
            # Create new file with header
            file_content = f"# Journal: {today_str}\n\n"

        # Replace or Append
        if MARKER_START in file_content and MARKER_END in file_content:
            # Regex replacement is riskier with multiline, manual string slicing is safer here
            start_idx = file_content.find(MARKER_START)
            end_idx = file_content.find(MARKER_END) + len(MARKER_END)
            
            updated_content = (
                file_content[:start_idx] + 
                new_content_block + 
                file_content[end_idx:]
            )
        else:
            # Append to top (after title if present)
            lines = file_content.splitlines()
            if lines and lines[0].startswith("# "):
                # Insert after title
                updated_content = "\n".join(lines[:1]) + "\n\n" + new_content_block + "\n" + "\n".join(lines[1:])
            else:
                # Insert at top
                updated_content = new_content_block + "\n\n" + file_content

        # 5. Write back
        with open(journal_file, "w") as f:
            f.write(updated_content)
            
        logger.info(f"Updated journal entry: {journal_file}")

    except Exception as e:
        logger.error(f"Journal update failed: {e}")

async def start_journal_scheduler():
    """Background task to run journal updates periodically."""
    while True:
        await update_daily_journal()
        # Update every hour
        await asyncio.sleep(3600)
