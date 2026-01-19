---
name: Bullet Campaign Strategy (Master Protocol)
description: The authoritative "Ultrathink" protocol for the E5 Bullet Campaign. A systematic, evergreen cash extraction system maximizing offer frequency without list burnout.
version: 2.1
status: Stable
source: Todd Brown (Bullet Campaign Masterclass)
---

# Bullet Campaign Master Protocol

> **Core Mantra:** "More Offers, More Frequently, Without Burnout."

## 1. The Strategic Philosophy (The "Why")

### The "Newsstand" Reality
You own a newsstand in Times Square (your list). You pay rent (hosting/CRM) and staff (team) every day.
*   **The Error:** Opening the window only once a month (Launches).
*   **The Fix:** Open the window *every day*. Give people the *opportunity* to buy daily.

### "Singles" vs. "Grand Slams"
*   **Launch Mindset:** High pressure. Must hit a Grand Slam ($1M+). If it fails, the quarter is ruined. High stress.
*   **Bullet Mindset:** consistently hit "Singles" and "Doubles" ($40k - $100k).
    *   If one strikes out? Who cares. We fire another next week.
    *   **The Target:** 45 Bullets per year.
    *   **Result:** Cumulative, stress-free revenue that often outperforms the "big launch" annual total.

### The "Filter & Funnel" Mechanism
We do not pound the house list with offers. We pound them with *opportunities to raise their hand*.
1.  **The Filter (Phase A):** Validates interest.
2.  **The Funnel (Phase B):** Pitches the interested.
3.  **The Outcome:** The 90% who aren't interested *never see the pitch*, preserving the "Golden Goose" (List Responsiveness).

---

## 2. Asset Mining: Where do Bullets Come From?

Don't create from scratch. You are sitting on a goldmine of "dormant assets".
**The "Old Hard Drive" Audit:**
*   **Private Calls:** Recordings of "private" consults or chats with experts (e.g., "I called Paris to talk to John Ford").
*   **Old QA Sessions:** 20 valuable minutes from a 60-minute coaching call.
*   **Deleted Webinars:** The content is still gold, even if the offer expired years ago.
*   **Guest Appearances:** Talks you gave on other masterminds or podcasts.
*   **Presentations:** Keynotes or workshops from years ago.

**The Packaging Hook:**
Frame the asset as a "Private Insight" or "Discovery."
*   *Example:* "I found this hidden recording..."
*   *Example:* "I called [Expert] to ask the one question nobody is asking..."

---

## 3. The Architecture (The "How")

### Phase A: The Interest Sequence (The Filter)
*   **Goal:** Generate a **Click** (Hand-Raise).
*   **Structure:** 3 Days, 2 Emails/Day (AM/PM). Total 6 Emails.
*   **The Rule of "Semi-Blind" Copy:**
    *   **Do Not:** Be totally blind ("I have a secret, click here"). This fills the funnel with curiosity-seekers who won't buy.
    *   **Do Not:** Pitch the product ("Buy my course"). This burns the list.
    *   **Do:** Tease the *Topic/Benefit* ("The one hormone stopping fat loss," or "Why old hooks fail").
*   **The "Paris" Hook Framework (Example):**
    *   **Email 1 (Narrative):** "Why I called Paris..." (The story of seeking the answer).
    *   **Email 2 (Problem):** "The New Marketing Blindness" (Why the old way is broken).
    *   **Email 3 (Credibility):** "The Legend behind the $100M copy."
    *   **Email 4 (Insight):** "The one forbidden word."
    *   **Email 5/6 (Urgency):** "Closing the vault on this recording."
*   **Logic:**
    *   **Click?** -> Stop Phase A -> Start Phase B immediately.
    *   **No Click?** -> Campaign Ends. They remain "Cool".

### Phase B: The Conversion Sequence (The Pitch)
*   **Logic:** "The Car Lot." Once they walk on the lot (Click), treat them as a buyer. No further segmentation. Pitch hard.
*   **Structure:** 3 Days (Dynamic).
*   **Cadence:**
    *   Day 1: 2 Emails (AM/PM)
    *   Day 2: 2 Emails (AM/PM)
    *   Day 3: 4 Emails (The "Closeout" Stack)
*   **Logic:** Uniformity. Every lead gets the exact same experience to preserve metric integrity.
*   **Tagging Rule:** Apply `in_campaign_donotmail`.
    *   **Why?** Do not introduce variables (other broadcasts, newsletters) while they are in the "lab" of the campaign. Only science allowed here.

### Phase C: The Dynamic Deadline (The Engine)
*   **The "Trickle Effect":** Because the deadline is *individual* to the user's click time, a bullet fired 3 weeks ago will still generate unrelated sales today from stragglers. This creates a compounding "revenue layer" on top of current promotions.
*   **Mechanics:**
    *   Deadline = (Time remaining in current day) + 3 Full Days.
    *   Expires @ 11:59 PM of Day 3.
*   **The "Expired Redirect" Tactic (Revenue Multiplier):**
    *   **Never** send to a dead "Sorry, expired" page.
    *   **The Setup:**
        1.  User clicks expired link.
        2.  Land on Page A: Shows a "Loading/Checking" GIF. Text: "Offer Expired... Redirecting to [Downsell/Alternative]..."
        3.  Wait 2-3 seconds.
        4.  Redirect to Page B: A dedicated sales page for a logical next step or downsell.
    *   **Result:** Monetizes the "late" traffic instead of blocking it.

---

## 4. Technical Implementation Protocol

