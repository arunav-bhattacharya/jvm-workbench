# Writing brief for JVM Workbench lessons

Read this whole file before you write a lesson. Then read the golden lesson,
`content/lessons/conc-03.json`, and its lab files under
`labs/concurrency/src/*/java/workbench/concurrency/l03/`. Match its depth, tone and shape.

## Research notes (read the ones for your track first)

Fact-checked notes for every track are in
`research_notes/JVM concurrency course research/`, and the summary report is in
`reports/JVM concurrency course research.md`. Treat them as your source of
truth for versions, API shapes, misconceptions and verified URLs. Each notes
file ends with "Verified URLs" and "Teaching notes" sections: use them. If the
notes and your memory disagree, trust the notes or check the primary source.
`learning_science.md` explains why the lesson has the shape it has.

## Who the learner is

One person: a senior backend engineer. They write Kotlin and Java every day, on
services built with Quarkus, Temporal, Oracle and Kafka, mostly in payments.
They know the syntax of both languages. They do not yet have a deep, lasting model
of concurrency, the memory model, reactive code, coroutines, generics variance
or design patterns. Earlier attempts to learn generics "did not stick", so the
generics track must build intuition step by step, with many small examples.

They study 30 to 40 focused minutes a day, one lesson per sitting:

1. about 5 minutes of flashcard review (the site does this),
2. about 20 minutes reading the sections and doing the small "Try it" steps,
3. about 10 to 15 minutes on the lab exercise or drill, then the 5-question quiz.

So a lesson has about 1,000 to 1,800 words of section prose (not counting code),
plus the callouts, worked example, lab and quiz. Do not go over.
If a topic is too big, cut it and move the rest to "Go deeper".

## Novice on the topic, taught from first principles

The learner knows both languages but may know nothing about the topic of a
track (GC, bytecode, Netty, JIT). Every track must take them from zero on that
topic to a model good enough to reason about cases the course never showed.

- The first lesson of a track assumes no knowledge of the topic. Later lessons
  assume only earlier lessons.
- Show the problem before the fix. Start from the smallest program that breaks
  or is slow, let the learner feel it, then name the mechanism that solves it.
- Go one level down. Say what the CPU, the OS, the JVM or the compiler really
  does, enough that the learner could predict the result of a variant you did
  not show. A rule without its cause does not count.
- Build the small version first where it fits: a toy pool before
  `ThreadPoolExecutor`, a proxy by hand before `java.lang.reflect.Proxy`, a
  select loop before Netty. Then show what the real library adds and why.
- Define every term in plain words the first time it appears.
- End each section with a check the learner can do: a prediction, a run, or a
  question whose answer follows from the mechanism, not from memory.

## Voice: blog mode, human, simple

Write like a strong engineer's personal blog post that teaches one idea well.
Follow the human-writing skill at
`/root/.claude/skills/synced/5c806f8d-0769-4e35-ac24-a3ea18081c67_433d709e-8728-4258-b10c-98909f71fe68/human-writing/SKILL.md`
(read it once). The parts that matter most here:

- Very simple English. Short sentences. One idea per sentence. A non-native
  reader should never have to read a sentence twice.
- Open each section with information: a claim, a bug, a number, a line of code.
  Never open with scene-setting ("In today's world", "Have you ever wondered").
- Take positions. "Use `ConcurrentHashMap.merge` here. `synchronized` on the
  whole map is slower and buys you nothing." Say when something is just worse.
- Show, don't grade. Replace "this is crucial" with the thing that breaks.
- Name the actor: "the JIT hoists the read out of the loop", not "the read is hoisted".
- No em dashes or en dashes anywhere in prose. Use a period, comma, colon or
  parentheses. (The validator rejects them.)
- No "not X but Y" staging, no one-line dramatic closers, no "Let's dive in",
  no "Here's the thing", no "In conclusion", no forced triads.
- Avoid these words: delve, crucial, pivotal, robust (unless it is a
  technical term), leverage, seamless, tapestry, landscape, game-changer,
  unlock, empower, elevate, vibrant, meticulous, testament, foster,
  showcase, underscore.
- Sentence case for every heading. No emojis. No bold labels at the start of
  list items. Bold at most one or two key phrases per section.
