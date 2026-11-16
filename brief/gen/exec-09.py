import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/executors/src"
P = "java/workbench/executors/l09"
KP = "kotlin/workbench/executors/l09"
read = lambda p: (ROOT / p).read_text()

def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l09.{name}",
            "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{KP}/{name}.kt"),
                    "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l09.{name}Kt",
                    "file": f"{lab}/demo/{KP}/{name}.kt"}}

def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

def rect(cls, x, y, w, h, title, sub=None, tcls="t t-code"):
    cx = x + w / 2
    out = f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>'
    if sub:
        out += f'<text class="{tcls}" x="{cx:.0f}" y="{y + 20}" text-anchor="middle">{title}</text>'
        out += f'<text class="t-s" x="{cx:.0f}" y="{y + 38}" text-anchor="middle">{sub}</text>'
    else:
        out += f'<text class="{tcls}" x="{cx:.0f}" y="{y + h / 2 + 5:.0f}" text-anchor="middle">{title}</text>'
    return out

SVG = ('<svg viewBox="0 0 680 270" role="img" aria-label="Pool-induced deadlock: both threads of a 2-thread pool run bill tasks that wait for fetch tasks, and the fetch tasks sit in the queue behind them, so nothing can ever run">'
       '<text class="t" x="140" y="24" text-anchor="middle">2 pool threads</text>'
       '<text class="t" x="520" y="24" text-anchor="middle">the pool\'s queue</text>'
       + rect("box-bad", 20, 40, 240, 50, "bills-0: bill(t1)", "blocked in fetch(t1).get()")
       + rect("box-bad", 20, 130, 240, 50, "bills-1: bill(t2)", "blocked in fetch(t2).get()")
       + rect("box", 420, 40, 200, 36, "bill(t3)")
       + rect("box-dim", 420, 90, 200, 36, "fetch(t1)")
       + rect("box-dim", 420, 140, 200, 36, "fetch(t2)")
       + '<line class="ln-bad" x1="260" y1="65" x2="416" y2="108" marker-end="url(#arr)"/>'
       + '<line class="ln-bad" x1="260" y1="155" x2="416" y2="158" marker-end="url(#arr)"/>'
       + '<text class="t-s t-bad" x="340" y="75" text-anchor="middle">waits for</text>'
       + '<text class="t-s t-bad" x="340" y="148" text-anchor="middle">waits for</text>'
       + '<line class="ln-d" x1="20" y1="210" x2="660" y2="210"/>'
       + '<text class="t-s t-m" x="340" y="234" text-anchor="middle">the fetches can only start on a free thread, and no thread will ever be free:</text>'
       + '<text class="t-s t-m" x="340" y="252" text-anchor="middle">CPU near zero, no exception, and no "deadlock found" in the thread dump</text>'
       + '</svg>')

# ---------------------------------------------------------------- opening
OPENING = """Picture the kitchen at nine on a Saturday night, when the orders stop coming out. The manager walks in with questions. Which cook is stuck? Every cook wears the same white jacket, and nobody has a name tag. Which table was the burned dish for? The note with the table number stayed with the waiter. How long has the rail been this full? Nobody kept count. And at closing time, someone turns off the lights with two dishes still in the oven.

A pool in a real program meets the same questions, and its defaults answer none of them. Its threads are called `pool-3-thread-7`. A task sent with `submit` can fail without a word. The request's label stays on the thread that started the work. And `shutdown()`, as the first lesson showed, waits for nothing. None of this shows up in a test.

The last lesson split arithmetic among cooks who steal from each other. This one is about running any pool for real. In this lesson, we'll add name tags, catch every failure, carry each request's note along, read the numbers that warn of trouble, untangle a pool that waits for itself, and close the kitchen in order. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_NAMED = """ThreadFactory named = Thread.ofPlatform().name("grill-", 0).factory();   // JDK 21+: grill-0, grill-1, ...
ExecutorService grill = Executors.newFixedThreadPool(4, named);"""
K_NAMED = """val named = Thread.ofPlatform().name("grill-", 0).factory()            // JDK 21+: grill-0, grill-1, ...
val grill = Executors.newFixedThreadPool(4, named)"""

S0 = """Start with the name tags. A thread's name shows up in log lines, in profilers and in thread dumps. A **thread dump** is a snapshot of every thread in a running JVM, with its name, its state and the line of code it is on. You can take one with `jcmd <pid> Thread.print`, where `<pid>` is the number the operating system gave the program.

The pools from `Executors` name their threads `pool-3-thread-7`, the seventh thread of the third pool. In a dump of a program with eight pools, that tells you nothing. A **thread factory** is the object a pool asks for each new thread. Hand the pool one that names its threads:

""" + pair(J_NAMED, K_NAMED) + """

Before JDK 21, you write a small `ThreadFactory` with an `AtomicInteger` that counts, or use `ThreadFactoryBuilder` from Guava, a widely used library of Java helpers.

Now failures. The first lesson of this track showed that `execute` and `submit` treat a failing task in opposite ways. In production, that difference decides whether you ever hear about it.

`FailureDemo`, in the Try it below, makes a pool with one thread. The factory names it `grill-0` and gives it an **`UncaughtExceptionHandler`**, the method the JVM calls when an exception escapes a thread. This one prints a line. Then the demo sends one failing task through each method. Predict what each half prints:

```text
1. execute() a task that throws
  handler: grill-0 died of java.lang.IllegalStateException: the grill went out
   the next task runs on grill-1
2. submit() a task that throws
   (nothing printed) the next task runs on grill-1
   only get() shows it: java.lang.IllegalStateException: a negative price
```

