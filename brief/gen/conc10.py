import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/concurrency/src"
P = "java/workbench/concurrency/l10"
K = "kotlin/workbench/concurrency/l10"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"./gradlew :concurrency:demo -Pmain=workbench.concurrency.l10.{name}"
def code(name):
    """A Java demo with its Kotlin twin (Foo.kt with a top-level main, class FooKt)."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": demo(name), "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": demo(f"{name}Kt"), "file": f"{lab}/demo/{K}/{name}.kt"}}
def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

# ---------------------------------------------------------------- code samples in the prose
J_NAP = """// Naive: a guess about how long loading takes
startLoading();            // three threads: 200, 300 and 400 ms
Thread.sleep(250);
openDoors();"""
K_NAP = """// Naive: a guess about how long loading takes
startLoading()             // three threads: 200, 300 and 400 ms
Thread.sleep(250)
openDoors()"""

J_LATCH = """CountDownLatch loaded = new CountDownLatch(3);

// each loading thread, when its list is in (in a finally):
loaded.countDown();

// the thread that opens the doors:
if (!loaded.await(2, TimeUnit.SECONDS)) {
    throw new IllegalStateException("lists not loaded after 2 s");
}
openDoors();"""
K_LATCH = """val loaded = CountDownLatch(3)

// each loading thread, when its list is in (in a finally):
loaded.countDown()

// the thread that opens the doors:
if (!loaded.await(2, TimeUnit.SECONDS)) {
    throw IllegalStateException("lists not loaded after 2 s")
}
openDoors()"""

J_BARRIER = """CyclicBarrier endOfDay = new CyclicBarrier(3, () -> report(sum(sales)));   // the barrier action

// each of the 3 till threads, for every day:
sales[me] = addUp(me, day);
endOfDay.await();          // the 3rd to arrive runs the action, then all 3 go on"""
K_BARRIER = """val endOfDay = CyclicBarrier(3) { report(sales.sum()) }   // the barrier action

// each of the 3 till threads, for every day:
sales[me] = addUp(me, day)
endOfDay.await()          // the 3rd to arrive runs the action, then all 3 go on"""

J_SEM = """private final Semaphore bankPermits = new Semaphore(5);

Approval check(Payment p) throws InterruptedException {
    bankPermits.acquire();             // before the try, like lock()
    try {
        return bank.check(p);          // at most 5 threads in here
    } finally {
        bankPermits.release();
    }
}"""
K_SEM = """private val bankPermits = Semaphore(5)

fun check(p: Payment): Approval {
    bankPermits.acquire()              // before the try, like lock()
    try {
        return bank.check(p)           // at most 5 threads in here
    } finally {
        bankPermits.release()
    }
}"""

J_PHASER = """Phaser phaser = new Phaser(1);          // the main thread is a party until it leaves
phaser.register();                      // each helper joins before it starts
phaser.arriveAndAwaitAdvance();         // end of a phase: wait for everyone still registered
phaser.arriveAndDeregister();           // arrive one last time and leave"""
K_PHASER = """val phaser = Phaser(1)          // the main thread is a party until it leaves
phaser.register()               // each helper joins before it starts
phaser.arriveAndAwaitAdvance()  // end of a phase: wait for everyone still registered
phaser.arriveAndDeregister()    // arrive one last time and leave"""

J_W1 = """// Naive: one bad receipt and this never ends
CountDownLatch done = new CountDownLatch(4);
List<Long> totals = new CopyOnWriteArrayList<>();
for (Till till : tills) {
    new Thread(() -> {
        totals.add(addUp(till));
        done.countDown();
    }).start();
}
done.await();
report(totals);"""
K_W1 = """// Naive: one bad receipt and this never ends
val done = CountDownLatch(4)
val totals = CopyOnWriteArrayList<Long>()
for (till in tills) {
    thread {
        totals.add(addUp(till))
        done.countDown()
    }
}
done.await()
report(totals)"""
J_W2 = """CountDownLatch done = new CountDownLatch(tills.size());
List<Long> totals = new CopyOnWriteArrayList<>();
List<Throwable> failures = new CopyOnWriteArrayList<>();
for (Till till : tills) {
    new Thread(() -> {
        try {
            totals.add(addUp(till));              // 1. do the work
        } catch (Throwable e) {
            failures.add(e);                      // 2. keep the failure instead of losing it
        } finally {
            done.countDown();                     // 3. always count down
        }
    }, "till-" + till.id()).start();
}
if (!done.await(1, TimeUnit.MINUTES)) {           // 4. never wait forever
    throw new IllegalStateException("tills still adding up after 1 min");
}
if (!failures.isEmpty()) throw new IllegalStateException("tills failed: " + failures);
report(totals);                                   // 5. countDown happens-before await returns: all totals visible"""
K_W2 = """val done = CountDownLatch(tills.size)
val totals = CopyOnWriteArrayList<Long>()
val failures = CopyOnWriteArrayList<Throwable>()
for (till in tills) {
    thread(name = "till-${till.id}") {
        try {
            totals.add(addUp(till))              // 1. do the work
        } catch (e: Throwable) {
            failures.add(e)                      // 2. keep the failure instead of losing it
        } finally {
            done.countDown()                     // 3. always count down
        }
    }
}
if (!done.await(1, TimeUnit.MINUTES)) {          // 4. never wait forever
    throw IllegalStateException("tills still adding up after 1 min")
}
if (failures.isNotEmpty()) throw IllegalStateException("tills failed: $failures")
report(totals)                                   // 5. countDown happens-before await returns: all totals visible"""

