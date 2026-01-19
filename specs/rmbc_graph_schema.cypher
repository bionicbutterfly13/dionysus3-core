// RMBC Graphiti Schema: The Inner Architect System
// Target Avatar: The Vigilant Sentinel
// Core Mechanism: Neuro-Adaptive Scaffolding

// 1. Define the Avatar Identity
MERGE (a:Avatar {id: "vigilant_sentinel"})
SET a.name = "The Vigilant Sentinel",
    a.iq_level = "High / Gifted",
    a.neurotype = "2e (Twice-Exceptional)",
    a.core_conflict = "Ferrari Engine / Bicycle Brakes",
    a.primary_fear = "Hollow Futility";

// 2. Define the Unique Mechanism of the Problem (UMP)
MERGE (ump:Mechanism {id: "ump_bandwidth_collapse"})
SET ump.name = "Prefrontal Bandwidth Collapse",
    ump.type = "Problem",
    ump.metaphor = "Metabolic Insolvency",
    ump.scientific_basis = "Deane et al. (Computational Unconscious)";

MERGE (def:Defense {id: "adaptive_narrative_control"})
SET def.name = "Adaptive Narrative Control",
    def.function = "Motivated Inattention",
    def.trigger = "System Overheat";

// 3. Define the Unique Mechanism of the Solution (UMS)
MERGE (ums:Mechanism {id: "ums_neuro_scaffolding"})
SET ums.name = "Neuro-Adaptive Scaffolding",
    ums.type = "Solution",
    ums.metaphor = "External Architecture / Exoskeleton",
    ums.promise = "Cognitive Sovereignty";

// 4. Define the Solution Components (The Offer Stack)
MERGE (comp1:Component {id: "exocortex"})
SET comp1.name = "The Exocortical Schematics",
    comp1.function = "Externalize Executive Function",
    comp1.format = "Notion/Obsidian Templates";

MERGE (comp2:Component {id: "vagal_safety"})
SET comp2.name = "Vagal Safety Protocols",
    comp2.function = "Restore Physiological Safety",
    comp2.format = "Audio/Kinetic Triggers";

MERGE (comp3:Component {id: "ritual_library"})
SET comp3.name = "The Ritual Library",
    comp3.function = "Bypass Willpower",
    comp3.format = "Initiation Scripts";

// 5. Establish Theoretical Relationships
MERGE (a)-[:SUFFERS_FROM]->(ump)
MERGE (a)-[:DEPLOYS_DEFENSE]->(def)
MERGE (def)-[:CONTRIBUTES_TO]->(ump)
MERGE (ums)-[:SOLVES]->(ump)
MERGE (ums)-[:COMPOSED_OF]->(comp1)
MERGE (ums)-[:COMPOSED_OF]->(comp2)
MERGE (ums)-[:COMPOSED_OF]->(comp3)

// 6. Connect to RMBC Framework Nodes (Metanodes)
MERGE (p:PainPoint {id: "2pm_fog"}) SET p.name = "The 2 PM Fog"
MERGE (p2:PainPoint {id: "masking_tax"}) SET p2.name = "The Masking Tax"

MERGE (a)-[:EXPERIENCES]->(p)
MERGE (a)-[:EXPERIENCES]->(p2)
MERGE (ump)-[:MANIFESTS_AS]->(p)
