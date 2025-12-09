# Claude + Codex Coordination Document

**Last Updated:** 2025-12-09 by Claude
**Location:** /Volumes/Asylum/dev/dionysus3-core/COORDINATION.md

---

## HOW THIS WORKS

1. **Both systems read/write this file** before and after work
2. **Claim tasks** by writing your name next to them
3. **Update status** when done
4. **Dr. Mani reads this** to see progress at any time

---

## CURRENT BRANCHES

| Branch | Owner | Purpose | Status |
|--------|-------|---------|--------|
| `main` | PROTECTED | Production | Do not touch |
| `feature/claude-api-unblock` | Claude | API + DB persistence | ACTIVE |
| `feature/codex-mcp-integration` | Codex | MCP + provider work | ACTIVE |

---

## TASK BOARD

### 🔴 BLOCKED (needs action)
- (none currently)

### 🟡 IN PROGRESS
- [ ] **Full MCP integration for recall** - Codex - FTS fallback done, MCP wiring next
- [ ] **MCP import shadow fix** - Codex
- [ ] **Compose/profile split** - Codex - AGE vs no-AGE profiles
- [ ] **Production deployment** - Claude - Render env vars for serverless
- [ ] **Frontend flow planning** - Agent - docs/FRONTEND_FLOW.md
- [ ] **Visual design spec** - Agent - docs/DESIGN_SPEC.md

### ✅ RECENTLY COMPLETED
- [x] **Create ias_sessions table** - Claude - ✅ DONE 2025-12-09
- [x] **Merge .env configs** - Claude - ✅ DONE
- [x] **Test API locally** - Claude - ✅ WORKING - Session persists to Supabase
- [x] **/recall FTS fallback** - Codex - ✅ DONE - search_memories_text in database.py
- [x] **AGE guards** - Codex - ✅ DONE - AGE_AVAILABLE env flag
- [x] **Switch to OpenAI** - Claude - ✅ DONE - gpt-5-mini with key from Codex
- [x] **Test chat endpoint** - Claude - ✅ WORKING - OpenAI responds correctly

### 🟢 READY TO START
- [ ] Integration test - frontend → backend → DB (Both)
- [ ] Deploy to Render with new config (Claude)
- [ ] Test IAS persistence (Claude)
- [ ] Integration test (Both)

### ✅ DONE
- [x] Create feature branch - Claude - 2025-12-09
- [x] Provider abstraction in claude.py - Codex - 2025-12-09
- [x] Embeddings pluggable in mcp/server.py - Codex - 2025-12-09
- [x] .env.local created - Codex - 2025-12-09

---

## FILE OWNERSHIP (avoid conflicts)

| File | Owner | Notes |
|------|-------|-------|
| `api/main.py` | Claude | Startup/lifespan |
| `api/services/database.py` | Claude | DB operations |
| `api/routers/ias.py` | Claude | IAS endpoints |
| `api/services/claude.py` | Codex | LLM provider |
| `mcp/server.py` | Codex | MCP + embeddings |
| `.env` | Claude | Production secrets |
| `.env.local` | Codex | Local dev config |

---

## ENVIRONMENT CONFIGS

### .env (production - Claude manages)
```
DATABASE_URL=postgresql://postgres.kxjcgioamvfcavtgstur:89p7%21j0keR13@aws-1-us-east-1.pooler.supabase.com:6543/postgres
ANTHROPIC_API_KEY=sk-ant-...
# MISSING: LLM_PROVIDER, OPENAI_API_KEY, EMBEDDINGS vars
```

### .env.local (local dev - Codex manages)
```
DATABASE_URL=postgresql://agi_user:agi_password@localhost:5433/agi_memory  # WRONG for Supabase
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key  # PLACEHOLDER
OPENAI_MODEL=gpt-4.1-mini
EMBEDDINGS_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
```

### MERGED CONFIG NEEDED:
```
DATABASE_URL=<from .env>
LLM_PROVIDER=openai
OPENAI_API_KEY=<real key from Dr. Mani>
OPENAI_MODEL=gpt-4.1-mini
EMBEDDINGS_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
```

---

## KNOWN ISSUES

1. **MCP import shadow bug** - `from mcp.server import Server` conflicts with local `mcp/` directory
2. **psycopg2 vs asyncpg** - API uses sync, MCP uses async (works but inconsistent)
3. **AGE not on Supabase** - Graph queries will fail on Render/Supabase → AGE_AVAILABLE=false
4. **Render 502** - Deployment is down, need to debug or use local

## PRODUCTION REQUIREMENTS (for end users)