J_DRILL = """static boolean awaitAll(List<Runnable> tasks, Duration deadline) throws InterruptedException {
    CountDownLatch done = new CountDownLatch(tasks.size());
    for (Runnable task : tasks) {
        new Thread(() -> {
            try {
                task.run();
            } finally {
                done.countDown();          // even when the task throws
            }
        }).start();
    }
    return done.await(deadline.toMillis(), TimeUnit.MILLISECONDS);
}"""
K_DRILL = """fun awaitAll(tasks: List<() -> Unit>, deadline: Duration): Boolean {
    val done = CountDownLatch(tasks.size)
    for (task in tasks) {
        thread {
            try {
                task()
            } finally {
                done.countDown()          // even when the task throws
            }
        }
    }
    return done.await(deadline.toMillis(), TimeUnit.MILLISECONDS)
}"""

# ---------------------------------------------------------------- the figure: three tills, two days
def bar(x1, x2, y, cls="box"):
    return f'<rect class="{cls}" x="{x1}" y="{y - 8}" width="{x2 - x1}" height="16" rx="6"/>'
def gap(x1, x2, y):
    return f'<line class="ln-d" x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"/>'

ROWS = [60, 105, 150]
FIG = (
    '<svg viewBox="0 0 680 240" role="img" aria-label="Three till threads add up day 1 and day 2. Each waits at the barrier until the last one arrives; the barrier action totals the day once, then all three start the next day together">'
    + "".join(f'<text class="t" x="20" y="{y + 5}">till {i}</text>' for i, y in enumerate(ROWS))
    + '<line class="ln-a" x1="290" y1="40" x2="290" y2="170"/><text class="t-s t-a" x="290" y="30" text-anchor="middle">end of day 1</text>'
    + '<line class="ln-a" x1="530" y1="40" x2="530" y2="170"/><text class="t-s t-a" x="530" y="30" text-anchor="middle">end of day 2</text>'
    + bar(80, 160, ROWS[0]) + gap(160, 288, ROWS[0])
    + bar(80, 220, ROWS[1]) + gap(220, 288, ROWS[1])
    + bar(80, 286, ROWS[2], "box-a")
    + bar(300, 360, ROWS[0]) + gap(360, 528, ROWS[0])
    + bar(300, 440, ROWS[1]) + gap(440, 528, ROWS[1])
    + bar(300, 526, ROWS[2], "box-a")
    + '<rect class="box-ok" x="235" y="186" width="110" height="30" rx="8"/><text class="t-s" x="290" y="206" text-anchor="middle">day 1 total</text>'
    + '<rect class="box-ok" x="475" y="186" width="110" height="30" rx="8"/><text class="t-s" x="530" y="206" text-anchor="middle">day 2 total</text>'
    + '<text class="t-s t-m" x="556" y="65">bar: work</text><text class="t-s t-m" x="556" y="110">dashes: wait</text><text class="t-s t-a" x="556" y="155">last to arrive</text>'
    + '</svg>'
)

OPENING = """Picture a small shop that opens at nine. Before the doors open, its program loads three lists: the price list, the stock counts and today's offers. Three threads load them side by side. (A thread is one path of work that runs side by side with others in the same program.) The thread that opens the doors has to wait until all three are done.

One morning the doors open early, and the first customer buys a loaf of bread for 0.00. The price list was still loading.

The fix most people reach for first is a nap, `Thread.sleep(2000)`, which feels like plenty of time. It makes every morning two seconds slower, and on the day the price list takes three seconds, bread is free again.

In Concurrent collections, a queue carried work from one thread to another. Here nothing changes hands: the threads just have to wait for each other, the way runners wait for the starting gun. In this lesson, we'll meet four tools for four shapes of waiting: a latch, a barrier, a semaphore and a phaser. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0: the latch
S0 = """Let's write the naive version first, so we can watch it fail. The thread that opens the doors starts the three loads, naps for a fixed time and opens:

""" + pair(J_NAP, K_NAP) + """

The Try it below runs exactly this, with loads that take 200, 300 and 400 ms. It printed:

```text
  220 ms  price list loaded
  271 ms  doors open after a 250 ms nap, lists still loading: 2
```

Two of the three lists were still loading when the first customer walked in. A longer nap would pass this run, and it would still be a guess, because loading time changes with the machine, the network and the day.

We don't want to wait for a time. We want to wait for three events: the prices are in, the stock counts are in, the offers are in. (The aside below explains why waiting for the threads to end with `join()` isn't the answer either.)

`java.util.concurrent`, the package of concurrency tools that comes with Java, has a class for exactly this job. A **CountDownLatch** is a gate with a counter on it. It starts at a count, here 3. Any thread can call `countDown()` to lower the count by one. Threads that call `await()` wait at the gate until the count reaches zero, and then all of them go through at once. You met a latch with a count of 1 in Race conditions: it was the starting gun that released all the test threads together.

""" + pair(J_LATCH, K_LATCH) + """

