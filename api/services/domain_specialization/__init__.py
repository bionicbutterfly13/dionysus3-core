"""
Domain Specialization Service Package.

Provides neuroscience/AI domain specialization capabilities:
- Terminology databases for neuroscience and AI
- Cross-domain concept mapping
- Academic structure recognition
- Domain-specific prompt generation

Migrated from Dionysus 2.0 domain_specialization.py.
"""

from .neuroscience_db import NeuroscienceTerminologyDatabase
from .ai_db import AITerminologyDatabase
from .cross_domain_mapper import CrossDomainMapper
from .academic_structure import AcademicStructureRecognizer
from .service import (
    DomainSpecializationService,
    DomainSpecificPromptGenerator,
    get_domain_specialization_service,
)

__all__ = [
    "NeuroscienceTerminologyDatabase",
    "AITerminologyDatabase",
    "CrossDomainMapper",
    "AcademicStructureRecognizer",
    "DomainSpecializationService",
    "DomainSpecificPromptGenerator",
    "get_domain_specialization_service",
]
