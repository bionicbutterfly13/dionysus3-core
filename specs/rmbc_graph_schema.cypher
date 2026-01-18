// Schema for RMBC Copy Projects
// This file defines the nodes and relationships for the Marketing Knowledge Graph.

// 1. Core Project Node
// (CopyProject {name: "Eye Serum VSL", status: "Drafting", created_at: timestamp()})

// 2. The Brief Components (Nodes)
// (:Avatar {demographics: "Women 45+", identity: "Frustrated Skincare User"})
// (:Mechanism {type: "Problem", name: "Collagen Architecture Breakdown", logic: "Weave is broken"})
// (:Mechanism {type: "Solution", name: "Structural Renewal System", logic: "Retightens the weave"})
// (:Product {name: "Eye Serum X", price: 49.00})
// (:PainPoint {name: "Sagging Eyes", type: "External"})
// (:PainPoint {name: "Invisible/Old", type: "Internal"})

// 3. Relationships
// (CopyProject)-[:TARGETS]->(Avatar)
// (CopyProject)-[:PROMOTES]->(Product)
// (Mechanism {type: "Solution"})-[:SOLVES]->(Mechanism {type: "Problem"})
// (Product)-[:UTILIZES]->(Mechanism {type: "Solution"})
// (Avatar)-[:SUFFERS_FROM]->(PainPoint)
// (Mechanism {type: "Problem"})-[:CAUSES]->(PainPoint)

// 4. Template Structures
// (:Template {type: "VSL", name: "Standard 10-Step"})
// (:TemplateStep {name: "The Lead", order: 2})
// (Template)-[:HAS_STEP]->(TemplateStep)

