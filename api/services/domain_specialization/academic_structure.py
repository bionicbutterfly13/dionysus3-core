"""
Academic Structure Recognizer.

Recognizes and analyzes academic paper structure,
detecting sections, citations, and quality metrics.

Migrated from Dionysus 2.0 domain_specialization.py.
"""

import logging
import re
from typing import Any

from api.models.domain_specialization import (
    AcademicSection,
    AcademicStructure,
    Citation,
    SectionInfo,
)

logger = logging.getLogger(__name__)


class AcademicStructureRecognizer:
    """Recognizes and analyzes academic paper structure."""

    def __init__(self):
        self.section_patterns: dict[AcademicSection, list[str]] = {
            AcademicSection.ABSTRACT: [r"\babstract\b", r"\bsummary\b"],
            AcademicSection.INTRODUCTION: [
                r"\bintroduction\b",
                r"\b1\.\s*introduction\b",
                r"\bbackground\b",
            ],
            AcademicSection.METHODS: [
                r"\bmethods?\b",
                r"\bmethodology\b",
                r"\bexperimental\s+design\b",
                r"\bprocedure\b",
            ],
            AcademicSection.RESULTS: [
                r"\bresults?\b",
                r"\bfindings?\b",
                r"\banalysis\b",
            ],
            AcademicSection.DISCUSSION: [r"\bdiscussion\b", r"\binterpretation\b"],
            AcademicSection.CONCLUSION: [
                r"\bconclusions?\b",
                r"\bsummary\b",
                r"\bimplications?\b",
            ],
            AcademicSection.REFERENCES: [
                r"\breferences?\b",
                r"\bbibliography\b",
                r"\bcitations?\b",
            ],
        }

        self.citation_patterns = [
            r"\([^)]*\d{4}[^)]*\)",  # (Author, 2024)
            r"\[[^\]]*\d+[^\]]*\]",  # [1], [Author et al.]
            r"\b[A-Z][a-z]+\s+et\s+al\.\s+\(\d{4}\)",  # Smith et al. (2024)
            r"\b[A-Z][a-z]+\s+\(\d{4}\)",  # Smith (2024)
        ]

    def analyze_structure(self, text: str) -> AcademicStructure:
        """Analyze academic structure of text."""
        structure = AcademicStructure()

        # Detect sections
        detected_sections: dict[str, SectionInfo] = {}
        text_lower = text.lower()

        for section, patterns in self.section_patterns.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, text_lower, re.IGNORECASE))
                if matches:
                    match = matches[0]  # Take first match
                    if section.value not in detected_sections:
                        detected_sections[section.value] = SectionInfo(
                            found=True,
                            position=match.start(),
                            text=match.group(),
                            confidence=0.8,
                        )
                    break

        structure.detected_sections = detected_sections

        # Check for key academic elements
        structure.abstract_present = AcademicSection.ABSTRACT.value in detected_sections
        structure.methodology_described = (
            AcademicSection.METHODS.value in detected_sections
        )
        structure.results_reported = AcademicSection.RESULTS.value in detected_sections

        # Find citations
        structure.citations_found = self._extract_citations(text)

        # Calculate quality metrics
        structure.structure_completeness = len(detected_sections) / len(
            AcademicSection
        )
        structure.academic_rigor_score = self._calculate_rigor_score(structure)

        return structure

    def _extract_citations(self, text: str) -> list[Citation]:
        """Extract citations from text."""
        citations = []

        for pattern in self.citation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                citation = Citation(
                    raw_text=match.group(),
                    citation_type="in_text",
                )

                # Try to extract year
                year_match = re.search(r"\b(19|20)\d{2}\b", citation.raw_text)
                if year_match:
                    citation.year = int(year_match.group())

                citations.append(citation)

        return citations[:20]  # Limit to prevent overflow

    def _calculate_rigor_score(self, structure: AcademicStructure) -> float:
        """Calculate academic rigor score."""
        score = 0.0

        # Section completeness (40%)
        score += structure.structure_completeness * 0.4

        # Citations present (30%)
        if structure.citations_found:
            citation_score = min(1.0, len(structure.citations_found) / 10)
            score += citation_score * 0.3

        # Methodology described (20%)
        if structure.methodology_described:
            score += 0.2

        # Results reported (10%)
        if structure.results_reported:
            score += 0.1

        return score

    def get_section_content(
        self, text: str, section: AcademicSection
    ) -> tuple[str, int, int]:
        """Extract content of a specific section.

        Returns:
            Tuple of (content, start_position, end_position)
        """
        text_lower = text.lower()

        # Find section start
        start_pos = -1
        for pattern in self.section_patterns.get(section, []):
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                start_pos = match.start()
                break

        if start_pos == -1:
            return "", -1, -1

        # Find next section (to determine end)
        next_section_pos = len(text)
        all_positions = []

        for other_section, patterns in self.section_patterns.items():
            if other_section == section:
                continue
            for pattern in patterns:
                match = re.search(pattern, text_lower[start_pos + 1 :], re.IGNORECASE)
                if match:
                    all_positions.append(start_pos + 1 + match.start())
                    break

        if all_positions:
            next_section_pos = min(all_positions)

        content = text[start_pos:next_section_pos].strip()
        return content, start_pos, next_section_pos

    def detect_document_type(self, text: str) -> str:
        """Detect the type of academic document."""
        structure = self.analyze_structure(text)
        sections = set(structure.detected_sections.keys())

        # Research paper: has methods and results
        if (
            AcademicSection.METHODS.value in sections
            and AcademicSection.RESULTS.value in sections
        ):
            return "research_paper"

        # Review paper: has background/introduction, no methods
        if (
            AcademicSection.INTRODUCTION.value in sections
            and AcademicSection.METHODS.value not in sections
            and len(structure.citations_found) > 10
        ):
            return "review_paper"

        # Technical report: has methods but informal structure
        if AcademicSection.METHODS.value in sections:
            return "technical_report"

        # Essay/commentary: introduction and discussion
        if (
            AcademicSection.INTRODUCTION.value in sections
            and AcademicSection.DISCUSSION.value in sections
        ):
            return "commentary"

        return "general_document"

    def assess_completeness(self, text: str) -> dict[str, Any]:
        """Assess completeness of academic document.

        Returns dict with:
        - present_sections: list of detected sections
        - missing_sections: list of missing standard sections
        - completeness_score: 0-1 score
        - recommendations: suggestions for improvement
        """
        structure = self.analyze_structure(text)
        present = set(structure.detected_sections.keys())

        # Standard academic sections
        standard_sections = {
            AcademicSection.ABSTRACT.value,
            AcademicSection.INTRODUCTION.value,
            AcademicSection.METHODS.value,
            AcademicSection.RESULTS.value,
            AcademicSection.DISCUSSION.value,
            AcademicSection.CONCLUSION.value,
            AcademicSection.REFERENCES.value,
        }

        missing = standard_sections - present
        completeness = len(present & standard_sections) / len(standard_sections)

        recommendations = []
        if AcademicSection.ABSTRACT.value in missing:
            recommendations.append("Add an abstract summarizing the work")
        if AcademicSection.METHODS.value in missing:
            recommendations.append("Add a methods section describing your approach")
        if AcademicSection.REFERENCES.value in missing:
            recommendations.append("Add a references section with citations")
        if len(structure.citations_found) < 5:
            recommendations.append("Consider adding more citations to support claims")

        return {
            "present_sections": list(present),
            "missing_sections": list(missing),
            "completeness_score": completeness,
            "recommendations": recommendations,
            "citation_count": len(structure.citations_found),
        }
