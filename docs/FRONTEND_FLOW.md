# FRONTEND_FLOW.md - Complete User Flow Design Document

## Executive Summary

The Inner Architect System frontend is a React 19 single-page application that guides users through a 4-phase coaching experience:

1. **Chat/Discovery** - Conversational exploration with the IAS coach
2. **Diagnosis Reveal** - Visual mapping of user's position in the 9-step framework
3. **WOOP Planning** - Structured goal-setting with AI-generated implementation plans
4. **Final Brief** - Summary with optional audio briefing and practice plan

**Current State Analysis:**
- Frontend uses stateless mode (passes full message history per request)
- Local storage persistence exists but backend session persistence is also available
- The dionysus API is live at `https://dionysus-api-x7mu.onrender.com`
- ViewState machine: `'chat' | 'diagnosis' | 'woop' | 'final'`

---

## User Journey Map

```
                           FIRST-TIME USER
                                 |
                                 v
+------------------------------------------------------------------+
|                        ONBOARDING                                |
|  "Where are you right now?" - single inviting question           |
|  No account creation, no friction, just start talking            |
+------------------------------------------------------------------+
                                 |
                                 v
+------------------------------------------------------------------+
|                      CHAT/COACHING SESSION                       |
|  Conversational flow with confidence meter (0-100%)              |
|  Coach asks ONE clarifying question at a time                    |
|  Visual: User messages right, Coach messages left with avatar    |
|  Typing effect creates human-like response appearance            |
+------------------------------------------------------------------+
                                 |
                          confidence >= 85%
                                 |
                                 v
+------------------------------------------------------------------+
|                     DIAGNOSIS REVEAL                             |
|  1.5s delay for dramatic effect                                  |
|  "Locating your position in the framework..." spinner            |
|  VisualMap scrolls to highlight their specific step (1-9)        |
|  2s animation then auto-advance to WOOP                          |
+------------------------------------------------------------------+
                                 |
                                 v
+------------------------------------------------------------------+
|                        WOOP PLANNING                             |
|  4-step wizard: Wish -> Outcome -> Obstacle -> Plan              |
|  AI generates 3 If-Then implementation intentions                |
|  User selects one that resonates                                 |
+------------------------------------------------------------------+
                                 |
                                 v
+------------------------------------------------------------------+
|                        FINAL BRIEF                               |
|  Practice plan locked in visual card                             |
|  Insight + Contrarian Truth side by side                         |
|  Audio briefing (TTS of step intro script) - currently stubbed   |
|  "Start a new session" to reset                                  |
+------------------------------------------------------------------+
```

---

## Screen-by-Screen Breakdown

### Screen 1: Chat Interface (ViewState: 'chat')

**Purpose:** Build rapport and gather enough information to diagnose the user's position in the IAS framework.

**Visual Layout:**
```
+----------------------------------------------------------+
|  [M]  Inner Architect System    [Confidence: 45%] -----  |
+----------------------------------------------------------+
|                                                          |
|   [Empty State]                                          |
|   "Where are you right now?"                             |
|   Tell me about your current situation, and we'll        |
|   find the specific block holding you back.              |
|                                                          |
+----------------------------------------------------------+
|  Chat Messages Area (scrollable)                         |
|                                                          |
|  [Sparkles] Coach:                                       |
|  "It sounds like you're experiencing..." [typing effect] |
|                                                          |
|                              [User]:                     |
|                              "I keep procrastinating..." |
|                                                          |
+----------------------------------------------------------+
|  [Glow Border]                                           |
|  [ I'm feeling...                          [Mic] [Send] ]|
+----------------------------------------------------------+
```

**Components Used:**
- `ConfidenceMeter` - Shows analysis progress (red < 40, yellow < 75, green >= 75)
- `TypingEffect` - Humanizes AI responses with character-by-character rendering
- Chat bubbles with avatars (User icon vs Sparkles icon)