Let's read it in order. First we make a latch with a count of 3, one for each list. Each loading thread calls `countDown()` when its list is in, inside a `finally`, so a load that fails still counts. Finally the door thread waits at the gate. Read its `if` aloud: wait until all three lists have loaded, but no longer than two seconds.

The same run with the latch printed:

```text
  228 ms  price list loaded
  328 ms  today's offers loaded
  428 ms  stock counts loaded
  428 ms  ready=true, count=0
```

The doors opened the moment the slowest list arrived, no earlier and no later. Notice what the latch counted: events, not threads. One thread could count down three times, or three threads once each. The latch doesn't care who calls `countDown()`, only how many times.

One level down, the count is a single `int` inside the latch. `countDown()` lowers it with a compare-and-set, the "update it only if nobody beat me to it" call from Atomics and compare-and-set. The call that takes it to zero wakes every waiting thread, and no method ever raises it again. So a latch is **one-shot**: once it's open, it stays open. Every later `await()` returns at once, an extra `countDown()` does nothing, and there's no reset.

A latch also carries visibility. Everything a loading thread did before its `countDown()` happens-before `await()` returns in the door thread. Happens-before is the Java memory model's promise that one thread sees what another wrote, and the memory model track explains it. Here it means the door thread can read the three lists with no extra lock.

Two habits keep a latch from hanging a program. If a loading thread throws before it reaches `countDown()`, the count never gets to zero, and a plain `await()` waits forever. A thread dump, a printout of every thread's state and the method calls it is in the middle of, shows the door thread `WAITING` inside `CountDownLatch.await`. Nothing is left that could ever wake it.

**A latch that misses one countDown() waits forever. Count down in finally, and await with a deadline.**

The deadline is the second habit. `await(2, TimeUnit.SECONDS)` returns `false` if time runs out, so the program can say "the stock counts didn't load" instead of hanging in silence. The Try it makes one load hang for a minute so you can see it.

A latch opens once and stays open. That suits a morning. It doesn't suit a group that has to meet again every evening."""

ASIDE0 = {
 "title": "Threads from zero waited with join(). Why not here?",
 "body": "`join()` waits for a thread to end. Our loading threads happen to end when their list is in, so `join()` would work today. But a thread that keeps running after its first job never ends: say it loads the prices, then reloads them every hour. A `join()` on it waits forever. And once you hand tasks to a thread pool, a fixed group of threads that is reused for many tasks (the thread pools track), the thread outlives every task it runs. A latch waits for the event you care about, whoever makes it happen and whatever that thread does next."
}

# ---------------------------------------------------------------- section 1: the barrier
S1 = """The shop's year of sales from Threads from zero comes back, with a twist. The shop has three tills, the cash registers at its counter, and three threads add them up, one till each, one day at a time. At the end of each day, someone adds the three subtotals into the day's total and sends the day's report. No thread may start the next day until that's done.

So the three threads have to meet at the end of every day. Let's try the tool we know first. Each thread counts down a latch of 3 when its till is done and then waits on it, and when the latch opens, thread 0 adds up the day. Day 1 works. Day 2 is worth tracing:

1. Thread 0 finishes its till first, counts down and calls `await()`. The count is still zero from yesterday, so `await()` returns at once.
2. Thread 0 adds up the day while threads 1 and 2 are still counting their tills, so the total uses yesterday's numbers for two tills.
3. Thread 0 moves on to day 3, a day ahead of the others.

A one-shot gate can't close again behind the group. We'd need a fresh latch every day, and someone to hand it out at exactly the right moment, which is a new race.

What we want is a meeting point that resets itself, and that's a **CyclicBarrier**. You give it a number of parties, the threads that must meet, here 3. Each thread calls `await()` when it reaches the meeting point and waits there until the last party arrives. Then all of them go on together, and the barrier closes again for the next round. That reset is the cyclic part.

A tour bus works the same way. At every stop, the bus leaves only when everyone is back on board, and the guide counts heads before it moves off. The barrier is the bus, and the guide's head count is the **barrier action**. That's code the barrier runs once per round, on the last thread to arrive, before anyone is released.

""" + pair(J_BARRIER, K_BARRIER) + """

Each thread writes only its own slot of `sales`, before it calls `await()`. The barrier action then adds the three slots, and it can read them with no lock. Everything before `await()` happens-before the barrier action, and the action happens-before each thread's return from `await()`. The figure shows two days. The bars are work, the dashes are waiting, and the slowest till runs the action.

The Try it runs three tills for three days. It printed:

```text
  day 1 closed by till-2: sales 6,000
  day 2 closed by till-2: sales 12,000
  day 3 closed by till-2: sales 18,000
```

Till 2 is the slowest, so it always arrives last and runs the action. One barrier served all three days.

Now the part that hurts in real programs: a barrier can break. If a waiting thread is interrupted (asked by another thread to stop), or its timed `await` runs out, or the barrier action throws, the barrier is broken. The thread that timed out gets `TimeoutException`, and every other waiting thread, now and later, gets `BrokenBarrierException` until someone calls `reset()`. That's on purpose. A round with a missing party can't finish, and failing everyone beats leaving them all waiting.

But look at what doesn't break it: a thread that throws before it ever reaches `await()`. A guide would go looking for a missing tourist. A barrier just waits, and with a plain `await()`, it waits forever. On day 4 of the Try it, till 2 never arrives, and the other two give up after 300 ms:

```text
  till-0: TimeoutException, barrier now broken
  till-1: BrokenBarrierException
```

**A barrier waits for every party, even one that will never come. Give await() a timeout.**

In short, a latch is a gate opened by events ("three lists loaded"), once. A barrier is a meeting point for a fixed group of threads ("all three tills finished day 3"), every round.

Both of them make threads wait for each other. The next problem is the opposite one: too many threads doing the same thing at once."""