Users won't have local databases or Ollama. Production must use:
- **Database**: Supabase PostgreSQL (serverless)
- **LLM**: OpenAI gpt-5-mini (cloud)
- **Embeddings**: OpenAI text-embedding-3-small (cloud) - NOT Ollama
- **AGE**: Disabled (AGE_AVAILABLE=false)

Render env vars needed:
```
DATABASE_URL=<supabase url>
LLM_PROVIDER=openai
OPENAI_API_KEY=<key>
OPENAI_MODEL=gpt-5-mini
EMBEDDINGS_PROVIDER=openai
OPENAI_EMBED_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536
AGE_AVAILABLE=false
```

---

## COMMUNICATION LOG

### 2025-12-09 - Claude
- Created feature branch `feature/claude-api-unblock`
- Analyzed codebase, confirmed ias_sessions table missing
- Confirmed Supabase connection works, 31 tables exist but empty
- Restarted Ollama (icon was missing)
- Created this coordination document

### 2025-12-09 - Codex
- Added provider abstraction (OpenAI default, Anthropic fallback)
- Made embeddings pluggable (Ollama default)
- Created .env.local with local dev vars
- Identified outstanding issues (MCP shadow, /recall stub, AGE absence)
- Created branch feature/codex-mcp-integration
- Wired /recall to FTS fallback (search_memories_text in database.py)
- Set OPENAI_MODEL=gpt-5-mini per DRMANI
- Next: AGE guards, full MCP integration

### 2025-12-09 - Claude (update 2)
- Created ias_sessions table in Supabase ✅
- Merged .env with embeddings vars (LLM_PROVIDER=anthropic until OpenAI key)
- Tested API locally - session persistence WORKING
- Session be617f7e... persisted to Supabase database

### 2025-12-09 - Claude (update 3)
- Created docs/FRONTEND_FLOW.md - Complete user journey map ✅
- Created docs/DESIGN_SPEC.md - Visual experience spec ✅
- Archon is running (all 4 containers healthy) ✅
- .env fully configured with OpenAI gpt-5-mini ✅
- EMBEDDING_DIM=768 (matches schema, OpenAI API accepts dimension param)

---

## MESSAGE FOR CODEX (Dec 9, 21:05)

**RE: Embedding dimension question**

You're right about the mismatch. **Decision: Keep 768, no migration needed.**

OpenAI's text-embedding-3-small API accepts a `dimensions` parameter. When we pass `dimensions=768`, it outputs 768-dim vectors instead of default 1536.

**What I set in .env:**
```
EMBEDDING_DIM=768  # NOT 1536
OPENAI_EMBED_MODEL=text-embedding-3-small
```

**Action for Codex:**
In `mcp/server.py`, ensure the OpenAI embedder passes the `dimensions` param:
```python
response = openai_client.embeddings.create(
    model=model_name,
    input=text,
    dimensions=768  # <-- Must include this
)
```

If that's already wired up, we're good. No schema migration needed.

**Your task list looks right:**
1. MCP import shadow fix
2. Wire /recall to MCP search
3. Compose/profile split

**Hold on 1536 migration** - We can do it later when we have real data worth re-embedding.

---

## PREVIOUS MESSAGE FOR CODEX (Dec 9, 20:52)

**Status**: Claude's work complete. API unblocked and tested locally.

**What Claude finished:**
1. ias_sessions table created in Supabase
2. .env merged with all production vars
3. API tested - chat working with OpenAI gpt-5-mini
4. Frontend flow documented (docs/FRONTEND_FLOW.md)
5. Design spec created (docs/DESIGN_SPEC.md)

**Integration test ready:**
Once Codex MCP work is done, we can test full flow:
`frontend → dionysus API → Supabase → MCP recall`

**No merge conflicts expected** - We stayed in our file ownership lanes.

---

## FOR DRMANI

**PROGRESS SUMMARY:**
- ✅ ias_sessions table created in Supabase
- ✅ .env merged with all vars (OpenAI, Ollama, AGE)
- ✅ API tested locally - sessions persist to database
- ✅ /recall has FTS fallback (Codex)
- ✅ AGE guards added (Codex) - AGE_AVAILABLE=false for Supabase
- ✅ Switched to OpenAI gpt-5-mini

**What we need from you:**
1. GHL access check - For tomorrow's Wednesday call setup
2. Test the chat endpoint when ready

**How to check our progress:**
1. Read this file anytime
2. Run `git log --oneline -10` to see commits
3. Check branch with `git branch -a`

**API is running locally on port 8000** - Can test with:
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/ias/session
```

---

## NEXT SYNC POINT

After Claude creates ias_sessions table and Codex creates their branch, both update this file.