- Lists only when the content is a real list. Prose otherwise.
- Use "you". Contractions are fine.
- Never refer to the schedule with calendar dates or weekdays. Refer to other lessons by
  title or as "lesson N of this track".
- Concrete, made-up examples from the learner's world: payment authorizations,
  ledger balances, idempotency keys, a Kafka consumer, a card-issuer API that
  takes 120 ms, a connection pool with 20 connections. All company names, people
  and numbers are invented.

## Accuracy rules

- Facts must be right. When a claim depends on a version, say the version:
  "virtual threads became final in JDK 21 (JEP 444)", "JDK 24 removed most
  pinning on synchronized (JEP 491)". If you are not sure of a version detail,
  check it with WebSearch or WebFetch on openjdk.org, docs.oracle.com,
  kotlinlang.org, projectreactor.io or github.com/Kotlin/kotlinx.coroutines.
  If you still can't confirm it, write around it rather than guess.
- The learner should install JDK 25 (the current LTS). The labs compile with
  `release 21`, so they also run on JDK 21+. Features newer than 21 belong in
  lesson prose and Try-it code that says which JDK it needs. Preview APIs
  (for example structured concurrency) must say "preview in JDK NN, run with
  `--enable-preview`" and must not go into the Gradle labs.
- Library versions in the labs: Kotlin 2.4.21, kotlinx.coroutines 1.11.0,
  Reactor 3.8.8, JUnit 6.1.3, AssertJ 3.27.7.
- `curl` cannot reach docs.oracle.com from this machine (the proxy blocks it). Use
  WebFetch to check those pages. The research notes list URLs that were verified.
