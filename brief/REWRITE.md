# Rewriting a lesson in the book voice

Every lesson on the site is being rewritten so it reads like a chapter by an experienced author in the
style of Venkat Subramaniam's books, for a complete newcomer. Part 1 (Concurrency on the JVM) is done
and approved by the user; it is the model for everything else. The user's words: build intuition with
simple examples and plain language; open to anyone, so a complete novice can start reading
immediately; analogies that fit the topic, with an overview before using them; a light touch of humor,
not too much; a nicely linked flow. A little longer is fine when it builds intuition.

## Read first

1. The skill `venkat-voice` (load it with the Skill tool; the file is
   /root/.claude/skills/venkat-voice/SKILL.md). Sections 0 to 4 matter most.
2. brief/VOICE.md (the newcomer reader, the house rules, how the skill maps onto the lesson JSON) and
   brief/BRIEF.md (the lesson contract: quiz "from" rule, banned words, sources).
3. Two finished Part 1 lessons for tone, structure and length: content/lessons/conc-02.json and
   content/lessons/vt-02.json (and their generators brief/gen/conc02.py, brief/gen/vt02.py).
4. The lessons just before and after yours in the track (and the previous track's last lesson, if
   yours is a track's first lesson), so the opening links back and the closing hands forward.
5. Your lessons, their generators (brief/gen/<id>.py or similar), their labs (labs/<lab>/src/...) and
   their videos (content/videos/part*.json: keep each video's section index).
6. Optional depth: the research notes in research_notes/ for facts, and the style notes in
   /tmp/claude-0/-home-user/b1ec521c-18dd-5b5d-967f-de5283ba1787/scratchpad/books/venkat-style-*.md
   (never copy the books' text, examples or class names).

## What to produce, for each lesson

- Rewrite through the generator script, then run it, so the generator and the JSON stay in step.
- Add `opening` (90 to 200 words: an everyday scene set up in plain words, then the surprise, the easy
  trap, a link to the previous lesson, the plan; it may end "Before we start, make a guess, and keep it
  in mind."), `closing` (60 to 120 words: look back, one concrete thing to look for in the reader's own
  code, then "Next, we'll..." and the question the next lesson answers), and at most one `aside`.
- One family of everyday pictures per track, set up in plain words, mapped part by part, with the place
  each picture breaks said out loud. Your coordinator's message names the family if an earlier batch of
  the same track already chose it; otherwise choose it, and list it clearly in your final message.
- Define every technical term in one plain sentence the first time it appears in each lesson, even if
  an earlier lesson defined it.
- Sections (3 to 5): problem first, the naive version failing in public with real output from the
  demos, a ladder of versions, honest numbers (the machine is busy: label loaded timings), one short
  bold rule per section at most, a bridge sentence at the end, and headings that name the step and say
  plainly what the section covers.
- Humor per the skill: 3 or 4 touches per lesson, each carrying a fact, one character per lesson, none
  in definitions, rules, traces or recaps.
- Remove `analogy`, `in_your_world` and `mistake` when they are woven into the prose. Rewrite the
  warm-up, Try-it steps, worked example, lab steps, recap (4 to 6 bullets, one stating the limit of
  today's tool), quiz "why" texts, explain-back and deeper in the same voice. Keep quiz correctness, the
  quiz "from" rule, flashcard facts, terms and sources accurate.
- No industry or framework jargon in openings and running examples (payments, settlement, card
  issuers, fraud checks, Quarkus, Kafka, Kubernetes, pods and the like). A real tool may appear later
  as a short, labeled aside after the idea is clear, explained in plain words. When the lesson IS about
  a real tool (Netty, Vert.x, Jetty, Reactor, a GC, JMH...), introduce it plainly as the subject.
- Facts correct for JDK 25 and Kotlin 2.4; say the version when a fact depends on it.
- Keep code consistent with the labs and demos on disk. You may change demo strings, names and
  comments to remove jargon; if you change lab or demo code, run the Gradle checks in
  brief/outlines/_common.md for that lesson (solution tests pass, stubs fail as the lab steps say,
  demos run), and keep any line numbers the prose quotes.
- Validate each lesson: `python3 site/validate.py content/lessons/<id>.json` (0 errors; fix real
  warnings). If you were asked to do the track page too, rewrite it through its generator
  (intro, cheatsheet with a "Picture it" column or line, recap, quiz still correct; see brief/gen/jmm.py
  for a finished example) and run `python3 site/validate.py --track <track>`.
- Reread each lesson as a complete newcomer and run the skill's final checklist.

## Don'ts

- Don't run site/build.py. Never run git commands. Never run git checkout or git restore on anything
  (video makers write files in web/ and videos/ at the same time).
- Edit only your own lessons, generators, labs and (if asked) track page.

## Final message (under 300 words)

The picture family and running example, the opening scene and headings per lesson, humor touches,
video section indexes, code changes with test results, validator status, and anything you are unsure
about.
