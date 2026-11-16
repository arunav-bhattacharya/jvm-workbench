# Book voice for JVM Workbench lessons

Part 1 (Concurrency on the JVM) and any lesson the user asks to read "like a real author" are written in
the voice described by the **venkat-voice** skill (installed in the user's Claude profile, so it is
available in every session: use the Skill tool with `venkat-voice`). This file adds what is specific to
this course: how the skill's moves map onto the lesson JSON, the course's house rules, and the examples
Part 1 reuses.

## House rules that win over the skill

From the user and brief/BRIEF.md:

- Very simple English: average sentence about 15 words, rarely over 30, short paragraphs.
- No em dashes or en dashes anywhere (the validator rejects them).
- No banned words from brief/BRIEF.md.
- Every code sample in Java and in Kotlin (the validator enforces it). Java first, then Kotlin as a direct
  translation, noting only what got shorter or safer.
- Facts correct for JDK 25 and Kotlin 2.4; say the version when a fact depends on it.
- No invented biography: "I" for opinions, expectations and reactions only.
- Humor: subtle and rare, as the skill says. Many sections have none.

## Mapping the skill's moves onto the lesson JSON

- `opening` (90 to 180 words): the scene, the easy trap, a link to the previous lesson, the plan. Its
  last line can lead into the warm-up: "Before we start, make a guess, and keep it in mind."
- `warmup`: unchanged contract; word it in the same voice.
- `sections` (3 to 5): one idea each, problem first, the naive version failing in public, one running
  example evolving version by version, honest numbers, one short bold rule at most, and a bridge sentence
  at the end. Headings name the step of the journey, in sentence case, and say plainly what the section
  covers (a reader scanning the table of contents must see the topic, for example "The six states a
  thread lives through", not only "Finding out what the relay is doing").
- `aside` (optional, at most one per lesson): `{"title": "the reader's question", "body": "3 to 6 sentences"}`.
- `recap`: 4 to 6 bullets, one of them stating the limit of today's tool.
- `closing` (60 to 120 words): look back, one concrete thing to search for in the reader's own code,
  then "Next, we'll..." and the question the next lesson answers.
- `analogy`, `in_your_world`, `mistake`: optional when `opening` is present. Weave them into the prose and
  keep one only if it adds something the prose doesn't.
- Try-it steps, worked example, lab steps, quiz "why", explain-back, deeper: same calm voice; contracts
  from brief/BRIEF.md unchanged.
- Validate with `python3 site/validate.py content/lessons/<id>.json` (0 errors), then `python3 site/build.py`.

## Veteran examples for Part 1

Reuse these across the Concurrency on the JVM tracks so new tools are judged on old friends (same
correctness figure first, then complexity and time):

- The ledger: accounts, balances, transfers (races, locks, deadlock, atomics, the capstone).
- The settlement batch: a day of card payments to total (threads, pools, sizing, futures, fork/join,
  virtual threads). conc-01 uses it.
- The outbox relay: a background thread moving payment events to Kafka (thread states, interrupts,
  shutdown, scheduled executors). conc-02 uses it.
- A slow downstream: a card-issuer API that takes 120 ms (IO-bound pools, timeouts, cancellation,
  virtual threads).

Don't force them where an existing lab already uses another example. Keep prose consistent with the labs
and the Try-it demos on disk.

## Private research

Style analyses of the author's books (used to build the skill) live outside the repo, in the session's
scratchpad. They describe techniques only. Never copy text, examples or class names from the books.