- Every URL in `refs` and `sources` must be a real page you are confident
  exists: JEP pages (`https://openjdk.org/jeps/444`), Javadoc
  (`https://docs.oracle.com/en/java/javase/25/docs/api/...`), Kotlin docs
  (`https://kotlinlang.org/docs/...`), Reactor reference
  (`https://projectreactor.io/docs/core/release/reference/...`), the JLS chapter
  17 page, well-known talks or articles (Shipilëv's "Close Encounters of The
  Java Memory Model Kind", Goetz's book page). Fetch a URL if unsure. Never
  invent one. Fewer real links beats more fake ones.
- Code must compile and do what the prose says. Lab code is compiled and
  tested by Gradle (see below). Code shown only in prose must still be correct.

## Both languages in every sample (the learner asked for this)

Every code sample in a lesson appears in Java AND Kotlin. The site shows each pair with a
Java / Kotlin / Both switch. `site/validate.py` enforces this.

- In Markdown prose (section bodies, steps, mistake, deeper): write the Java fence and
  then, right after it, the Kotlin fence for the same sample. Nothing between them but a
  blank line. Either order works; the site always shows Java first.
- Try-it `code` in java or kotlin gets an `alt` object with the same program in the other
  language: `{"lang", "title", "src", "run", "file"}`. If the original is a runnable demo,
  the twin is a runnable demo too. Naming: the Kotlin twin of `Foo.java` is `Foo.kt` with a
  top-level `fun main()` (its class is `FooKt`); the Java twin of `Foo.kt` is
  `FooJava.java`. Never declare a Kotlin class with the same name as the Java class in that
  package.
- Worked-example steps with code get `alt_code` and `alt_lang`.
- Drill answers get `alt` (same shape as the Try-it alt, without file/run).
- `compare` is required in every lesson.
- When the other language has no real twin, mark the fence ```` ```kotlin solo ```` or set
  `"solo": true` on the code object or worked step. At most 3 per lesson. For coroutines
  and Flow, the Java twin is the closest Java equivalent (CompletableFuture, virtual threads,
  Reactor, or Java calling the Kotlin API through `future {}`), with a first-line comment
  that says so. For Java mechanisms (bytecode, the memory model), the Kotlin twin shows the
  same thing in Kotlin (`@Volatile`, `@Synchronized`, `synchronized(lock) {}`, atomics).
- Labs stay in one language per lesson. Only the samples come in pairs.

## Java and Kotlin together

Every lesson teaches the idea once and then shows it in both languages where
that makes sense. Use the `compare` block for a side-by-side: the Java version,
the Kotlin version, and a note on what really differs (not just syntax).
Patterns and generics lessons must always have a `compare`. Coroutine and
Reactor lessons can show the Java or Kotlin counterpart when one exists
(for example `CompletableFuture` vs `async`, Reactor `Flux` vs Kotlin `Flow`).
Labs are in Java for the Java-only tracks, Kotlin for generics and coroutines,
and either or both elsewhere. Pick the language that teaches the point best,
and use both across a track.

## What makes it stick (use these on purpose)

- Warm-up question: one prediction question before reading. Make the wrong
  options tempting. It is not scored.
- Try it boxes: 2 to 6 minute steps at the end of a section, using runnable code
  in the labs repo (`src/demo`). Tell the learner what to change and what
  they should see. Prefer "predict, run, explain" over "copy, run".
- An interactive simulation (`sim`) where it fits: races, locks, deadlock,
  check-then-act. See "Interleaving simulator" below. Use it in at most one
  section of a lesson, and only where stepping through threads by hand teaches
  something.
- One diagram per lesson (in the `figure` of a section) where a picture
  explains the mechanism: thread states, a pool's queue, happens-before edges,
  a carrier thread mounting a virtual thread, a coroutine tree, the
  producer/consumer arrows of `out` and `in`.
- The lab: real code with real tests. This builds muscle memory.
- The drill: a short "write it from memory" task (3 to 6 minutes). Example:
  "Close this page. Write a bounded buffer with `wait` and `notifyAll` from
  memory." Then the answer.
- Quiz: 5 questions that apply the idea to new cases, not recall of wording.
  One of the five must revisit an earlier lesson in the same or an earlier
  track. Mark it with `"from": "<that lesson id>"`. (The first lesson of the
  first track is exempt.)
- Flashcards: 5 to 7 cards. These drive the spaced-repetition review for weeks,
  so make each card one atomic fact or one "what happens if" question. The
  front is a question. The back is short (one to three sentences or a tiny code
  fragment).
- Explain it back: one prompt that asks the learner to explain the core idea in
  their own words, plus a model answer.
- Worked examples carry subgoal labels: short comments that name what each
  chunk does (`// 1. claim the key atomically`, `// 2. charge`, `// 3. release on failure`).
- Quiz distractors come from real misconceptions, never tricks. The `why`
  explains the right answer and says why the most tempting wrong option fails.
  Prefer "what does this print?", "which line races?", "which tool fits?"
  over definitions. Later lessons in a track should mix in "pick the right
  tool" questions that contrast confusable tools (synchronized vs volatile vs
  atomics, flatMap vs concatMap, launch vs async, out vs in).
- Flashcards follow the minimum information principle: one fact or one
  decision per card. Split lists ("the four conditions for deadlock") into
  separate cards. A card may show three lines of code and ask what happens.

## Lesson JSON schema

One file per lesson: `content/lessons/<id>.json`. All prose fields are
Markdown (inline code with backticks, fenced code blocks with a language tag:
java, kotlin, bash, text, json, properties, xml). Tables are allowed.

