"""
Meta-Learning Document Enhancer Service
Feature: D2 Migration - Meta-Learning Document Enhancer

Service for extracting meta-learning patterns and algorithms
from documents, with consciousness enhancement detection.

Migrated from D2 meta_learning_document_enhancer.py
"""

import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from api.models.meta_learning import (
    ConsciousnessEnhancementSignal,
    MetaLearningAlgorithm,
    MetaLearningConfig,
    MetaLearningExtraction,
    MetaLearningPaperType,
    MetaLearningPattern,
    MetaLearningProcessingResult,
    PatternLibrary,
)

logger = logging.getLogger(__name__)


class MetaLearningEnhancer:
    """
    Enhances document processing through meta-learning.

    Extracts meta-learning algorithms, learns patterns from documents,
    and detects consciousness-relevant content for system enhancement.

    Migrated from D2 MetaLearningDocumentEnhancer class.
    """

    # Paper type keywords for classification
    PAPER_TYPE_KEYWORDS: Dict[MetaLearningPaperType, List[str]] = {
        MetaLearningPaperType.LEARNING_TO_LEARN: [
            "meta-learning", "learning to learn", "meta learner",
            "task-agnostic", "meta-train", "meta-test"
        ],
        MetaLearningPaperType.FEW_SHOT: [
            "few-shot", "k-shot", "n-way", "episodic", "support set",
            "query set", "prototypical", "matching network"
        ],
        MetaLearningPaperType.ZERO_SHOT: [
            "zero-shot", "zero shot", "unseen class", "attribute-based",
            "semantic embedding", "cross-modal"
        ],
        MetaLearningPaperType.TRANSFER_LEARNING: [
            "transfer learning", "domain adaptation", "fine-tuning",
            "pre-training", "feature extraction", "domain shift"
        ],
        MetaLearningPaperType.NEURAL_ARCHITECTURE_SEARCH: [
            "neural architecture search", "nas", "automl", "architecture search",
            "cell search", "darts", "enas"
        ],
        MetaLearningPaperType.HYPERPARAMETER_OPTIMIZATION: [
            "hyperparameter", "bayesian optimization", "random search",
            "grid search", "hyperband", "learning rate schedule"
        ],
        MetaLearningPaperType.KNOWLEDGE_DISTILLATION: [
            "knowledge distillation", "teacher-student", "soft labels",
            "dark knowledge", "model compression", "hint learning"
        ],
        MetaLearningPaperType.CURRICULUM_LEARNING: [
            "curriculum learning", "self-paced", "difficulty ordering",
            "sample weighting", "learning progression"
        ],
        MetaLearningPaperType.SELF_SUPERVISED: [
            "self-supervised", "contrastive", "pretext task", "ssl",
            "representation learning", "masked", "autoencoder"
        ],
        MetaLearningPaperType.CONTINUAL_LEARNING: [
            "continual learning", "lifelong learning", "catastrophic forgetting",
            "elastic weight", "rehearsal", "progressive neural"
        ],
    }

    # Algorithm patterns for extraction
    ALGORITHM_PATTERNS: Dict[str, Dict[str, Any]] = {
        "MAML": {
            "keywords": ["maml", "model-agnostic meta-learning"],
            "type": MetaLearningPaperType.LEARNING_TO_LEARN,
            "consciousness_relevance": 0.7,
        },
        "Reptile": {
            "keywords": ["reptile", "first-order meta-learning"],
            "type": MetaLearningPaperType.LEARNING_TO_LEARN,
            "consciousness_relevance": 0.6,
        },
        "ProtoNet": {
            "keywords": ["prototypical network", "protonet", "prototype"],
            "type": MetaLearningPaperType.FEW_SHOT,
            "consciousness_relevance": 0.5,
        },
        "MatchingNet": {
            "keywords": ["matching network", "attention kernel"],
            "type": MetaLearningPaperType.FEW_SHOT,
            "consciousness_relevance": 0.4,
        },
        "RelationNet": {
            "keywords": ["relation network", "relational reasoning"],
            "type": MetaLearningPaperType.FEW_SHOT,
            "consciousness_relevance": 0.5,
        },
        "BERT": {
            "keywords": ["bert", "bidirectional encoder"],
            "type": MetaLearningPaperType.SELF_SUPERVISED,
            "consciousness_relevance": 0.3,
        },
        "GPT": {
            "keywords": ["gpt", "generative pre-training", "autoregressive"],
            "type": MetaLearningPaperType.SELF_SUPERVISED,
            "consciousness_relevance": 0.4,
        },
        "Transformer": {
            "keywords": ["transformer", "attention mechanism", "self-attention"],
            "type": MetaLearningPaperType.GENERAL,
            "consciousness_relevance": 0.5,
        },
        "EWC": {
            "keywords": ["elastic weight consolidation", "ewc"],
            "type": MetaLearningPaperType.CONTINUAL_LEARNING,
            "consciousness_relevance": 0.8,
        },
        "ActiveInference": {
            "keywords": ["active inference", "free energy", "variational"],
            "type": MetaLearningPaperType.LEARNING_TO_LEARN,
            "consciousness_relevance": 1.0,
        },
    }

    # Consciousness-relevant keywords
    CONSCIOUSNESS_KEYWORDS: Dict[str, float] = {
        # High relevance (0.8-1.0)
        "consciousness": 1.0,
        "self-awareness": 1.0,
        "metacognition": 0.95,
        "active inference": 0.95,
        "free energy": 0.9,
        "markov blanket": 0.9,
        "autopoiesis": 0.9,
        "self-model": 0.85,
        "introspection": 0.85,
        "phenomenal": 0.8,
        "qualia": 0.8,

        # Medium relevance (0.5-0.8)
        "attention": 0.7,
        "working memory": 0.7,
        "global workspace": 0.75,
        "predictive coding": 0.75,
        "prediction error": 0.7,
        "uncertainty": 0.6,
        "belief update": 0.65,
        "inference": 0.5,
        "learning": 0.5,

        # Lower relevance (0.3-0.5)
        "representation": 0.4,
        "embedding": 0.35,
        "feature": 0.3,
        "optimization": 0.3,
    }

    def __init__(self, config: Optional[MetaLearningConfig] = None):
        """Initialize the meta-learning enhancer.

        Args:
            config: Configuration settings. Uses defaults if not provided.
        """
        self.config = config or MetaLearningConfig()
        self.pattern_library = PatternLibrary()
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._compile_patterns()
        logger.info("MetaLearningEnhancer initialized")

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for efficiency."""
        for algo_name, algo_info in self.ALGORITHM_PATTERNS.items():
            pattern_str = "|".join(
                re.escape(kw) for kw in algo_info["keywords"]
            )
            self._compiled_patterns[algo_name] = re.compile(
                pattern_str, re.IGNORECASE
            )

    async def process_document(
        self,
        document_id: str,
        content: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MetaLearningProcessingResult:
        """
        Process a document through meta-learning enhancement.

        Args:
            document_id: Unique identifier for the document
            content: Document text content
            title: Optional document title
            metadata: Optional additional metadata

        Returns:
            MetaLearningProcessingResult with extraction and recommendations
        """
        start_time = time.time()

        try:
            # 1. Classify paper type
            paper_type, type_confidence = self._classify_paper_type(content)

            # 2. Extract algorithms
            algorithms = self._extract_algorithms(content)

            # 3. Extract patterns (if enabled)
            patterns = []
            if self.config.enable_pattern_learning:
                patterns = self._extract_patterns(content, document_id)

            # 4. Detect consciousness signals (if enabled)
            consciousness_signals = []
            if self.config.enable_consciousness_enhancement:
                consciousness_signals = self._detect_consciousness_signals(content)

            # 5. Extract key concepts
            key_concepts = self._extract_key_concepts(content)

            # 6. Calculate quality metrics
            extraction_quality = self._calculate_extraction_quality(
                algorithms, patterns, consciousness_signals
            )
            consciousness_potential = self._calculate_consciousness_potential(
                consciousness_signals, algorithms
            )

            # 7. Create extraction
            processing_time_ms = (time.time() - start_time) * 1000
            extraction = MetaLearningExtraction(
                document_id=document_id,
                document_title=title,
                paper_type=paper_type,
                paper_type_confidence=type_confidence,
                algorithms=algorithms,
                patterns=patterns,
                consciousness_signals=consciousness_signals,
                key_concepts=key_concepts,
                domain_tags=self._infer_domain_tags(content, paper_type),
                extraction_quality=extraction_quality,
                consciousness_enhancement_potential=consciousness_potential,
                processing_time_ms=processing_time_ms
            )

            # 8. Generate recommendations
            recommendations = self._generate_recommendations(extraction)
            related_basins = self._suggest_related_basins(extraction)
            suggested_thoughtseeds = self._suggest_thoughtseeds(extraction)

            # 9. Learn patterns for future use
            patterns_learned = 0
            patterns_reinforced = 0
            for pattern in patterns:
                if pattern.pattern_id in self.pattern_library.patterns:
                    patterns_reinforced += 1
                else:
                    patterns_learned += 1
                self.pattern_library.add_pattern(pattern)

            # 10. Suggest Graphiti entities
            graphiti_entities = self._suggest_graphiti_entities(extraction)

            return MetaLearningProcessingResult(
                extraction=extraction,
                success=True,
                enhancement_recommendations=recommendations,
                related_basins=related_basins,
                suggested_thoughtseeds=suggested_thoughtseeds,
                patterns_learned=patterns_learned,
                patterns_reinforced=patterns_reinforced,
                graphiti_entities_suggested=graphiti_entities
            )

        except Exception as e:
            logger.exception(f"Error processing document {document_id}: {e}")
            # Return error result
            extraction = MetaLearningExtraction(
                document_id=document_id,
                document_title=title,
                paper_type=MetaLearningPaperType.UNKNOWN
            )
            return MetaLearningProcessingResult(
                extraction=extraction,
                success=False,
                error_message=str(e)
            )

    def _classify_paper_type(
        self,
        content: str
    ) -> Tuple[MetaLearningPaperType, float]:
        """Classify document by meta-learning paper type."""
        content_lower = content.lower()
        scores: Dict[MetaLearningPaperType, float] = {}

        for paper_type, keywords in self.PAPER_TYPE_KEYWORDS.items():
            score = 0.0
            for keyword in keywords:
                count = content_lower.count(keyword.lower())
                if count > 0:
                    # Diminishing returns for repeated keywords
                    score += min(count * 0.1, 0.5)
            scores[paper_type] = score

        if not scores or max(scores.values()) == 0:
            return MetaLearningPaperType.GENERAL, 0.3

        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]

        # Normalize confidence
        confidence = min(1.0, best_score / 2.0)

        if confidence < 0.2:
            return MetaLearningPaperType.GENERAL, 0.4

        return best_type, confidence

    def _extract_algorithms(self, content: str) -> List[MetaLearningAlgorithm]:
        """Extract meta-learning algorithms from content."""
        algorithms = []

        for algo_name, pattern in self._compiled_patterns.items():
            if pattern.search(content):
                algo_info = self.ALGORITHM_PATTERNS[algo_name]
                algorithms.append(MetaLearningAlgorithm(
                    name=algo_name,
                    description=f"Detected {algo_name} algorithm",
                    paper_type=algo_info["type"],
                    consciousness_relevance=algo_info["consciousness_relevance"]
                ))

        return algorithms

    def _extract_patterns(
        self,
        content: str,
        document_id: str
    ) -> List[MetaLearningPattern]:
        """Extract learnable patterns from content."""
        patterns = []
        content_lower = content.lower()

        # Pattern: Methodology sections
        if "method" in content_lower and "result" in content_lower:
            patterns.append(MetaLearningPattern(
                pattern_type="structural",
                pattern_content="Standard methodology-results structure",
                confidence=0.6,
                source_documents=[document_id],
                transferability=0.8,
                domain_specificity=0.2
            ))

        # Pattern: Multi-step reasoning
        step_indicators = ["first", "then", "next", "finally", "step"]
        step_count = sum(content_lower.count(ind) for ind in step_indicators)
        if step_count > 5:
            patterns.append(MetaLearningPattern(
                pattern_type="conceptual",
                pattern_content="Multi-step reasoning structure",
                confidence=min(0.9, 0.5 + step_count * 0.05),
                source_documents=[document_id],
                transferability=0.7,
                domain_specificity=0.3
            ))

        # Pattern: Comparative analysis
        comparison_indicators = ["compared to", "versus", "outperforms", "baseline"]
        if any(ind in content_lower for ind in comparison_indicators):
            patterns.append(MetaLearningPattern(
                pattern_type="analytical",
                pattern_content="Comparative analysis pattern",
                confidence=0.65,
                source_documents=[document_id],
                transferability=0.75,
                domain_specificity=0.4
            ))

        # Limit patterns per document
        return patterns[:self.config.max_patterns_per_document]

    def _detect_consciousness_signals(
        self,
        content: str
    ) -> List[ConsciousnessEnhancementSignal]:
        """Detect consciousness-relevant signals in content."""
        signals = []
        content_lower = content.lower()

        for keyword, base_strength in self.CONSCIOUSNESS_KEYWORDS.items():
            if keyword in content_lower:
                # Find context around keyword
                idx = content_lower.index(keyword)
                start = max(0, idx - 50)
                end = min(len(content), idx + len(keyword) + 50)
                source_span = content[start:end]

                # Determine signal type
                if keyword in ["consciousness", "self-awareness", "phenomenal", "qualia"]:
                    signal_type = "phenomenal_consciousness"
                elif keyword in ["metacognition", "introspection", "self-model"]:
                    signal_type = "metacognitive"
                elif keyword in ["active inference", "free energy", "markov blanket"]:
                    signal_type = "active_inference"
                elif keyword in ["attention", "working memory", "global workspace"]:
                    signal_type = "global_workspace"
                else:
                    signal_type = "general_consciousness"

                # Calculate relevance scores
                metacog_relevance = 0.8 if signal_type == "metacognitive" else 0.3
                self_model_relevance = 0.7 if "self" in keyword else 0.2
                active_inf_relevance = 0.9 if signal_type == "active_inference" else 0.2

                signals.append(ConsciousnessEnhancementSignal(
                    signal_type=signal_type,
                    strength=base_strength,
                    source_span=source_span.strip(),
                    metacognitive_relevance=metacog_relevance,
                    self_model_relevance=self_model_relevance,
                    active_inference_relevance=active_inf_relevance
                ))

        # Filter by threshold and deduplicate by type
        signals = [
            s for s in signals
            if s.strength >= self.config.consciousness_signal_threshold
        ]

        # Keep strongest signal per type
        seen_types: Set[str] = set()
        unique_signals = []
        for signal in sorted(signals, key=lambda s: s.strength, reverse=True):
            if signal.signal_type not in seen_types:
                seen_types.add(signal.signal_type)
                unique_signals.append(signal)

        return unique_signals

    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content."""
        concepts = []
        content_lower = content.lower()

        # Check for meta-learning concepts
        meta_concepts = [
            "meta-learning", "transfer", "few-shot", "zero-shot",
            "attention", "transformer", "embedding", "representation",
            "optimization", "gradient", "loss function", "architecture"
        ]

        for concept in meta_concepts:
            if concept in content_lower:
                concepts.append(concept)

        # Check for consciousness concepts
        for keyword in self.CONSCIOUSNESS_KEYWORDS:
            if keyword in content_lower and keyword not in concepts:
                concepts.append(keyword)

        return concepts[:20]  # Limit to top 20

    def _infer_domain_tags(
        self,
        content: str,
        paper_type: MetaLearningPaperType
    ) -> List[str]:
        """Infer domain tags from content and paper type."""
        tags = [paper_type.value]

        content_lower = content.lower()

        domain_keywords = {
            "nlp": ["language", "text", "nlp", "bert", "gpt", "translation"],
            "computer_vision": ["image", "vision", "cnn", "convolution", "visual"],
            "reinforcement_learning": ["reinforcement", "reward", "policy", "agent"],
            "robotics": ["robot", "manipulation", "control", "motor"],
            "healthcare": ["medical", "clinical", "diagnosis", "patient"],
            "neuroscience": ["neural", "brain", "cognitive", "neuron"],
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in content_lower for kw in keywords):
                tags.append(domain)

        return tags

    def _calculate_extraction_quality(
        self,
        algorithms: List[MetaLearningAlgorithm],
        patterns: List[MetaLearningPattern],
        signals: List[ConsciousnessEnhancementSignal]
    ) -> float:
        """Calculate overall extraction quality."""
        # Base quality
        quality = 0.3

        # Algorithms found
        if algorithms:
            quality += min(0.3, len(algorithms) * 0.1)

        # Patterns found
        if patterns:
            avg_pattern_conf = sum(p.confidence for p in patterns) / len(patterns)
            quality += avg_pattern_conf * 0.2

        # Consciousness signals
        if signals:
            avg_signal_strength = sum(s.strength for s in signals) / len(signals)
            quality += avg_signal_strength * 0.2

        return min(1.0, quality)

    def _calculate_consciousness_potential(
        self,
        signals: List[ConsciousnessEnhancementSignal],
        algorithms: List[MetaLearningAlgorithm]
    ) -> float:
        """Calculate consciousness enhancement potential."""
        if not signals and not algorithms:
            return 0.0

        # Signal contribution
        signal_score = 0.0
        if signals:
            signal_score = sum(s.strength for s in signals) / len(signals)

        # Algorithm contribution
        algo_score = 0.0
        if algorithms:
            algo_score = sum(
                a.consciousness_relevance for a in algorithms
            ) / len(algorithms)

        # Combined score with signal priority
        return signal_score * 0.7 + algo_score * 0.3

    def _generate_recommendations(
        self,
        extraction: MetaLearningExtraction
    ) -> List[str]:
        """Generate enhancement recommendations based on extraction."""
        recommendations = []

        # Paper type recommendations
        if extraction.paper_type == MetaLearningPaperType.LEARNING_TO_LEARN:
            recommendations.append(
                "Meta-learning content - useful for task adaptation strategies"
            )
        elif extraction.paper_type == MetaLearningPaperType.CONTINUAL_LEARNING:
            recommendations.append(
                "Continual learning content - apply to memory tier management"
            )
        elif extraction.paper_type == MetaLearningPaperType.FEW_SHOT:
            recommendations.append(
                "Few-shot learning patterns - useful for rapid task adaptation"
            )

        # Consciousness potential recommendations
        if extraction.consciousness_enhancement_potential > 0.7:
            recommendations.append(
                "High consciousness enhancement potential - route to metacognition"
            )
        elif extraction.consciousness_enhancement_potential > 0.4:
            recommendations.append(
                "Moderate consciousness content - index for future reference"
            )

        # Algorithm-specific recommendations
        for algo in extraction.algorithms:
            if algo.consciousness_relevance > 0.8:
                recommendations.append(
                    f"Algorithm {algo.name} highly relevant to consciousness - integrate patterns"
                )

        return recommendations

    def _suggest_related_basins(
        self,
        extraction: MetaLearningExtraction
    ) -> List[str]:
        """Suggest related attractor basins."""
        basins = []

        # Map paper types to basins
        type_basin_map = {
            MetaLearningPaperType.LEARNING_TO_LEARN: "machine_learning",
            MetaLearningPaperType.FEW_SHOT: "machine_learning",
            MetaLearningPaperType.SELF_SUPERVISED: "machine_learning",
            MetaLearningPaperType.CONTINUAL_LEARNING: "cognitive_science",
            MetaLearningPaperType.KNOWLEDGE_DISTILLATION: "machine_learning",
        }

        if extraction.paper_type in type_basin_map:
            basins.append(type_basin_map[extraction.paper_type])

        # Check consciousness signals for basin hints
        if extraction.consciousness_signals:
            for signal in extraction.consciousness_signals:
                if signal.signal_type == "active_inference":
                    basins.append("consciousness")
                elif signal.signal_type == "metacognitive":
                    basins.append("cognitive_science")
                elif signal.signal_type == "phenomenal_consciousness":
                    basins.append("philosophy")

        return list(set(basins))

    def _suggest_thoughtseeds(
        self,
        extraction: MetaLearningExtraction
    ) -> List[str]:
        """Suggest ThoughtSeed activations based on extraction."""
        thoughtseeds = []

        # High consciousness potential -> metacognition thoughtseed
        if extraction.consciousness_enhancement_potential > 0.6:
            thoughtseeds.append("metacognition_enhancement")

        # Multiple algorithms -> synthesis thoughtseed
        if len(extraction.algorithms) > 2:
            thoughtseeds.append("algorithmic_synthesis")

        # Pattern learning -> pattern recognition thoughtseed
        if extraction.patterns:
            thoughtseeds.append("pattern_recognition")

        # Active inference content -> free energy thoughtseed
        for signal in extraction.consciousness_signals:
            if signal.signal_type == "active_inference":
                thoughtseeds.append("free_energy_minimization")
                break

        return thoughtseeds

    def _suggest_graphiti_entities(
        self,
        extraction: MetaLearningExtraction
    ) -> List[str]:
        """Suggest entities for Graphiti storage."""
        entities = []

        # Algorithms as entities
        for algo in extraction.algorithms:
            entities.append(f"Algorithm:{algo.name}")

        # Key concepts as entities
        for concept in extraction.key_concepts[:10]:
            entities.append(f"Concept:{concept}")

        # Paper type as entity
        entities.append(f"PaperType:{extraction.paper_type.value}")

        return entities

    def get_pattern_library_stats(self) -> Dict[str, Any]:
        """Get statistics about the learned pattern library."""
        library = self.pattern_library
        return {
            "total_patterns": len(library.patterns),
            "total_documents_processed": library.total_documents_processed,
            "high_confidence_count": len(
                library.get_high_confidence_patterns(threshold=0.7)
            ),
            "high_transferability_count": len(
                library.get_transferable_patterns(threshold=0.7)
            ),
            "last_updated": library.last_updated.isoformat(),
        }

    def get_high_value_patterns(
        self,
        limit: int = 10
    ) -> List[MetaLearningPattern]:
        """Get patterns with both high confidence and transferability."""
        patterns = list(self.pattern_library.patterns.values())
        scored = [
            (p, p.confidence * 0.6 + p.transferability * 0.4)
            for p in patterns
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in scored[:limit]]


# Singleton instance
_enhancer_instance: Optional[MetaLearningEnhancer] = None


async def get_meta_learning_enhancer(
    config: Optional[MetaLearningConfig] = None
) -> MetaLearningEnhancer:
    """Get or create singleton MetaLearningEnhancer instance.

    Args:
        config: Optional configuration. Only used on first call.

    Returns:
        MetaLearningEnhancer singleton instance
    """
    global _enhancer_instance
    if _enhancer_instance is None:
        _enhancer_instance = MetaLearningEnhancer(config)
    return _enhancer_instance


# Convenience function for direct processing
async def enhance_document(
    document_id: str,
    content: str,
    title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> MetaLearningProcessingResult:
    """Process a document through meta-learning enhancement.

    Convenience function that uses the singleton enhancer.

    Args:
        document_id: Unique identifier for the document
        content: Document text content
        title: Optional document title
        metadata: Optional additional metadata

    Returns:
        MetaLearningProcessingResult with extraction and recommendations
    """
    enhancer = await get_meta_learning_enhancer()
    return await enhancer.process_document(
        document_id=document_id,
        content=content,
        title=title,
        metadata=metadata
    )
