# RESTART NOTE (read first)

This track was started by an earlier writer who stopped part-way. Before writing anything:
1. List content/lessons/ for your track. Finished lessons validate clean: leave them alone
   unless site/validate.py reports an error in one.
2. Look for half-written lab code for the first missing lesson (labs/<lab>/src/*/.../lNN/).
   Read it, then finish it or replace it so it passes the checks below. Delete stray files you
   don't use.
3. Re-read brief/BRIEF.md: it has rules added after the first writers started. The important
   ones: every code sample in BOTH Java and Kotlin (section "Both languages in every sample",
   enforced by the validator), and never refer to the schedule with calendar dates or weekdays.
4. Write the remaining lessons in order, then the track file content/tracks/<id>.json.
Do not run any git command. The coordinator commits, pushes and deploys.

# Instructions shared by every track writer

Working directory: /home/user/jvm-workbench (no git commands, please).

Read these first, in this order:
1. brief/BRIEF.md, all of it. It is the contract.
2. content/lessons/conc-03.json, the golden lesson, and its lab under
   labs/concurrency/src/{main,solution,test,demo}/java/workbench/concurrency/l03/.
   Match its depth, voice, and the way the lab, tests and demos fit together.
3. The research notes for your track (named in your outline) under
   "research_notes/JVM concurrency course research/". They are your source of truth
   for versions, API shapes, misconceptions and verified URLs. Their "Teaching notes"
   sections have demo and exercise ideas with expected outcomes: use them.
4. The "Recommendations for the site" section of learning_science.md in the same folder.
5. content/course.json for your exact lesson ids and titles.

What you deliver, for every lesson in your outline:
- content/lessons/<id>.json, valid against site/validate.py with zero errors.
- Lab code in labs/<lab>/src/{main,solution,test}/(java|kotlin)/workbench/<lab>/lNN/,
  and demo code for the Try-it steps in labs/<lab>/src/demo/... .
And one track file: content/tracks/<track id>.json (intro, cheatsheet, recap, 10-question quiz).

Work one lesson at a time: write the lab code, run Gradle, then write the lesson JSON
(write it with a small Python script and json.dump, as brief/gen/conc03.py does; put
your generator scripts in brief/gen/<id>.py so they can be re-run), then validate.
Copy demo sources into the lesson JSON from the files on disk so they never drift.

Verify each lesson before moving on (run from labs/):
  ./gradlew :<lab>:solutionTest --tests 'workbench.<lab>.lNN.*' --console=plain   (must pass, run it twice for concurrency tests)
  ./gradlew :<lab>:test --tests 'workbench.<lab>.lNN.*' --console=plain --continue  (must FAIL on the stubs)
  ./gradlew :<lab>:demo -Pmain=<each demo class> --console=plain                     (must run, under 10 s)
  python3 site/validate.py content/lessons/<id>.json                                   (0 errors)
At the end: python3 site/validate.py --track <track id>  and  ./gradlew :<lab>:solutionTest --console=plain

Rules:
- Touch only your own track's files: content/lessons/<your ids>.json, content/tracks/<your id>.json,
  labs/<your lab>/**, brief/gen/<your ids>.py. Never edit brief/BRIEF.md, site/, content/course.json,
  the root Gradle files, or another track's folders. Other writers are working in parallel.
- No new dependencies unless your outline allows one.
- The network blocks docs.oracle.com and openjdk.org for curl and often for WebFetch. Prefer the
  URLs your research notes list as verified. If you cite a JEP or Javadoc page you could not fetch,
  use only the standard, stable URL shapes (https://openjdk.org/jeps/444,
  https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ExecutorService.html).
- The learner may install JDK 25 while labs compile with release 21: nothing in labs/ may use an API
  newer than JDK 21 or a preview API.
- If a fact in a lesson depends on something you could not verify, write around it.
- Eight writers run Gradle on this 4-core machine at the same time. Tests must not depend on tight
  timings: use counts, latches, max-concurrency counters, virtual time, or very generous margins.
  If Gradle waits on a lock for a while, that is another writer's build; wait.

Your final message back (keep it under 300 words): the lessons written, the Gradle results
(solutionTest pass counts, confirmation that stubs fail), validator status, and any claim you
could not verify or any place you departed from the outline.