### 1. Tagging Schema
*   `bullet_[name]_start` -> Applied at trigger.
*   `bullet_[name]_clicked` -> Applied on Interest Click. (Goal of Phase A).
*   `bullet_[name]_purchased` -> Goal of Phase B.
*   `status_in_campaign_donotmail` -> **Global Exclusion Tag.**

### 2. The Flow (Automation)
```mermaid
graph TD
    A[Start: List Selection] -->|Format: Sunday Night| B(Queue Phase A)
    B -->|Wait: Monday 08:30| C[Phase A: Interest Sequence]
    C --> D{Click?}
    D -- No (3 Days) --> E[End Campaign]
    D -- Yes --> F[Stop Phase A]
    F --> G[Apply: in_campaign_donotmail]
    G --> H[Redirect to Sales Page]
    H --> I[Trigger: Dynamic Deadline (3 Days)]
    I --> J[Phase B: Conversion Sequence]
    J --> K{Purchase?}
    K -- Yes --> L[Thank You Seq]
    K -- No --> M[Remove Tags & Exit]
```

### 3. The Deadline Tooling
*   **Software:** Countdown Hero / Deadline Funnel.
*   **Trigger:** "First Page Visit" (Pixel based).
*   **Expiration:** Redirects to the "GIF Redirect" Page.

---

## 5. Execution Targets

*   **Frequency:** Fire a new Bullet every week (or minimum every 2 weeks).
*   **Annual Target:** 45 Bullets.
*   **Consistency:** The system works because of the *volume of swings*.
*   **Metric of Success:** Ideally 80%+ of total email revenue comes from these automated "Singles".

## 6. Detailed Step-by-Step Instructions

**(Follow this exactly to launch your first Bullet Campaign)**

### Step 1: Preparation & Asset Mining (Duration: 2-3 Hours)
1.  **Select the Asset:** Find a 20-30 minute piece of existing content (video, audio, old webinar, interview). It must deliver *value* on its own.
2.  **Select the Offer:** Define what you are selling (e.g., The Masterclass, The Bundle, The Coaching Call).
3.  **Define the Hook:** Write out the "story wrapper" (e.g., "I called Paris...").
4.  **Create the Redirect Page (One-Time):** Build the generic "Offer Expired... Redirecting" page with the loading GIF. Set it to redirect to your generic "Downsell" or "Waitlist" page after 3 seconds.

### Step 2: Tech Setup (Duration: 1 Hour)
1.  **Deadline Software:**
    *   Create a new campaign in Countdown Hero/Deadline Funnel.
    *   Set duration: **3 Days**.
    *   Set trigger: **Page Visit**.
    *   Set Expiration URL: **Your Redirect Page** from Step 1.4.
    *   Copy the script code.
2.  **Sales Page:**
    *   Duplicate your existing sales page.
    *   Paste the Deadline Script into the header.
    *   Test: Visit the page. Confirm the timer appears. Wait 3 days (or simulate) and confirm redirect works.

### Step 3: Interest Sequence (Phase A) (Duration: 2 Hours)
1.  **Write Email 1 (Monday AM):** "The Hook". Introduce the narrative. Link to the Sales Page. *Do not pitch*.
2.  **Write Email 2 (Monday PM):** "The Problem". Why the old way fails. Link to the Sales Page.
3.  **Write Email 3 (Tuesday AM):** "The Credibility". Why this expert/method is legit. Link to Sales Page.
4.  **Write Email 4 (Tuesday PM):** "The Insight". One specific nugget. Link to Sales Page.
5.  **Write Emails 5 & 6 (Wednesday):** Urgency for the *content* disappearing (or the "recording going into the vault").
6.  *Key:* Ensure all links go to the Sales Page (where the timer will start).

### Step 4: Conversion Sequence (Phase B) (Duration: 2 Hours)
1.  **Write Day 1 Emails (2x):** Shift tone. "Hope you enjoyed the video... Did you see the offer?" Focus on the product.
2.  **Write Day 2 Emails (2x):** Social Proof. Case studies. "If you're on the fence..."
3.  **Write Day 3 Emails (4x):** Hard Deadline.
    *   08:30 AM: "Last Day."
    *   01:30 PM: "Logic/Reason."
    *   06:30 PM: "Warning."
    *   11:00 PM: "Final Notice."
4.  *Key:* Use the Deadline Software synchronization to show the *correct* time remaining in the email body (optional but recommended).

### Step 5: Automation Build (Duration: 45 Mins)
1.  **Create Workflow A (Interest):**
    *   Trigger: `bullet_[name]_start` tag.
    *   Action: Send Interest Emails 1-6.
    *   **Goal Goal:** Link Click.
    *   **If Click:** Stop Workflow A. Apply `bullet_[name]_clicked`. Start Workflow B.
2.  **Create Workflow B (Conversion):**
    *   Trigger: `bullet_[name]_clicked`.
    *   Action: Apply `in_campaign_donotmail`.
    *   Action: Send Conversion Emails (Day 1-3).
    *   Action: Remove `in_campaign_donotmail` at end.

### Step 6: Launch (Duration: 10 Mins)
1.  **Select Segment:** Your main house list.
2.  **Exclude:** `purchased_[product]` AND `in_campaign_donotmail`.
3.  **Apply Tag:** `bullet_[name]_start`.
4.  **Schedule:** Set the tag to apply on Sunday night or Monday morning.
5.  **Monitor:** Check for the "Trickle Effect" over the next 14 days.
