---
description: Codebase Health Check (4 questions)
---

# /broken - Codebase Health Check

Run the **4 health check questions** for the current project. Same assessment as `/good`; use `/broken` when you want to quickly ask "what's broken?" and get the full diagnostic.

## Instructions

Analyze the current project/codebase and provide concise, actionable answers to:

1. **What's good?** - Working features, clean code, solid patterns
2. **What's broken?** - Known bugs, failing tests, errors
3. **What works but shouldn't?** - Hacky code, technical debt, fragile implementations
4. **What doesn't but pretends to?** - Silent failures, incomplete features, misleading code

## Output Format

```
📊 Codebase Health Check

✅ What's good:
- [findings]

❌ What's broken:
- [findings]

⚠️ What works but shouldn't:
- [findings]

🎭 What doesn't but pretends to:
- [findings]
```

## Execution

1. Scan project structure
2. Check for test results, build status, error logs
3. Review recent changes and known issues
4. Provide honest, direct assessment
