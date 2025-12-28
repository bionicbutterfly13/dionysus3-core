---
name: ias-hook-generator
description: Smol agent for generating hooks targeting Analytical Empaths using Panksepp's 7 emotional systems. Pulls patterns from Neo4j hook database via Graphiti API and generates new variations.
namespace: inner-architect
category: copywriting
version: 1.0.0
created: 2025-12-26
tags: [hooks, panksepp, emotional-triggers, analytical-empath, copywriting, neo4j, graphiti]
dependencies:
  - skills/analytical-empath-core.md
related:
  - skills/ias-email-writer/SKILL.md
  - research/voice-of-market-summary.md
executable: true
---

# IAS Hook Generator Skill

Generate hooks for Analytical Empaths using Panksepp's 7 Primary Emotional Systems and patterns from the Neo4j hook database.

## Quick Start

**Input Required:**
- Hook category or pain point
- Emotional system to target (optional)
- Number of hooks to generate

**Output:** Hook variations ready for emails, ads, or social content

---

## PANKSEPP'S 7 EMOTIONAL SYSTEMS

### 1. SEEKING (Curiosity/Anticipation)
**Neuroscience:** Dopamine-driven exploration system
**Triggers:** Curiosity gaps, incomplete information, discovery promises
**For Analytical Empaths:** Appeals to their need to understand, solve, diagnose

**Hook Patterns:**
- "What if the reason you feel X is actually Y?"
- "There's something nobody tells you about..."
- "The mechanism behind X that explains everything"
- "What [experts] won't tell you about..."

**Examples:**
> "What if the exhaustion isn't from your job, but from pretending to enjoy your job?"
> "There's a mechanism running underneath your success that nobody talks about."

---

### 2. RAGE (Frustration/Injustice)
**Neuroscience:** Activated when goals are blocked or injustice perceived
**Triggers:** Unfairness, being held back, systems that fail you
**For Analytical Empaths:** Their competence isn't recognized, solutions don't work

**Hook Patterns:**
- "You've tried everything and it still doesn't work because..."
- "The system is designed to keep you stuck"
- "They profit from you staying exactly where you are"
- "You've been lied to about..."

**Examples:**
> "Your executive coach is not addressing this because they profit from you staying exactly where you are."
> "You've tried to logic your way out of this before. How has that worked for you?"

---

### 3. FEAR (Anxiety/Threat Detection)
**Neuroscience:** Amygdala-driven threat response
**Triggers:** Loss, danger, uncertainty, exposure
**For Analytical Empaths:** Fear of being exposed as fraud, losing status, health consequences

**Hook Patterns:**
- "You are one [event] away from..."
- "The cost of waiting is..."
- "What happens when [protective mechanism] fails?"
- "Your body has been keeping score..."

**Examples:**
> "You are one diagnosis away from being forced to change. Why wait?"
> "Your body has been keeping score and it is about to send you the bill."

---

### 4. LUST (Desire/Attraction)
**Neuroscience:** Sexual and sensory pleasure systems
**Triggers:** Desire for connection, intimacy, being truly seen
**For Analytical Empaths:** Deep desire to be loved for self, not achievement

**Hook Patterns:**
- "Imagine being loved for who you are, not what you do"
- "What would it feel like to..."
- "The version of you that [desirable state]"
- "There's a life where you..."

**Examples:**
> "What would it feel like to wake up without the dread?"
> "There is a version of your life where you are fully alive and not just fully functional."

---

### 5. CARE (Nurturing/Protection)
**Neuroscience:** Oxytocin-driven bonding and nurturing
**Triggers:** Protecting loved ones, legacy, being present
**For Analytical Empaths:** Fear of failing family, teaching wrong lessons to children

**Hook Patterns:**
- "Your children are learning that..."
- "The version of you your family needs..."
- "What legacy are you actually leaving?"
- "The people who love you see..."

**Examples:**
> "You are teaching your children that success equals suffering. Is that the legacy you want?"
> "Your partner sees the shell of you. Your kids are learning that achievement requires absence."

---

