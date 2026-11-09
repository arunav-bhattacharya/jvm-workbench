# Track: fp, "Functional programming in Kotlin" (lab: labs/functional, package workbench.functional.lNN)

Research notes: "research_notes/Functional programming in Kotlin/" (fp_foundations.md, collections_sequences.md,
scope_functions_nulls.md, errors_and_data.md). They are your source of truth: versions, verified compiler output,
exact exception messages, misconceptions, demo ideas with observed output. Many facts there were checked by compiling
with Kotlin 2.4.21; anything marked unverified or "search only" must not be stated as fact.

Who this track is for: a senior Java/Kotlin engineer who writes lambdas every day but has never learned functional
programming as a way of thinking. Assume NO functional programming knowledge. Build intuition first, then the
Kotlin feature, then what it compiles to. Every lesson opens with a small payments program that hurts (hard to test,
a bug from shared state, an unreadable loop) and shows how the functional idea removes that pain. Name a concept only
after the reader has felt why it exists. Follow brief/BRIEF.md (especially "Novice on the topic, taught from first
principles") and the human-writing skill it links.

Labs are Kotlin. Every code sample in the prose still comes as a Kotlin and Java pair: the Java side is the
equivalent Java (streams, Function<T,R>, Optional, records) so the reader sees what Kotlin changes. Where Java has
no equivalent (scope functions, tailrec), say so in the solo note the validator allows.

Dependencies already in labs/functional/build.gradle.kts: arrow-core 2.3.0, kotlinx-collections-immutable 0.5.2,
kotlinx-coroutines-core and -test. Don't add others. Package per lesson: workbench.functional.l01 .. l08.

Lessons:
- fp-01 Pure functions: the idea everything else builds on. Start from a fee calculator that reads the clock, a
  global config and writes a log line: show why it is hard to test and to reason about. Define side effects,
  pure functions and referential transparency in plain words; expressions over statements (if/when/try as
  expressions). Functional core, imperative shell, as the target shape (cite carefully: notes mark which sources
  were only seen via search). Lab: pull the pure fee rule out of the impure function; tests call it with fixed
  inputs and no clock.
- fp-02 Function types, lambdas and closures. Functions as values: (A) -> B, function references, receivers
  (A.() -> B) only briefly, nullable function types. What a lambda compiles to in Kotlin 2.x (invokedynamic, no
  class; non-capturing lambdas are shared; references still generate classes) from the verified notes. Closures:
  a captured var becomes a Ref box with a plain field, so a counter captured by four threads loses updates (the
  notes' demo; loop it so it shows reliably). Lab: rules as values (a list of (Payment) -> Rejection?), a
  makeCounter that is safe for one thread, and a fix for the shared one.
- fp-03 Higher-order functions: functions in, functions out. Write your own: retry, timed, memoize; return
  functions: partial application (feeFor(country) returns the fee function), currying by hand, compose/andThen
  by hand (the stdlib has none; Arrow's arrow-functions module has them, not a dependency here). inline and why
  the stdlib's HOFs cost nothing (link to the Advanced Kotlin track's inline lesson as coming later in Part 3).
  Lab: a small pipeline of fee adjustments built by composing functions; memoize with a counting test.
- fp-04 Collections without loops: map, filter, fold and friends. Rewrite a loop-based settlement report into
  map, filter, mapNotNull, flatMap, groupBy, associateBy, partition, sumOf, fold. fold as the general loop.
  The traps from the notes, with exact messages: reduce on empty, first(), associateBy silently keeping the last
  duplicate (Java's toMap throws), groupBy keeping first-seen order. Java Streams side by side for each. Lab:
  the settlement report, with tests for the empty and duplicate cases.
- fp-05 Sequences: lazy pipelines, and where Java Streams fit. Eager List chains make a list per step; a
  Sequence moves one element through the whole chain (show the exact print order from the notes as a
  predict-the-output warm-up). Short-circuiting, sorted() forcing everything, sequence { yield } builders and
  generateSequence, reuse (sequences re-run; Java streams are single-use; some sequences are once-only).
  Allocation numbers from the notes' JMH run (bytes per call are stable; label timings as indicative only).
  Lab: find the first suspicious payment in a large generated feed and prove, with a counter, how many elements
  were processed; a paging sequence built with yield.
- fp-06 Scope functions: let, run, with, apply and also, on purpose. The 2x2 (this or it, result or object),
  the official choosing guide, contracts (callsInPlace EXACTLY_ONCE lets a val be set inside), and the
  anti-patterns with their cost: nesting and this/it shadowing, long let chains, the ?.let { } ?: run { } bug when
  the let block returns null, apply used to compute, also used to change state. Null handling as a functional
  pattern: ?., ?:, ?.let, takeIf/takeUnless, requireNotNull/checkNotNull with smart casts, mapNotNull; nullable
  types vs Optional (and Arrow's own advice to prefer nullable). End with the decision checklist. Lab: a module
  that misuses scope functions; tests catch the ?: run bug; the learner rewrites it.
- fp-07 Errors as values: sealed results, Result and Either. Exceptions for bugs, values for expected failures
  (Kotlin's Result KEEP and the rich-errors KEEP words, as the notes quote them). A hand-written sealed result,
  then kotlin.Result and runCatching with the verified pitfalls (swallows CancellationException, so work runs on
  after cancel; map vs mapCatching). Arrow 2.3.0: Either, either { } with ensure and bind (fail fast),
  zipOrAccumulate for collecting every validation error. Rich errors (A | B) are not in Kotlin 2.4.21: say so
  plainly. Lab: payment validation that collects all errors, a fail-fast pipeline, and a cancellation-safe
  runCatching replacement tested with kotlinx-coroutines-test.
- fp-08 Immutable data and a functional core. val vs immutable, read-only List that still changes, copy() is
  shallow, BigDecimal equality in data classes (10.00 vs 10.0), persistent collections (kotlinx.collections.immutable
  0.5.2: say it is still marked experimental, and name the new method names from the notes). Recursion: tailrec
  compiles to a loop, misuse is only a warning, DeepRecursiveFunction for deep non-tail recursion, and when fold
  is simpler. Then put the track together: refactor a settlement job into a pure core that decides and a thin
  shell that does the I/O. Lab: that refactor, with tests that run the core with no I/O at all.

Track file content/tracks/fp.json: intro (what the reader will be able to do, and that no FP background is
needed), a cheatsheet (the scope-function table, the collection operation picker, the error-handling picker),
recap, and a 10-question quiz mixing all eight lessons.