```json
{
  "id": "conc-03",
  "title": "must equal the title in content/course.json",
  "minutes": 35,
  "goal": "By the end you can ... (one sentence)",
  "warmup": { "q": "...", "options": ["...", "...", "..."], "answer": 1, "why": "..." },
  "sections": [
    {
      "h": "Sentence-case heading that states the idea",
      "body": "Markdown, about 200 to 450 words",
      "figure": { "svg": "<svg ...>...</svg>", "caption": "One sentence." },
      "sim": { "...": "see Interleaving simulator" },
      "try": {
        "title": "Short title",
        "minutes": 4,
        "steps": ["Markdown step", "..."],
        "code": { "lang": "java", "title": "file name", "src": "full source", "run": "./gradlew ...", "file": "labs/<lab>/src/demo/..." },
        "expect": "What they should see, and why"
      },
      "refs": [ { "title": "...", "url": "https://...", "kind": "docs|read|watch" } ]
    }
  ],
  "analogy": "One paragraph. End by saying where the analogy breaks.",
  "in_your_world": "One paragraph tying the idea to the learner's services (payments, Kafka, Quarkus, Temporal).",
  "mistake": "The most common real mistake, why people make it, and the fix.",
  "compare": {
    "title": "...",
    "java": { "title": "file or label", "src": "..." },
    "kotlin": { "title": "file or label", "src": "..." },
    "note": "What really differs, in prose"
  },
  "worked": { "title": "...", "steps": [ { "say": "Markdown", "code": "...", "lang": "java" } ] },
  "lab": {
    "title": "...",
    "minutes": 12,
    "files": ["labs/concurrency/src/main/java/workbench/concurrency/l03/SeatMap.java"],
    "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l03.*'",
    "steps": ["Markdown", "..."],
    "hints": ["Markdown", "..."],
    "done_when": "All tests in ... pass."
  },
  "drill": { "title": "...", "minutes": 5, "prompt": "Markdown", "answer": { "lang": "java", "src": "..." } },
  "recap": ["4 to 6 short Markdown bullets"],
  "quiz": [ { "q": "...", "options": ["...", "...", "...", "..."], "answer": 0, "why": "...", "from": "optional earlier lesson id" } ],
  "flashcards": [ { "front": "...", "back": "..." } ],
  "terms": [ { "term": "...", "plain": "..." } ],
  "explain_back": { "prompt": "...", "answer": "..." },
  "deeper": { "minutes": 10, "body": "Markdown: optional extra depth for curious days" },
  "sources": [ { "title": "...", "url": "https://..." } ]
}
```

Counts: 3 to 5 sections (each with a `try`, except at most one), 1 figure or
sim per lesson at least, 4 to 6 recap bullets, exactly 5 quiz questions with 4
options each (3 is fine when a 4th would be silly), 5 to 7 flashcards, 4 to 8
terms, 2 to 6 worked steps, 2 to 5 sources. `compare`, `sim`, `figure`, `refs`
and `deeper` are optional except as stated above. Vary the correct answer
index across quiz questions.

Escape carefully: the file is JSON, so newlines in code are `\n` and quotes are
`\"`. Write the file with a small Python script (json.dump) if that is easier
than hand-writing JSON. Use 4-space indentation in Java and Kotlin code.

## Diagrams (SVG)

Inline SVG in `figure.svg`. Rules, so the diagram works in dark and light themes:

- `viewBox="0 0 W H"` with W between 520 and 720. No width/height attributes.
- Never set colors inline. Use only these classes:
  - boxes: `box` (neutral), `box-a` (accent), `box-b` (second accent), `box-ok` (green), `box-bad` (red), `box-dim` (faded)
  - text: `t` (normal 14px), `t-s` (small 12px), `t-m` (muted), `t-a` (accent colored), `t-b`, `t-ok`, `t-bad`, `t-code` (monospace)
  - lines: `ln` (solid), `ln-d` (dashed), `ln-a` (accent solid), `ln-bad`
  - arrows: add `marker-end="url(#arr)"` to a line or path.
- Text uses `text-anchor="middle"` and fits inside its box (about 7.5 px per
  character at 14px, 6.5 px at 12px). Keep labels short.
- Add `role="img"` and an `aria-label` that says what the picture shows.
- Simple shapes only: rect (rx="8"), line, path, circle, text. No filters, no
  gradients, no foreignObject, no scripts.

## Interleaving simulator (`sim`)

An interactive widget where the learner picks which thread runs its next step.
It shows shared variables, each thread's local registers and who holds each lock.

```json
"sim": {
  "title": "Two threads run count++",
  "intro": "Pick which thread runs next. Try to end with count = 1.",
  "vars": { "count": 0 },
  "locks": ["lock"],
  "threads": [
    { "name": "T1", "steps": [
      { "op": "read", "var": "count", "reg": "r", "code": "int r = count;" },
      { "op": "add", "reg": "r", "n": 1, "code": "r = r + 1;" },
      { "op": "write", "var": "count", "reg": "r", "code": "count = r;" }
    ]},
    { "name": "T2", "steps": [ "..." ] }
  ],
  "goal": { "var": "count", "eq": 1, "say": "Lost update: two increments, one result." }
}
```

