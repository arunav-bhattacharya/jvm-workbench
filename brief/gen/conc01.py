import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/concurrency/src"
P = "java/workbench/concurrency/l01"
K = "kotlin/workbench/concurrency/l01"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"./gradlew :concurrency:demo -Pmain=workbench.concurrency.l01.{name}"
def kt(name):
    """The Kotlin twin of a Java demo: Foo.kt with a top-level main, class FooKt."""
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
            "run": demo(f"{name}Kt"), "file": f"{lab}/demo/{K}/{name}.kt"}
def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

FIG = (
    '<svg viewBox="0 0 640 270" role="img" aria-label="One JVM process: a heap shared by all threads on top, and three threads below, each with its own stack">'
    '<rect class="box-dim" x="10" y="10" width="620" height="250" rx="8"/>'
    '<text class="t-s t-m" x="320" y="30" text-anchor="middle">one JVM process (its own memory, invisible to other processes)</text>'
    '<rect class="box-a" x="30" y="44" width="580" height="78" rx="8"/>'
    '<text class="t t-a" x="320" y="64" text-anchor="middle">heap: objects and static fields, shared by every thread</text>'
    '<rect class="box" x="70" y="78" width="130" height="32" rx="8"/><text class="t-s t-code" x="135" y="99" text-anchor="middle">Sale</text>'
    '<rect class="box" x="255" y="78" width="130" height="32" rx="8"/><text class="t-s t-code" x="320" y="99" text-anchor="middle">salesList</text>'
    '<rect class="box" x="440" y="78" width="130" height="32" rx="8"/><text class="t-s t-code" x="505" y="99" text-anchor="middle">static count</text>'
    '<rect class="box" x="40" y="160" width="170" height="84" rx="8"/><text class="t" x="125" y="182" text-anchor="middle">main</text>'
    '<text class="t-s t-m" x="125" y="204" text-anchor="middle">own stack: locals,</text><text class="t-s t-m" x="125" y="222" text-anchor="middle">call frames, position</text>'
    '<rect class="box" x="235" y="160" width="170" height="84" rx="8"/><text class="t" x="320" y="182" text-anchor="middle">worker-0</text>'
    '<text class="t-s t-m" x="320" y="204" text-anchor="middle">own stack: locals,</text><text class="t-s t-m" x="320" y="222" text-anchor="middle">call frames, position</text>'
    '<rect class="box" x="430" y="160" width="170" height="84" rx="8"/><text class="t" x="515" y="182" text-anchor="middle">worker-1</text>'
    '<text class="t-s t-m" x="515" y="204" text-anchor="middle">own stack: locals,</text><text class="t-s t-m" x="515" y="222" text-anchor="middle">call frames, position</text>'
    '<line class="ln-d" x1="125" y1="158" x2="135" y2="124" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="320" y1="158" x2="320" y2="124" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="515" y1="158" x2="505" y2="124" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="420" y="146" text-anchor="middle">every thread can read and write the heap</text>'
    '</svg>'
)

OPENING = """Picture a small shop that records every sale. At the end of the year, the owner wants one number: the total of a million sales. A Java program adds them up one after another, on a single thread. A thread is one path of work that the computer follows, step by step.

The owner's laptop has four cores, the parts of the processor that can each run work at the same moment. While the program adds, three of them sit idle. So why not cut the list into four parts and add all four at once?

That sounds like a ten-minute change. Yet the first version people write usually compiles, passes every test and runs no faster than before. A `Thread` looks like any other Java object, and the method that sounds as if it runs the thread doesn't.

In this lesson, we'll meet the threads every Java program already has (even an empty `main` has company), split the total across threads of our own, and measure the gain. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Let's begin with the emptiest program we can write: a `main` method that only asks the JVM which threads exist. (The JVM, the Java Virtual Machine, is the program that runs your compiled Java and Kotlin code.) Before our code has started a single thread, the list already has six:

```text
Reference Handler (daemon)
Finalizer (daemon)
Common-Cleaner (daemon)
Signal Dispatcher (daemon)
main
Notification Thread (daemon)
```

That list comes from the first Try it below, run on JDK 21. `main` is the thread that runs your `main` method. The other five are the JVM's housekeepers, and they were up before your `main` was. Most of them clean up after objects the program no longer uses, and `Signal Dispatcher` handles signals, the short messages the operating system sends to a running program.

Not every JVM thread makes that list. The garbage collector, which frees the memory of objects nobody uses any more, has threads of its own. So does the JIT compiler, the part of the JVM that turns code that runs often into fast machine code while your program runs. Neither shows up in the list. So you've been writing multithreaded programs all along.

Two words will carry us through this track. A **process** is a running program with its own memory, which other processes can't see. When you run a Java program, the JVM running it is one process. Your web browser is another.

A **thread** is one path of execution inside that process. It runs one statement after another, and it always knows where it is in the code. All the threads of a process live in its memory, and they split it in a simple way.

Before computers, our shop would have given this job to people. Picture four clerks in a back room, adding up a year of paper receipts. The receipts sit in one shared filing cabinet. Each clerk, though, keeps a running total on a notepad of their own.

In programming terms, each clerk is a thread. The filing cabinet is the **heap**: every object you create with `new` and every `static` field lives there, and any thread with a reference can reach it. The notepad is the thread's **stack**: its local variables, its parameters and the chain of method calls in progress. Every clerk can open the cabinet but writes only on their own notepad, just as every thread can reach the heap but sees only its own stack.

That split explains most of this track. Sharing the heap is what makes threads useful: one thread puts a `Sale` into a list and another reads it, with no copying. Sharing is also what makes threads dangerous, because two of them can change the same object at the same moment. Lesson 3 of this track (Race conditions: why count++ lies) shows how that quietly loses money.

If you go on to write web services, the programs that answer requests from browsers and phone apps, you'll meet the same picture on a larger scale. The framework, the ready-made library your service is built on, starts a whole crowd of threads for you and runs each request on one of them. A busy service often has more than a hundred, all sharing one heap.

**Locals belong to one thread. The heap belongs to all of them.** Code is thread-safe when it still works with several threads running it at once. So when you ask whether some code is thread-safe, start with one question: which of its values live on the heap?

Six threads, and we haven't started one yet. Let's start some of our own and put those idle cores to work."""

