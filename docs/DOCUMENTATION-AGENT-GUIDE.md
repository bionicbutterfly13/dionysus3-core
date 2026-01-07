# Documentation Agent Guide - Silver Bullets Maintenance

**Purpose**: Enable parallel agents to maintain and expand silver bullets documentation
**Pattern**: Atomic concept pages with bidirectional links
**Scope**: All Dionysus cognitive architecture and IAS curriculum documentation

**Created**: 2026-01-02
**Author**: Dr. Mani Saint-Victor, MD

---

## 🎯 Documentation Philosophy

**Silver Bullets Pattern**: Self-contained atomic concept pages that mirror the graph structure of the codebase

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
docs/
├── silver-bullets/
│   ├── 00-INDEX.md                    # Main navigation hub
│   ├── 01-10-*.md                     # Main documents (sequential reading)
│   └── concepts/                      # Atomic concept library
│       ├── declarative-metacognition.md
│       ├── thoughtseed.md
│       ├── attractor-basin.md
│       └── [30-40 more atomic concepts]
│
├── IAS-INDEX.md                       # IAS documentation hub
├── IAS-MERGED-DATA-MODEL.md          # IAS data model
├── IAS-CURRICULUM-IMPLEMENTATION-GUIDE.md
│
└── visualizations/                    # Interactive HTML/SVG
    └── thoughtseed-competition.html
```

---

## 🤖 Agent Roles & Parallel Workflows

### Agent Specializations

#### 1. **Concept Extractor Agent**
**Role**: Identify undocumented concepts from code
**Trigger**: New features merged, code reviews
**Output**: List of concepts needing atomic pages

**Workflow**:
```bash
# 1. Scan recent commits for new concepts
git log --since="1 week ago" --grep="feat\|refactor" --oneline

# 2. Search for undefined terms in code comments
rg "TODO: document" --type py

# 3. Check INDEX for missing concepts
# 4. Create list: concepts_to_document.md
```

**Scope**: Read-only until list approved

---

#### 2. **Atomic Writer Agent**
**Role**: Create individual concept pages
**Trigger**: Assigned concept from backlog
**Output**: Single atomic concept markdown file

**Workflow**:
```bash
# 1. Receive assignment: "Document 'precision-weighting'"
# 2. Research in codebase
rg "precision.?weight" --type py
# 3. Find related concepts
# 4. Write concept page following template
# 5. Create PR: docs-concept-precision-weighting
```

**Template**: See "Atomic Concept Template" below

**Branch naming**: `docs/concept-{concept-name}`

---

#### 3. **Link Weaver Agent**
**Role**: Ensure bidirectional links between concepts
**Trigger**: New concept pages merged
**Output**: Updated existing pages with back-links

**Workflow**:
```bash
# 1. New page merged: concepts/basin-transition.md
# 2. Find pages it links TO
# 3. Add reciprocal links FROM those pages
# 4. Update relationship map in INDEX
# 5. Create PR: docs-links-basin-transition
```

**Branch naming**: `docs/links-{concept-name}`

---

#### 4. **Index Curator Agent**
**Role**: Maintain navigation indexes and relationship maps
**Trigger**: Multiple new concepts merged
**Output**: Updated INDEX files with new entries

**Workflow**:
```bash
# 1. Weekly: Review all new concept pages
# 2. Categorize by domain (Core, Agency, Implementation, etc.)
# 3. Update 00-INDEX.md with new entries
# 4. Update relationship map
# 5. Create domain-specific indexes if needed
# 6. Create PR: docs-index-update-{date}
```

**Branch naming**: `docs/index-update`

---

#### 5. **Code Linker Agent**
**Role**: Add implementation references to concept pages
**Trigger**: Concept pages exist but lack code links
**Output**: Concept pages with code file references

**Workflow**:
```bash
# 1. Find concept implementation in code
rg "class Thoughtseed" --type py
# 2. Add "## Implementation" section to concept page
# 3. Link to files: api/models/thoughtseed.py:15
# 4. Link to tests
# 5. Create PR: docs-code-links-{concept}
```

**Branch naming**: `docs/code-links-{concept-name}`

---

#### 6. **Visualization Builder Agent**
**Role**: Create interactive diagrams and relationship maps
**Trigger**: Complex concepts with multiple relationships
**Output**: HTML/SVG visualizations in docs/visualizations/

**Workflow**:
```bash
# 1. Identify visualization candidates (>5 related concepts)
# 2. Create Mermaid or D3.js visualization
# 3. Save to docs/visualizations/
# 4. Link from concept pages
# 5. Create PR: docs-viz-{concept-cluster}
```

**Branch naming**: `docs/viz-{topic}`

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

#### Work Claiming
```markdown
# docs/DOCUMENTATION_BACKLOG.md
- [ ] precision-weighting (CLAIMED: Agent-2, Branch: docs/concept-precision-weighting)
- [ ] basin-stability (CLAIMED: Agent-5, Branch: docs/concept-basin-stability)
- [ ] selective-attention (AVAILABLE)
```

**Process**:
1. Agent checks backlog
2. Claims item by updating backlog
3. Creates branch
4. Completes work
5. Creates PR
6. Unclaims on merge

---

## 📝 Atomic Concept Template

```markdown
# {Concept Name}

