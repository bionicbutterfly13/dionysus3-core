"""
Documentation Agent

Paired agent that ensures all repairs have corresponding documentation updates.
Updates docstrings, README sections, and creates migration notes.
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from datetime import datetime


class DocumentationAgent:
    """
    Documentation agent that accompanies repair agents.

    Responsibilities:
    - Update docstrings for changed functions
    - Update README if architectural changes
    - Create migration notes for breaking changes
    - Log all documentation changes
    """

    name = "documentation_agent"

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.changes_log: List[dict] = []

    async def document_repair(
        self,
        repair_description: str,
        file_path: str,
        repair_type: str
    ) -> Tuple[bool, str]:
        """
        Document a repair that was made.

        Args:
            repair_description: What was repaired
            file_path: File that was repaired
            repair_type: Type of repair (promise, orphan, doc)

        Returns:
            Tuple of (success, description)
        """
        self.changes_log.append({
            "timestamp": datetime.now().isoformat(),
            "file": file_path,
            "repair_type": repair_type,
            "description": repair_description,
        })

        # For now, just log the change
        # In a full implementation, this would:
        # 1. Update function docstrings if signature changed
        # 2. Update README if exports changed
        # 3. Create CHANGELOG entry

        return True, f"Documented repair: {repair_description}"

    async def generate_repair_summary(self) -> str:
        """Generate a summary of all repairs for commit message."""
        if not self.changes_log:
            return "No repairs documented"

        summary_lines = ["QA Sweep Repairs:"]

        by_type: Dict[str, List[str]] = {}
        for change in self.changes_log:
            repair_type = change["repair_type"]
            if repair_type not in by_type:
                by_type[repair_type] = []
            by_type[repair_type].append(change["description"])

        for repair_type, descriptions in by_type.items():
            summary_lines.append(f"\n{repair_type.title()} repairs:")
            for desc in descriptions[:5]:  # Limit to 5 per type
                summary_lines.append(f"  - {desc}")
            if len(descriptions) > 5:
                summary_lines.append(f"  - ... and {len(descriptions) - 5} more")

        return "\n".join(summary_lines)

    async def update_readme_if_needed(
        self,
        changes: List[dict]
    ) -> Tuple[bool, str]:
        """
        Update README if repairs affected documented APIs.

        Returns:
            Tuple of (updated, description)
        """
        readme_path = self.project_root / "README.md"
        if not readme_path.exists():
            return False, "No README.md found"

        # Check if any repairs affected exported/documented functions
        # This is a simplified check
        api_changes = [
            c for c in changes
            if "api/" in c.get("file", "") and c.get("repair_type") == "doc"
        ]

        if not api_changes:
            return False, "No API changes requiring README update"

        # In a full implementation, we would:
        # 1. Parse README for API documentation sections
        # 2. Update any sections that reference changed functions
        # 3. Add a note about the changes

        return False, "README update would require manual review"

    async def create_migration_note(
        self,
        breaking_changes: List[dict]
    ) -> Optional[Path]:
        """
        Create migration notes for breaking changes.

        Returns:
            Path to migration notes file if created
        """
        if not breaking_changes:
            return None

        # Create migration notes file
        migrations_dir = self.project_root / "docs" / "migrations"
        migrations_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y%m%d")
        migration_file = migrations_dir / f"migration-{date_str}-qa-sweep.md"

        content_lines = [
            f"# QA Sweep Migration Notes - {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "## Breaking Changes",
            "",
        ]

        for change in breaking_changes:
            content_lines.append(f"### {change.get('file', 'Unknown file')}")
            content_lines.append(f"- {change.get('description', 'No description')}")
            content_lines.append("")

        content_lines.extend([
            "## Migration Steps",
            "",
            "1. Review the changes listed above",
            "2. Update any code that depends on removed/modified functions",
            "3. Run tests to verify compatibility",
            "",
        ])

        migration_file.write_text("\n".join(content_lines))

        return migration_file

    def get_changes_for_commit(self) -> List[str]:
        """Get list of files changed for git add."""
        return list(set(c["file"] for c in self.changes_log))