# ---------------------------------------------------------------- section 1
J_NAIVE = """// Naive: looks like four threads, runs on one
long[] partial = new long[4];
for (int w = 0; w < 4; w++) {
    int slot = w;
    Thread t = new Thread(() -> partial[slot] = sumSlice(slot), "sales-worker-" + w);
    t.run();
}"""
K_NAIVE = """// Naive: looks like four threads, runs on one
val partial = LongArray(4)
for (w in 0 until 4) {
    val t = Thread({ partial[w] = sumSlice(w) }, "sales-worker-$w")
    t.run()
}"""
J_FIXED = """// Fixed: four real threads, and main waits for all of them
Thread[] workers = new Thread[4];
for (int w = 0; w < 4; w++) {
    int slot = w;
    workers[w] = new Thread(() -> partial[slot] = sumSlice(slot), "sales-worker-" + w);
    workers[w].start();
}
for (Thread t : workers) t.join();   // only now is partial complete"""
K_FIXED = """// Fixed: four real threads, and main waits for all of them
val workers = List(4) { w ->
    thread(name = "sales-worker-$w") { partial[w] = sumSlice(w) }   // created and started
}
workers.forEach { it.join() }        // only now is partial complete"""

S1 = """Back to the shop's year of sales. The plan is simple: cut the million amounts into four slices, give each slice to a thread, and add up the four partial sums at the end. Each worker writes only its own slot of a `long[]` array, so no two threads ever write the same memory.

We hand a `Thread` two things: the work to do, as a `Runnable`, and a name. `Runnable` has a single method, `void run()`, so a lambda fits. (You can also subclass `Thread`, but I'd avoid it. The thread pools you'll meet later, ready-made groups of threads that run your tasks, take a `Runnable`.)

Here's the first version. It contains the most common first bug with threads, so let's make it once, on purpose:

""" + pair(J_NAIVE, K_NAIVE) + """

Before we run it, make a guess: which thread will sum each slice? Let's print the thread name inside the lambda and run it on a million amounts.

Four lines come out, and they all end the same way: `slice 0 summed on main`, `slice 1 summed on main`, and so on. The total is right and the tests pass, which is what makes this bug so sneaky. Four threads were created, and not one of them ran.

The culprit is the call. `run()` is an ordinary method call, so the lambda runs on the calling thread, one slice after another, exactly as slowly as before. The call that creates a thread is `start()`: the JVM asks the operating system for a new thread, and that new thread calls `run()`. (A thread runs at most once. Call `start()` a second time and it throws `IllegalThreadStateException`.)

So let's change `run()` to `start()`, and add up `partial` right after the loop. That brings out a second bug. We ran it five times in a row on the same million amounts. The first total came out at about a quarter of the right answer, and the other four at about three quarters.

The cause is timing. `main` added up the slots while the workers were still filling them. Call it the impatient total.

You may be tempted to cure the impatience with a `Thread.sleep(100)` "to give them time". It will pass on your laptop and fail one day on a slower or busier computer, because `sleep` only lets time pass. The tool for waiting is `join()`. It blocks, that is, makes the caller wait, until the thread has ended, and it guarantees that the caller then sees everything that thread wrote:

""" + pair(J_FIXED, K_FIXED) + """

Both versions start every worker first and join them afterwards. Joining inside the first loop would wait for worker 0 before starting worker 1, and we'd be back to one slice at a time. The Kotlin version differs in one place: `thread { }` from `kotlin.concurrent` builds a `java.lang.Thread` and calls `start()` for you, so the `run()` mistake is hard to make.

We also gave every worker a name. When a program misbehaves and you print its list of threads, `sales-worker-2` tells you whose job it was. `Thread-7` just shrugs.

**Start every worker, then join every worker. Read nothing before the last join.**

The total is right now, and the work really is spread over four threads. But is it four times faster? That depends on what sits underneath the threads."""