### 6. PANIC/GRIEF (Loss/Separation)
**Neuroscience:** Separation distress and social bonding loss
**Triggers:** Isolation, losing connection, grief for lost self
**For Analytical Empaths:** Grief for person they could have been, isolation at top

**Hook Patterns:**
- "There is a version of you that is still grieving..."
- "You are surrounded by people and completely alone"
- "The person you actually are has not had the stage..."
- "Nobody knows the real you"

**Examples:**
> "There is a grief in high achievers that nobody talks about - the grief of never becoming what you could have been."
> "People know a version of you. Nobody knows you."

---

### 7. PLAY (Joy/Social Bonding)
**Neuroscience:** Social play and joy circuits
**Triggers:** Lightness, freedom, possibility, connection
**For Analytical Empaths:** Remember who they were before, reconnection to joy

**Hook Patterns:**
- "Do you remember who you were before..."
- "What if [serious thing] could feel like..."
- "The stillness you've never felt before"
- "Work that feels like play"

**Examples:**
> "Do you remember who you were before you became what you needed to be?"
> "It is possible to be driven and calm at the same time. Most high achievers have never experienced that."

---

## HOOK STRUCTURE FORMULAS

### Formula 1: Pattern Recognition
```
[Observation about their experience] + [Reframe that names it]
```
> "You can still perform. You just cannot remember why it matters."

### Formula 2: Mechanism Reveal
```
[What they think is the problem] + "but actually" + [real mechanism]
```
> "You're not burned out from the work. You're burned out from the lying."

### Formula 3: Question That Lands
```
"What if" + [reframe of their situation] + "?"
```
> "What if the reason you feel so lost is because you've stopped listening to the part of you that knows exactly what you need?"

### Formula 4: Cost Awareness
```
[What they're doing] + "at the cost of" + [what they're losing]
```
> "You are making money at the cost of your life. That is not strategy. That is a hostage situation."

### Formula 5: Identity Paradox
```
[Their strength] + "is also" + [their prison]
```
> "Your greatest strength, self-reliance, is also the thing keeping you stuck."

### Formula 6: Permission Grant
```
"You are allowed to" + [thing they secretly want] + "even if" + [guilt trigger]
```
> "You are allowed to want something different even if you got everything you said you wanted."

### Formula 7: Loop-Back (Meta)
```
[Observation about their reading behavior] + [what it reveals]
```
> "If this doesn't apply to you, then why are you still reading?"

---

## HOOK CATEGORIES (FROM NEO4J DATABASE)

### Primary Categories
| Category | Emotional Systems | Use Case |
|----------|------------------|----------|
| Identity & Authenticity | PANIC, SEEKING | Early awareness, connection |
| Burnout & Exhaustion | FEAR, RAGE | Problem agitation |
| Imposter Syndrome | FEAR, PANIC | Validation, recognition |
| Neuroscience & Subconscious | SEEKING | Mechanism explanation |
| Performance & Capability | RAGE, FEAR | Competence trap |
| Decision Paralysis | FEAR, PANIC | Golden handcuffs |
| Authenticity & Reconnection | PLAY, CARE | Transformation vision |
| Hidden Knowledge | SEEKING, RAGE | Authority positioning |
| Transformation Possibility | LUST, PLAY | Future pacing |
| Specific Pain Points | FEAR, CARE | Targeted agitation |

### Retrieve Patterns from Neo4j
```bash
# Search for hooks by category
curl -s "http://72.61.78.89:8001/api/graphiti/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "identity authenticity hooks analytical empaths"}'
```

---

## AVATAR QUICK REFERENCE

**The Analytical Empath:**
- Age: 38-55
- Net worth: $1M-$5M+ liquid
- Roles: C-Suite, Founders, Surgeons, Senior Partners
- Core trait: High-fidelity emotional processing + intellectual achievement

**Big 3 Pain Points:**
1. The Split Self (two identities draining energy)
2. The Replay Loop (rumination cycle)
3. Hollow Success Paradox (have everything, feel nothing)

**VOM Language to Use:**
- "I'm a husk"
- "Two people"
- "Golden handcuffs"
- "Is this it?"
- "Ghost in my own home"

