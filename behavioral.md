# Behavioral + resume prep for the TikTok e-commerce intern round

TikTok round 1 spends 10–15 minutes here. Interviewers reported asking about: a project in
depth (design choices, hardest bug, what you'd change), "why TikTok / why e-commerce",
"any e-commerce experience", how you use AI coding tools (it's in the JD), teamwork across
time zones (team is global; Seattle + Singapore + China), and availability/dates.

## 1. 90-second self-intro (write yours here, then say it out loud 3 times)

Template: who you are (degree, year, graduation) → 1 sentence on what you like building →
the project you want them to ask about (what, your role, one number) → why this role.

> "I'm ___, a ___ student at ___ graduating ___. I like backend work where correctness
> under load matters. Most recently I built ___, where I owned ___ and got ___ (a number:
> latency, throughput, bugs found, users). I'm interested in the e-commerce team because
> orders, inventory and payments are exactly the kind of system where a small consistency
> bug becomes real money, and I want to learn how that's done at TikTok's scale."

## 2. Project deep-dive: prepare ONE project with these answers ready

- What problem, for whom, what was your part (be precise: "I wrote the ingest and the
  storage layer; a teammate did the UI").
- Architecture in 4 sentences: components, data flow, storage, why those choices.
- The hardest bug: symptom → how you found it (logs? metrics? bisect?) → root cause → fix →
  what you added so it can't recur (test, alert). Interviewers reported asking
  "how did you measure P50/P99 before and after", "how do you know async logging finished",
  "what happens to logs on power loss" — have a measurement story.
- A trade-off you made consciously (consistency vs latency, simplicity vs generality).
- What you'd change now. (Say something real, e.g. "I'd put the queue in front of the DB writes".)
- Scale: what breaks first at 10x and what you'd do.

## 3. "Why TikTok / why Global E-Commerce?"

Concrete beats generic. Know these facts:
- TikTok Shop = content-driven commerce: short video + LIVE + product links + affiliate
  creators; the JD says "make more affordable and high-quality products sell easily".
- The backend problems are the classic hard ones: inventory during LIVE spikes, order
  state machines across sellers/warehouses/payment providers, promotions and coupons,
  cross-border (currency, tax, logistics), fraud/risk, and search/recommendation.
- Say what you want to learn: high-concurrency services in Go/Java, MQ-based
  architectures, and how AI tools are used in their dev workflow (JD mentions it).

## 4. "Any e-commerce experience?"

If none: "Not professionally. I prepared by building [the practice components in this
folder: an inventory reservation service with expiry, an order state machine with
idempotent events, a cart pricing engine with coupon stacking] and by reading about how
flash sales avoid overselling — Redis atomic decrement as the gate, DB conditional update
as the truth, MQ to smooth the burst." Then ask them what their team owns.

## 5. "How do you use AI-assisted coding tools?" (JD bullet, likely 1 question)

- Where it helps: boilerplate, tests, explaining unfamiliar code, drafting docs/commit
  messages, brainstorming edge cases, rubber-ducking a bug.
- Where you stay in control: design decisions, correctness (you run the tests), security
  (no secrets in prompts), reading every generated line.
- One story: a time it produced a plausible but wrong answer and how you caught it.
- Bonus: you used it to build this prep (mock interviews, reference solutions you compared
  against your own) — that is a legitimate, honest example.

## 6. Standard behavioral set (STAR, 60–90 s each; prepare the situation once, reuse)

- A time you disagreed with a teammate about a technical choice.
- A time you missed a deadline or shipped a bug; what changed after.
- A time you learned a new technology fast.
- A time you took ownership of something nobody asked you to.
- How you handle ambiguous requirements.
- Working across time zones / asynchronously (their team is global).

## 7. Questions to ask them (pick 2)

- "What does the intern project typically look like — a feature end-to-end, or a component inside a larger service?"
- "Which parts of the stack does this team own: order, inventory, promotions, logistics?"
- "How does the team use AI tools day to day, and what has actually stuck?"
- "What does a good first month look like for an intern here?"
- "How does the Seattle team split work with Singapore/China time zones?"

## 8. Logistics they will ask

- Start/end dates (JD asks to state availability), 12-week program, Seattle location,
  work authorization, graduation date, whether you applied to other ByteDance roles (max two).