ASIDE1 = {
    "title": "Why not just call parallelStream()?",
    "body": "You could. For a plain sum, `amounts.parallelStream().mapToLong(Long::longValue).sum()` does the whole job in one line (in Kotlin, `amounts.parallelStream().mapToLong { it }.sum()`). Underneath, it does what we're doing by hand: it splits the list, sums the pieces on threads, and combines the results. Those threads come from the common `ForkJoinPool`, a pool of threads that the whole JVM shares. By default it has one thread fewer than you have cores, because the calling thread joins in. We build the split by hand once, so that you know what that one line costs and where it can go wrong. The lesson ForkJoinPool, work stealing and parallel streams, in the executors track, picks it up from there."
}

# ---------------------------------------------------------------- section 2
S2 = """Look back at the first line `HelloThreads` printed. On our test machine it said `cores the JVM sees: 4`, and that number decides how much our four workers can buy.

A **core** is the part of the processor that carries out instructions, and it runs one thread at a time. (Hyper-threading lets one physical core run two, each a little slower.) `Runtime.getRuntime().availableProcessors()` tells you how many cores the JVM may use. That can be fewer than the machine has, when the program is only allowed some of them.

A program often has far more threads than cores, and the operating system's scheduler, the part that decides which thread runs next, makes that work. It lets a thread run for a short slice of time, then saves its registers and switches to another thread. (Registers are the handful of values a core is working on right now.)

That switch is a **context switch**. It happens thousands of times a second, which is why 200 threads on 4 cores all seem to make progress.

Back in the shop's back room, give the clerks calculators, one for each core. Four clerks with four calculators all add at once. With eight clerks and four calculators, the clerks take turns. That's fine while most of them are on the phone waiting for an answer, and pointless when every one of them needs a calculator.

Adding at once and taking turns have names, and the names get mixed up. Several tasks in progress at the same time, taking turns if they must, is **concurrency**, and it works even on one core. Several tasks running at the same instant on different cores is **parallelism**. Clerks taking turns at one calculator are concurrent; clerks at four calculators are parallel.

Our four sales workers are concurrent on any machine. They run fully in parallel only when four cores are free for them.

So here's my guess before we time anything. Two threads should take about half the time of one, four threads about a quarter, and eight threads should be no better than four.

Now the measurement. Summing a million longs takes a few milliseconds, too quick to time honestly. A real program also does more work per sale (checking it, rounding it, adding the tax). So the `ParallelSum` demo below stands in for that work with 400 million small sums of pure arithmetic, split over 1, 2, 4 and 8 threads.

`ParallelSum` runs a few warm-up rounds first, so that the JIT compiler has turned the loop into machine code before we time it. On a 4-core Linux machine, one run printed 510 ms, 257 ms, 121 ms and 125 ms.

Correctness first: every run printed the same checksum, so splitting the work lost nothing. Then speed. Two threads halved the time, and four threads cut it to about a quarter, as we guessed. (Slightly better than four times, which is just the noise of one short run.)

Eight threads were no faster than four, which matched the guess too. The extra four threads had no cores of their own, so they took turns on the same four.

That wall is for **CPU-bound** work, work that keeps a core busy the whole time. Waiting work is different. Picture a thread that asks a slow web service, a program on another computer, for a price, and waits 120 ms for the answer. It uses no core while it waits. So a program that mostly waits can usefully run many more threads than it has cores.

**CPU-bound work wants one thread per core. Waiting work can use many more.** The executors track, on Java's ready-made thread pools, turns that into a sizing formula.

So threads can buy real speed, up to the core count. They aren't free, though, and they have one more habit that surprises people when a program ends. Let's look at both."""

