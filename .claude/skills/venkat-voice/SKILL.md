---
name: venkat-voice
description: Write or rewrite JVM Workbench lessons in the teaching voice of a seasoned technical author in the style of Venkat Subramaniam's "Programming Concurrency on the JVM": a scene that opens each lesson, one running example that evolves and gets measured, naive code that fails in public before the fix, rules stated short, every approach given its limits, and a bridge into the next lesson. Use it for Part 1 (Concurrency on the JVM) lessons and any lesson the user asks to read "like a real author".
---

# Writing in the Venkat voice

The goal is a lesson that reads like a chapter from a patient, experienced author who is sitting next
to the reader. It should never feel like a list of facts with headings. Every paragraph should make the
reader want to read the next one.

This skill describes teaching moves. It never copies the book: no sentences, examples or class names
from it. Write everything fresh, about the learner's world (payments, ledgers, card issuers, Kafka,
Quarkus, Temporal).

## The house rules still apply

These come from the user and from brief/BRIEF.md, and they win over anything below:

- Very simple English. Short and medium sentences (aim for about 15 words on average, rarely over 30).
  A non-native reader must never read a sentence twice. Prefer plain words to idioms. One light idiom
  per section at most, and only if its meaning is obvious ("back to the drawing board" is fine,
  "get out of this pickle" is not).
- No em dashes or en dashes, ever. Venkat leans on them; we use a comma, a colon, a period or
  parentheses instead.
- No banned words from brief/BRIEF.md (delve, crucial, leverage, seamless, unlock, and the rest).
- Every code sample in Java and in Kotlin (the validator enforces it). Show Java first, then Kotlin as a
  direct translation, and say only what got shorter or safer.
- Facts must be right and current (JDK 25, Kotlin 2.4). When a fact depends on a version, say the version.
- Don't invent biography. "I" is for opinions, expectations and reactions ("I expected about twice the
  speed", "I prefer to fix one problem at a time", "I find this the most surprising line in the JDK").
  Never claim experiences that didn't happen ("I once worked at a bank..."). For a story, put the reader
  or a plausible team in the scene: "Picture a payments team on the night before a card-network deadline."

## The shape of a lesson

Map the moves onto the lesson JSON fields like this.

### `opening`: the scene, the stumble, the plan (90 to 180 words)

1. Put the reader in a concrete scene with a small stake: a deadline, a surprise, a promise to a
   colleague. Two or three sentences, second person.
2. Admit that the trap is easy to fall into. Say why smart people fall into it. Keep it warm, never
   blaming.
3. Connect to what came before: one sentence that names the previous lesson's idea and the question it
   left open.
4. State the plan in one or two sentences: what we'll build or break, and what the reader will be able to
   do at the end. "In this lesson, we'll..." is fine here, and only here.

The warm-up question follows the opening. Introduce it in the opening's last line when it fits:
"Before we start, make a guess, and keep it in mind."

### `sections`: one idea each, problem first, ending on a bridge

- Start from something the reader can see: a program, an output, a timing, a bug report. Then explain the
  mechanism one level down (what the CPU, the OS, the JVM or the compiler does), so the reader could
  predict a variant. Name the concept only after the picture has done its work.
- Run the naive version first and let it fail in public. Mark it in the listing: `// Naive: this will not
  work`, or a status line such as `// Fixed: the lost update... still pending: the stale read`. Show the
  real output. React calmly ("That's not the total we were hoping for."), then explain the cause.
- One running example per lesson, and when you can, the same few veteran examples across the track
  (see "Veteran examples"). Evolve it version by version: name the versions in prose (the naive
  counter, the synchronized counter, the atomic counter) and fix one defect at a time. Say so:
  "Let's take these one at a time."
- Measure with discipline. Before a run, say what you expect. After it, check correctness first (the same
  total as before, nothing lost), then speed, as a ratio ("about 1.8 times faster"). Admit odd results
  and explain them. Use numbers that came from a real run on the labs, or say they are illustrative.
- Use an everyday scene for a mechanism, then map it to code in one move: "In programming terms, each
  cashier is a thread and the tip jar is the shared field." Keep most analogies to one or two sentences.
  Save an extended analogy (one scene carried through several designs) for at most one lesson in a few.
- Weigh options before writing code. List two or three designs, give each its one flaw, reject the
  losers in a sentence ("Strike that one."), then build the survivor.
- Voice the reader's objection in their words, then answer it: "You may be thinking, 'But every field is
  private.' Private stops other classes. It doesn't stop two threads in the same method."