# ---------------------------------------------------------------- section 2: the semaphore
S2 = """The shop takes card payments, and a web service at the bank checks each one. A web service is a program on another computer that answers over the network. This one is the slow web service from Threads from zero: each call takes about 120 ms. The bank also has a rule. One shop may have at most five calls in progress at once, and it refuses a sixth.

On a busy Saturday, twenty customers pay at the same moment, so twenty threads call the bank together, and fifteen of them are refused. Fifteen customers are asked to try their card again. The shop needs to let five threads into the call at a time and make the others wait their turn.

A car park works this way. It has five spaces and a barrier at the entrance, with a sign that shows how many spaces are free. A car that drives in takes a space, and the sign counts down. A car that leaves gives one back, and the sign counts up. When the sign shows zero, the next car waits at the entrance until someone leaves.

A **Semaphore** is that car park in code. It holds a number of **permits**, here 5. `acquire()` takes a permit, and waits while none are left. `release()` gives one back. So at most five threads can be between the two calls at any moment:

""" + pair(J_SEM, K_SEM) + """

The idiom is the one from Explicit locks: `acquire()` on the line before the `try`, `release()` in the `finally`. The Try it sends twenty calls through a `Semaphore(5)`. Correctness first: the most calls in flight at once was 5. Then time: 502 ms, which is four waves of five calls at 120 ms each, plus a little start-up. `tryAcquire(timeout, unit)` waits a bounded time and returns `false` if no permit came free, so a payment can fail fast with a clear message instead of joining a long line.

Now the surprise from the warm-up. A lock, the key that lets one thread at a time into a piece of code, knows which thread holds it. It throws if a stranger tries to release it. A semaphore knows nothing of the kind. **Permits have no owner.** A semaphore is just a counter, and `release()` adds one, whoever calls it. The car park's sign believes every car that says it's leaving. The Try it ends by proving it:

```text
new Semaphore(5), then one stray release(): 6 permits
```

The sign now shows six free spaces in a car park built for five. That freedom is useful, since one thread can acquire a permit and another can release it. It's also how two common bugs quietly raise the limit:

- calling `acquire()` inside the `try`, so a wait that is interrupted still runs the `release()` in `finally` (a waiting `acquire()` answers an interrupt by throwing `InterruptedException`);
- ignoring what `tryAcquire` returns, then making the call and releasing anyway.

The lab's `IssuerGate` has both bugs. Each stray release is an extra permit for good. Over a day of cancelled payments and timeouts, a limit of 5 drifts to 8, then 12. The bank starts refusing calls again, and no exception or log line explains why.

**A semaphore trusts every release. Release only the permits you took.**

Two more details. A `Semaphore` limits one running program. If the shop runs three copies of its program on three computers, each with 5 permits, the bank sees up to 15 calls at once. Divide the bank's limit by the number of copies. And `new Semaphore(5, true)` makes it fair: waiting threads get permits in the order they arrived, so a fast thread can't keep grabbing a free permit ahead of one that has waited longer.

A latch, a barrier and a semaphore all have their number fixed the day you create them. The last tool is for a group that changes size."""

# ---------------------------------------------------------------- section 3: the phaser, and the limits
S3 = """Once a year, the shop counts its stock. The job runs in three phases: count every shelf, check the counts against the books, write the report. Three helpers start the job, and nobody may start checking before every shelf is counted. A barrier fits so far. Then it turns out that one helper was only booked for the counting, and goes home when it's done.

With a `CyclicBarrier(3)`, the two helpers who stay would wait at the end of the check phase for a third party who has gone home. They'd wait forever, or until a timeout broke the barrier. A barrier's number of parties is fixed when you create it.

A **Phaser** is a barrier whose group can change size. A thread calls `register()` to join. It calls `arriveAndAwaitAdvance()` at the end of a phase, which waits just like `await()` on a barrier. And it calls `arriveAndDeregister()` to arrive one last time and leave. Each phase waits only for the parties registered at that moment. Phases are numbered from 0, and you can override `onAdvance(phase, parties)` to run code between phases, which makes it the phaser's barrier action. When `onAdvance` returns `true`, the phaser ends.

""" + pair(J_PHASER, K_PHASER) + """

The Try it runs the stocktake, and its `onAdvance` prints each phase with the parties still taking part:

```text
  phase 0 (count) done, 3 parties
  phase 1 (check) done, 2 parties
  phase 2 (report) done, 2 parties
terminated: true
```

Helper 2 counted with the others. At the check phase, its `arriveAndDeregister()` arrived and left in one call, so that phase didn't wait for it, and no later phase counted it. Notice the `1` in `new Phaser(1)`: the main thread registers itself first, so no phase can finish while helpers are still joining, and it leaves once all three have joined. Use a phaser when the number of workers isn't known up front or changes between phases. When the group is fixed, a `CyclicBarrier` is simpler and says what it means.

The smallest synchronizer needs only two sentences. An `Exchanger` lets exactly two threads meet and swap one object each, for example a full basket for an empty one. You'll rarely need it.

Now the limits, which all of these tools share. Each one parks its waiting threads, that is, puts them to sleep until something wakes them. In a thread dump they show as `WAITING` or `TIMED_WAITING`, with the tool's class in the stack. And none of them has an owner. That's what makes them flexible, and it's also why the JVM's deadlock detector from Deadlock, livelock and starvation can't see through them. (A deadlock is a group of threads that wait for each other forever.) Twenty threads that each hold one permit and wait for a second are deadlocked, and the dump reports nothing. You find them by reading the stacks.

In real programs you'll often get these tools without creating them yourself. The thread pools track shows `invokeAll` and `CompletableFuture.allOf`, which each do a latch's job in one call. They're built from the same parts, so when one of them hangs, the thread dump shows the same parked threads."""

