// Neo4j Skills Schema (Contract)
// Feature: 006-procedural-skills

// Unique identifier for Skills
CREATE CONSTRAINT skill_id_unique IF NOT EXISTS
FOR (s:Skill) REQUIRE s.skill_id IS UNIQUE;

// Helpful indexes
CREATE INDEX skill_name IF NOT EXISTS
FOR (s:Skill) ON (s.name);

CREATE INDEX skill_proficiency IF NOT EXISTS
FOR (s:Skill) ON (s.proficiency);