Ops: `read` (reg = var), `add` (reg += n), `write` (var = reg), `set` (var = n),
`lock` (blocks while another thread holds it), `unlock`, `check` (if var != eq
the thread jumps to its end: use for check-then-act), `note` (does nothing,
shows `code`). Every step needs `code`, the line of Java it stands for. The
widget detects deadlock (every unfinished thread blocked) and shows `goal.say`
when the goal state is reached.

## Labs (Gradle)

The labs live in `labs/`, one Gradle subproject per track:
concurrency, jmm, executors, vthreads, generics, reactive, coroutines, patterns.
Each subproject has:

- `src/main/{java,kotlin}`: the exercises. Stubs with the final signatures,
  javadoc/KDoc saying what to do, and bodies that throw
  `UnsupportedOperationException("TODO: ...")` in Java or `TODO("...")` in Kotlin.
  Where the lesson is "fix the bug", the stub is the buggy code instead.
- `src/solution/{java,kotlin}`: reference answers with the same class names,
  packages and public signatures. Comment the important lines.
- `src/test/{java,kotlin}`: tests that fail on the stubs and pass on the
  solutions. The same tests run against both.
- `src/demo/{java,kotlin}`: small runnable programs for the Try-it steps.

Package per lesson: lesson `conc-03` uses package `workbench.concurrency.l03`
(track lab name, then `l` and the two-digit lesson number). Use that package
in main, solution, test and demo. Demos may add `.demo` (for example
`workbench.concurrency.l03.demo`) or live in the lesson package.

Rules for lab code:

- Public signatures in `main` and `solution` must match exactly, because the
  same compiled tests run against both. Do not use Kotlin `internal`.
- Tests must be deterministic on the solution and fail reliably on the stub
  (or the buggy version). For race tests, use 8 threads, enough iterations to
  lose updates (around 100,000 each) and a start latch so threads overlap.
  Keep each test under 5 seconds on the solution. Use `assertTimeoutPreemptively`
  or JUnit `@Timeout` for anything that could deadlock.
- Tests read like specs: `@DisplayName` in Java or backtick names in Kotlin
  that say the behavior.
- No new dependencies and no edits to the root `build.gradle.kts`,
  `settings.gradle.kts` or `gradle.properties`. If you truly need a library,
  stop and say so in your final report.
- Keep demos fast (under 10 seconds) and quiet.

Commands (run from `labs/`, for your own track only):

```bash
./gradlew :<lab>:solutionTest --console=plain            # must pass
./gradlew :<lab>:testClasses --console=plain             # stubs and tests must compile
./gradlew :<lab>:test --console=plain --continue         # should fail on the stubs (that is expected)
./gradlew :<lab>:demo -Pmain=workbench.<lab>.l03.demo.RaceDemo --console=plain
```

For a Kotlin file `Foo.kt` with a top-level `main`, the class is `FooKt`.
Other agents are building other tracks in the same Gradle build at the same
time, so you may see a short wait for a lock. That is normal. Never touch
another track's folders.

The lesson's `lab.run` uses the learner command,
`./gradlew :<lab>:test --tests 'workbench.<lab>.lNN.*'`.
Try-it code that lives in `src/demo` sets `code.file` to its repo path and
`code.run` to the demo command.

## Track file

One per track: `content/tracks/<track id>.json`:

```json
{
  "id": "conc",
  "intro": "Markdown, 2 or 3 short paragraphs: what you will be able to do at the end, what you need first, how the labs for this track work.",
  "cheatsheet": "Markdown: a one-page reference for the whole track (tables welcome). This is what the learner will come back to in six months.",
  "recap": ["6 to 10 bullets for the whole track"],
  "quiz": [ "10 MCQs across the whole track, same shape as lesson quiz items" ]
}
```

## Check your work

```bash
python3 site/validate.py content/lessons/conc-03.json     # one lesson
python3 site/validate.py --track conc                      # a whole track, including its track file
```

The validator checks the schema, counts, dashes and banned words, SVG classes,
lab file paths and quiz `from` ids. Fix every error. Read warnings and fix the
ones that are real.

Before you finish a lesson, reread it once as the learner: does each section
open with information, does every claim hold up, does every Try it say what
they should see, and could the learner do the lab in about 12 minutes?