# ---------------------------------------------------------------- section 3
S3 = """Every `Thread` we've created so far is a **platform thread**: one Java thread backed by one operating system thread. That pairing has a price, in memory and in time.

Memory first. Each platform thread gets its own stack, and on 64-bit Linux the JVM reserves 1 MB for it by default. (`java -XX:+PrintFlagsFinal -version` shows `ThreadStackSize = 1024`, in KB.) The operating system hands out real memory only as the stack grows, so a thread with shallow calls uses much less.

Still, 10,000 threads means 10 GB set aside for stacks, at least on paper, and 10,000 operating system threads sharing the cores. Somewhere along that road, your program dies with an `OutOfMemoryError` that says it is unable to create a native thread, meaning an operating system thread.

Then time. Creating, starting and ending a thread is a round trip to the kernel, the core of the operating system. The `ThreadCost` demo starts and joins 10,000 empty threads, and on a 4-core Linux machine it printed about 130 microseconds per thread.

For one 120 ms call to a slow web service, 130 microseconds is noise. Adding up one sale, though, takes a few nanoseconds. Start a new thread for each of our million sales, and the program spends over two minutes just starting and ending threads. That cost is why the executors track reuses threads in pools, and why the virtual threads track exists at all.

Now back to the warm-up question: `main` starts a worker and returns at once. Does the program end? Not yet. A **daemon** thread is a background helper that the JVM doesn't wait for. Every other thread is non-daemon, and the JVM exits only when the last non-daemon thread ends, or when something calls `System.exit`.

Returning from `main` ends the main thread and nothing else, so a worker that's still printing a report keeps the JVM alive until it's done. Threads are non-daemon unless you say otherwise. The housekeepers from the first section are the other kind. All five are daemons: they do their chores in the background, and the JVM never waits for them.

**Returning from `main` ends one thread, not the program.**

That's the whole toolkit of this lesson, so let's be honest about where it stops. A new thread per task suits four long slices. For thousands of short tasks, starting the threads can cost more than the work itself.

A worker that fails dies alone. If its `run()` throws an exception that nothing catches, the thread ends and its stack trace goes to standard error. `main` isn't told, because `join()` simply returns. And while we can wait for a thread to finish, we have no way yet to ask a running thread to stop."""