**API Call:**
```typescript
// services/dionysus.ts - interactWithGuide()
POST /ias/chat
{
  "messages": [
    { "role": "user", "content": "I keep procrastinating on important tasks..." },
    { "role": "assistant", "content": "It sounds like..." },
    // ... full conversation history (stateless mode)
  ]
}

Response:
{
  "response": "Coach's reply text",
  "confidence_score": 65,
  "status": "gathering_info",  // or "complete"
  "diagnosis": null  // populated when status is "complete"
}
```

**State Management:**
```typescript
// App.tsx state
const [viewState, setViewState] = useState<ViewState>('chat');
const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
const [input, setInput] = useState('');
const [loading, setLoading] = useState(false);
const [analysisState, setAnalysisState] = useState<AnalysisResponse | null>(null);
```

**Transition Trigger:**
When `response.status === 'complete'` and `response.diagnosis` is present, after 1.5s delay:
```typescript
setTimeout(() => setViewState('diagnosis'), 1500);
```

---

### Screen 2: Diagnosis Reveal (ViewState: 'diagnosis')

**Purpose:** Create a meaningful reveal moment showing the user where they are in the 9-step framework.

**Visual Layout:**
```
+----------------------------------------------------------+
|  [M]  Inner Architect System             [New Session]   |
+----------------------------------------------------------+
|                                                          |
|                    Your Journey                          |
|  [--1--]--[--2--]--[--3--]--[--4--]--[--5--]--[--6--]   |
|          REVEAL      ^        IGNITE       ALIGN         |
|                     150%                                 |
|                  (Current)                               |
|                                                          |
+----------------------------------------------------------+
|                                                          |
|        Locating your position in the framework...        |
|                   [Spinning loader]                      |
|                                                          |
+----------------------------------------------------------+
```

**Components Used:**
- `VisualMap` - Horizontal scrolling journey map with 9 steps in 3 phases
  - Phases: Reveal (1-2-3), Ignite (4-5-6), Align (7-8-9)
  - Current step scales to 150% with gold border
  - Past steps show checkmarks
  - Auto-scrolls to active step on mount

**Timing/Animation:**
1. VisualMap mounts and auto-scrolls to current step
2. 1 second for scroll animation
3. `onAnimationComplete` callback fires
4. 2 second pause for user to absorb
5. Auto-advance to WOOP: `setTimeout(() => setViewState('woop'), 2000)`

**No API Call:** Diagnosis data comes from previous chat response.

**Diagnosis Data Structure:**
```typescript
interface Diagnosis {
  stepId: number;      // 1-9
  actionId: number;    // 1-3
  obstacleId: number;  // 0-2
  explanation: string;
  contrarianInsight: string;
}
```

---

### Screen 3: WOOP Planning (ViewState: 'woop')

**Purpose:** Guide user through structured goal-setting using WOOP methodology (Wish, Outcome, Obstacle, Plan).

**4-Step Flow:**

| Step | Icon | Title | Prompt | Input Type |
|------|------|-------|--------|------------|
| 1 | Sparkles | The Wish | "What is one specific goal or state of being you want to achieve regarding this block?" | Textarea |
| 2 | Flag | The Outcome | "If you fulfilled this wish, what is the best thing you would feel or experience? Visualize it." | Textarea |
| 3 | AlertTriangle | The Inner Obstacle | "We've identified what holds you back. Acknowledge it fully." | Display only (from diagnosis) |
| 4 | Check | The Plan (If-Then) | "Select the implementation intention that resonates most with you:" | Radio selection from AI-generated plans |

**API Call (Step 3 -> Step 4):**
```typescript
// services/dionysus.ts - generateWoopPlan()
POST /ias/woop
{
  "wish": "I want to feel calm when facing deadlines",
  "outcome": "I would feel a sense of lightness and control",
  "obstacle": "Fear of Confronting Personal Flaws",  // from diagnosis
  "diagnosis_context": "The user's pattern of avoidance stems from..."
}

Response:
{
  "plans": [
    "If I notice myself avoiding a task, then I will pause, take 3 breaths, and commit to just 5 minutes.",
    "If I feel overwhelmed by a deadline, then I will break the task into the smallest possible step and do only that.",
    "If I start criticizing myself for procrastinating, then I will acknowledge the feeling and redirect to one concrete action."
  ]
}
```