With `execute`, the exception escaped the task. The worker `grill-0` died, the handler ran, and the pool started `grill-1` in its place. With `submit`, the `FutureTask` caught the exception and kept it. Nothing printed, and `grill-1` carried on. The grill going out at least made some noise. The negative price would have stayed quiet forever if the demo hadn't called `get()`, and in fire-and-forget code, nobody does.

The default handler doesn't help much either. It prints a stack trace to `System.err`, outside your logs, with no request id. So a handler on the thread factory covers only half the cases, and that half badly.

To cover both, catch failures in one place that every task passes through. `submit`, `invokeAll` and `CompletableFuture.supplyAsync(task, pool)` all end up calling `execute`. So a `ThreadPoolExecutor` subclass that overrides `execute` and wraps each task sees all of them.

The wrapper runs the task inside a `try`. A task from `execute` throws, and the `catch` reports it. A task from `submit` doesn't throw: it's a `FutureTask`, and after it runs, `state()` says `FAILED` and `exceptionNow()` (both JDK 19) hands over the original exception. Report it with the request id, and don't rethrow. Rethrowing only kills the worker and prints the same stack trace a second time. The lab builds exactly that pool, `ProductionPool`.

**`submit` hides failures and `execute` kills workers. Report both from one wrapper.**

The wrapper reports a request id. That raises a fair question: whose request id does a pool thread have?"""

# ---------------------------------------------------------------- section 1
J_WRAP = """static Runnable withRequestId(Runnable task) {
    String captured = RequestContext.get();            // 1. on the submitting thread
    return () -> {
        String previous = RequestContext.get();
        RequestContext.set(captured);                  // 2. on the worker
        try {
            task.run();
        } finally {
            if (previous == null) RequestContext.clear(); else RequestContext.set(previous);   // 3. never leak
        }
    };
}"""
K_WRAP = """fun withRequestId(task: Runnable): Runnable {
    val captured = RequestContext.get()                // 1. on the submitting thread
    return Runnable {
        val previous = RequestContext.get()
        RequestContext.set(captured)                   // 2. on the worker
        try {
            task.run()
        } finally {
            if (previous == null) RequestContext.clear() else RequestContext.set(previous)   // 3. never leak
        }
    }
}"""

S1 = """A **request id** is a short label, such as `req-42`, that a program gives each request it handles and prints on every log line about it. With it, you can find the twenty lines of one request among millions. Programs often keep it in a **`ThreadLocal`**: a variable that has a separate value for each thread, as Don't share: immutability, confinement, ThreadLocal showed. Any code on that thread can read it without passing it around.

The trouble starts at the hand-off. Picture a note about table 4, "nut allergy", pinned to the jacket of the waiter who took the order instead of clipped to the order itself. The order goes to the grill, and the note stays with the waiter. The grill cook sees no note at all. Or he still has an old note pinned to his own jacket, from the last order he cooked.

`ContextDemo` acts that out with a pool of one thread. `main` sets the request id to `req-42`, then submits three tasks. Predict all three lines:

```text
1. plain task sees:   null
2. wrapped task sees: req-42
3. next task sees:    req-7  (left over from an earlier task)
```

Line 1 is the missing note: the pool's thread never saw `req-42`. Line 3 is the old note. An earlier task set `req-7` on the worker and never removed it, and the next caller had no request id at all. Every log line from that task now blames request 7, which finished long ago and did nothing wrong.

Line 2 is the fix, in three steps. Capture the value on the submitting thread, install it on the worker before the task runs, and put the worker's old value back afterwards:

""" + pair(J_WRAP, K_WRAP) + """

In the kitchen, that is copying the note onto the order ticket, pinning it on whichever cook cooks the dish, and taking it off when the dish leaves.

The capture must happen in the method that runs on the submitting thread, which is why it sits outside the lambda. Read the `ThreadLocal` inside the lambda instead, and you read the worker's value, which is the bug you set out to fix. The `finally` matters just as much. Pool threads are reused, so whatever a task leaves behind becomes the next task's context.

Here the kitchen picture breaks, in an instructive way. A paper note falls off or gets thrown away. A `ThreadLocal` value never goes anywhere: it stays on the thread until some code removes it.

Don't make every caller remember to wrap. Wrap once, in the executor that everyone uses, as the lab's `ProductionPool` does.

Virtual threads, the subject of the next track, don't change any of this: a new thread starts with empty `ThreadLocal`s, except inheritable ones. Scoped values, final in JDK 25 (JEP 506), are the newer tool for request context, and that track covers them too.

**A `ThreadLocal` belongs to a thread, not to a task. Capture it at the hand-off, and clean up after.**

Names, failures and context make one task easy to trace. The next question is about all of them at once: is the pool keeping up?"""

ASIDE1 = {
    "title": "What is an MDC, and why do log lines need it?",
    "body": "If your program logs with SLF4J, a widely used logging library for Java, it has an MDC, short for Mapped Diagnostic Context. The MDC is a small map of values for the current thread, such as the request id, and the log format can print a value from it on every line. It is built on a `ThreadLocal`, so everything in this section applies to it. Frameworks for web services often put the request id into the MDC when a request arrives, on the thread that handles it. The lab's `RequestContext` is a one-value stand-in for it."
}

# ---------------------------------------------------------------- section 2
S2 = """A pool is a queue in front of a few threads, and it's often the first place a slow service shows up. A good kitchen keeps a board by the pass with a few numbers on it, and a pool needs one too. Four numbers tell you most of what you need.