L = {
 "id": "conc-01",
 "title": "Threads from zero",
 "minutes": 35,
 "goal": "By the end you can say what a thread is and what it costs, start threads with `start()` and wait for them with `join()`, and split a job across several workers.",
 "opening": OPENING,
 "warmup": {
  "q": "`main` starts a thread that prints \"done\" after 2 seconds. Then `main` returns at once. What happens?",
  "options": ["The program exits at once and \"done\" never prints", "\"done\" prints after about 2 seconds, then the program exits", "An IllegalThreadStateException is thrown because main ended first", "It depends on how many cores the machine has"],
  "answer": 1,
  "why": "The JVM keeps running until every non-daemon thread has finished, and the threads you create are non-daemon unless you say otherwise. (A daemon thread is a background helper that the JVM doesn't wait for.) Returning from `main` ends the main thread and nothing else. So the worker carries on, prints \"done\", and only then does the JVM exit. The core count changes how fast things run, not whether the JVM waits. We'll watch it happen in the last section."
 },
 "sections": [
  {
   "h": "The threads you already have",
   "body": S0,
   "figure": {"svg": FIG, "caption": "Threads in one process share the heap. Each thread has a private stack for its local variables and calls."},
   "try": {
    "title": "Meet the threads you already have",
    "minutes": 3,
    "steps": [
     "Run `HelloThreads` with the command below, from the `labs/` folder. It lists the threads that exist before `main` starts any, then starts two of its own.",
     "Look at the list. Which of these threads are daemons? (A daemon thread is one the JVM doesn't wait for when it exits. The last section of this lesson comes back to that.)",
     "Now run it three more times and watch the two `hello` lines. Does `worker-a` always speak first?"
    ],
    "code": {"lang": "java", "title": "HelloThreads.java", "src": read(f"{lab}/demo/{P}/HelloThreads.java"),
             "run": demo("HelloThreads"), "file": f"{lab}/demo/{P}/HelloThreads.java", "alt": kt("HelloThreads")},
    "expect": "You'll see `main` and five daemon helpers, in an order that can change from run to run. The two workers usually print in the order they were started, but not always: in one run on a 4-core Linux machine, `worker-b` said hello first. Nothing in the code promises an order, so the scheduler is free to pick. Code that depends on that order is a bug waiting for a busy day."
   }
  },
  {
   "h": "Splitting the total across four threads",
   "body": S1,
   "aside": ASIDE1,
   "try": {
    "title": "Break it with run()",
    "minutes": 3,
    "steps": [
     "In `HelloThreads`, change `a.start()` and `b.start()` to `a.run()` and `b.run()`. Before you run it, predict the two \"hello from\" lines.",
     "Run it with the same command as the first Try it.",
     "Now put the `start()` calls back, and add a second `a.start();` right after the first one. What do you expect this time? Run it and see."
    ],
    "expect": "With `run()`, both lines say `hello from main`. No new thread was ever created, and the two joins return at once, because a thread that never started has nothing to wait for. With the double `start()`, `main` dies with an `IllegalThreadStateException`, yet `worker-a` still prints its line, because the first `start()` worked. A thread runs once, and only `start()` runs it."
   }
  },
  {
   "h": "Measuring the speedup, and where it stops",
   "body": S2,
   "try": {
    "title": "Find the core count by timing",
    "minutes": 4,
    "steps": [
     "Check how many cores your machine has (the first line of `HelloThreads` tells you). Then write down a guess for 1, 2, 4 and 8 threads.",
     "Run `ParallelSum` with the command below. Every run does the same 400 million additions, split across the threads.",
     "Compare the times with your guess. Where does adding threads stop helping?"
    ],
    "code": {"lang": "java", "title": "ParallelSum.java", "src": read(f"{lab}/demo/{P}/ParallelSum.java"),
             "run": demo("ParallelSum"), "file": f"{lab}/demo/{P}/ParallelSum.java", "alt": kt("ParallelSum")},
    "expect": "The bend in the curve sits at your core count. Each doubling roughly halves the time until the threads outnumber the cores, and after that the extra threads just take turns. If your machine is busy with something else, the curve flattens. On a 4-core machine with other heavy programs running, one run printed 498, 422, 410 and 326 ms. Our threads were now sharing the cores with other programs, and eight threads even came out ahead, because the scheduler shares the cores out thread by thread, so more threads got more turns. Measure on a quiet machine, and run it more than once."
   }
  },
  {
   "h": "What a thread costs, and who the JVM waits for",
   "body": S3,
   "try": {
    "title": "Measure a thread, then let main go first",
    "minutes": 4,
    "steps": [
     "Run `ThreadCost` with `" + demo("ThreadCost") + "`. It starts and joins 10,000 empty threads, three rounds in a row. Note the microseconds per thread.",
     "Now read `MainEndsFirst` below. `main` starts one worker, which prints a five-page sales report, and returns at once. How many \"printing page\" lines will print? Commit to a number.",
     "Run it with `" + demo("MainEndsFirst") + "`."
    ],
    "code": {"lang": "java", "title": "MainEndsFirst.java", "src": read(f"{lab}/demo/{P}/MainEndsFirst.java"),
             "run": demo("MainEndsFirst"), "file": f"{lab}/demo/{P}/MainEndsFirst.java", "alt": kt("MainEndsFirst")},
    "expect": "`ThreadCost` prints tens to a couple of hundred microseconds per thread on most machines. Under heavy load it can be far more: with other heavy programs running alongside, a 4-core Linux machine printed 900 to 1,300. `MainEndsFirst` prints `main: returning from main()` first, then all five pages and `worker: report printed`. The JVM waited for the non-daemon worker, long after `main` was gone."
   }
  }
 ],
 "compare": {
  "title": "Starting and joining workers in Java and Kotlin",
  "java": {"title": "Java", "src": "long[] partial = new long[4];\nList<Thread> workers = new ArrayList<>();\nfor (int w = 0; w < 4; w++) {\n    int slot = w;\n    Thread t = new Thread(() -> partial[slot] = sumSlice(slot), \"sales-worker-\" + w);\n    t.start();                      // nothing runs until start()\n    workers.add(t);\n}\nfor (Thread t : workers) t.join();  // join() throws the checked InterruptedException"},
  "kotlin": {"title": "KotlinThreads.kt", "src": read(f"{lab}/demo/{K}/KotlinThreads.kt")},
  "note": "Both versions start four named workers and then join them in a second loop. Three things differ. First, Kotlin's `thread { }` is a small standard-library function: it builds a `java.lang.Thread`, sets its options and calls `start()` for you, unless you pass `start = false`, so forgetting `start()` mostly stops being a mistake you can make. Second, Kotlin has no checked exceptions, so `join()` needs no `throws InterruptedException`. The interruption rules still apply, and lesson 2 of this track covers them. Third, a Java lambda can only use local variables that never change after they're set (Java calls them effectively final), which is why the Java code copies `w` into `slot`. The Kotlin lambda captures the `w` parameter of `List(4) { w -> }` directly. Java's rule is a quiet safety net here: a lambda running on another thread can never see a captured local change under it. Kotlin lets a lambda capture and change a local `var`, so with threads, keeping that net is up to you."
 },
 "worked": {
  "title": "Split the year's sales total across four threads",
  "steps": [
   {"say": "Let's write the fixed version properly, the way the lab wants it. We have the shop's one million sale amounts, in cents, in a `List<Long>`, and four workers. First, the slices: each worker gets a contiguous range, one unbroken stretch of the list, and the remainder is spread out so that sizes differ by at most one.",
    "code": "int slices = Math.min(workers, amounts.size());   // no idle threads\nint base = amounts.size() / slices;\nint extra = amounts.size() % slices;               // the first `extra` slices get one more", "lang": "java",
    "alt_code": "val slices = minOf(workers, amounts.size)   // no idle threads\nval base = amounts.size / slices\nval extra = amounts.size % slices             // the first `extra` slices get one more", "alt_lang": "kotlin"},
   {"say": "Next, one slot per worker. Worker 2 writes only `partial[2]`, so no two threads ever write the same memory, and there's nothing for them to fight over.",
    "code": "long[] partial = new long[slices];\nThread[] threads = new Thread[slices];", "lang": "java",
    "alt_code": "val partial = LongArray(slices)\nval threads = ArrayList<Thread>(slices)", "alt_lang": "kotlin"},
   {"say": "Now start every thread. Before you read on, ask yourself: what would happen if you called `join()` inside this same loop, right after `start()`?",
    "code": "int from = 0;\nfor (int w = 0; w < slices; w++) {\n    int start = from, end = start + base + (w < extra ? 1 : 0), slot = w;\n    // 1. each worker sums its own slice into its own slot\n    threads[w] = new Thread(() -> {\n        long sum = 0;\n        for (int i = start; i < end; i++) sum += amounts.get(i);\n        partial[slot] = sum;\n    }, \"sales-worker-\" + w);\n    threads[w].start();\n    from = end;\n}", "lang": "java",
    "alt_code": "var from = 0\nfor (w in 0 until slices) {\n    val start = from\n    val end = start + base + if (w < extra) 1 else 0\n    // 1. each worker sums its own slice into its own slot\n    threads += thread(name = \"sales-worker-$w\") {   // thread {} also starts it\n        var sum = 0L\n        for (i in start until end) sum += amounts[i]\n        partial[w] = sum\n    }\n    from = end\n}", "alt_lang": "kotlin"},
   {"say": "Joining inside the loop would wait for worker 0 before starting worker 1, and we'd be back to one thread at a time. So start them all, then join them all. Only after the last join is it safe to read `partial`, because `join()` makes each worker's write visible to the caller.",
    "code": "// 2. wait for every worker\nfor (Thread t : threads) t.join();\n// 3. combine on the calling thread\nlong total = 0;\nfor (long p : partial) total += p;", "lang": "java",
    "alt_code": "// 2. wait for every worker\nthreads.forEach { it.join() }\n// 3. combine on the calling thread\nval total = partial.sum()", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Total a list of sales on N threads",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/LedgerTotals.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l01.*'",
  "steps": [
   "Open `LedgerTotals`. (A ledger is a book of money records, so read the name as \"money totals\".) Its one method, `total(amountsInCents, workers)`, adds up a list of amounts, such as the shop's sales, on `workers` threads. Run the tests once: all six fail with `UnsupportedOperationException`.",
   "In `LedgerTotals.total`, reject `workers < 1` with an `IllegalArgumentException`.",
   "Work out the slices: `Math.min(workers, size)` threads, contiguous ranges, sizes that differ by at most one.",
   "Start one named thread per slice. Each thread sums its slice into its own slot of a `long[]`.",
   "Join every thread, then add up the slots and return the total. Run the tests until all six pass."
  ],
  "hints": [
   "One test wraps the list so it can record which threads call `get`. It fails if the caller reads any amount itself, or if the number of reading threads isn't the number of slices.",
   "A lambda can only use local variables that never change. Copy loop variables into fresh locals (`int slot = w;`) before the lambda.",
   "If the totals come out wrong only sometimes, check that you read `partial` after the joins, not before. That's the impatient total from the second section."
  ],
  "done_when": "All six tests in `LedgerTotalsTest` pass."
 },
 "drill": {
  "title": "Start, then join, from memory",
  "minutes": 4,
  "prompt": "Close this page. Write a `main` that starts three threads named `helper-0`, `helper-1` and `helper-2`. Each one prints its own name. `main` waits for all three, then prints `all done`. When you compare with the answer, check one thing first: did you start all three before joining any?",
  "answer": {"lang": "java", "src": "public static void main(String[] args) throws InterruptedException {\n    List<Thread> threads = new ArrayList<>();\n    for (int i = 0; i < 3; i++) {\n        Thread t = new Thread(() -> System.out.println(Thread.currentThread().getName()), \"helper-\" + i);\n        t.start();\n        threads.add(t);\n    }\n    for (Thread t : threads) t.join();\n    System.out.println(\"all done\");\n}",
            "alt": {"lang": "kotlin", "title": "Kotlin", "src": "fun main() {\n    val threads = List(3) { i ->\n        thread(name = \"helper-$i\") { println(Thread.currentThread().name) }   // created and started\n    }\n    threads.forEach { it.join() }\n    println(\"all done\")\n}"}}
 },
 "recap": [
  "A process has its own memory. Its threads share the heap (objects, static fields), and each thread has a private stack (locals, calls in progress).",
  "`start()` creates a thread, which then calls `run()`. Call `run()` yourself and the code runs on the current thread, with no warning.",
  "`join()` waits for a thread to end and makes its writes visible to you. Start every worker, then join them all, then read the results.",
  "Concurrency is many tasks in progress; parallelism is many running at the same instant. CPU-bound work stops getting faster at about one thread per core, while a waiting thread uses no core.",
  "The JVM exits when the last non-daemon thread ends. Returning from `main` ends only the main thread.",
  "The limit: a platform thread is an operating system thread, with 1 MB of stack reserved by default on 64-bit Linux and a trip to the kernel to create. A new thread per small task doesn't scale, and a worker that fails dies without telling anyone."
 ],
 "closing": "We started with a shop's year of sales on one thread and three idle cores. We found six threads before we wrote any, then made the `run()` mistake and the impatient total. We fixed both with `start()` and `join()`, and watched the speedup stop at the core count.\n\nNow search some Java or Kotlin code, your own or an open-source project, for `new Thread(` (and `thread {` in Kotlin). For each hit, ask who waits for that thread, and how. If the answer is a `Thread.sleep`, or nobody, you've found an impatient total.\n\nNext, we'll follow one thread through the six states of its life, and answer the question this lesson left open: how do you stop a thread that doesn't want to finish?",
 "quiz": [
  {"q": "What does this print?\n\n```java\nThread t = new Thread(() -> System.out.println(Thread.currentThread().getName()), \"helper\");\nt.run();\n```",
   "options": ["helper", "main", "Thread-0", "Nothing, because the thread was never started"],
   "answer": 1, "why": "`run()` is an ordinary method call, so the lambda runs on the thread that called it, and that's `main`. No new thread ever exists. You'd see `helper` only with `t.start()`. It does print something, though: `run()` executes the code, just on the wrong thread."},
  {"q": "A program resizes 10,000 photos. It is pure CPU work, with no waiting for the disk or the network. The laptop has 4 cores. Which thread count finishes the job about the fastest?",
   "options": ["1", "4", "64", "400"],
   "answer": 1, "why": "Pure CPU work keeps a core busy, and each core runs one thread at a time. Four threads keep all four cores working. More threads only take turns on the same cores and add context switches, just as the 8-thread run of `ParallelSum` showed. Counts like 400 make sense only when most threads spend their time waiting."},
  {"q": "A worker thread throws a `NullPointerException` out of its `run()` method. What happens to `main`, which started it?",
   "options": ["`main` gets the NullPointerException at its next line", "The JVM shuts down", "`main` carries on. The worker ends and its stack trace is printed to standard error", "`main` gets it when it calls `join()`"],
   "answer": 2, "why": "An uncaught exception ends only the thread that threw it. The default handler prints the stack trace to standard error, and nobody else is told: `join()` simply returns once the worker has ended. Getting the exception back to the caller is a job for `Future`, in the executors track."},
  {"q": "What is wrong with this loop?\n\n```java\nfor (Runnable job : jobs) {\n    Thread t = new Thread(job);\n    t.start();\n    t.join();\n}\n```",
   "options": ["Nothing. It runs the jobs in parallel", "It runs the jobs one at a time, because each join waits before the next thread starts", "It deadlocks on the second job", "`join()` must be called before `start()`"],
   "answer": 1, "why": "Each `join()` blocks until that thread ends, so the next thread starts only after the previous one has finished. You pay for a thread per job and still get one job at a time. Start every thread in one loop, then join them in a second loop."},
  {"q": "A program asks a slow web service for 12 prices at once, one thread per price, on a laptop with 2 cores. Each thread spends about 120 ms waiting for its answer. Which statement is true?",
   "options": ["It is concurrent: 12 requests are in progress, at most 2 threads run at any instant, and most are waiting anyway", "It is parallel: all 12 threads run at the same instant", "It cannot work, because threads must not outnumber cores", "It is neither concurrent nor parallel"],
   "answer": 0, "why": "Twelve requests in progress at once is concurrency. With 2 cores, at most 2 threads run at the same instant, and that's the parallel part. Each thread spends most of its time waiting for the web service and uses no core while it waits, so 12 threads on 2 cores is a sensible setup. One thread per core is the rule for CPU-bound work."}
 ],
 "flashcards": [
  {"front": "What do threads in one process share, and what does each thread have of its own?", "back": "They share the heap: objects and static fields. Each thread has its own stack: local variables, parameters and the calls in progress."},
  {"front": "What happens if you call `t.run()` instead of `t.start()`?", "back": "The code runs on the current thread, like any method call. No new thread is created, and nothing warns you."},
  {"front": "Concurrency vs parallelism, in one line each.", "back": "Concurrency: several tasks in progress at the same time (works on one core). Parallelism: several tasks running at the same instant on different cores."},
  {"front": "When does the JVM exit?", "back": "When the last non-daemon thread ends, or when something calls `System.exit`. Returning from `main` ends only the main thread."},
  {"front": "How much stack does the JVM reserve for a platform thread on 64-bit Linux by default?", "back": "1 MB (`ThreadStackSize = 1024` KB). It is set aside up front and filled in as the stack grows. Change it with `-Xss`."},
  {"front": "What happens when you call `start()` twice on the same Thread?", "back": "The second call throws `IllegalThreadStateException`. A thread runs at most once."},
  {"front": "A worker thread throws an uncaught exception. Who finds out?", "back": "Only that thread dies. The default handler prints the stack trace to standard error. The starting thread is not told."}
 ],
 "terms": [
  {"term": "Process", "plain": "A running program with its own memory, such as one JVM."},
  {"term": "Thread", "plain": "One path of execution inside a process, with its own stack, sharing the process heap."},
  {"term": "Heap", "plain": "The memory where objects and static fields live. Every thread can reach it."},
  {"term": "Core", "plain": "A part of the processor that runs one thread at a time."},
  {"term": "Context switch", "plain": "The operating system pausing one thread and resuming another on the same core."},
  {"term": "Concurrency", "plain": "Several tasks in progress at once, taking turns or not."},
  {"term": "Parallelism", "plain": "Several tasks running at the same instant on different cores."},
  {"term": "Platform thread", "plain": "A Java thread backed one-to-one by an operating system thread."}
 ],
 "explain_back": {
  "prompt": "A friend moved a slow report onto \"four threads\" by writing `new Thread(job).run()` four times. All the tests pass, but the report is exactly as slow as before. Explain to them, in your own words, what happened and how to fix it.",
  "answer": "`run()` is just a method call, so each job ran on the calling thread, one after the other. No new thread was ever created, which is why nothing got faster and nothing failed. `start()` is the call that creates a thread and has it call `run()`. So call `start()` on all four threads first, then `join()` each one before reading the results. That way the jobs really overlap, and `join()` makes their results visible to the caller."
 },
 "deeper": {
  "minutes": 8,
  "body": "Since JDK 21 there's a builder API for threads. It's worth knowing now, because the virtual threads track uses the same shape:\n\n" + pair(
      "Thread t = Thread.ofPlatform()\n        .name(\"sales-worker-\", 0)    // sales-worker-0, sales-worker-1, ...\n        .start(task);",
      "val t = Thread.ofPlatform()\n    .name(\"sales-worker-\", 0)        // sales-worker-0, sales-worker-1, ...\n    .start(task)") +
   "\n\n`Thread.ofPlatform()` gives you the same kind of thread as `new Thread(...)`. `Thread.ofVirtual()` gives you a virtual thread, which isn't tied to one operating system thread and costs far less. That's a whole track of its own.\n\nIf you're curious about the threads the JVM keeps for itself, look inside any running Java program with `jcmd <pid> Thread.print`. `jcmd` is a tool that comes with the JDK, and `<pid>` is the process id, the number the operating system gives each running program (`jcmd` with no arguments lists them). Besides the Java threads from the first Try it, you'll see entries such as `VM Thread`, the JIT compiler threads and the garbage collector's workers. They live inside the JVM itself, so `Thread.getAllStackTraces()` doesn't list them, but they use cores and memory like any other thread.\n\nOne more cost to keep in mind: a context switch isn't free. The kernel saves and restores registers, and the incoming thread often finds the CPU caches, the core's small and fast copies of recently used memory, full of the previous thread's data. That's part of why `ParallelSum` stops improving past the core count, and why a thousand busy threads can run slower than ten."
 },
 "sources": [
  {"title": "Thread (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Thread.html"},
  {"title": "Defining and starting a thread (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/essential/concurrency/runthread.html"},
  {"title": "kotlin.concurrent.thread (Kotlin standard library)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.concurrent/thread.html"},
  {"title": "Java Concurrency in Practice, Goetz et al.", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/conc-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