**State Management (WoopSession.tsx):**
```typescript
const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
const [wish, setWish] = useState('');
const [outcome, setOutcome] = useState('');
const [plans, setPlans] = useState<string[]>([]);
const [selectedPlan, setSelectedPlan] = useState('');
const [loading, setLoading] = useState(false);
```

**Transition:**
User clicks "Lock in This Plan" with a selected plan -> `onComplete(selectedPlan)` -> Parent sets `viewState('final')`

---

### Screen 4: Final Brief (ViewState: 'final')

**Purpose:** Provide a summary of the session with the locked-in practice plan and optional audio briefing.

**Data Displayed:**
- `woopPlan` - The selected If-Then implementation intention
- `diagnosis.explanation` - Why this block applies
- `diagnosis.contrarianInsight` - Reframing insight
- `currentStep.title` - e.g., "Breakthrough Mapping"
- `currentStep.introScript` - For audio briefing

**Actions:**
- "Start a new session" -> `handleReset()` clears all state and localStorage

---

## Session Persistence

### Current Implementation (localStorage)

```typescript
// Load on mount
useEffect(() => {
  const saved = localStorage.getItem('ias_session');
  if (saved) {
    const data = JSON.parse(saved);
    setChatHistory(data.chatHistory || []);
    setAnalysisState(data.analysisState || null);
    setWoopPlan(data.woopPlan || '');
    setViewState(data.viewState || 'chat');
  }
}, []);

// Save on state change
useEffect(() => {
  localStorage.setItem('ias_session', JSON.stringify({
    chatHistory,
    analysisState,
    woopPlan,
    viewState
  }));
}, [chatHistory, analysisState, woopPlan, viewState]);
```

### Backend Session Support (Available)

**Endpoints:**
```
POST /ias/session        -> Create new session (returns session_id)
GET  /ias/session/{id}   -> Get session state
POST /ias/chat           -> Supports session_id parameter
POST /ias/diagnose       -> Uses session_id to analyze stored conversation
```

---

## API Reference Summary

| Endpoint | Method | Purpose | Request Body | Response |
|----------|--------|---------|--------------|----------|
| `/ias/chat` | POST | Main coaching conversation | `{ messages: [...] }` | `{ response, confidence_score, status, diagnosis? }` |
| `/ias/woop` | POST | Generate implementation plans | `{ wish, outcome, obstacle, diagnosis_context }` | `{ plans: [...] }` |
| `/ias/session` | POST | Create new session | - | `{ session_id, created_at }` |
| `/ias/session/{id}` | GET | Get session state | - | `{ session_id, message_count, confidence_score, status, has_diagnosis }` |
| `/ias/diagnose` | POST | Force diagnosis from session | `{ session_id }` | Full diagnosis response |
| `/ias/framework` | GET | Get full IAS framework | - | `{ framework: [...] }` |
| `/ias/recall` | GET | Memory search | `?query=...&limit=10` | `{ memories: [...] }` |

---

## UX Design Principles

1. **Conversational, Not Clinical**
   - Coach speaks naturally, not in bullet points
   - One question at a time builds trust
   - Typing effect creates presence

2. **Progressive Revelation**
   - Confidence meter shows progress without pressure
   - Diagnosis reveal is a moment of insight, not judgment
   - Visual map provides context without overwhelming

3. **Empowerment Over Prescription**
   - User chooses their own implementation plan
   - Contrarian insight challenges without criticizing
   - "Lock in" language gives ownership

4. **Minimal Friction**
   - No signup required to start
   - Local persistence handles casual use
   - Clear reset option without guilt

---

## Critical Files

- `/Volumes/Asylum/dev/inner-architect-companion/App.tsx` - Core application logic
- `/Volumes/Asylum/dev/inner-architect-companion/services/dionysus.ts` - API client
- `/Volumes/Asylum/dev/inner-architect-companion/components/WoopSession.tsx` - WOOP wizard
- `/Volumes/Asylum/dev/dionysus3-core/api/routers/ias.py` - Backend API endpoints
- `/Volumes/Asylum/dev/inner-architect-companion/constants.ts` - IAS_FRAMEWORK definition