The queue size, `getQueue().size()`, is the number of tickets on the rail. A queue that keeps growing means tasks arrive faster than they finish. Little's law, from Sizing a pool, says each task's wait grows with it.

The active count, `getActiveCount()`, compared with the maximum, says how many cooks are busy. A pool stuck at its maximum for minutes is saturated, and it's usually waiting on something further along the path, not working hard.

The rejections are the tasks the pool turned away. `ThreadPoolExecutor` doesn't count them for you. Wrap the `RejectedExecutionHandler`, the code a pool calls when it refuses a task (Inside ThreadPoolExecutor), in one that adds to a counter and then throws.

The time in queue is how long each task waited before a thread picked it up. The caller feels that wait, and the task itself never measures it. Record the time when a task is submitted, in the same wrapper that carries the context, and compare it when the task starts.

`MetricsDemo` sends a burst of 10 tasks of 300 ms each to a pool of 2 threads, named `orders-`, with a queue of 4 and a counting handler. Then it prints the board every 200 ms. Predict the first row before you read it:

```text
  ms  threads  active  queued  done  rejected
   0        2       2       4     0         4
 244        2       2       4     0         4
 446        2       2       2     2         4
 647        2       2       0     4         4
 849        2       2       0     4         4
1050        2       0       0     6         4
```

Two tasks run, four wait in the queue, and four are rejected at once, since 2 + 4 = 6 is all the pool can hold. After that, every 300 ms two more finish. The queue goes 4, 2, 0, `done` climbs 0, 2, 4, 6, and `active` drops to 0 at about 900 ms. (The rows come every 200 ms, a little late on a busy machine, so they catch the 300 ms steps unevenly.) The rejected count stays at 4: four customers told to come back later, and told at once.

Picture the same burst on `newFixedThreadPool(2)`, whose queue has no limit. The board would show `rejected 0` and a queue of 8. Every task is accepted, and the last two wait 1.2 seconds before a thread even picks them up. Only the time in queue would show the trouble. That's why it belongs on the board.

The getters are approximate. The Javadoc says so, because the threads keep changing the numbers while you read them. That's fine for a dashboard and wrong for program logic. If your program already sends numbers to a dashboard, a metrics library such as Micrometer can read most of these from a pool for you.

Of the four, time in queue and rejections are what your customers feel. A pool with an empty queue and no rejections is healthy, however busy its threads look.

**Watch the queue, not just the threads. Count every rejection.**

Now picture a board where every number has frozen: all threads active, the queue full and not moving, nothing done, and the CPU idle."""

# ---------------------------------------------------------------- section 3
J_BUG = """pool.submit(() -> {
    Future<List<String>> lines = pool.submit(() -> orders.lines(table));   // a task inside a task
    return render(table, lines.get());                                     // waits for it
});"""
K_BUG = """pool.submit<String> {
    val lines = pool.submit<List<String>> { orders.lines(table) }   // a task inside a task
    render(table, lines.get())                                     // waits for it
}"""

S3 = """At closing time, a job prints the day's bill for every table. For each table, a task fetches the table's order lines from the order book, a database, and then renders the bill. Someone split the fetch into a task of its own, on the same pool:

""" + pair(J_BUG, K_BUG) + """

With 20 threads and the 5 tables of a test, it's fine. On a busy Saturday there are 400 tables. Let's trace it with those numbers.

1. The first 20 bill tasks take all 20 threads.
2. Each one submits its fetch, and the 20 fetches join the back of the queue, behind 380 waiting bill tasks.
3. Each bill task then waits in `get()` for its fetch.

Every thread now waits for a task that can only run on a free thread, and no thread will ever be free. In the kitchen, every cook has taken a bill ticket, pinned a "fetch the orders" ticket at the back of the rail, and stands waiting for it. No cook is left to take the fetch tickets.

`DeadlockDemo` builds the smallest case: two bill tasks on a pool of two threads named `bills-`, where each fetch takes microseconds:

```text
after 300 ms: active=2, queued=2, completed=0
no bill after 2 s: both threads wait for fetches that can never start
```

Both threads are active, the two fetches are queued, and nothing has completed. Speed isn't the problem. The demo gives up after 2 seconds, but the pool would wait forever. This is **pool-induced deadlock**, which *Java Concurrency in Practice* calls thread starvation deadlock: every thread in a bounded pool waits for a task that is queued in that same pool.

It feels different from the lock deadlock of Deadlock, livelock and starvation. The CPU drops to zero. Nothing throws. A thread dump has no "deadlock found" line, because no lock is involved: every thread is simply `WAITING` in `FutureTask.get`. The figure shows the moment.

There are three fixes, and I'd try them in this order:

1. Don't block inside the pool. Compose: `supplyAsync(() -> orders.lines(t), pool).thenApply(lines -> render(t, lines))`. The render step runs as a callback when the fetch completes, so no thread waits. Only the caller joins at the end. The demo's `fixed` mode does this and prints both bills at once, on the same two threads.
2. Don't split what doesn't need splitting. If the bill task only waits for the fetch, do the fetch inline, in the same task.
3. Give each stage its own pool. Bill tasks may wait for a separate fetch pool, as long as fetch tasks never wait for the bill pool. That's a bulkhead, from Sizing a pool.

A cached pool, with no limit on threads, also makes the hang go away, by starting a thread for every waiting task. That only moves the problem to memory and to the database's connections. Calling `join()` inside a `CompletableFuture` stage is the same bug, which is why CompletableFuture: composing async steps warned against it.

