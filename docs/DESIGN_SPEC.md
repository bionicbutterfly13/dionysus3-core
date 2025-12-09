# DESIGN_SPEC.md - Inner Architect System Visual Experience

## Executive Summary

This design specification outlines the visual and interaction experience for the Inner Architect System (IAS) coaching app. The goal is to create an experience that feels like talking to a wise mentor, not using a therapy app.

**Mobile-forward, web-first**: Designed primarily for mobile web browsers, works on desktop.

---

## 1. Visual Tone: "Grounded Wisdom"

The visual tone should evoke:
- **A private study or library** - not a doctor's office
- **Late evening conversation** - intimate, unhurried
- **Well-worn leather journal** - personal, lived-in, trusted
- **Candlelight rather than fluorescent** - warm, focused attention

**Key Principles:**
1. **Warmth over sterility**: Avoid pure whites and clinical blues
2. **Depth over flatness**: Use subtle shadows and layering
3. **Organic over mechanical**: Rounded corners, breathing animations
4. **Confident restraint**: Premium feel through what is NOT shown

**Anti-patterns to avoid:**
- Medical/therapy aesthetic (clipboards, clinical progress bars)
- Gamification (badges, streaks, points)
- Corporate SaaS (dashboards, metrics-heavy)
- Social media patterns (likes, shares)

---

## 2. Color Palette

### Primary Palette (Aligned with innerarchitectsystem.com)

| Name | Hex | Usage |
|------|-----|-------|
| **Deep Navy** | `#0F172A` | Primary backgrounds, header |
| **Slate** | `#1E293B` | Secondary backgrounds, cards |
| **Architectural Gold** | `#D4AF37` | Primary accent, CTAs, highlights |
| **Off-White** | `#F8FAFC` | Text on dark, light backgrounds |
| **Muted Gold** | `#C5A059` | Secondary accent, button variants |

### Supporting Palette

| Name | Hex | Usage |
|------|-----|-------|
| **Sage** | `#7D8471` | Success states, completed steps |
| **Dusty Rose** | `#C4A4A4` | Emotional content, obstacles |
| **Cloud** | `#E8E4DD` | Borders, subtle dividers |
| **Ink** | `#333333` | Primary text on light backgrounds |

### Semantic Colors

| State | Color | Note |
|-------|-------|------|
| Confidence Low | Dusty Rose | Not alarming red |
| Confidence Medium | Muted Copper | Warm, progressing |
| Confidence High | Aged Gold | Achievement without gamification |
| Error | `#8B4049` | Muted burgundy |
| Focus | Aged Gold at 20% opacity | Subtle highlight |

---

## 3. Typography

### Font Pairing
- **Headings**: Playfair Display (serif) - wisdom, gravitas
- **Body**: Inter (sans-serif) - clarity, readability

### Scale
**Desktop:**
- H1: 48px (Playfair, 600)
- H2: 36px (Playfair, 600)
- H3: 28px (Playfair, 500)
- Body: 18px (Inter, 400)
- Secondary: 16px (Inter, 400)
- Meta: 14px (Inter, 400)

**Mobile:**
- H1: 36px
- H2: 28px
- H3: 24px
- Body: 18px (maintain readability)

### Guidelines
- Line height: 1.6-1.7 for body text
- Letter spacing: +0.02em on headings
- Max line length: 65 characters

---

## 4. Key UI Components

### 4.1 Chat Interface

**Message Styling:**
```
User Messages:
- Background: Warm Slate (#2D3142)
- Text: Soft Ivory (#F5F2EB)
- Corner radius: 20px (4px top-right)
- Subtle inner shadow

Coach Messages:
- Background: Soft Ivory (#F5F2EB)
- Text: Ink (#333333)
- Corner radius: 20px (4px top-left)
- Aged Gold left border (2px)
```

**Coach Avatar:**
- Size: 48px (touch-friendly)
- Subtle breathing animation (scale 1.0 to 1.02, 4s cycle)
- Indicates presence

**Typing Indicator:**
- Rotating text: "Reflecting..." / "Considering..." / "Understanding..."
- Aged Gold glow behind indicator

**Input Area:**
- Contextual placeholders:
  - Initial: "Share what's on your mind..."
  - Mid-conversation: "Tell me more..."
  - Deep: "What comes up for you?"

### 4.2 Clarity Indicator (Confidence Meter Redesign)

**Concept: "Focus Lens"** - not a progress bar

- Circular element that starts blurry
- Progressively sharpens as confidence increases
- At 100%, reveals a clear symbol
- No percentage shown
- Micro-copy: "Finding your focus area" → "Almost there" → "Found it"

**Metaphor**: Bringing the block into focus, not grading the user.

### 4.3 Diagnosis Reveal

**Phase 1: Building Anticipation (2-3s)**
- Background dims slightly
- Text: "I see something emerging..."
- JourneyMap appears with all nodes dimmed

**Phase 2: The Reveal (1-2s)**
- User's specific step lights up with Aged Gold glow
- Connecting lines animate from start to position
- Step name appears in large Playfair Display

