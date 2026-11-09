# JVM Workbench

A 138-lesson course on how Java and Kotlin really run: concurrency, async servers, generics and design, and the JVM itself. One lesson a day, about 35 minutes each, with real code to write and tests that tell you when it works. Live at https://jvm-workbench.ai-arunav.workers.dev.

The course has four parts. Each one ends with a capstone: three sittings that build one working program from everything the part taught.

| Part | Track | Lessons | Lab project |
|---|---|---|---|
| 1. Concurrency on the JVM | Threads and the bugs they cause | 13 | `labs/concurrency` |
| | The Java Memory Model | 6 | `labs/jmm` |
| | Thread pools and executors | 9 | `labs/executors` |
| | Virtual threads | 6 | `labs/vthreads` |
| | Capstone: a payment ledger under load | 3 | `labs/ledger` |
| 2. Async, reactive and servers | Reactive programming | 8 | `labs/reactive` |
| | Kotlin coroutines | 11 | `labs/coroutines` |
| | Servers and event loops: NIO, Netty, Vert.x and Jetty | 8 | `labs/nio` |
| | Capstone: a non-blocking quote service | 3 | `labs/quotes` |
| 3. Types and design | Kotlin generics, properly | 11 | `labs/generics` |
| | Functional programming in Kotlin | 8 | `labs/functional` |
| | Design patterns in Java and Kotlin | 11 | `labs/patterns` |
| | Modern Java data modeling | 4 | `labs/modernjava` |
| | Advanced Kotlin | 6 | `labs/kotlin` |
| | Capstone: a typed event library | 3 | `labs/events` |
| 4. Inside the JVM | Class loading, bytecode and dynamic proxies | 7 | `labs/bytecode` |
| | Memory and garbage collection | 7 | `labs/memory` |
| | JIT, profiling and benchmarking | 7 | `labs/performance` |
| | Startup and footprint | 4 | `labs/startup` |
| | Capstone: a tiny dependency injection container | 3 | `labs/container` |

Every track assumes no knowledge of its topic. Lessons show the program that breaks before they name the fix, and go one level down (what the CPU, the OS, the JVM or the compiler does) so you can predict cases the lesson never showed.

Each lesson has a warm-up question to answer before reading, 3 to 5 short sections that each end in a "Try it", a Java and Kotlin comparison, a worked example, a lab with tests, a write-it-from-memory drill, and a 5-question quiz. One quiz question always comes from an earlier lesson.

The site also has:

- **Review**: spaced-repetition flashcards (FSRS-4.5 scheduler). Each finished lesson adds 5 to 7 cards, and every quiz question you miss joins them.
- **Mixed practice**: quiz questions drawn from all finished lessons, so you practice telling similar tools apart.
- **Plan**: lessons laid out as Week N, Day N at 3 to 7 study days a week (no calendar dates, so missing a day never makes you "late"), and copy/paste sync between devices.
- **Cheat sheets** and a **glossary** for when you need the answer, not the lesson.
- A **35-minute focus timer**: 10 minutes review, 12 learning, 13 practice.
- **Concept videos**: 53 narrated animations (1440p, with captions) at the top of the sections they explain, from the `count++` race to G1's regions. Pick the narrator voice and speed under any video; the choice applies to all of them.

There is no sign-in. Progress is saved in the browser (`localStorage`); to move it between devices, use "Copy my progress" and "Import" on the Plan page.

## Do the labs

You need JDK 21 or newer (JDK 25 recommended).

```bash
cd labs
./gradlew :concurrency:solutionTest                                   # proves the setup works
./gradlew :concurrency:test --tests 'workbench.concurrency.l03.*'     # lesson conc-03's lab, against your code
./gradlew :concurrency:demo -Pmain=workbench.concurrency.l03.RaceDemo # a Try-it demo
```

Every track module has `src/main` (exercises), `src/test` (the tests), `src/demo` (Try-it programs) and `src/solution` (reference answers with the same class names). `test` runs the tests against your code; `solutionTest` runs the same tests against the answers.

## Build the site

```bash
pip install markdown pygments
python3 site/validate.py --all    # checks every lesson against the writing brief
python3 site/build.py             # writes web/index.html
```

`web/` is committed, so deploying needs no build step.

## Deploy to Cloudflare

Step-by-step instructions are in [DEPLOY.md](DEPLOY.md). In short, the site is a static Cloudflare Worker (`wrangler.jsonc`, assets only). Either:

- connect this repo in the Cloudflare dashboard (Workers & Pages, Create, Import a repository) with deploy command `npx wrangler deploy`, so every push to `main` deploys (DEPLOY.md explains how to start a build by hand if pushes don't trigger one); or
- add `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` as repository secrets, and the `ci` workflow deploys after the content and lab checks pass; or
- run `npx wrangler deploy` from the repo root.

## What is in this repo

| Folder | What it holds |
|---|---|
| `content/course.json` | Tracks and lesson order |
| `content/lessons/` | One JSON file per lesson |
| `content/tracks/` | Track intro, cheat sheet, recap and track quiz |
| `labs/` | The Gradle project with every exercise, test, demo and solution |
| `site/` | `build.py`, `validate.py`, `app.js`, `style.css` |
| `web/` | The built site that Cloudflare serves, including `web/video/` and the extra narrator tracks in `web/vvoice/` |
| `videos/` | The Manim scene for every video, `render.sh` and `revoice.py` (see `brief/VIDEO.md`) |
| `content/videos/` | Which video sits in which lesson section, and `_live.json`, the videos that are checked and published |
| `brief/` | The writing brief, track outlines and lesson generator scripts |
| `research_notes/`, `reports/` | Fact-checked research behind the lessons |
| `art/` | An earlier cover plate and its design philosophy (no longer used on the site) |

All company names, people and numbers in examples are made up.