**No task may wait for another task in its own bounded pool. Compose, inline, or use a second pool.**

Our pools can now run well all day. At night, they have to stop."""

# ---------------------------------------------------------------- section 4
STOP_JAVA = """void stop() throws InterruptedException {
    intake.stop();                                                      // 1. no new orders come in
    long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(20);   //    inside the 30 s grace period
    for (ExecutorService pool : List.of(kitchenPool, billingPool)) {    // 2. upstream first: kitchen feeds billing
        pool.shutdown();
        long left = Math.max(0, deadline - System.nanoTime());
        if (!pool.awaitTermination(left, TimeUnit.NANOSECONDS)) {
            List<Runnable> neverStarted = pool.shutdownNow();           // 3. interrupt what is still running
            log.warn("{} tasks never started", neverStarted.size());    // 4. say what was lost
        }
    }
}"""
STOP_KOTLIN = """fun stop() {
    intake.stop()                                                       // 1. no new orders come in
    val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(20)     //    inside the 30 s grace period
    for (pool in listOf(kitchenPool, billingPool)) {                    // 2. upstream first: kitchen feeds billing
        pool.shutdown()
        val left = maxOf(0L, deadline - System.nanoTime())
        if (!pool.awaitTermination(left, TimeUnit.NANOSECONDS)) {
            val neverStarted = pool.shutdownNow()                       // 3. interrupt what is still running
            log.warn("{} tasks never started", neverStarted.size)       // 4. say what was lost
        }
    }
}"""

S4 = """A good restaurant closes in a fixed order. First someone locks the front door, so no new guests come in. Then the kitchen finishes the orders it has, starting with the stations that feed the others. Only then do the lights go off, and all of it has to fit before the night's deadline.

A program is told to stop in much the same way. As the first lesson of this track described, the system that runs a service usually sends a polite signal first. After a grace period, 30 seconds by a common default, it stops the program by force. Everything in flight has to finish inside that window, or be written down as lost.

Here is a stop method for a program with two pools. The kitchen pool's tasks cook dishes, and each finished dish is handed to the billing pool, which adds it to the table's bill:

""" + pair(STOP_JAVA, STOP_KOTLIN) + """

First we stop intake. In a web service, that means no longer accepting requests. Otherwise new work keeps arriving at pools that are trying to drain.

Then we shut the pools down upstream first: the pool that hands work to the other one goes first. Get it backwards, and shut down `billingPool` first. The dishes still cooking in `kitchenPool` then get a `RejectedExecutionException` when they try to add themselves to the bill. They were cooked and served and never billed, a free dinner nobody planned.

The whole sequence gets one deadline, shorter than the grace period, shared between the pools. When a pool misses it, `shutdownNow()` interrupts what is still running and returns the tasks that never started. Log them, with request ids if your wrapper keeps them, so somebody can run them again. Don't forget the schedulers from Scheduled executors: after `shutdown()`, their periodic tasks stop, which is what you want.

If your program runs inside a framework, it usually offers a hook that runs at shutdown, such as a method marked `@PreDestroy`. Put this code there. Never leave a pool for the garbage collector to clean up: its threads keep it alive.

