# Documentation Agent Guide - Quartz Maintenance

**Purpose**: Enable parallel agents to maintain and expand Quartz documentation
**Pattern**: Atomic concept pages with bidirectional links
**Scope**: All Dionysus cognitive architecture and IAS curriculum documentation

**Created**: 2026-01-02
**Author**: Dr. Mani Saint-Victor, MD

---

## 🎯 Documentation Philosophy

**Pattern**: Self-contained atomic concept pages that mirror the graph structure of the codebase

### Why This Matters
- **Codebase is a graph**: Concepts interconnect across domains (neuroscience, AI, therapy, business)
- **Docs must be a graph**: Each concept page is complete independently but richly linked
- **No hierarchies**: Don't force concepts into trees - use bidirectional links

### Core Principles
1. **Atomic**: One concept per file, fully explained
2. **Self-Contained**: Can read any page without prerequisites
3. **Bidirectional Links**: Link TO related concepts, ensure they link BACK
4. **Code-Linked**: Reference actual implementation files
5. **Multi-Entry**: Support navigation from concept, implementation, use case, or chronology

---

## 📁 Documentation Structure

```
docs/garden/content/           # Quartz content root
├── index.md                   # Main navigation hub
├── concepts/                  # Atomic concept library
│   ├── hopfield-attractors.md
│   ├── act-r-ooda.md
│   ├── abm-smolagents.md
│   └── [other atomic concepts]
│
├── evolution/                 # System evolution tracking
│   └── thoughtseed_dashboard.md
│
├── journal/ -> ../../journal  # Symlink to journal
├── papers/ -> ../../papers    # Symlink to papers
│
docs/
├── IAS-INDEX.md              # IAS documentation hub
├── concepts/                  # Legacy concept documentation
└── journal/                   # Development journal entries
```

---

## 🤖 Agent Roles & Parallel Workflows

### Agent Specializations

#### 1. **Concept Extractor Agent**
**Role**: Identify undocumented concepts from code
**Trigger**: New features merged, code reviews
**Output**: List of concepts needing atomic pages

#### 2. **Atomic Writer Agent**
**Role**: Create individual concept pages
**Trigger**: Assigned concept from backlog
**Output**: Single atomic concept markdown file

**Branch naming**: `docs/concept-{concept-name}`

#### 3. **Link Weaver Agent**
**Role**: Ensure bidirectional links between concepts
**Trigger**: New concept pages merged
**Output**: Updated existing pages with back-links

**Branch naming**: `docs/links-{concept-name}`

#### 4. **Index Curator Agent**
**Role**: Maintain navigation indexes and relationship maps
**Trigger**: Multiple new concepts merged
**Output**: Updated INDEX files with new entries

**Branch naming**: `docs/index-update`

#### 5. **Code Linker Agent**
**Role**: Add implementation references to concept pages
**Trigger**: Concept pages exist but lack code links
**Output**: Concept pages with code file references

**Branch naming**: `docs/code-links-{concept-name}`

---

### Parallel Execution Protocol

#### Conflict Avoidance
```
Agent 1: docs/concept-free-energy     ✅ No conflict
Agent 2: docs/concept-attractor-basin ✅ No conflict
Agent 3: docs/links-free-energy       ⚠️  Waits for Agent 1 to merge
Agent 4: docs/index-update            ⚠️  Waits for all concepts merged
```

**Rule**: Only ONE agent per concept file at a time
**Rule**: Link Weaver waits for Atomic Writer to merge
**Rule**: Index Curator waits for all updates in batch to merge

---

## 📝 Atomic Concept Template

```markdown
---
title: {Concept Name}
description: {Brief description}
tags:
  - {tag1}
  - {tag2}
created: {YYYY-MM-DD}
---

# {Concept Name}

**Category**: {Core Concept | Implementation | Clinical | Business}
**Type**: {Cognitive Unit | Process | Pattern | Tool}
**Implementation**: {Code reference or N/A}

---

## Definition

A **{concept}** is {concise 1-2 sentence definition}.

## Key Characteristics

- **Property 1**: Description
- **Property 2**: Description
- **Property 3**: Description

## How It Works

### Step-by-Step Process
1. **Step 1**: What happens
2. **Step 2**: What happens
3. **Step 3**: What happens

## Implementation

**Code**: `{file_path}:{line_numbers}`
**Tests**: `{test_file_path}`

## Related Concepts

- [[prerequisite-concept-1]]
- [[related-concept]]

## References

- **Research**: {Academic papers or sources}
```

---

## 🚀 Quick Start for Agents

### Claiming a Documentation Task

```bash
# 1. Read backlog
cat docs/DOCUMENTATION_BACKLOG.md

# 2. Choose unclaimed task
TASK="precision-weighting"

# 3. Create branch
git checkout -b docs/concept-$TASK

# 4. Research concept
rg "precision.?weight" --type py api/

# 5. Write concept page
vim docs/garden/content/concepts/$TASK.md

# 6. Create PR
git add docs/garden/content/concepts/$TASK.md
git commit -m "docs: add $TASK atomic concept page"
git push origin docs/concept-$TASK
```

---

## 📊 Quality Checklist

Before merging any documentation PR, verify:

### Atomic Concept Page
- [ ] Follows template structure
- [ ] Has clear definition (1-2 sentences)
- [ ] Lists key characteristics (3-5 bullets)
- [ ] Explains how it works (step-by-step)
- [ ] Links to implementation code (if exists)
- [ ] Has bidirectional links to 3+ related concepts
- [ ] Includes at least 1 example
- [ ] Has Quartz frontmatter (title, description, tags, created)
- [ ] Markdown lints cleanly

### Links
- [ ] All [[wikilinks]] resolve to existing files
- [ ] Bidirectional links exist (A→B and B→A)
- [ ] Code references use exact file:line format

---

## 🎯 Success Metrics

Track documentation health:

### Coverage
```bash
# Concepts documented vs code classes/functions
CONCEPTS=$(ls docs/garden/content/concepts/*.md 2>/dev/null | wc -l)
CLASSES=$(rg "^class " api/ --type py | wc -l)
echo "Coverage: $((CONCEPTS * 100 / CLASSES))%"
```

### Link Density
```bash
# Average links per concept page
LINKS=$(rg "\[\[" docs/garden/content/concepts/ 2>/dev/null | wc -l)
echo "Avg links/page: $((LINKS / CONCEPTS))"
```

**Goals**:
- Coverage: >60% of code classes documented
- Link density: >5 links per concept page
- Code integration: >80% of concepts link to code

---

## 🚨 Anti-Patterns (Don't Do This)

❌ **Hierarchical organization**: Don't nest concepts by category trees
✅ **Graph organization**: Flat structure with rich linking

❌ **Long documents**: Don't create 50-page guides
✅ **Atomic pages**: One concept, one file, complete

❌ **Code duplication**: Don't copy code into docs
✅ **Code references**: Link to actual implementation

❌ **Orphaned concepts**: No incoming or outgoing links
✅ **Richly connected**: Every concept links to 3+ others

---

**This guide itself is a living document. Update it as the documentation system evolves.**

**Last Updated**: 2026-01-26
**Maintainer**: Dr. Mani Saint-Victor, MD
**Status**: Production
