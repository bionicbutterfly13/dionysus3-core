from typing import List, Dict, Any
import os

class RelatioNarrativeService:
    """
    Service for extracting structured narrative roles (Agent-Verb-Patient) 
    from unstructured text.
    
    Originally planned to use 'relatio' library, but due to dependency conflicts 
    (torch versions), this service now implements SVO extraction natively using Spacy.
    
    This enhances Nemori's semantic layer by providing causal structure 
    (Who did what to whom) rather than just thematic embeddings.
    """
    
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """
        Initialize the narrative extractor.
        
        Args:
            spacy_model: The spaCy model to use for dependency parsing.
        """
        if os.getenv("DIONYSUS_DISABLE_SPACY", "").lower() in ("1", "true", "yes"):
            self.nlp = None
            return

        import spacy

        # Ensure spacy model is downloaded (handled in Dockerfile ideally, but check here)
        if not spacy.util.is_package(spacy_model):
            spacy.cli.download(spacy_model)

        self.nlp = spacy.load(spacy_model)
        
    def extract_svo_triplets(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract Subject-Verb-Object triplets from text using native Spacy dependency parsing.
        
        Args:
            text: Unstructured narrative text.
            
        Returns:
            List of dictionaries containing 'subject', 'verb', 'object'.
        """
        if not text.strip():
            return []
            
        if not self.nlp:
            return []

        doc = self.nlp(text)
        triplets = []
        
        # Iterate over tokens to find verbs
        for token in doc:
            if token.pos_ == "VERB":
                subject = None
                obj = None
                
                # Check children for nsubj (subject) and dobj (object)
                for child in token.children:
                    if child.dep_ in ("nsubj", "nsubjpass"):
                        subject = child.text
                    if child.dep_ in ("dobj", "attr", "acomp"):
                        obj = child.text
                        
                if subject and obj:
                    triplets.append({
                        "agent": subject,
                        "action": token.text,
                        "patient": obj
                    })
                    
        return triplets

    def cluster_entities(self, triplets: List[Dict]) -> Dict[str, Any]:
        """
        Cluster the extracted entities to find common 'Roles' (e.g., 'The Hero', 'The Villain').
        
        Args:
            triplets: List of SVO dictionaries (Agent-Action-Patient).
            
        Returns:
             Dictionary of clustered roles.
        """
        if not triplets:
            return {}
            
        # To cluster, we need to extract vectors for the agents/patients.
        # Relatio's NarrativeModel usually does this on a corpus.
        # For a single stream, we might accumulate or just return the raw roles.
        
        # Simplified: We just return the unique agents and patients for now,
        # as true clustering requires a fitted model on a larger dataset.
        
        agents = list(set([t['agent'] for t in triplets]))
        patients = list(set([t['patient'] for t in triplets]))
        actions = list(set([t['action'] for t in triplets]))
        
        return {
            "agents": agents,
            "patients": patients,
            "actions": actions,
            "narrative_count": len(triplets)
        }