Check yourself: why does `stop()` share one 20-second deadline between the pools, instead of giving each pool 20 seconds? (Because the waits add up. Two pools at 20 seconds each can take 40, and the program is stopped by force at 30, in the middle of the billing pool's drain, before the `log.warn` line can say what was lost.)

**Stop intake first, then drain pools upstream first, all within one deadline.**

Look back over the whole track for its limit. Every pool we sized, named and drained holds one platform thread for each task that waits, and platform threads are costly. A pool of 200 threads stops at 200 waiting requests, however idle the CPU is."""

L = {
 "id": "exec-09",
 "title": "Pools in production: names, errors, context, shutdown",
 "minutes": 38,
 "goal": "By the end you can set up a pool you can debug on its worst night: named threads, every failure reported with its request id, context carried to the worker, the right numbers on a dashboard, a clean shutdown, and no task waiting on another task in the same pool.",
 "opening": OPENING,
 "warmup": {
  "q": "At closing time, a job prints the day's bill for every table, on a fixed pool of 20 threads. Each table's task submits a fetch of that table's orders to the same pool and calls `get()` on it. With the 5 tables of a test, it takes 2 seconds. On a busy Saturday there are 400 tables. What happens?",
  "options": [
   "It takes about 80 times longer, because the pool is busy",
   "The pool grows past 20 threads to keep up",
   "It hangs forever, with the CPU near zero",
   "The JVM detects the deadlock and throws in one of the tasks"
  ],
  "answer": 2,
  "why": "The first 20 bill tasks take every thread, and each one waits for a fetch that is queued behind 380 other bill tasks. No thread will ever be free to run a fetch, so the job hangs. A fixed pool never grows, and the JVM's deadlock detector looks for threads holding locks in a circle, not for tasks waiting on queued tasks, so nothing throws. The fourth section takes it apart."
 },
 "sections": [
  {
   "h": "Name tags and lost failures: naming threads, and catching what submit hides",
   "body": S0,
   "try": {
    "title": "Find out who hears about a failure",
    "minutes": 3,
    "steps": [
     "Read `FailureDemo`. Its threads are named `grill-N` and have an `UncaughtExceptionHandler`.",
     "Before you run it, predict for each case: does the handler print, and which thread runs the next task?"
    ],
    "code": demo("FailureDemo"),
    "expect": "For `execute`, the handler prints `grill-0 died of ... the grill went out`, and the next task runs on `grill-1`: the pool replaced the dead worker. For `submit`, nothing prints, the next task still runs on `grill-1`, and the exception appears only when `get()` is called."
   },
   "refs": [
    {"title": "Thread.Builder (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Thread.Builder.html", "kind": "docs"}
   ]
  },
  {
   "h": "The note pinned to the wrong jacket: carrying request context to the worker",
   "body": S1,
   "aside": ASIDE1,
   "try": {
    "title": "Lose a request id, then leak one",
    "minutes": 3,
    "steps": [
     "Read `ContextDemo`. The main thread sets `req-42` and submits three tasks to a pool with one thread.",
     "Predict all three lines before you run it. For line 3, find the task that caused it."
    ],
    "code": demo("ContextDemo"),
    "expect": "Line 1 prints `null`: the plain task runs on a pool thread that never saw `req-42`. Line 2 prints `req-42`, because the wrapper captured it on `main`. Line 3 prints `req-7`, left over from the earlier task that set the `ThreadLocal` and never removed it, although the new caller had no request at all."
   }
  },
  {
   "h": "The board by the pass: four numbers that show a pool falling behind",
   "body": S2,
   "try": {
    "title": "Read a pool's board",
    "minutes": 3,
    "steps": [
     "`MetricsDemo` sends 10 tasks of 300 ms to a pool with 2 threads and a queue of 4. Predict how many are rejected, and when the queue empties.",
     "Run it, and read the table row by row."
    ],
    "code": demo("MetricsDemo"),
    "expect": "Two tasks run, four wait in the queue, and four are rejected right away (2 + 4 = 6 accepted). Every 300 ms two more finish: the queue goes 4, 2, 0 while `done` climbs 0, 2, 4, 6, and `active` drops to 0 after about 900 ms. The rejected count stays at 4."
   },
   "refs": [
    {"title": "ThreadPoolExecutor (Java SE 25 API): hooks and monitoring", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html", "kind": "docs"}
   ]
  },
  {
   "h": "Cooks waiting for tickets behind them: pool-induced deadlock",
   "body": S3,
   "figure": {"svg": SVG, "caption": "Both threads wait for fetches that sit in the queue behind them. The fetches need a free thread, and none will ever be free."},
   "try": {
    "title": "Hang a pool on purpose",
    "minutes": 3,
    "steps": [
     "Run `DeadlockDemo`: two bill tasks on a pool of two threads, each waiting for a fast fetch on the same pool. Read the active and queued counts.",
     "Run it with `-Pargs=fixed`, which composes the fetch and the render with `CompletableFuture`. Predict how long it takes."
    ],
    "code": demo("DeadlockDemo"),
    "expect": "The default run shows `active=2, queued=2, completed=0` after 300 ms, then gives up after 2 s with no bill, although each fetch takes microseconds. The `fixed` run prints both bills at once, on the same two threads."
   }
  },
  {
   "h": "Closing the kitchen at night: shutting pools down in order, within one deadline",
   "body": S4
  }
 ],
 "compare": {
  "title": "Carrying the MDC: an executor wrapper vs a coroutine context element",
  "java": {"title": "MdcExecutor.java (SLF4J)", "src": "static Executor withMdc(Executor delegate) {\n    return task -> {\n        Map<String, String> captured = MDC.getCopyOfContextMap();     // 1. on the submitting thread\n        delegate.execute(() -> {\n            Map<String, String> previous = MDC.getCopyOfContextMap();\n            if (captured != null) MDC.setContextMap(captured); else MDC.clear();     // 2. on the worker\n            try {\n                task.run();\n            } finally {\n                if (previous != null) MDC.setContextMap(previous); else MDC.clear(); // 3. never leak\n            }\n        });\n    };\n}\n\nCompletableFuture.runAsync(() -> bills.add(dish), withMdc(billingPool));"},
  "kotlin": {"title": "MdcCoroutine.kt (kotlinx-coroutines-slf4j)", "src": "// MDCContext() copies the MDC now and installs it every time the coroutine\n// runs, on whichever thread that is, then restores the thread's own MDC\nscope.launch(Dispatchers.IO + MDCContext()) {\n    bills.add(dish)\n    delay(100)                      // may resume on another thread\n    log.info(\"added\")               // the request id is still in the MDC\n}\n\n// the same idea for your own ThreadLocal\nscope.launch(Dispatchers.IO + requestId.asContextElement(value = \"req-42\")) { /* ... */ }"},
  "note": "The Java wrapper installs the context once, because a task stays on one thread from start to finish. A coroutine, Kotlin's own light task, can move to another thread every time it suspends, so a wrapper around the whole coroutine wouldn't be enough. `MDCContext()` and `asContextElement` are thread context elements: the dispatcher installs the value each time the coroutine resumes on a thread, and restores the thread's old value when it suspends. One trap: an `MDC.put` inside the coroutine is lost at the next suspension, because the element keeps reinstalling the map it captured. The kotlinx docs say to wrap the change in `withContext(MDCContext())`."
 },
 "worked": {
  "title": "Diagnose a bill job that stopped on a busy Saturday",
  "steps": [
   {"say": "The closing-time bill job has printed nothing for 30 minutes, and the CPU is near zero. A thread dump (`jcmd <pid> Thread.print`) shows all 20 `bills-` threads at the same spot. Before reading on, say what they are waiting for.",
    "code": "\"bills-3\" #41 prio=5 os_prio=0 ... waiting on condition\n   java.lang.Thread.State: WAITING (parking)\n\tat jdk.internal.misc.Unsafe.park(Native Method)\n\t- parking to wait for <0x...> (a java.util.concurrent.FutureTask)\n\tat java.util.concurrent.locks.LockSupport.park(...)\n\tat java.util.concurrent.FutureTask.awaitDone(...)\n\tat java.util.concurrent.FutureTask.get(...)\n\tat com.example.restaurant.BillJob.lambda$run$0(BillJob.java)\n\t...", "lang": "text"},
   {"say": "Every thread is inside a bill task, parked in `FutureTask.get()`, waiting for another task's result. The pool's board finishes the story: `active=20`, the queue at 380 and not moving, `completed` flat. The fetch tasks they wait for are in that queue, behind the other bill tasks, and they need a free thread that will never come. The dump has no \"Found one Java-level deadlock\" line, because the detector looks for threads holding locks in a circle, and a `Future` has no owner.",
    "code": "", "lang": ""},
   {"say": "The fix is to stop holding a thread while waiting. Compose the fetch and the render, start every table's pipeline, and let only the job's own thread wait at the end.",
    "code": "List<CompletableFuture<String>> bills = tables.stream()\n        .map(t -> CompletableFuture.supplyAsync(() -> orders.lines(t), pool)   // 1. fetch on the pool\n                .thenApply(lines -> render(t, lines)))                       // 2. render as a callback\n        .toList();\nreturn bills.stream().map(CompletableFuture::join).toList();                // 3. only the caller waits", "lang": "java",
    "alt_code": "val bills = tables.map { t ->\n    CompletableFuture.supplyAsync({ orders.lines(t) }, pool)                // 1. fetch on the pool\n        .thenApply { lines -> render(t, lines) }                           // 2. render as a callback\n}\nreturn bills.map { it.join() }                                             // 3. only the caller waits", "alt_lang": "kotlin"},
   {"say": "Then make the next bad night shorter. The `bills-` name tags already paid off: they showed at once which pool was stuck. Add the queue size and the oldest task's wait for this pool to the dashboard, with an alert, so a queue that stops moving wakes someone up within minutes.",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A production pool, and a bill job to untangle",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/ProductionPool.java", f"{lab}/main/{P}/BillJob.java", f"{lab}/main/{P}/RequestContext.java", f"{lab}/main/{P}/FailureLog.java"],
  "run": "./gradlew :executors:test --tests 'workbench.executors.l09.*'",
  "steps": [
   "Meet the classes. `ProductionPool` is a `ThreadPoolExecutor` with a bounded queue, and you'll give it named threads, carried context and failure reports. `RequestContext` holds the current thread's request id in a `ThreadLocal`. `FailureLog` is where the pool reports a failed task. `BillJob` prints a bill for each table, and it hangs. Run the tests: all eight fail, and the two `BillJob` tests time out after 5 seconds. That is the deadlock.",
   "Write `ProductionPool.create`: build the factory with `Thread.ofPlatform().name(name + \"-\", 0).factory()` and pass it to the private constructor, which already sets up the bounded queue.",
   "Write `ProductionPool.execute`. Read `RequestContext.get()` first, on the calling thread. Then call `super.execute` with a lambda that saves the worker's own context, sets the captured id, runs the task, and restores the saved context in a `finally`.",
   "Report failures inside that lambda: catch `RuntimeException | Error` from `task.run()` and report it without rethrowing. After `run()` returns, if the task is a `Future` whose `state()` is `FAILED`, report `exceptionNow()`.",
   "Fix `BillJob.run`: start a `supplyAsync(fetch, pool).thenApply(render)` pipeline for every table, then join them all on the calling thread.",
   "Run the tests until all eight pass."
  ],
  "hints": [
   "Capture the id before `super.execute`. Inside the lambda you are already on the worker, where `RequestContext.get()` returns the worker's value.",
   "`task instanceof Future<?> f && f.state() == Future.State.FAILED` (JDK 19+), then `f.exceptionNow()`, gives you the original exception, not an `ExecutionException`.",
   "If `reportsExecuteFailures` sees the next task on `orders-1`, your wrapper rethrew: the worker died, and the pool replaced it.",
   "The `BillJob` fix needs no second pool. A `thenApply` callback never holds a thread while it waits."
  ],
  "done_when": "All eight tests in `ProductionTest` pass."
 },
 "drill": {
  "title": "A context-carrying executor from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `Executor withRequestId(Executor delegate)`: every task runs with the `RequestContext` of the thread that called `execute`, and the worker's own value is restored afterwards. Then compare. Where did you read the context, and is the restore in a `finally`?",
  "answer": {"lang": "java", "title": "Contexts.java", "src": "static Executor withRequestId(Executor delegate) {\n    return task -> {\n        String captured = RequestContext.get();          // on the caller's thread\n        delegate.execute(() -> {\n            String previous = RequestContext.get();\n            RequestContext.set(captured);                // on the worker\n            try {\n                task.run();\n            } finally {\n                if (previous == null) RequestContext.clear();\n                else RequestContext.set(previous);\n            }\n        });\n    };\n}",
   "alt": {"lang": "kotlin", "title": "Contexts.kt", "src": "fun withRequestId(delegate: Executor) = Executor { task ->\n    val captured = RequestContext.get()                  // on the caller's thread\n    delegate.execute {\n        val previous = RequestContext.get()\n        RequestContext.set(captured)                     // on the worker\n        try {\n            task.run()\n        } finally {\n            if (previous == null) RequestContext.clear() else RequestContext.set(previous)\n        }\n    }\n}"}}
 },
 "recap": [
  "Name every pool's threads (`Thread.ofPlatform().name(\"grill-\", 0).factory()` on JDK 21+), so dumps and logs say which pool is stuck.",
  "An `UncaughtExceptionHandler` only sees `execute` failures, and `submit` hides them in the `Future`. Wrap `execute` once to report both, with the request id.",
  "`ThreadLocal` context such as a request id doesn't follow a task to a pool. Capture it at submission, install it in the worker, and restore it in `finally`.",
  "Watch the queue size, the active count against the maximum, rejections and time in queue. Count rejections yourself, in the handler.",
  "A task that blocks on another task in the same bounded pool can hang the pool forever. Compose instead, do the work inline, or give each stage its own pool. Shut down in order: intake first, then pools upstream first, within one deadline.",
  "The limit: every pool here holds one costly platform thread for each waiting task, so the thread count caps how many requests can wait at once."
 ],
 "closing": "We started with a stuck kitchen and questions nobody could answer. Now each one has an answer: name tags on every thread, one wrapper that reports every failure with its request id, a note that travels with the order, four numbers on the board, no cook waiting for a ticket behind him, and a closing routine that fits the deadline.\n\nNow find the places in your own code that create pools, and give each one a named thread factory. Then search for `.get()` and `.join()` inside tasks, and check that none of them waits on its own pool.\n\nNext, we'll start the virtual threads track with the thread-per-request wall. If every waiting request holds a costly platform thread, what happens when the requests outnumber the threads?",
 "quiz": [
  {
   "q": "A report job uses a fixed pool of 4. Each report task submits two smaller queries to the same pool and calls `get()` on both. It passes every test, then hangs on the busiest day with the CPU near zero. What happened?",
   "options": [
    "The queries got slow, so the reports need more time",
    "Four report tasks hold all four threads, and each waits for queries queued behind other reports, so nothing can ever finish",
    "Two report tasks locked each other's monitors",
    "The queue overflowed, and the queries were rejected"
   ],
   "answer": 1,
   "why": "This is pool-induced deadlock. The awaited tasks need a free thread, and all the threads are busy waiting for them. Slowness wouldn't keep the CPU at zero forever, no monitors are involved, and a fixed pool's queue has no limit, so nothing is rejected."
  },
  {
   "q": "A request thread puts `req-42` in a `ThreadLocal` (such as a logging library's MDC) and submits a task to a fixed pool. The task logs a line. With no context propagation in place, which request id is on that line?",
   "options": [
    "`req-42`, because pool threads inherit the submitter's ThreadLocals",
    "None, every time, because pool threads clear their ThreadLocals between tasks",
    "Whatever that pool thread last had: often none, sometimes a stale id from an earlier task",
    "The logging call throws, because a ThreadLocal isn't thread-safe"
   ],
   "answer": 2,
   "why": "The value lives on the worker thread. That thread was created long ago and is reused, so it holds nothing, or whatever an earlier task put there and never cleaned up. Nothing clears it between tasks unless your wrapper does."
  },
  {
   "q": "Which number warns you first that a bounded `ThreadPoolExecutor` is falling behind, before it starts rejecting?",
   "options": [
    "`getPoolSize()`",
    "`getCompletedTaskCount()`",
    "`getLargestPoolSize()`",
    "`getQueue().size()` climbing, or the time tasks spend in the queue"
   ],
   "answer": 3,
   "why": "A queue that keeps growing means arrivals outpace completions, and every queued task's wait grows with it. The pool size is fixed in a fixed pool, the completed count only ever rises, and the largest pool size is history. When the queue is full, rejections start."
  },
  {
   "q": "The program's intake hands orders to `kitchenPool`, whose tasks submit to `billingPool`. The program is told to stop. In what order do you shut down?",
   "options": [
    "Stop intake, shut down `kitchenPool` and wait for it, then shut down `billingPool` and wait for it",
    "Shut down `billingPool`, then `kitchenPool`, then stop intake",
    "Call `shutdownNow()` on both pools at once, to be quick",
    "Stop intake, then shut down `billingPool` first, because it handles the money"
   ],
   "answer": 0,
   "why": "Upstream first. While `kitchenPool` drains, its tasks still submit to `billingPool`, so `billingPool` must keep accepting work until then. Shutting it down first makes those submissions fail with `RejectedExecutionException`, and `shutdownNow` on both interrupts work that could have finished."
  },
  {
   "q": "From \"Inside ThreadPoolExecutor\": a `ProductionPool` has 4 threads and a queue of 100, with the default `AbortPolicy`. 200 slow tasks arrive at once. How many are rejected?",
   "options": [
    "0",
    "96",
    "100",
    "196"
   ],
   "answer": 1,
   "why": "Four tasks start the four threads, the next 100 fill the queue, and the core size equals the maximum, so the pool can't grow. The remaining 96 are rejected with `RejectedExecutionException`, which is what a bounded queue is for: the caller hears about the overload at once.",
   "from": "exec-02"
  }
 ],
 "flashcards": [
  {"front": "How do you name pool threads on JDK 21+?", "back": "Pass `Thread.ofPlatform().name(\"grill-\", 0).factory()` to the executor. The threads are named grill-0, grill-1, ..."},
  {"front": "Which pool failures reach an `UncaughtExceptionHandler`?", "back": "Only tasks run with `execute()`. With `submit()` the exception is stored in the Future, and nothing is printed."},
  {"front": "Why does a ThreadLocal value, such as a request id, disappear when you hand a task to a pool?", "back": "The value belongs to the submitting thread, and the task runs on another thread. Capture it at submission and install it in the worker."},
  {"front": "Why must a context wrapper restore the worker's value in `finally`?", "back": "Pool threads are reused. Whatever one task leaves behind becomes the next task's context."},
  {"front": "What is pool-induced deadlock?", "back": "Tasks in a bounded pool block waiting for other tasks queued in the same pool. Every thread waits, and the awaited tasks never start."},
  {"front": "Name two fixes for pool-induced deadlock.", "back": "Compose instead of blocking (`supplyAsync(...).thenApply(...)`), or give each stage its own pool, so waits never point back into the same pool."},
  {"front": "In what order do you shut down chained pools?", "back": "Stop intake, then shut down the upstream pool and wait, then the downstream one, all within one deadline."}
 ],
 "terms": [
  {"term": "Thread factory", "plain": "The object a pool asks for new threads; it sets their names, daemon flag and exception handler."},
  {"term": "Thread dump", "plain": "A snapshot of every thread in a running JVM: its name, its state and the code it is running."},
  {"term": "UncaughtExceptionHandler", "plain": "Code that runs when an exception escapes a thread's run method."},
  {"term": "ThreadLocal", "plain": "A variable with a separate value for each thread."},
  {"term": "MDC", "plain": "Mapped Diagnostic Context: a per-thread map of values, such as a request id, that SLF4J adds to log lines."},
  {"term": "Context propagation", "plain": "Copying thread-local state such as a request id from the submitting thread to the worker."},
  {"term": "Pool-induced deadlock", "plain": "Every thread in a pool waits for a task that is queued in that same pool. Also called thread starvation deadlock."},
  {"term": "Graceful shutdown", "plain": "Stopping intake, letting work in progress finish within a deadline, and recording what didn't."}
 ],
 "explain_back": {
  "prompt": "A friend's closing-time bill job works with 5 tables and hangs with 400, on a fixed pool of 20 threads. Explain what is happening and two ways to fix it.",
  "answer": "Each table's task submits the fetch of its orders to the same pool and blocks on `get()`. With 400 tables, the first 20 tasks take every thread, and their fetches are queued behind the other 380 bill tasks. A fetch can only run on a free thread, and every thread is waiting for a fetch, so nothing ever finishes. The CPU is idle and nothing throws, because no lock is involved. One fix is to stop blocking inside the pool: start `supplyAsync(fetch, pool).thenApply(render)` for each table, so rendering is a callback and only the job's own thread waits at the end. Another is to run the fetches on a separate pool, so the bill threads wait on a pool that never waits back on them. Simplest of all, if the bill task only waits for the fetch, do the fetch inline."
 },
 "deeper": {
  "minutes": 8,
  "body": "Why is the JVM's deadlock detector silent? `jcmd <pid> Thread.print` (and `ThreadMXBean.findDeadlockedThreads`) look for cycles of threads that each hold a lock another one needs: monitors from `synchronized`, and ownable synchronizers such as `ReentrantLock`. A thread waiting in `Future.get()` parks on the future, which has no owner, so there is no cycle to find. Names and stack traces are your only tools, which is one more reason to name threads.\n\nThe `ThreadPoolExecutor` Javadoc shows a second way to catch failures: override the `afterExecute` hook, which runs on the worker after each task:\n\n```java\n@Override\nprotected void afterExecute(Runnable r, Throwable t) {\n    super.afterExecute(r, t);\n    if (t == null && r instanceof Future<?> f && f.isDone()) {\n        try {\n            f.get();\n        } catch (CancellationException e) {\n            t = e;\n        } catch (ExecutionException e) {\n            t = e.getCause();\n        } catch (InterruptedException e) {\n            Thread.currentThread().interrupt();\n        }\n    }\n    if (t != null) log.error(\"task failed on {}\", Thread.currentThread().getName(), t);\n}\n```\n\n```kotlin\noverride fun afterExecute(r: Runnable, t: Throwable?) {\n    super.afterExecute(r, t)\n    var failure = t\n    if (failure == null && r is Future<*> && r.isDone) {\n        try {\n            r.get()\n        } catch (e: CancellationException) {\n            failure = e\n        } catch (e: ExecutionException) {\n            failure = e.cause\n        } catch (e: InterruptedException) {\n            Thread.currentThread().interrupt()\n        }\n    }\n    if (failure != null) log.error(\"task failed on {}\", Thread.currentThread().name, failure)\n}\n```\n\nIt works, with two limits. It can't stop an `execute` failure from killing the worker, because the exception is rethrown after the hook runs. And it doesn't know the submitter's request id unless a wrapper stored it. That's why the lab wraps `execute`. Its sister hook, `beforeExecute(Thread, Runnable)`, is the natural place to measure time in queue, and `terminated()` runs once, when the pool has fully stopped."
 },
 "sources": [
  {"title": "ThreadPoolExecutor (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html"},
  {"title": "ExecutorService (Java SE 25 API): shutdown and awaitTermination", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ExecutorService.html"},
  {"title": "Thread.Builder (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Thread.Builder.html"},
  {"title": "MDCContext (kotlinx-coroutines-slf4j API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-slf4j/kotlinx.coroutines.slf4j/-m-d-c-context/"},
  {"title": "Java Concurrency in Practice, Goetz et al., section 8.1 (thread starvation deadlock)", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/exec-09.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