**Phase 3: Context (3-4s hold)**
- Diagnosis card animates up from bottom
- Contains: Phase name, Step name, Obstacle identified, Brief explanation
- CTA: "Let's work with this"

### 4.4 WOOP Planner

**Visual Differentiation Per Step:**

| Step | Icon | Accent | Style |
|------|------|--------|-------|
| Wish | Star | Aged Gold | Inspirational |
| Outcome | Sunrise | Copper | Sensory |
| Obstacle | Mountain | Dusty Rose | Direct |
| Plan | Compass | Sage | Grounded |

**Step Transitions:**
- Wish: Fade up (aspiration rising)
- Outcome: Expand from center (vision expanding)
- Obstacle: Subtle shake then settle (confronting reality)
- Plan: Slide in from bottom (grounding into action)

### 4.5 Journey Visualization (Tree Metaphor)

**Concept: Single tree representing growth**

- REVELATION (Steps 1-3): Roots being uncovered
- REPATTERNING (Steps 4-6): Trunk strengthening
- STABILIZATION (Steps 7-9): Branches/leaves growing

**Visual:**
- SVG-based illustration
- Muted earth tones for completed sections
- Aged Gold glow for current position
- Future sections as dotted/ghosted lines
- Touch-friendly hit areas

---

## 5. Micro-Interactions

### Presence Indicators
- Coach "breathing" while listening (subtle scale pulse)
- Attention cue after 5s user pause (avatar tilts)

### Response Timing
- 0.5-1.5s thinking delay (scales with input complexity)
- Variable typing speed (slow at emotional moments)

### Emotional Acknowledgment
- Subtle "received" animation on send
- Aged Gold pulse on success
- Phase transitions: Background color shift

### Error States
Conversational, not technical:
- "I lost my train of thought. Could you say that again?"
- "Something interrupted us. Let's try that again."

### Contextual Micro-Copy
- Empty: "Ready when you are."
- Generating: "Crafting something just for you..."
- After deep share: "That took courage to name."
- After WOOP wish: "A worthy aim."

---

## 6. Mobile-First Considerations

### Touch Targets
- Minimum: 48px × 48px
- Avatar: 48px (not 40px)
- Send button: Full tap area
- Plan cards: Adequate

### Thumb-Zone Optimization
- Input at bottom of viewport
- Primary actions within thumb reach
- WOOP "Next" buttons full-width

### Safe Areas
```css
padding-top: env(safe-area-inset-top);
padding-bottom: env(safe-area-inset-bottom);
```

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  .animate-bounce, .animate-pulse { animation: none; }
  transition-duration: 0ms;
}
```

### Dark Mode
- Default to dark (matches "evening study" tone)
- Light mode optional
- Use `prefers-color-scheme` for system preference

---

## 7. Animation Specification

### Timing Functions
```css
--ease-gentle: cubic-bezier(0.4, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
--ease-breathe: cubic-bezier(0.37, 0, 0.63, 1);
```

### Duration Scale
```css
--duration-instant: 100ms;
--duration-fast: 200ms;
--duration-normal: 300ms;
--duration-slow: 500ms;
--duration-reveal: 800ms;
--duration-breathe: 3000ms;
```

### Key Animations

| Element | Animation | Duration |
|---------|-----------|----------|
| Coach avatar (idle) | Scale 1.0-1.02 | 3s loop |
| Message appear | Fade + slide up 8px | 300ms |
| Diagnosis reveal | Fade + scale 1.05→1.0 | 800ms |
| Step highlight | Scale 1.0→1.5 | 700ms |
| WOOP step enter | Fade + slide 16px | 500ms |

---

## 8. Implementation Priorities

### Phase 1: Quick Wins (1-2 days)
1. Update color palette in Tailwind config
2. Adjust avatar sizes to 48px
3. Add coach breathing animation
4. Conversational error messages

### Phase 2: Core Enhancements (3-5 days)
1. Clarity Indicator (Focus Lens)
2. Enhanced Diagnosis Reveal
3. Contextual placeholder text
4. WOOP step transitions

### Phase 3: Full Vision (1-2 weeks)
1. Tree metaphor journey visualization
2. Natural response timing
3. Micro-copy throughout
4. Mobile polish and safe areas

---

## 9. Critical Files

| File | Purpose |
|------|---------|
| `inner-architect-companion/index.html` | Tailwind config, color definitions |
| `inner-architect-companion/App.tsx` | Main view states, layout |
| `inner-architect-companion/components/ConfidenceMeter.tsx` | Redesign to Clarity Indicator |
| `inner-architect-companion/components/VisualMap.tsx` | Redesign to Tree metaphor |
| `inner-architect-companion/components/WoopSession.tsx` | Enhanced transitions |

---

## 10. Brand Alignment

**"Success Without Sabotage"**

Every design choice should reinforce:
- You're not broken, you're blocked
- This is about growth, not fixing
- Wisdom over instruction
- Partnership, not prescription

The interface should feel like the space Dr. Mani creates in his hypnotherapy sessions: safe, warm, focused, and transformative.