---

## HOOK QUALITY CHECKLIST

### Before Generating
- [ ] Identified target emotional system(s)
- [ ] Clear on pain point or category
- [ ] Know the context (email, ad, social)

### After Generating
- [ ] Does it stop the scroll?
- [ ] Does it name HER experience specifically?
- [ ] Does it create curiosity without satisfying it?
- [ ] Is it at 5th grade reading level?
- [ ] Zero em dashes?
- [ ] No woo/bro language?
- [ ] Would she feel SEEN, not categorized?

---

## WORKFLOW

### Generate New Hooks
1. **Receive request** with category/pain point
2. **Identify emotional system(s)** most relevant
3. **Query Neo4j** for existing patterns in that category
4. **Apply formula** to generate variations
5. **Voice check** - 5th grade, no em dashes, no woo
6. **Output hooks** with emotional system labels

### Example Session
```
User: Generate 5 hooks about imposter syndrome

Agent:
1. [FEAR] You are waiting for someone to expose you. They never do because there is nothing to expose.

2. [SEEKING] What if the imposter is not you, but the story you have been telling yourself about you?

3. [PANIC] That voice saying you do not belong here has been wrong every single time. And you still believe it.

4. [RAGE] You can intellectually acknowledge your success and still feel like a complete fraud. That is not a character flaw. That is a pattern.

5. [FEAR + SEEKING] The goal posts keep moving. The finish line keeps disappearing. What if your definition of success is literally impossible?
```

---

## BANNED ELEMENTS

**Words:**
- healing, journey, vulnerable, self-care, balance
- manifest, attract, hustle, grind
- high performers / high achievers (use HER experience)

**Phrases:**
- "Here's the uncomfortable truth"
- "No spike. No tightening. No urge."
- Any checklist-style phrases

**Punctuation:**
- Em dashes (ZERO allowed)
- Title Case in hooks

**Tone:**
- Bro energy
- Woo energy
- Therapy-speak
- Hedging (maybe, perhaps)

---

## INTEGRATION WITH OTHER SKILLS

**Email Writer (`/sc:email-writer`):**
- Generate 3-5 hooks for email opening
- Match emotional system to email position in sequence

**Advertorial Agent (future):**
- Generate hook variations for A/B testing
- Create curiosity loops for long-form

**Copy Chief Agent (future):**
- Review hooks for CTR optimization
- Tighten language

---

## NEO4J QUERY EXAMPLES

### Search for hooks by emotion
```bash
curl -s "http://72.61.78.89:8001/api/graphiti/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "fear anxiety hooks analytical empaths"}'
```

### Search for hooks by category
```bash
curl -s "http://72.61.78.89:8001/api/graphiti/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "burnout exhaustion hooks"}'
```

### Search for hooks by pain point
```bash
curl -s "http://72.61.78.89:8001/api/graphiti/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "imposter syndrome fraud feeling"}'
```

---

## EXAMPLE OUTPUTS

### Identity Hooks (PANIC + SEEKING)
1. Have you noticed that the version of you everyone applauds does not actually exist?
2. That high-achiever personality you have been maintaining for 20 years. When did it stop being you?
3. You are performing a character 24/7 and everyone thinks that character is having the time of their life.
4. The professional armor you built to survive the corporate world is now the prison you cannot get out of.
5. You have become a stranger to yourself. And the scary part is, nobody can tell.

### Burnout Hooks (FEAR + RAGE)
1. Your burnout is not showing up as exhaustion. It is showing up as numbness.
2. You are not tired. You are hollowed out.
3. Burnout in high achievers does not look like a breakdown. It looks like checking out.
4. You can still perform. You just cannot remember why it matters.
5. The most dangerous burnout is the kind where you keep going because you do not know how to stop.

### Transformation Hooks (LUST + PLAY)
1. What if you could feel like yourself again without having to rebuild everything from scratch?
2. What would it feel like to wake up without the dread?
3. There is a version of your life where you are fully alive and not just fully functional.
4. People who make the change describe a stillness they have never felt before.
5. It is possible to be driven and calm at the same time. Most high achievers have never experienced that.
