import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/executors/src"
P = "java/workbench/executors/l05"
KP = "kotlin/workbench/executors/l05"
read = lambda p: (ROOT / p).read_text()

def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l05.{name}",
            "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{KP}/{name}.kt"),
                    "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l05.{name}Kt",
                    "file": f"{lab}/demo/{KP}/{name}.kt"}}

# timeline: x = 110 + ms * 0.6
def x(ms): return 110 + ms * 0.6
def run_rects(starts, durs, y):
    out = []
    for i, (s, d) in enumerate(zip(starts, durs)):
        cls = "box-bad" if d > 100 else "box-a"
        out.append(f'<rect class="{cls}" x="{x(s):.0f}" y="{y}" width="{max(d * 0.6, 5):.0f}" height="30" rx="4"/>')
    return "".join(out)

rate_s, durs = [0, 100, 350, 360, 400, 500, 600], [10, 250, 10, 10, 10, 10, 10]
delay_s = [0, 110, 460, 570, 680, 790, 900]
SVG = (
    '<svg viewBox="0 0 680 235" role="img" aria-label="Timeline: with fixed rate, runs after a slow run start back to back to catch up; with fixed delay, every run starts 100 ms after the previous one ends">'
    '<text class="t" x="55" y="60" text-anchor="middle">fixed rate</text>'
    '<text class="t" x="55" y="140" text-anchor="middle">fixed delay</text>'
    + run_rects(rate_s, durs, 40) +
    f'<text class="t-s" x="{x(100) + 75:.0f}" y="60" text-anchor="middle">run 2: 250 ms</text>'
    '<text class="t-s t-m" x="338" y="90" text-anchor="middle">3 and 4 run back to back</text>'
    + run_rects(delay_s, durs, 120) +
    f'<text class="t-s" x="{x(110) + 75:.0f}" y="140" text-anchor="middle">run 2: 250 ms</text>'
    '<text class="t-s t-m" x="420" y="170" text-anchor="middle">each start waits 100 ms after the last end</text>'
    f'<line class="ln" x1="110" y1="200" x2="{x(910):.0f}" y2="200"/>'
    + "".join(f'<line class="ln" x1="{x(t):.0f}" y1="195" x2="{x(t):.0f}" y2="205"/>' for t in range(0, 901, 100)) +
    '<text class="t-s t-m" x="110" y="222" text-anchor="middle">0</text>'
    f'<text class="t-s t-m" x="{x(500):.0f}" y="222" text-anchor="middle">500 ms</text>'
    f'<text class="t-s t-m" x="{x(900):.0f}" y="222" text-anchor="middle">900 ms</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Picture a restaurant that hires a cleaner to wipe the tables during dinner. The manager can give one of two instructions. "Start a round at 6:00, 6:10, 6:20, by the clock." Or: "When you finish a round, rest ten minutes, then start the next one."

On a quiet evening you can't tell the two apart, because every round takes a minute or two. Then someone knocks over a pot of soup, and one round takes twenty-five minutes. Now the two give very different evenings.

And one evening the cleaner slips on that soup, goes home, and never comes back. Nobody tells the manager. The tables just get dirtier.

Java's scheduled executor takes both instructions. It's a thread pool, a small team of threads (paths of work that run side by side), that runs tasks later or over and over. And it treats a failed run the way that cleaner did.

The last lesson gave us a ticket for a task that runs once. In this lesson, we'll put tasks on a timetable, watch one slow run bend it, and stop one failure from ending a schedule for good. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Programs are full of small jobs that must happen later, or over and over. Our shop shows prices in dollars as well as euros. So it keeps an exchange rate in memory, the number of dollars one euro buys, and fetches a fresh one from a rate service every 5 seconds. It sends the bank a heartbeat every 30 seconds, a short "still here" message that the bank expects on a steady beat. And when a customer reserves a table, the reservation is dropped after 15 minutes unless they confirm it.

You could write each job by hand, like the mail-room relay in A thread's life. The relay was a thread that did its job, slept, and looped. That works, and it's easy to read. But it costs a thread for every job, and stopping each one cleanly means getting the interrupt rules from the last lesson right, every time.

The first scheduler in the JDK, Java's standard library, was `java.util.Timer`, from Java 1.3. It runs every task on one thread, and it has a trap. If one task throws, that thread dies and the whole `Timer` is cancelled. Every other task on it stops too, and the next call to `schedule` throws `IllegalStateException`. So skip `Timer`.

JDK 5 replaced it with `ScheduledExecutorService`. It's a thread pool, a small team of threads that take tasks from a queue, and it can also run tasks later or over and over. You get one from `Executors.newScheduledThreadPool(n)` or `Executors.newSingleThreadScheduledExecutor()`. Three of its methods do nearly all the work:

```java
ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(2);

scheduler.schedule(this::dropReservation, 15, TimeUnit.MINUTES);               // once, after a delay
scheduler.scheduleAtFixedRate(this::sendHeartbeat, 0, 30, TimeUnit.SECONDS);   // by the clock
scheduler.scheduleWithFixedDelay(this::refreshRate, 0, 5, TimeUnit.SECONDS);   // a gap after each run
```

```kotlin
val scheduler = Executors.newScheduledThreadPool(2)

scheduler.schedule(this::dropReservation, 15, TimeUnit.MINUTES)               // once, after a delay
scheduler.scheduleAtFixedRate(this::sendHeartbeat, 0, 30, TimeUnit.SECONDS)   // by the clock
scheduler.scheduleWithFixedDelay(this::refreshRate, 0, 5, TimeUnit.SECONDS)   // a gap after each run
```

Read them as the manager's instructions. `schedule` says "do this once, in 15 minutes". `scheduleAtFixedRate` says "start at 0, 30 and 60 seconds and so on, by the clock". `scheduleWithFixedDelay` says "when you finish, wait 5 seconds, then go again". The first number in the last two is the **initial delay**, how long to wait before the first run.

Each call hands back a `ScheduledFuture`. It's the ticket from the last lesson, plus one extra: it knows how long until its next run. Cancel it to stop a repeating task. Don't wait on it, though. For a repeating task, `get()` returns only when the task is cancelled or fails, and that matters in the third section.

The scheduler is a pool like any other, so shut it down when you're done. Otherwise its threads keep the JVM, the program that runs your Java code, alive.

Not every timetable belongs inside your program, and the aside below says where the others go. For the ones that do, the two repeating methods behave the same until one run is slow."""

ASIDE0 = {
    "title": "Where do schedules that must survive a restart live?",
    "body": "Outside the program, because a scheduler in memory forgets every plan when the program restarts. Busy websites also run several copies of the same program, and each copy would run the job. A job that matters to the business, such as emailing the day's sales report, needs a scheduler that writes its plans down. If you run services, look at cron, the Unix tool that runs commands on a timetable, or Quartz, a Java library that keeps its jobs in a database. Workflow engines such as Temporal can hold schedules too. Keep the scheduler inside the program for housekeeping, such as refreshing a value in memory or sending heartbeats."
}

# ---------------------------------------------------------------- section 1
S1 = """The two repeating methods measure their period from different places.

`scheduleAtFixedRate(task, initialDelay, period, unit)` follows a timetable fixed in advance, like the cleaner who goes by the clock. Runs are due at `initialDelay`, then `initialDelay + period`, then `initialDelay + 2 x period`, and so on. `scheduleWithFixedDelay(task, initialDelay, delay, unit)` waits `delay` after each run ends, then starts the next one, like the cleaner who rests after each round.

While every run is short, you can't tell them apart. They split when one run is slow. Let's work one case by hand first. The period is 100 ms, the second run takes 250 ms, and every other run takes 10 ms. The lab's model counts make-believe milliseconds, so no real clock gets in the way, and it gives these start times:

```text
fixed rate:   0, 100, 350, 360, 400, 500, 600
fixed delay:  0, 110, 460, 570, 680, 790, 900
```

Take fixed rate first. Run 2 starts on time at 100 and ends at 350. Run 3 was due at 200, so it's late, and it starts the moment run 2 ends, at 350. Run 4 was due at 300, so it starts as soon as run 3 ends, at 360. Run 5 is due at 400, and by then the timetable is back on track.

Fixed delay has no timetable to catch up with. Run 2 starts 100 ms after run 1 ends, at 110, and ends at 360. Run 3 starts 100 ms after that, at 460, and every later run moves along with it.

`RateVsDelayDemo`, in the Try it below, runs the fixed-rate schedule on a real clock. The machine was busy, so every start came a few tens of milliseconds late:

```text
scheduleAtFixedRate, 100 ms
run 1 started at   42 ms, took  10 ms
run 2 started at  139 ms, took 250 ms
run 3 started at  395 ms, took  10 ms
run 4 started at  413 ms, took  10 ms
run 5 started at  442 ms, took  10 ms
run 6 started at  555 ms, took  10 ms
run 7 started at  639 ms, took  10 ms
```

The shape matches the model. Runs 3 and 4 start 18 ms apart, as the scheduler hurries to catch up, like a cleaner jogging from table to table. From run 5 on, the starts are back on the 100 ms grid, give or take the same 40 or so milliseconds of lateness that run 1 had. That lateness is the busy machine, not the slow run.

Both rows come from one thing the executor does. It puts a repeating task back in its queue only when a run returns, with a new due time. For fixed rate, the new due time is the old due time plus the period. For fixed delay, it's the current time plus the delay. A due time that's already in the past means "run as soon as a thread is free".

The same rule means a task never runs at the same time as itself, even on a scheduler with many threads. A task that takes 3 minutes on a 1-minute rate doesn't pile up three copies. It just runs late, every time. Here the cleaner picture breaks: a real manager might send a second cleaner to help. A scheduler never will.

**Fixed rate catches up after a slow run. Fixed delay never does.**

So pick fixed rate when the timing itself is the point, such as a heartbeat the bank expects every 30 seconds, or a count of sales per minute. Pick fixed delay when the task calls something that can slow down, such as the rate service or a database. A service that has just recovered from a slow spell doesn't need a burst of catch-up calls.

A slow run only bends the timetable. A run that throws does something worse."""

# ---------------------------------------------------------------- section 2
S2 = """The `ScheduledExecutorService` Javadoc has a sentence that surprises most people. A repeating task keeps running until it's cancelled, until the executor shuts down, or until one of its runs throws an exception. After that, "subsequent executions are suppressed." In plain words, every later run is skipped, for good.

Nothing is logged, and the cause is the rule from the last section. The task goes back in the queue only when a run returns normally. A run that throws leaves its exception inside the `ScheduledFuture`, the same way `submit` hid a failure in Why pools. And the task never goes back in the queue.

`SilentDeathDemo` shows it. A health check, a small task that checks that the program can still reach the bank, runs every 100 ms. On its third run, the bank doesn't answer, and the check throws. After one second, the demo reads the ticket:

```text
health check 1
health check 2
health check 3
after 1 s: runs=3 isDone=true
get() threw ExecutionException, cause: java.lang.IllegalStateException: bank did not answer
```

Ten periods passed, three checks ran, and the scheduler said nothing. It didn't log, and it didn't retry. It didn't stop its other tasks either, which is exactly why nobody notices. It may be the most discreet class in `java.util.concurrent`. Only the `get()` call at the end, which hardly anyone writes for a repeating task, shows what happened.

Now picture the same thing in the shop. The exchange-rate refresher throws once, on a day the rate service has a short outage, and it never runs again. The shop keeps showing dollar prices from a rate that's hours old. The first sign is a customer asking why a price looks wrong. That's the cleaner who slipped and went home.

The fix is to catch the exception inside the task, so that no exception ever reaches the scheduler:

```java
scheduler.scheduleWithFixedDelay(() -> {
    try {
        refreshRate();
    } catch (RuntimeException e) {
        log.warn("rate refresh failed, keeping the last rate", e);   // report it, keep the schedule
    }
}, 0, 5, TimeUnit.SECONDS);
```

```kotlin
scheduler.scheduleWithFixedDelay({
    try {
        refreshRate()
    } catch (e: RuntimeException) {
        log.warn("rate refresh failed, keeping the last rate", e)    // report it, keep the schedule
    }
}, 0, 5, TimeUnit.SECONDS)
```

I'd catch `RuntimeException` here, or `Exception` if the body calls code that throws checked exceptions, but not `Throwable`. An `Error`, such as `OutOfMemoryError`, means the JVM itself is in trouble, and a schedule that hides it would keep failing out of sight. Let errors stop the task, and alert on them. The lab wraps this pattern once, as `SafeTask.wrap`, so every repeating task can use it.

**A repeating task that throws once never runs again, and nothing logs it. Catch inside the task.**

For a second line of defense, check the ticket. Many programs serve a health page, a small web page that monitoring tools read to see whether the program is well. Have it report `future.isDone()`: for a task that should run forever, done means dead.

Every schedule so far ran on a scheduler with one thread. What does one thread mean for the tasks that share it?"""

# ---------------------------------------------------------------- section 3
S3 = """`Executors.newScheduledThreadPool(n)` returns a `ScheduledThreadPoolExecutor`. It's a `ThreadPoolExecutor`, the class from Inside ThreadPoolExecutor, with one change. Its queue is a **delay queue**, a queue ordered by due time that hands out each task only when it comes due.

Its Javadoc says it "acts as a fixed-sized pool using corePoolSize threads and an unbounded queue". You saw in that lesson what an unbounded queue does to the maximum pool size: it never comes into play. Three things follow.

First, a scheduler with one thread runs one task at a time. A refresh that hangs for a minute delays every other task on that scheduler by a minute, heartbeats included. So give slow repeating work its own scheduler, or let the scheduled task just hand the real work to another pool.

Second, a cancelled task stays in the queue until its due time, by default. If you schedule and cancel a lot, for example one time limit per request, call `setRemoveOnCancelPolicy(true)` so cancelled tasks don't pile up.

Third, after `shutdown()`, one-time delayed tasks still run when they come due, but repeating tasks stop. Those are the defaults of `setExecuteExistingDelayedTasksAfterShutdownPolicy` and `setContinueExistingPeriodicTasksAfterShutdownPolicy`. They matter when a program shuts down with reservations still waiting to be dropped.

Check yourself on the first one. One single-thread scheduler sends a heartbeat at a 30-second fixed rate and refreshes the rate with a 5-second fixed delay. A refresh starts just after a heartbeat and hangs for 90 seconds. How many heartbeats go out during the hang, and what happens when it ends?

None go out during the hang, because the only thread is busy. When the refresh returns, the three heartbeats that came due in the meantime run back to back, because their due times are all in the past. The next refresh starts 5 seconds after the hung one ended. The bank saw 90 seconds of silence, then three beats at once.

JDK 25 adds a second scheduler you already have. `ForkJoinPool`, the JDK's other big pool, now implements `ScheduledExecutorService` too (lesson 8 of this track covers `ForkJoinPool`). So does its common pool, `ForkJoinPool.commonPool()`, one pool that the whole JVM shares. Fixed rate, fixed delay and the rule about exceptions work the same way there.

`ForkJoinPool` also gains `submitWithTimeout`, which cancels a task if it hasn't finished in time. Both compile only on JDK 25 or later, so they stay out of the labs:

```java
// JDK 25+
ForkJoinPool pool = ForkJoinPool.commonPool();
pool.scheduleWithFixedDelay(this::refreshRate, 0, 5, TimeUnit.SECONDS);
ForkJoinTask<BigDecimal> rate = pool.submitWithTimeout(() -> fetchRate("EUR", "USD"), 300, TimeUnit.MILLISECONDS, null);
// a null timeout action means: cancel(true) if it isn't done after 300 ms
```

```kotlin
// JDK 25+
val pool = ForkJoinPool.commonPool()
pool.scheduleWithFixedDelay(this::refreshRate, 0, 5, TimeUnit.SECONDS)
val rate: ForkJoinTask<BigDecimal> = pool.submitWithTimeout({ fetchRate("EUR", "USD") }, 300, TimeUnit.MILLISECONDS, null)
// a null timeout action means: cancel(true) if it isn't done after 300 ms
```

Keep work that waits off the common pool, scheduled or not. Every parallel stream in the JVM (a stream that splits its work across threads) shares it, and so does the next lesson's tool when you don't name a pool.

**A scheduler is a fixed pool. A slow task delays every task that shares its threads.**

Every tool in this lesson shares one limit: each task runs on its own, start to finish. A refresh can't say "when the rate arrives, convert the price, then charge the card". Steps that follow each other need a different kind of ticket."""

L = {
 "id": "exec-05",
 "title": "Scheduled executors: fixed rate vs fixed delay",
 "minutes": 35,
 "goal": "By the end you can choose between schedule, fixed rate and fixed delay, predict when each run starts, and keep a repeating task alive when one run throws.",
 "opening": OPENING,
 "warmup": {
  "q": "You schedule a health check, a small task that checks that the program can still reach the bank, with `scheduleAtFixedRate(check, 0, 10, SECONDS)`. On its fifth run, the call to the bank throws an `IllegalStateException` that nothing catches. What happens next?",
  "options": [
   "The exception is logged, and the check runs again 10 seconds later",
   "The scheduler's thread dies, a new one starts, and the check carries on",
   "The check never runs again, and nothing is logged",
   "The whole scheduler shuts down"
  ],
  "answer": 2,
  "why": "The Javadoc says that if any run throws, \"subsequent executions are suppressed\": every later run is skipped. The exception is stored in the `ScheduledFuture`, and nothing prints it. The scheduler itself is fine and keeps running its other tasks, which is why the failure is so easy to miss. The third section shows it."
 },
 "sections": [
  {
   "h": "Three ways to ask for later: schedule, fixed rate and fixed delay",
   "body": S0,
   "aside": ASIDE0,
   "try": {
    "title": "Pick the method",
    "minutes": 3,
    "steps": [
     "For each job, choose `schedule`, `scheduleAtFixedRate`, `scheduleWithFixedDelay`, or \"not in this program\": (a) drop a table reservation 15 minutes after it was made, unless someone confirmed it; (b) send the bank a heartbeat every 30 seconds, which it expects on a steady beat; (c) refresh the exchange rate from a service whose answers sometimes take 20 seconds; (d) email the day's sales report to the accountant once a night.",
     "Write one sentence of reasoning for each before you read the answer."
    ],
    "expect": "(a) `schedule`: it happens once, after a delay. (b) Fixed rate: the timing itself is the point. (c) Fixed delay: a slow answer pushes the next fetch later, instead of causing a burst of catch-up calls, as the next section shows. (d) Not in this program: a restart would lose the plan, and every copy of the program would send the report."
   },
   "refs": [
    {"title": "ScheduledExecutorService (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html", "kind": "docs"}
   ]
  },
  {
   "h": "When one run is slow: fixed rate catches up, fixed delay moves everything later",
   "body": S1,
   "figure": {"svg": SVG, "caption": "The same slow second run under both instructions. Fixed rate catches up with its timetable; fixed delay moves every later run."},
   "try": {
    "title": "Watch a slow run",
    "minutes": 3,
    "steps": [
     "Run `RateVsDelayDemo` and compare its start times with the fixed-rate row of the model.",
     "Run it again with `-Pargs=delay`. Before you do, predict when run 3 starts."
    ],
    "code": demo("RateVsDelayDemo"),
    "expect": "With fixed rate, runs 3 and 4 start within about 10 to 20 ms of each other, right after the slow run, and from run 5 the starts are back near the 100 ms grid. With fixed delay, run 3 starts about 100 ms after run 2 ends (around 460 ms, or 529 ms in a run here on a busy machine), and each later run starts about 110 ms after the one before. On a busy machine, every time drifts a little later."
   }
  },
  {
   "h": "When one run throws: the schedule stops without a word",
   "body": S2,
   "try": {
    "title": "Stop a schedule, then save it",
    "minutes": 3,
    "steps": [
     "Run `SilentDeathDemo`. Count the health checks before the `after 1 s` line.",
     "Run it with `-Pargs=safe`, which wraps the check in a `try`/`catch`. Predict the number of runs after one second."
    ],
    "code": demo("SilentDeathDemo"),
    "expect": "The first run prints three health checks and then nothing for the rest of the second. It reports `isDone=true`, and `get()` shows the hidden exception. With `safe`, run 3 prints `caught and logged: bank did not answer`, and the checks go on to about 10 or 11 in the second, with `isDone=false`."
   }
  },
  {
   "h": "Inside the scheduler: one fixed pool, and a new scheduler in JDK 25",
   "body": S3
  }
 ],
 "compare": {
  "title": "A fixed-delay refresher: a scheduler vs a coroutine loop",
  "java": {"title": "RateRefresh.java", "src": "ScheduledFuture<?> refresher = scheduler.scheduleWithFixedDelay(() -> {\n    try {\n        rate = fetchRate();\n    } catch (RuntimeException e) {\n        log.warn(\"rate refresh failed, keeping the last rate\", e);\n    }\n}, 0, 5, TimeUnit.SECONDS);\n\n// later\nrefresher.cancel(false);   // no more runs; a fetch already running finishes"},
  "kotlin": {"title": "RateRefresh.kt (kotlinx.coroutines)", "src": "val refresher = scope.launch {\n    while (isActive) {\n        try {\n            rate = fetchRate()\n        } catch (e: CancellationException) {\n            throw e                                  // let cancellation through\n        } catch (e: Exception) {\n            log.warn(\"rate refresh failed, keeping the last rate\", e)\n        }\n        delay(5.seconds)                             // the gap starts when the run ends\n    }\n}\n\n// later\nrefresher.cancel()         // stops at the next delay()"},
  "note": "Kotlin's coroutines, light tasks that can pause without holding a thread, have no scheduler API. A loop with `delay` is a fixed-delay schedule, because the wait starts when the run ends. A fixed rate needs you to work out the next due time yourself. Failures behave differently, in a useful way. An exception that escapes the JDK task disappears into the `ScheduledFuture`, while one that escapes `launch` travels up to the parent scope and its exception handler, so it's loud by default. Either way, you catch inside the loop to keep it running. In Kotlin, rethrow `CancellationException`, or `cancel()` would be swallowed like any other exception."
 },
 "worked": {
  "title": "Why did the exchange rate stop updating?",
  "steps": [
   {"say": "The shop's dollar prices have used the same exchange rate for six hours. The logs show no errors. Here is the refresher. Find the bug before reading on.",
    "code": "scheduler.scheduleAtFixedRate(\n        () -> rate = rateService.eurToUsd(),   // throws when the rate service has an error\n        0, 30, TimeUnit.SECONDS);", "lang": "java",
    "alt_code": "scheduler.scheduleAtFixedRate(\n    { rate = rateService.eurToUsd() },         // throws when the rate service has an error\n    0, 30, TimeUnit.SECONDS)", "alt_lang": "kotlin"},
   {"say": "Six hours ago, the rate service had a short outage and `eurToUsd()` threw. That run's exception went into the `ScheduledFuture`, which nobody kept, and every later run was skipped. There's no log line, because nothing ever printed the exception. Fixed rate is a second, smaller problem: when the rate service is slow, overdue runs fire back to back.",
    "code": "", "lang": ""},
   {"say": "Catch inside the task, keep the last good rate, and count the failure. Switch to fixed delay, so a slow rate service never gets a burst of catch-up calls.",
    "code": "ScheduledFuture<?> refresher = scheduler.scheduleWithFixedDelay(() -> {\n    try {\n        rate = rateService.eurToUsd();               // 1. fetch\n        lastSuccess = Instant.now();\n    } catch (RuntimeException e) {\n        failures.increment();                        // 2. count it\n        log.warn(\"rate refresh failed, keeping {}\", rate, e);   // 3. keep the old rate\n    }\n}, 0, 30, TimeUnit.SECONDS);", "lang": "java",
    "alt_code": "val refresher = scheduler.scheduleWithFixedDelay({\n    try {\n        rate = rateService.eurToUsd()                // 1. fetch\n        lastSuccess = Instant.now()\n    } catch (e: RuntimeException) {\n        failures.increment()                         // 2. count it\n        log.warn(\"rate refresh failed, keeping {}\", rate, e)    // 3. keep the old rate\n    }\n}, 0, 30, TimeUnit.SECONDS)", "alt_lang": "kotlin"},
   {"say": "Make the next failure visible. A health check that reports whether the schedule is still alive, and how old the rate is, turns six silent hours into one alert.",
    "code": "boolean healthy = !refresher.isDone()\n        && Duration.between(lastSuccess, Instant.now()).toMinutes() < 5;", "lang": "java",
    "alt_code": "val healthy = !refresher.isDone &&\n    Duration.between(lastSuccess, Instant.now()).toMinutes() < 5", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Model the timetable, then build a refresher that survives",
  "minutes": 14,
  "files": [f"{lab}/main/{P}/Schedules.java", f"{lab}/main/{P}/SafeTask.java", f"{lab}/main/{P}/FxRateRefresher.java"],
  "run": "./gradlew :executors:test --tests 'workbench.executors.l05.*'",
  "steps": [
   "Run the tests. All eight fail.",
   "Write `Schedules.startTimes`, the model from the second section. Keep the end time of the previous run in a variable. For fixed rate, a run starts at its due time or when the previous run ends, whichever is later. For fixed delay, it starts at that end time plus the period.",
   "Write `SafeTask.wrap`: a lambda that runs the task inside a `try`/`catch` for `RuntimeException`, and hands the exception to `onError`.",
   "Write `FxRateRefresher`, which keeps the euro to dollar rate fresh. `start()` calls `scheduleWithFixedDelay` with an initial delay of 0 and a `SafeTask` that stores the rate and counts failures. `close()` cancels the ticket that `scheduleWithFixedDelay` returned.",
   "Run the tests until all eight pass."
  ],
  "hints": [
   "Run 0 of the model always starts at `initialDelay`, whatever the mode.",
   "Many threads read `current()` while the scheduler's thread writes the rate. Store it in an `AtomicReference<BigDecimal>` (or a `volatile` field), not a plain field, so the readers see each new rate.",
   "`close()` must not shut down the scheduler: it belongs to the caller and may run other tasks. Cancel your own `ScheduledFuture` with `cancel(false)`."
  ],
  "done_when": "All eight tests in `SchedulingTest` pass."
 },
 "drill": {
  "title": "A refresher that can't stop quietly",
  "minutes": 4,
  "prompt": "Close this page. Write the code that refreshes a value in memory every 10 seconds, measured from the end of each refresh. It keeps the old value when a refresh throws, logs the failure, and can be stopped later. Then compare with the answer. Which method did you use, and where is the `try`?",
  "answer": {"lang": "java", "title": "Refresh.java", "src": "ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();\nAtomicReference<Limits> limits = new AtomicReference<>();\n\nScheduledFuture<?> refresh = scheduler.scheduleWithFixedDelay(() -> {\n    try {\n        limits.set(loadLimits());                     // replace only on success\n    } catch (RuntimeException e) {\n        log.warn(\"limit refresh failed, keeping the old value\", e);\n    }\n}, 0, 10, TimeUnit.SECONDS);\n\n// to stop it\nrefresh.cancel(false);\nscheduler.shutdown();",
   "alt": {"lang": "kotlin", "title": "Refresh.kt", "src": "val scheduler = Executors.newSingleThreadScheduledExecutor()\nval limits = AtomicReference<Limits>()\n\nval refresh = scheduler.scheduleWithFixedDelay({\n    try {\n        limits.set(loadLimits())                      // replace only on success\n    } catch (e: RuntimeException) {\n        log.warn(\"limit refresh failed, keeping the old value\", e)\n    }\n}, 0, 10, TimeUnit.SECONDS)\n\n// to stop it\nrefresh.cancel(false)\nscheduler.shutdown()"}}
 },
 "recap": [
  "`schedule` runs a task once after a delay, `scheduleAtFixedRate` follows a timetable, and `scheduleWithFixedDelay` waits a fixed gap after each run ends.",
  "After a slow run, fixed rate starts the overdue runs back to back to catch up. Fixed delay just moves the later runs. Runs of one task never overlap.",
  "If one run of a repeating task throws, every later run is skipped, and nothing is logged. Catch `RuntimeException` inside the task.",
  "`ScheduledThreadPoolExecutor` is a fixed pool with an unbounded delay queue. A slow task on its only thread delays every other task.",
  "Since JDK 25, `ForkJoinPool`, including the common pool, implements `ScheduledExecutorService` and adds `submitWithTimeout`.",
  "The limit: a scheduler in memory forgets its plans on a restart, runs once per copy of the program, and runs each task on its own. Jobs that matter to the business belong in a scheduler outside the program."
 ],
 "closing": "We started with a cleaner and two instructions: by the clock, or a rest after each round. One slow round showed the difference. Fixed rate hurried to catch up, and fixed delay moved everything later. Then one failed run ended a schedule for good, without a word, and a `try` inside the task kept it alive.\n\nNow search your own code for `scheduleAtFixedRate` and `scheduleWithFixedDelay`. Check that the body of every task they run sits inside a `try`/`catch`.\n\nNext, we'll chain steps instead of repeating them. What if a ticket could carry instructions: when the rate arrives, convert the price, then charge the card?",
 "quiz": [
  {
   "q": "A task scheduled with `scheduleAtFixedRate(task, 0, 1, SECONDS)` takes 3 seconds every time. What happens?",
   "options": [
    "Three copies run at once, one starting each second",
    "Each run starts as soon as the previous one ends, so it runs back to back",
    "The scheduler skips the missed slots and waits for the next whole second",
    "The scheduler throws RejectedExecutionException"
   ],
   "answer": 1,
   "why": "Runs of one repeating task never overlap. Every run is overdue by the time the last one ends, so it starts at once, and the task runs without a break. Missed slots are not skipped; they run late."
  },
  {
   "q": "`scheduleWithFixedDelay(task, 0, 10, SECONDS)` runs a task that always takes 2 seconds. When do the first three runs start?",
   "options": [
    "0, 10 and 20 seconds",
    "0, 2 and 12 seconds",
    "0, 8 and 16 seconds",
    "0, 12 and 24 seconds"
   ],
   "answer": 3,
   "why": "The delay counts from the end of each run. Run 1 ends at 2 s, so run 2 starts at 12 s and ends at 14 s, and run 3 starts at 24 s. 0, 10 and 20 is what fixed rate would give."
  },
  {
   "q": "A repeating refresh of a value in memory throws a NullPointerException on its 40th run. Nothing catches it. What do you see?",
   "options": [
    "It stops for good, nothing is logged, and its future reports isDone() = true",
    "It logs the exception and runs again next period",
    "The scheduler's thread dies and is replaced, and the task keeps running",
    "The scheduler shuts down"
   ],
   "answer": 0,
   "why": "Every later run is skipped, and the exception is stored in the `ScheduledFuture`. Nothing is printed, which is the dangerous part. The scheduler and its other tasks carry on as if nothing happened."
  },
  {
   "q": "A single-thread scheduler sends the bank a heartbeat every 30 seconds and runs a report job that sometimes takes 2 minutes. The bank complains about missing heartbeats. What is the right fix?",
   "options": [
    "Raise the scheduler's maximum pool size",
    "Switch the heartbeat to fixed delay",
    "Give the report job its own scheduler, or have its scheduled task hand the work to another pool",
    "Wrap the heartbeat in a try/catch"
   ],
   "answer": 2,
   "why": "With one thread, the heartbeat can't run while the report is running. The maximum pool size does nothing on a `ScheduledThreadPoolExecutor`, and neither fixed delay nor a try/catch frees the thread. Keep the slow job away from the one whose timing matters."
  },
  {
   "q": "From \"Callable, Future, cancellation and interruption\": a repeating task is in the middle of a run when you call `cancel(false)` on its `ScheduledFuture`. What happens?",
   "options": [
    "The run in progress is interrupted, and no more runs happen",
    "The run in progress finishes, and no more runs happen",
    "Nothing, because cancel(false) only affects tasks that have not started",
    "The run in progress finishes, and the schedule continues"
   ],
   "answer": 1,
   "why": "`cancel(false)` doesn't interrupt a running task, so the current run completes. Cancelling still marks the future cancelled, so the scheduler never queues the next run. `cancel(true)` would also interrupt the current run.",
   "from": "exec-04"
  }
 ],
 "flashcards": [
  {"front": "`scheduleAtFixedRate` vs `scheduleWithFixedDelay`: where is the period measured from?", "back": "Fixed rate: from a timetable fixed at the start (initialDelay + n x period). Fixed delay: from the end of the previous run."},
  {"front": "A repeating task throws once, and nothing catches it. What happens to later runs?", "back": "They are skipped forever. Nothing is logged; the exception sits in the ScheduledFuture."},
  {"front": "Can two runs of the same repeating task overlap?", "back": "No. A late run waits for the previous one to finish, however many threads the scheduler has."},
  {"front": "Why does `maximumPoolSize` do nothing on a ScheduledThreadPoolExecutor?", "back": "It's a fixed pool of core threads with an unbounded delay queue, so it never grows past its core size."},
  {"front": "What did JDK 25 add to ForkJoinPool for scheduling?", "back": "It implements ScheduledExecutorService (schedule, fixed rate, fixed delay) and adds `submitWithTimeout`."},
  {"front": "Why avoid `java.util.Timer`?", "back": "It runs all tasks on one thread, and one task that throws kills that thread and cancels every task on the Timer."}
 ],
 "terms": [
  {"term": "ScheduledExecutorService", "plain": "A thread pool that can run tasks after a delay, or over and over."},
  {"term": "Fixed rate", "plain": "Runs are due at fixed times (start + n x period), and late runs catch up."},
  {"term": "Fixed delay", "plain": "A fixed gap between the end of one run and the start of the next."},
  {"term": "ScheduledFuture", "plain": "The ticket for a scheduled task: cancel it, check isDone, or read the time until its next run."},
  {"term": "Suppressed execution", "plain": "A run of a repeating task that never happens, because an earlier run threw."},
  {"term": "Delay queue", "plain": "A queue ordered by due time that hands out each task only when it comes due."}
 ],
 "explain_back": {
  "prompt": "Explain to a friend the difference between fixed rate and fixed delay, and why every repeating task needs a try/catch inside it.",
  "answer": "Fixed rate keeps a timetable: runs are due at the start time plus whole periods, and if one run is slow, the overdue runs start back to back until the schedule is back on time. Fixed delay waits the full delay after each run finishes, so a slow run just moves everything later, and nothing bunches up. That makes fixed delay the safer choice for anything that calls a service that can slow down. In both modes, if any run throws an exception that escapes the task, the scheduler never runs it again and logs nothing. The exception sits in the ScheduledFuture that nobody reads. So the task body needs a try/catch that logs the failure and keeps the last good value, and ideally a health check that alerts when the future is done or the last success is too old."
 },
 "deeper": {
  "minutes": 7,
  "body": "The scheduler's clock is `System.nanoTime()`, a clock that only moves forward, not the time of day. So a repeating task is not affected when the computer corrects its clock from the network, or when daylight saving time starts, which is what you want for \"every 30 seconds\". It also means a `ScheduledExecutorService` can't say \"at 02:00 local time\". You can come close by working out the delay to the next 02:00 and calling `schedule` again after each run, but needing that is a sign the job belongs in a scheduler outside the program.\n\n`CompletableFuture`, the subject of the next lesson, has a small scheduling helper of its own: `CompletableFuture.delayedExecutor(delay, unit)` returns an `Executor` that runs each task after a delay. Lesson 7 of this track uses its relatives, `orTimeout` and `completeOnTimeout`."
 },
 "sources": [
  {"title": "ScheduledExecutorService (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ScheduledExecutorService.html"},
  {"title": "ScheduledThreadPoolExecutor (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ScheduledThreadPoolExecutor.html"},
  {"title": "ForkJoinPool (Java SE 25 API): scheduling and submitWithTimeout", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ForkJoinPool.html"},
  {"title": "Java Concurrency in Practice, Goetz et al., section 6.2.5 (delayed and periodic tasks)", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/exec-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
