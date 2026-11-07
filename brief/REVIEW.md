# First-principles review of the older tracks

The eight first tracks (conc, jmm, exec, vt, rx, co, gen, pat) were written before brief/BRIEF.md got
its section "Novice on the topic, taught from first principles". Your job is to bring each lesson up
to that rule without rewriting what already works. Read that section and the "Voice" section of
brief/BRIEF.md first, then the human-writing skill it links.

For each lesson in your tracks, check:
1. The first lesson of a track assumes no knowledge of the topic. Later lessons assume only earlier lessons.
2. Each section shows the problem (a program that breaks, is slow, or surprises) before it names the fix.
3. Each rule comes with its cause, one level down: what the CPU, the OS, the JVM, the compiler or the
   library really does, so the reader could predict a variant the lesson does not show. "Do X" with no
   "because" fails this check.
4. Every term is defined in plain words the first time it appears in the track.
5. Each section ends with a check the reader can do: a prediction, a run, or a question that follows
   from the mechanism. A Try-it box counts.
6. Where it would really help, the small version is built by hand before the library (a toy pool, a
   proxy by hand). Many labs already do this; do not add labs. A short code pair in the prose is enough.

How to fix:
- Make the smallest change that passes the check: add a short "why" paragraph, a definition, a closing
  question, or move a paragraph so the problem comes first. Keep the voice of the lesson.
- Keep section prose within 1,000 to 1,800 words per lesson; if you add, trim repetition elsewhere.
- Every new code sample must come as a Java and Kotlin pair (see "Both languages in every sample").
- Any new fact must be supported by the lesson's research notes ("research_notes/JVM concurrency course
  research/") or a primary source you checked. If you cannot verify a cause, do not add it.
- Do NOT add, remove or reorder sections: narrated videos are attached to sections by index. Do not
  change lesson ids, titles, quiz "from" fields, lab files, labs/ code or tests.
- The track order changed: Part 1 conc, jmm, exec, vt, cap1; Part 2 rx, co, io, cap2; Part 3 gen, pat,
  dop, kt, cap3; Part 4 cls, mem, perf, boot, cap4. Fix wording that now points the wrong way
  ("the next track", "as you saw in the generics track" from a track that now comes before generics).

Lesson JSON files were written by generator scripts in brief/gen/ (for example brief/gen/conc03.py).
Before editing a lesson, copy its JSON to your scratchpad, run its generator, and compare. If the
output is identical, edit the generator and re-run it. If it differs, the JSON was edited by hand
later: restore your copy and edit the JSON directly with a small Python script (json.load / json.dump
with ensure_ascii=False, indent=2, matching the file's current format).

After each lesson: `python3 site/validate.py content/lessons/<id>.json` must give 0 errors.
At the end: `python3 site/validate.py --track <id>` for each of your tracks.
No git commands. Other agents are working in the repo (video writers read lessons; do not touch
videos/, web/ or content/videos/).

Final message under 250 words: per lesson, one short line of what you changed, or "no change needed";
and anything you wanted to fix but could not verify.