**Category**: {Core Concept | Implementation | Clinical | Business}
**Type**: {Cognitive Unit | Process | Pattern | Tool}
**Implementation**: {Code reference or N/A}

---

## Definition

A **{concept}** is {concise 1-2 sentence definition}.

{Optional: Analogy or visual metaphor}

## Key Characteristics

- **Property 1**: Description
- **Property 2**: Description
- **Property 3**: Description

## How It Works

### Step-by-Step Process
1. **Step 1**: What happens
2. **Step 2**: What happens
3. **Step 3**: What happens

### Visual Representation
```
[ASCII diagram or reference to visualization]
```

## Implementation

**Code**: `{file_path}:{line_numbers}`
**Tests**: `{test_file_path}`
**Related Services**: `{service_files}`

## Related Concepts

**Prerequisites** (understand these first):
- [[prerequisite-concept-1]]
- [[prerequisite-concept-2]]

**Builds Upon** (this uses):
- [[foundation-concept]]

**Used By** (depends on this):
- [[dependent-concept-1]]
- [[dependent-concept-2]]

**Related** (similar or complementary):
- [[related-concept]]

## Examples

### Example 1: {Use Case}
```python
# Code example showing concept in action
```

### Example 2: {Clinical/Business Context}
{Real-world application}

## Common Misconceptions

**Misconception 1**: "{Wrong belief}"
**Reality**: {Correct understanding}

**Misconception 2**: "{Wrong belief}"
**Reality**: {Correct understanding}

## When to Use

✅ **Use when**:
- Condition 1
- Condition 2

❌ **Don't use when**:
- Condition 1
- Condition 2

## Further Reading

- **Research**: {Academic papers or sources}
- **Documentation**: [[related-doc-1]], [[related-doc-2]]
- **Blog posts**: {External links if relevant}

---

**Last Updated**: {YYYY-MM-DD}
**Maintainer**: {Agent or human}
**Status**: {Draft | Review | Production}
```

---

## 🔄 Maintenance Workflows

### Weekly: Concept Backlog Review
```bash
# Run by Index Curator Agent or human
# 1. Scan git log for new features
git log --since="1 week ago" --oneline --all

# 2. Extract technical terms
rg "class |def |async def " api/ --type py | grep -oE "class \w+|def \w+"

