# Capstone tracks (cap1 to cap4): shared rules

A capstone is the last track of a part. It has three lessons (three sittings of 35 to 40 minutes).
Across the three, the learner builds ONE working program, layer by layer, using what the part taught.
Each lesson has the normal lesson shape and must pass site/validate.py, with these differences:

- Less new theory, more building. Sections explain design decisions from first principles: what
  breaks if you choose differently, and which earlier lesson's mechanism decides it. Name the earlier
  lesson by its title the first time you lean on it ("as Race conditions: why count++ lies showed").
- Each lab extends the previous one. Lesson 2's starter code contains lesson 1's solution, and so on,
  so a learner who skipped a sitting can still start. Keep each lab to about 15 minutes of typing:
  the starter code gives the scaffolding, the learner writes the decisive parts.
- Tests check behaviour that matters in production: invariants under stress, cancellation, timeouts,
  backpressure, failure isolation. Never tight timings; use counts, latches, virtual time.
- The quiz leans on retrieval: at least 3 of the 5 questions use "from" to point at earlier lessons
  of the same part (any track in the part, not only this one).
- Lesson 3 ends with a design review: the explain_back asks the learner to defend their design to a
  sceptical reviewer, and "deeper" lists what a production version would add.
- Every code sample in both Java and Kotlin, as in every other lesson. Labs may pick one language per
  lesson, but use both across the three.
- The track file (content/tracks/capN.json) intro says what you will have built at the end and which
  tracks it draws on; the cheatsheet is the design checklist of the program.

Read brief/outlines/_common.md and brief/BRIEF.md (including "Novice on the topic, taught from first
principles"). The research notes for the part's tracks are your source of truth. Work in your own
lab module only. Do not edit content/course.json or Gradle files other than your module's
build.gradle.kts. No git commands.
