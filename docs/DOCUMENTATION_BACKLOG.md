# Documentation Backlog - Silver Bullets Concepts

**Purpose**: Track atomic concept pages that need to be written or updated
**Process**: Agents claim tasks, create branches, write pages, create PRs

**Last Updated**: 2026-01-02

---

## 🎯 Priority: High (Core Cognitive Architecture)

### Needs Creation
- [ ] precision-weighting (CLAIMED: Agent-1, Branch: docs/concept-precision-weighting)
- [ ] prediction-error (CLAIMED: Agent-2, Branch: docs/concept-prediction-error)
- [ ] free-energy (CLAIMED: Agent-3, Branch: docs/concept-free-energy)
- [ ] attractor-basin (CLAIMED: Agent-4, Branch: docs/concept-attractor-basin)
- [ ] basin-transition (CLAIMED: Agent-5, Branch: docs/concept-basin-transition)
- [x] basin-stability (COMPLETED: Agent-6, 2026-01-02)
- [x] surprise-score (COMPLETED: Agent-7, 2026-01-02)
- [x] activation-energy (COMPLETED: Agent-8, 2026-01-02)
- [x] thoughtseed-competition (COMPLETED: Agent-9, 2026-01-02)
- [x] selective-attention (COMPLETED: Agent-10, 2026-01-02)

### Needs Code Links
- [ ] declarative-metacognition (EXISTS but needs api/services/ links)
- [ ] procedural-metacognition (EXISTS but needs api/agents/ links)
- [ ] metacognitive-feelings (EXISTS but needs implementation refs)
- [ ] aha-moment (EXISTS but needs examples)

---

## 🎯 Priority: Medium (Implementation Components)

### Needs Creation
- [ ] ooda-loop (AVAILABLE)
- [ ] smolagents-architecture (AVAILABLE)
- [ ] meta-tot-engine (AVAILABLE)
- [ ] consciousness-pipeline (AVAILABLE)
- [ ] multi-tier-memory (AVAILABLE)
- [ ] heartbeat-agent (AVAILABLE)
- [ ] perception-agent (AVAILABLE)
- [ ] reasoning-agent (AVAILABLE)
- [ ] metacognition-agent (AVAILABLE)

---

## 🎯 Priority: Medium (Agency & Altered States)

### Needs Creation
- [ ] attentional-agency (AVAILABLE)
- [ ] cognitive-agency (AVAILABLE)
- [ ] meta-agency (AVAILABLE)
- [ ] psychedelic-mechanism (AVAILABLE)
- [ ] meditation-training (AVAILABLE)
- [ ] basin-reorganization (AVAILABLE)

---

## 🎯 Priority: Low (Clinical Applications)

### Needs Creation
- [ ] therapy-gap (AVAILABLE)
- [ ] declarative-to-procedural (AVAILABLE)
- [ ] procedural-competence (AVAILABLE)
- [ ] replay-loop (AVAILABLE - link to IAS docs)
- [ ] analytical-empath (AVAILABLE - link to IAS docs)

---

## 🎯 Priority: Low (IAS Business)

### Needs Creation
- [ ] ias-curriculum-structure (AVAILABLE)
- [ ] obstacle-matrix (AVAILABLE)
- [ ] true-false-actions (AVAILABLE)
- [ ] conviction-gauntlet (AVAILABLE)
- [ ] habit-harmonizer (AVAILABLE)

---

## 📊 Backlog Statistics

**Total Concepts Identified**: 44
**Total Created**: 13
**Coverage**: 30%

**Next Milestone**: 15 concepts (34% coverage)
**Target**: 40 concepts (91% coverage)

---

## 🔄 Recently Completed

### Batch 2 (2026-01-02)
- ✅ basin-stability (Agent-6, 536 lines)
- ✅ surprise-score (Agent-7, 489 lines)
- ✅ activation-energy (Agent-8, 519 lines)
- ✅ thoughtseed-competition (Agent-9, 482 lines)
- ✅ selective-attention (Agent-10, 723 lines)
- **Total**: 2,749 lines added, coverage 18% → 30%

---

## 📝 Claiming Instructions

**To claim a task**:
1. Find AVAILABLE task above
2. Edit this file: Change `(AVAILABLE)` to `(CLAIMED: YourName, Branch: docs/concept-{name})`
3. Commit and push to current branch
4. Create your documentation branch
5. Follow template in `docs/DOCUMENTATION-AGENT-GUIDE.md`

**Example**:
```markdown
- [ ] precision-weighting (CLAIMED: Agent-Claude-2, Branch: docs/concept-precision-weighting)
```

**On merge**:
1. Move task to "Recently Completed" section
2. Update statistics
3. Commit backlog update

---

## 🚀 Batch Operations

### Spawn Parallel Agents (Ralph)
```bash
# Assign 5 high-priority concepts to parallel agents
/ralph spawn-docs-team --concepts "precision-weighting,prediction-error,free-energy,attractor-basin,basin-transition"
```

### Weekly Backlog Refresh
```bash
# Scan codebase for new undocumented concepts
python scripts/audit_documentation_coverage.py
# → Updates this backlog automatically
```

---

**See `docs/DOCUMENTATION-AGENT-GUIDE.md` for complete workflow instructions**