L = {
 "id": "conc-10",
 "title": "Synchronizers: latch, barrier, semaphore, phaser",
 "minutes": 38,
 "goal": "By the end you can pick the right synchronizer for each shape of waiting (wait for a few events, meet every round, let only a few in, a group that changes size) and use each one without its classic bug.",
 "opening": OPENING,
 "warmup": {
  "q": "A `Semaphore` is a counter of permits: `acquire()` takes one, and `release()` gives one back. One starts with 5 permits. A thread calls `release()` without ever calling `acquire()`. What does `availablePermits()` return now?",
  "options": ["5, because the stray release is ignored", "6", "It throws `IllegalMonitorStateException`", "4"],
  "answer": 1,
  "why": "Permits belong to nobody. A semaphore is a counter, and `release()` adds one, whoever calls it. That's handy, since one thread can take a permit and another can give it back. It's also how a bug quietly raises a limit of 5 to 6, then 7. A lock would throw here; a semaphore can't, because it doesn't know who took what. The third section runs exactly this."
 },
 "sections": [
  {
   "h": "Waiting for three jobs to finish: the one-shot CountDownLatch",
   "body": S0,
   "aside": ASIDE0,
   "try": {
    "title": "Open the shop when the lists are in",
    "minutes": 3,
    "steps": [
     "Read `LatchDemo`. Three threads load three lists (200, 400 and 300 ms) and count down a latch. `main` opens the doors when the latch opens, waiting at most 2 seconds.",
     "Run it with `-Pargs=sleep` first, the naive nap. Then predict when `ready` is printed in the latch version, and what an extra `countDown()` does after that.",
     "Run it with no arguments. Then run it with `-Pargs=stuck`, where one load takes a minute."
    ],
    "code": code("LatchDemo"),
    "expect": "With `sleep`, the doors open at about 250 ms with 2 lists still loading. With the latch, the lists arrive at about 200, 300 and 400 ms (plus a few ms to start up), and `ready=true, count=0` follows right after the slowest one. The extra `countDown()` leaves the count at 0, and `await` returns at once. With `stuck`, `main` prints `ready=false, count=1` after 2 seconds instead of hanging."
   }
  },
  {
   "h": "Meeting at the end of every day: the CyclicBarrier",
   "body": S1,
   "figure": {"svg": FIG, "caption": "Each till thread waits at the barrier until the last one arrives. The barrier action totals the day once, then all three start the next day together."},
   "try": {
    "title": "Three days, then a missing till",
    "minutes": 3,
    "steps": [
     "Read `BarrierDemo`. Three threads add up three tills for three days. The barrier action prints the day's sales and the name of the thread that ran it.",
     "On day 4, till 2 never arrives, and the other two wait at most 300 ms. Predict what each of them prints.",
     "Run it twice."
    ],
    "code": code("BarrierDemo"),
    "expect": "Three lines `day N closed by till-2`, with sales of 6,000, 12,000 and 18,000: till 2 is the slowest, so it always arrives last and runs the action. On day 4, one till gets `TimeoutException` and breaks the barrier, and the other gets `BrokenBarrierException`. Which one gets which can change between runs. `broken: true` at the end."
   }
  },
  {
   "h": "Letting only five in at once: the Semaphore and its permits",
   "body": S2,
   "try": {
    "title": "Five permits, twenty calls",
    "minutes": 3,
    "steps": [
     "Read `SemaphoreDemo`. Twenty threads each make a 120 ms call to the bank through a `Semaphore(5)`, and the demo tracks the peak number of calls in flight.",
     "Predict the peak and the total time. Then run it.",
     "In the Java version, move `bank.acquire()` to just inside the inner `try`. Does anything change in this run? Why might it on a busy day?"
    ],
    "code": code("SemaphoreDemo"),
    "expect": "Peak in flight 5, total about half a second (502 and 519 ms in runs here): four waves of five calls. The stray `release()` turns 5 permits into 6. Moving `acquire()` inside the `try` changes nothing in this run, because nobody interrupts the waiting threads. On a busy day an interrupt during the wait (a cancelled payment, a shutdown) would release a permit that was never taken."
   },
   "refs": [
    {"title": "Semaphore (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Semaphore.html", "kind": "docs"}
   ]
  },
  {
   "h": "A group that changes size: the Phaser, and what all four can't do",
   "body": S3,
   "try": {
    "title": "A helper goes home early",
    "minutes": 3,
    "steps": [
     "Read `PhaserDemo`. Three helpers run three phases (count, check, report). Helper 2 leaves after the counting. `onAdvance` prints each phase and the parties left.",
     "Predict the party count printed for each phase.",
     "Run it. Then explain what would happen with a `CyclicBarrier(3)` instead."
    ],
    "code": code("PhaserDemo"),
    "expect": "`phase 0 (count) done, 3 parties`, then `phase 1 (check) done, 2 parties` and `phase 2 (report) done, 2 parties`, then `terminated: true`. `main` registered itself first so no phase could finish before every helper had joined, then left. With a `CyclicBarrier(3)`, the two helpers who stay would wait at the end of the check phase for helper 2, who has gone home."
   }
  }
 ],
 "compare": {
  "title": "A permit helper in Java and Kotlin",
  "java": {"title": "Java", "src": """static <T> T withPermit(Semaphore s, Callable<T> task) throws Exception {
    s.acquire();                  // before the try, like lock()
    try {
        return task.call();
    } finally {
        s.release();              // exactly the permit we took
    }
}

Approval a = withPermit(bankPermits, () -> bank.check(payment));"""},
  "kotlin": {"title": "Kotlin", "src": """inline fun <T> Semaphore.withPermit(block: () -> T): T {
    acquire()                     // before the try, like lock()
    try {
        return block()
    } finally {
        release()                 // exactly the permit we took
    }
}

val a = bankPermits.withPermit { bank.check(payment) }"""},
  "note": "Both versions use the same `java.util.concurrent.Semaphore`, and both block a thread while it waits for a permit. Java does the job well with a static helper that takes a `Callable`, and every caller passes a lambda. Kotlin's version is an extension function, one you call as if it were a method of `Semaphore` itself. It is also `inline`, so the compiler copies the lambda's code into each call site: no object is created, and a `return` inside the block works as usual. The safe idiom then reads like part of the language, and nobody writes the `try` and `finally` by hand again. The Kotlin standard library doesn't ship `withPermit` for this `Semaphore`, so you write it once, as here. kotlinx.coroutines has a `Semaphore` of its own with a built-in `withPermit`, which suspends a coroutine instead of blocking a thread; the coroutines track covers it."
 },
 "worked": {
  "title": "Adding up four tills without hanging",
  "steps": [
   {"say": "At closing time, the shop adds up its four tills. Each till takes a few seconds, so four threads do the work, and the main thread waits for all of them with a latch. Read this first version. What happens if `addUp` throws for one till, say because a receipt can't be read?",
    "code": J_W1, "lang": "java", "alt_code": K_W1, "alt_lang": "kotlin"},
   {"say": "The failing thread dies before it reaches `countDown()`. The count stays at 1, and `await()` waits forever. The program doesn't fail; it just never finishes. A thread dump shows `main` `WAITING` in `CountDownLatch.await`, and no till threads at all, because they have all finished or died. The fix has three parts: count down in `finally`, keep the failure so it isn't lost, and never wait without a deadline.", "code": "", "lang": ""},
   {"say": "Here's the version that always ends, with a label on each step.",
    "code": J_W2, "lang": "java", "alt_code": K_W2, "alt_lang": "kotlin"},
   {"say": "Before reading on, explain to yourself why `main` can read `totals` after `await` returns, without any lock. Answer: everything a till thread did before its `countDown()` happens-before `await()` returns in the waiting thread. `totals` is still a `CopyOnWriteArrayList`, a thread-safe list from Concurrent collections, because four threads add to it at the same time. In a real program you'd hand the four jobs to a thread pool and wait for all of them with `invokeAll`, which the thread pools track covers. A latch is one of the parts such tools are built from.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Fix a permit leak, then add up sales in rounds",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/IssuerGate.java", f"{lab}/main/{P}/RoundRunner.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l10.*'",
  "steps": [
   "Meet the two classes. `IssuerGate` is the shop's gate in front of the bank's card service from the third section (the bank behind a card is called its issuer). It lets at most `maxConcurrent` calls run at once, and it has both permit bugs. `RoundRunner` runs a job in rounds on several threads: in each round every worker computes its share, and the round's total is passed on once, just as the tills did for each day.",
   "Run the tests. Four of the six fail: the timed call runs its task with no permit, a caller interrupted while it waits adds a permit, and both `RoundRunner` tests hit `UnsupportedOperationException`.",
   "Fix `IssuerGate.call(task)`: move `acquire()` to the line before the `try`.",
   "Fix `IssuerGate.call(task, maxWait)`: if `tryAcquire` returns `false`, throw `TimeoutException` before the `try`, so the task doesn't run and nothing is released.",
   "Write `RoundRunner.run`. Keep a `long[] shares`, one slot per worker. Build a `CyclicBarrier(workers, action)` whose action sums `shares` and calls `onRoundTotal`. Start one thread per worker that loops over the rounds: `shares[me] = step.applyAsLong(me, r)`, then `await()`. Join every thread before returning.",
   "Run the tests until all six pass, then twice more."
  ],
  "hints": [
   "Why can the barrier action read `shares` without a lock? Each worker writes only its own slot, before `await()`, and everything before `await()` happens-before the action runs.",
   "`await()` throws `InterruptedException` and `BrokenBarrierException`. In the worker, restore the interrupt flag for the first, and stop the loop for both.",
   "The second `RoundRunner` test calls your step from 4 threads and checks that round `r` never starts before `r` totals have been passed on. The barrier action runs before anyone is released, so this holds by construction."
  ],
  "done_when": "All six tests in `SynchronizersTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Wait for N tasks, with a deadline",
  "minutes": 4,
  "prompt": "Close this page. Write `awaitAll(tasks, deadline)`: run each task on its own thread and return `true` if all of them finished within the deadline, `false` otherwise. A task that throws must not make it hang. Then check: where is your `countDown()`?",
  "answer": {"lang": "java", "src": J_DRILL, "alt": {"lang": "kotlin", "title": "Kotlin", "src": K_DRILL}}
 },
 "recap": [
  "`CountDownLatch` waits until N events have happened, once. Count down in `finally`, await with a timeout, and everything written before `countDown()` is visible after `await()`.",
  "`CyclicBarrier` makes N threads meet every round. The barrier action runs once, on the last to arrive, then all go on, and the barrier resets itself.",
  "A barrier breaks on a timeout or an interrupt, but a thread that never reaches `await()` leaves the others waiting forever unless they use the timed `await`.",
  "`Semaphore` lets at most N threads in at once. Permits have no owner, so release only what you took: `acquire()` before `try`, and check what `tryAcquire` returns.",
  "`Phaser` is a barrier whose parties can join and leave between phases. `Exchanger` swaps one object between two threads.",
  "The limit: none of these tools has an owner, so a missing `countDown()` or a stray `release()` fails silently, and the deadlock detector can't see a cycle through them."
 ],
 "closing": "We started with a shop that opened its doors before the prices had loaded. A latch let it open the moment the last list arrived. A barrier let three tills meet every evening, a semaphore kept the bank's limit of five, and a phaser let a helper go home early.\n\nNow search your own code for `countDown()` and `release()`. Each `countDown()` belongs in a `finally`, and each `release()` must match an `acquire()` that really happened. An `acquire()` inside the `try` that releases it is a car park sign waiting to show six free spaces.\n\nEvery tool here exists because threads share something. Next, we'll take the sharing away: if nothing is shared, or nothing ever changes, what is left to protect?",
 "quiz": [
  {"q": "The shop's program must not open its doors until four lists have loaded, each on its own thread. Which tool fits best?",
   "options": ["`CountDownLatch(4)`, counted down by each loading thread and awaited by the door thread", "`CyclicBarrier(4)`", "`Semaphore(4)`", "`Exchanger`"],
   "answer": 0, "why": "You're waiting for four events, once. That's a latch. A barrier would make the four loading threads wait for each other, which they don't need to do, and it's built for repeated rounds. A semaphore limits how many threads run at once; it doesn't wait for anything to finish."},
  {"q": "`try { sem.acquire(); callBank(); } finally { sem.release(); }` with `new Semaphore(10)`. A thread is interrupted while it waits in `acquire()`. What happens?",
   "options": ["Nothing: `acquire()` gives up cleanly", "The thread gets the permit anyway", "`acquire()` throws, the `finally` releases a permit that was never taken, and the semaphore now allows 11", "`release()` throws `IllegalMonitorStateException`"],
   "answer": 2, "why": "`acquire()` throws `InterruptedException`, and the `finally` still runs. Permits have no owner, so `release()` simply adds one. Nothing throws, which is why the bug is quiet. Move `acquire()` above the `try`."},
  {"q": "Three till threads use a `CyclicBarrier(3)` with a plain `await()`. One of them throws an exception before it reaches `await()` on day 5. What do the other two do?",
   "options": ["They get `BrokenBarrierException` at once", "The barrier notices the dead thread and lets them through", "They get `TimeoutException` after a default timeout", "They wait forever"],
   "answer": 3, "why": "A barrier breaks only when a waiting thread is interrupted or times out, or the barrier action fails. A thread that never arrives is invisible to it, and a plain `await()` has no timeout. Use `await(timeout, unit)` so the round fails instead of hanging."},
  {"q": "From Deadlock, livelock and starvation: 20 threads each take 1 permit from a `Semaphore(20)` that limits calls to the bank, then call a helper that takes a second permit from the same semaphore. Under full load everything stops. What does `jcmd <pid> Thread.print` show?",
   "options": ["`Found one Java-level deadlock`, naming the semaphore", "No deadlock report: permits have no owner, so the detector can't see the cycle; you see 20 threads `WAITING` in `Semaphore.acquire`", "A livelock report", "20 threads in `BLOCKED`"],
   "answer": 1, "why": "This is hold and wait: every thread holds one permit and waits for a second. It's a real deadlock, but the JVM's detector only follows locks with an owner (monitors and `ReentrantLock`-style locks). Parked threads show as `WAITING`, not `BLOCKED`. Take both permits at once with `acquire(2)`, or don't take a second while holding the first.",
   "from": "conc-06"},
  {"q": "A job runs in rounds, and the number of worker threads changes between rounds: some join late and some leave early. Which tool fits?",
   "options": ["One `CountDownLatch` per round, created up front", "A `CyclicBarrier` with the largest number of workers", "A `Phaser`, with workers registering when they start and deregistering when they finish", "A `Semaphore`"],
   "answer": 2, "why": "A phaser's group can grow and shrink between phases, and each phase waits only for the parties registered then. A barrier's number of parties is fixed, so missing workers would hang it. Latches are one-shot and need their count known in advance."}
 ],
 "flashcards": [
  {"front": "A `CountDownLatch` has reached zero. What do later `await()` and `countDown()` calls do?", "back": "`await()` returns at once. `countDown()` does nothing. A latch can't be reset."},
  {"front": "When does a `CyclicBarrier`'s barrier action run, and on which thread?", "back": "Once per round, on the last thread to arrive, before any waiting thread is released."},
  {"front": "What breaks a `CyclicBarrier`?", "back": "A waiting thread being interrupted or timing out, the barrier action throwing, or `reset()`. Then every waiting thread gets `BrokenBarrierException`."},
  {"front": "What does `release()` do on a `Semaphore` when the caller never acquired a permit?", "back": "It adds a permit anyway. Permits have no owner, so stray releases silently raise the limit."},
  {"front": "Where do `acquire()` and `release()` go around `try` and `finally`?", "back": "`acquire()` on the line before `try`, `release()` in `finally`. With `tryAcquire`, check its result before entering the `try`."},
  {"front": "Latch or barrier: \"open after 3 lists load\" vs \"3 tills finish day N before any starts day N+1\"?", "back": "The first is a latch (waiting for events, once). The second is a barrier (a fixed group meeting every round)."},
  {"front": "What can a `Phaser` do that a `CyclicBarrier` can't?", "back": "Change its number of parties between phases: `register()` to join, `arriveAndDeregister()` to leave."}
 ],
 "terms": [
  {"term": "Synchronizer", "plain": "An object that makes threads wait for each other or for events, such as a latch, a barrier or a semaphore."},
  {"term": "CountDownLatch", "plain": "A one-shot gate that opens when its count reaches zero."},
  {"term": "CyclicBarrier", "plain": "A meeting point for a fixed number of threads that resets itself after each round."},
  {"term": "Barrier action", "plain": "Code a `CyclicBarrier` runs once per round, on the last thread to arrive, before releasing the others."},
  {"term": "Semaphore", "plain": "A counter of permits that limits how many threads can do something at once."},
  {"term": "Permit", "plain": "One unit of a semaphore's count. It belongs to nobody."},
  {"term": "Phaser", "plain": "A reusable barrier whose group of parties can change between phases."}
 ],
 "explain_back": {
  "prompt": "Explain the difference between a `CountDownLatch`, a `CyclicBarrier` and a `Semaphore` to a friend who is new to threads, with one everyday example of each.",
  "answer": "A latch waits for a number of events and then opens for good: the shop's door thread waits until the price list, the stock counts and the offers have loaded, then opens. A barrier is a meeting point for a fixed group of threads, every round, like a tour bus that leaves each stop only when everyone is back on board. Three till threads each finish day 3, the last one to arrive adds up the day, and then all three start day 4. A semaphore limits how many threads do something at the same time, like a car park with five spaces: at most five threads may be inside a call to the bank. The traps differ too. A latch hangs if a task forgets to count down. A barrier hangs if a thread never arrives and nobody gave `await` a timeout. A semaphore quietly raises its limit if code releases a permit it never took."
 },
 "deeper": {
  "minutes": 10,
  "body": "`CountDownLatch` and `Semaphore`, like `ReentrantLock`, are thin layers over `AbstractQueuedSynchronizer`, a JDK class that holds one `int` of state and a queue of parked threads. For a latch the state is the count, and `await` parks until it is zero. For a semaphore it is the number of permits left. `CyclicBarrier` is a `ReentrantLock` with one `Condition`, and `Phaser` and `Exchanger` keep their own queues of parked threads. All of them park through `LockSupport`, which is why they look the same in a thread dump: `WAITING (parking)`, with a line like `parking to wait for <0x...> (a java.util.concurrent.Semaphore$NonfairSync)`.\n\nA few corners of the API are worth knowing. `Semaphore.acquire(n)` takes several permits in one step, which avoids the hold-one-and-wait-for-another deadlock from the quiz. `drainPermits()` takes all that are left, which is handy when you want to stop new work during a shutdown. `acquireUninterruptibly()` ignores interrupts, which you almost never want. `CyclicBarrier.await()` returns the arrival index (parties minus one for the first to arrive, zero for the last), so you can pick one thread to do extra work without a barrier action.\n\n`Phaser` supports tiering: you can build a tree of phasers so that thousands of parties don't all compete for one. Its Javadoc caps a single phaser at 65,535 registered parties.\n\nVirtual threads (JDK 21) are very light threads that the JVM runs on a few ordinary ones. Blocking in any of these tools is cheap there: the virtual thread parks, and the ordinary thread under it runs something else. A `Semaphore` is in fact the standard way to limit how many calls run at once when you start a virtual thread per task, because there's no pool size to do it for you. The virtual threads track comes back to that. In Kotlin coroutines, the equivalents suspend instead of blocking: `kotlinx.coroutines.sync.Semaphore`, `Job.join()` or `awaitAll()` where you'd use a latch, and channels for most of the rest."
 },
 "sources": [
  {"title": "CountDownLatch (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CountDownLatch.html"},
  {"title": "CyclicBarrier (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CyclicBarrier.html"},
  {"title": "Phaser (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Phaser.html"},
  {"title": "Java Concurrency in Practice, Goetz et al., section 5.5 (synchronizers)", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/conc-10.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