# 3. Check against existing concepts
ls docs/silver-bullets/concepts/*.md

# 4. Update backlog
vim docs/DOCUMENTATION_BACKLOG.md
```

### Monthly: Link Integrity Check
```bash
# Run by Link Weaver Agent
# 1. Find all [[wikilinks]]
rg "\[\[[\w-]+\]\]" docs/silver-bullets/ -o

# 2. Verify target files exist
# 3. Check for broken links
# 4. Report orphaned concepts (no incoming links)
# 5. Create PR to fix
```

### Quarterly: Visualization Refresh
```bash
# Run by Visualization Builder Agent
# 1. Review relationship maps
# 2. Update with new concepts
# 3. Refresh interactive HTML with latest data
# 4. Create new visualizations for concept clusters
```

---

## 🚀 Quick Start for Agents

### Claiming a Documentation Task

```bash
# 1. Read backlog
cat docs/DOCUMENTATION_BACKLOG.md

# 2. Choose unclaimed task
TASK="precision-weighting"

# 3. Claim it
echo "- [ ] $TASK (CLAIMED: $(whoami), Branch: docs/concept-$TASK)" >> docs/DOCUMENTATION_BACKLOG.md
git add docs/DOCUMENTATION_BACKLOG.md
git commit -m "docs: claim $TASK for documentation"
git push origin 050-marketing-strategist

# 4. Create branch
git checkout -b docs/concept-$TASK

# 5. Research concept
rg "precision.?weight" --type py api/

# 6. Write concept page
vim docs/silver-bullets/concepts/$TASK.md
# Follow template above

# 7. Create PR
git add docs/silver-bullets/concepts/$TASK.md
git commit -m "docs: add $TASK atomic concept page"
git push origin docs/concept-$TASK

# 8. Unclaim on merge
```

### Updating Existing Concept

```bash
# 1. Create branch
git checkout -b docs/update-thoughtseed

# 2. Edit concept
vim docs/silver-bullets/concepts/thoughtseed.md

# 3. Add implementation reference
# ## Implementation
# **Code**: `api/models/thoughtseed.py:15-45`

# 4. Commit and PR
git add docs/silver-bullets/concepts/thoughtseed.md
git commit -m "docs: add code reference to thoughtseed concept"
git push origin docs/update-thoughtseed
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
- [ ] Uses correct category/type tags
- [ ] Has "Last Updated" date
- [ ] Markdown lints cleanly

### Index Updates
- [ ] New concept added to appropriate section
- [ ] Relationship map updated if needed
- [ ] Cross-references are accurate
- [ ] Navigation paths still logical
- [ ] No duplicate entries

### Links
- [ ] All [[wikilinks]] resolve to existing files
- [ ] Bidirectional links exist (A→B and B→A)
- [ ] Code references use exact file:line format
- [ ] External links are valid (test with curl)

---

## 🎯 Success Metrics

Track documentation health:

### Coverage
```bash
# Concepts documented vs code classes/functions
CONCEPTS=$(ls docs/silver-bullets/concepts/*.md | wc -l)
CLASSES=$(rg "^class " api/ --type py | wc -l)
echo "Coverage: $((CONCEPTS * 100 / CLASSES))%"
```

### Link Density
```bash
# Average links per concept page
LINKS=$(rg "\[\[" docs/silver-bullets/concepts/ | wc -l)
echo "Avg links/page: $((LINKS / CONCEPTS))"
```

### Code Integration
```bash
# Concepts with implementation references
WITH_CODE=$(rg "## Implementation" docs/silver-bullets/concepts/ | wc -l)
echo "Code-linked: $((WITH_CODE * 100 / CONCEPTS))%"
```

### Freshness
```bash
# Concepts updated in last 30 days
find docs/silver-bullets/concepts/ -mtime -30 -name "*.md" | wc -l
```

**Goals**:
- Coverage: >60% of code classes documented
- Link density: >5 links per concept page
- Code integration: >80% of concepts link to code
- Freshness: >20% updated monthly

---

## 🔗 Integration Points

### With Ralph Orchestrator
```bash
# Ralph can spawn parallel documentation agents
/ralph spawn-docs-team --concepts "precision-weighting,basin-stability,selective-attention"
# → Spawns 3 Atomic Writer agents in parallel
# → Each claims task, creates branch, writes page
# → Link Weaver follows after all merge
# → Index Curator finalizes
```

### With Git Hooks
```bash
# .git/hooks/post-commit
# Auto-update backlog when new features added
if git log -1 --grep "feat:"; then
    echo "New feature detected - update documentation backlog"
fi
```

### With CI/CD
```bash
# .github/workflows/docs-check.yml
# On PR: verify links, check template compliance, measure coverage
```

---

## 📚 Reference Examples

### Good Atomic Concept Page
See: `docs/silver-bullets/concepts/thoughtseed.md`
- Clear definition
- Step-by-step lifecycle
- Code references
- 8+ bidirectional links
- Examples with code snippets

### Good Index Structure
See: `docs/silver-bullets/00-INDEX.md`
- Multiple navigation paths
- Topic clustering
- Quick navigation shortcuts
- Relationship map
- Usage guide

### Good Visualization
See: `docs/visualizations/thoughtseed-competition.html`
- Interactive parameters
- Real-time simulation
- Linked to concept pages
- Educational value

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

❌ **Stale content**: Last updated 6 months ago
✅ **Living documents**: Regular updates as code evolves

---

## 🎬 Next Steps

### For New Agents
1. Read this guide
2. Review `docs/silver-bullets/00-INDEX.md`
3. Read 2-3 existing atomic concept pages as examples
4. Check `docs/DOCUMENTATION_BACKLOG.md` for available tasks
5. Claim a task and create your first concept page

### For Existing Documentation
1. Audit current concepts for completeness
2. Add missing implementation references
3. Verify bidirectional links
4. Create visualizations for complex clusters

### For System Expansion
1. Create domain-specific indexes (Clinical, Technical, Business)
2. Build automated link checking
3. Integrate with Ralph for parallel workflows
4. Set up documentation metrics dashboard

---

**This guide itself is a living document. Update it as the documentation system evolves.**

**Last Updated**: 2026-01-02
**Maintainer**: Dr. Mani Saint-Victor, MD
**Status**: Production