- End every section with a one-sentence bridge that names the next step: "The counter is correct now,
  but it's slow under load. Next, we'll see why."
- Use "we" for the journey ("Let's run it and see what happens."), "you" for the reader's own code, and
  "I" for opinions. "Let's" is welcome; use it to start an action, not to announce a topic.

### Rules, stated short

When a section has earned a rule, state it as a short sentence followed by an even shorter command, and
put it in bold at most once per section: "**An unguarded shared field is a bug waiting for load. Guard
it.**" Contrast pairs work too: "Wait for the task, not the thread." Never more than one rule per section.

### Every approach gets its limits

Before a lesson ends, say where today's tool stops working and what that costs. Use the limit to motivate
the next lesson. "Locks keep the ledger correct. Put a hundred threads on one account, though, and most of
them just wait in line. That waiting is what the next lesson removes."

### Sidebars (`aside`, optional, at most one per lesson)

A short box for the question a careful reader asks at exactly that point ("Why not just make everything
volatile?"). Title it as the question. Three to six sentences. Use it only when the answer would break
the flow of the section. Most lessons need none.

### Humor

Light and rare: about one aside per section at most, aimed at tools, situations or ourselves, never at the
reader. A mock-dramatic aside or a wry parenthetical works ("The SDK swallows the exception and returns
null, presumably to spare our feelings."). Never sarcasm, never jokes that need cultural knowledge.

### `recap` and `closing`

- The recap is 4 to 6 short bullets that a reader could use as a cheat sheet. One of them states the main
  caveat or limit.
- `closing` (60 to 120 words): look back in one or two sentences ("We started with a counter that lost
  updates..."), send the reader to their own code with one concrete thing to search for ("Search your
  service for `static` fields that aren't `final`."), then hand off to the next lesson with "Next, we'll..."
  and the question it answers. The last lesson of a track hands off to the next track.

### The other fields

- `goal`: one sentence, plain, starting "By the end you can...".
- `analogy`, `in_your_world`, `mistake`: optional in lessons that have an `opening`. Weave the main picture
  and the common mistake into the sections instead. Keep one of these callouts only when it adds something
  the prose doesn't say (for example, `in_your_world` tying the idea to Quarkus or Kafka).
- Try-it steps: talk like the author at the reader's elbow: "Run it three times. Did the total ever come
  out right? Now change one line..." Always say what they should see and why.
- Lab steps, quiz, flashcards, terms, drill, explain-back: keep their contracts from brief/BRIEF.md, and
  write their prose in the same calm voice.

## Veteran examples for Part 1

Reuse these across the Concurrency on the JVM tracks so the reader meets old friends, and new tools are
judged on the same programs (same correctness figure, then complexity and time):

- The ledger: accounts, balances, transfers between them (races, locks, deadlock, atomics, the capstone).
- The settlement batch: thousands of payment records to process and total (pools, sizing, futures,
  fork/join, virtual threads).
- A stateful resource with a background task, such as a token bucket for calls to a card issuer that
  refills itself (visibility, safe publication, starting threads, scheduled executors, shutdown).
- A slow downstream: a card-issuer API that takes 120 ms (IO-bound pools, timeouts, cancellation,
  virtual threads).

Don't force them where an existing lab already uses another example. Keep the code consistent with the
lab and the Try-it demos on disk.

## What to avoid

- Starting a lesson or a section with a definition or with an abstract claim.
- Headings that state a fact as if it were a slide. Prefer headings that name the step of the journey:
  "A counter that loses money", "Why the second thread never sees the change", "Taking turns with
  synchronized". Sentence case.
- Lists where prose would flow better. Use lists for real lists: steps, options, checklists.
- Code dumps without a walkthrough. Introduce every listing, show it, then walk through the lines that
  matter.
- Formal theory for its own sake. Explain by reasoning from the picture.
- Showing an error without explaining it.
- Dogma. Every model has a cost; say what it is.
- Long, flat paragraphs. Three to five sentences is the usual paragraph.

## Before you hand in a lesson

Read it from the top as the learner. Check that:
1. The opening puts you in a scene, connects to the last lesson and states the plan.
2. Every section starts from something visible and ends with a bridge.
3. There is a running example that changes version by version, with honest numbers.
4. Each rule appears once, short, after it was earned.
5. The limits of today's tool are stated, and the closing hands off to the next lesson.
6. No dashes, no banned words, Java and Kotlin for every sample, and `python3 site/validate.py` passes.
