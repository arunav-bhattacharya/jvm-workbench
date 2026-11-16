import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/concurrency/src"
P = "java/workbench/concurrency/l02"
K = "kotlin/workbench/concurrency/l02"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"./gradlew :concurrency:demo -Pmain=workbench.concurrency.l02.{name}"
def kt(name):
    """The Kotlin twin of a Java demo: Foo.kt with a top-level main, class FooKt."""
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
            "run": demo(f"{name}Kt"), "file": f"{lab}/demo/{K}/{name}.kt"}
def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

FIG = (
    '<svg viewBox="0 0 700 300" role="img" aria-label="Thread state diagram: NEW goes to RUNNABLE on start; RUNNABLE moves to and from BLOCKED, WAITING and TIMED_WAITING; RUNNABLE goes to TERMINATED when run ends">'
    '<rect class="box-dim" x="20" y="130" width="110" height="40" rx="8"/><text class="t t-code" x="75" y="155" text-anchor="middle">NEW</text>'
    '<rect class="box-a" x="200" y="128" width="280" height="44" rx="8"/><text class="t t-code" x="340" y="155" text-anchor="middle">RUNNABLE</text>'
    '<rect class="box-dim" x="560" y="130" width="130" height="40" rx="8"/><text class="t t-code" x="625" y="155" text-anchor="middle">TERMINATED</text>'
    '<rect class="box-bad" x="255" y="18" width="170" height="40" rx="8"/><text class="t t-code" x="340" y="43" text-anchor="middle">BLOCKED</text>'
    '<rect class="box-b" x="150" y="240" width="160" height="40" rx="8"/><text class="t t-code" x="230" y="265" text-anchor="middle">WAITING</text>'
    '<rect class="box-b" x="370" y="240" width="180" height="40" rx="8"/><text class="t t-code" x="460" y="265" text-anchor="middle">TIMED_WAITING</text>'
    '<line class="ln" x1="130" y1="150" x2="198" y2="150" marker-end="url(#arr)"/><text class="t-s t-code" x="164" y="142" text-anchor="middle">start()</text>'
    '<line class="ln" x1="480" y1="150" x2="558" y2="150" marker-end="url(#arr)"/><text class="t-s t-code" x="519" y="142" text-anchor="middle">run() ends</text>'
    '<line class="ln" x1="325" y1="126" x2="325" y2="60" marker-end="url(#arr)"/><text class="t-s" x="318" y="98" text-anchor="end">lock is held</text>'
    '<line class="ln" x1="355" y1="60" x2="355" y2="126" marker-end="url(#arr)"/><text class="t-s" x="362" y="98" text-anchor="start">gets the lock</text>'
    '<line class="ln" x1="215" y1="174" x2="215" y2="238" marker-end="url(#arr)"/><text class="t-s t-code" x="208" y="200" text-anchor="end">wait(), join(), park()</text>'
    '<line class="ln" x1="245" y1="238" x2="245" y2="174" marker-end="url(#arr)"/><text class="t-s" x="252" y="196" text-anchor="start">notify, unpark, end</text>'
    '<line class="ln" x1="440" y1="174" x2="440" y2="238" marker-end="url(#arr)"/><text class="t-s t-code" x="433" y="224" text-anchor="end">sleep(ms), wait(ms)</text>'
    '<line class="ln" x1="470" y1="238" x2="470" y2="174" marker-end="url(#arr)"/><text class="t-s" x="477" y="224" text-anchor="start">time up or woken</text>'
    '</svg>'
)

OPENING = """Picture a rolling deploy of the payments service. Each old pod should stop in a second or two. One of them takes the full 30 seconds that Kubernetes allows, and then the kubelet kills it.

Its shutdown code had asked the outbox relay to stop, then waited for it. The relay, the thread that moves payment events from an outbox table to Kafka, replied with one polite log line: `relay interrupted, carrying on`. Then it carried on.

The bug behind that line is easy to write. Java makes you catch `InterruptedException`, and logging it is the quickest way to keep the compiler happy. JDK engineers have shipped the same mistake.

In Threads from zero, every thread we started finished on its own. The relay runs until someone asks it to stop, and how to ask is the question that lesson left open. In this lesson, we'll follow the relay through the six states of a thread's life and find it in a thread dump. Then we'll weigh the ways to stop it, and fix it so the request isn't lost. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_NEW = """Thread relay = new Thread(new OutboxRelay(outbox, publisher, 200), "outbox-relay");
System.out.println(relay.getState());   // NEW: only an object so far
relay.start();                          // now a real OS thread, which calls run()"""
K_NEW = """val relay = Thread(OutboxRelay(outbox, publisher, 200), "outbox-relay")
println(relay.state)                    // NEW: only an object so far
relay.start()                           // now a real OS thread, which calls run()"""

S0 = """A thread is always in one of six states, and `t.getState()` tells you which. They're the six values of the `Thread.State` enum, and every thread dump prints the same names. The easiest way to learn them is to follow one thread through its whole life. Let's follow the relay, from the line that creates it to the moment it ends.

The relay starts life as an ordinary object:

""" + pair(J_NEW, K_NEW) + """

Before `start()`, no operating system thread exists and nothing has run, so `getState()` returns `NEW`. (Kotlin reads `getState()` as the property `state`. Otherwise the two versions are the same.)

`start()` is the call that moves the relay on, as we saw in Threads from zero. The JVM creates the OS thread, and that thread calls `run()`. The relay polls the outbox and publishes what it finds, and `getState()` now returns `RUNNABLE`.

`RUNNABLE` covers two cases that the JVM doesn't tell apart: running on a core, and ready to run but waiting for one. It covers a third case too, which we'll meet in a thread dump.

Sooner or later the outbox is empty. The relay calls `Thread.sleep(idleMillis)` and gives up its core until the time is up. A thread that waits with a time limit is `TIMED_WAITING`, and `wait(ms)` and `join(ms)` lead there too.

When the time runs out, or an interrupt wakes it early (more on that soon), the relay is `RUNNABLE` again and polls once more.

Waiting with no time limit is `WAITING`. Picture a relay fed by a `BlockingQueue` instead of a table. On an empty queue, `queue.take()` parks the thread, that is, puts it to sleep until another thread wakes it, here by adding an event.

`Object.wait()` and `join()` wait the same way, with no time limit. In fact, the shutdown code from the opening was `WAITING` the whole time it sat in `relay.join()`.

The fifth state is about a door. Say the relay marks rows as sent inside a `synchronized (outboxLock)` block, and a cleanup job is already inside a block on the same lock. Only one thread gets through that door at a time, so the relay waits outside it, `BLOCKED`. When the cleanup job leaves, the relay gets the lock and is `RUNNABLE` again.

Last, `run()` returns or throws, and the relay is `TERMINATED`. That state is final. A second `start()` throws `IllegalThreadStateException`, so work that must run again needs a new thread, or better, a pool.

The figure below draws that life as a map. `RUNNABLE` sits in the middle because the relay keeps coming back to it: it publishes, sleeps, wakes up `RUNNABLE` and publishes again. The three waiting states differ in what ends the wait: a lock for `BLOCKED`, another thread for `WAITING`, and another thread or the clock for `TIMED_WAITING`.

That's a lot of claims, so let's not take my word for them. The `ThreadStates` demo in the Try it sends four small threads through the same moves, asks `getState()` at each stop and prints the answer. On JDK 21 it printed:

```text
before start():         NEW
inside sleep(2000):     TIMED_WAITING
in a busy loop:         RUNNABLE
inside wait():          WAITING
entering a held lock:   BLOCKED
waiter interrupted, flag now false
after join():           TERMINATED
```

Each state showed up where the walk said it would, though the demo visits them in its own order. The extra line about the waiter's flag is a clue for later, so hold on to it.

`getState()` only works on a thread you hold a reference to. On a stuck pod you hold nothing, but you can still ask every thread at once."""

# ---------------------------------------------------------------- section 1
SD = """Back to the pod that wouldn't stop. A thread dump lists every thread in the JVM with its state and its stack, and `jcmd <pid> Thread.print` takes one. Here's the relay a moment after it was interrupted, trimmed to the lines that matter:

```text
"outbox-relay" #19 prio=5 os_prio=0 ... waiting on condition
   java.lang.Thread.State: TIMED_WAITING (sleeping)
        at java.lang.Thread.sleep0(java.base@21.0.12.1/Native Method)
        at java.lang.Thread.sleep(java.base@21.0.12.1/Thread.java:509)
        at workbench.concurrency.l02.OutboxRelay.run(OutboxRelay.java:39)
```

The dump says what the relay is doing in two places. The state line says `TIMED_WAITING (sleeping)`, and the stack says where: in `Thread.sleep`, called from line 39 of `OutboxRelay.run`. So the relay heard the interrupt, logged that it had heard it, and went straight back to bed.

A state is a snapshot, so one dump can mislead. Take two or three, a few seconds apart, and compare them. A thread that shows the same state at the same line in all of them isn't just passing through.

Two states need care when you read a dump. The first is `RUNNABLE`, and here is the third case we put off. The Javadoc says a `RUNNABLE` thread is executing in the JVM "but it may be waiting for other resources from the operating system such as processor."

So a thread stuck in a socket read from Oracle shows `RUNNABLE` too, because the JVM only sees that it's inside native code. A dump full of `RUNNABLE` threads can still be a service that does nothing.

The second is `BLOCKED`, which is only for `synchronized`. A thread waiting for a `ReentrantLock` (lesson 7 of this track) is parked by the lock's own Java code. So the dump shows it `WAITING`, with `LockSupport.park` near the top of its stack. Search a dump for `BLOCKED` to find lock contention, and you'll miss every explicit lock.

**A state is a hint. The stack is the evidence. Read both.**

Our relay spends nearly all of its life in `TIMED_WAITING`, asleep. So the real question is how one thread can reach into another thread's sleep and ask it to stop. Java has offered more than one answer over the years."""

# ---------------------------------------------------------------- section 2
J_DAEMON = """Thread relay = new Thread(outboxRelay, "outbox-relay");
relay.setDaemon(true);   // before start(), or you get IllegalThreadStateException
relay.start();"""
K_DAEMON = """val relay = Thread(outboxRelay, "outbox-relay")
relay.isDaemon = true    // before start(), or you get IllegalThreadStateException
relay.start()            // or: thread(name = "outbox-relay", isDaemon = true) { outboxRelay.run() }"""

S1 = """We know where the relay spends its time: asleep, or busy publishing. Whatever we use to stop it has to reach it in both places. People try four ways, so let's take them in turn, oldest first.

The oldest is `Thread.stop()`. It threw an error inside the target thread, wherever that thread happened to be. The thread unwound, released its locks and left half-updated objects behind: half a batch published, say, with the outbox rows not yet marked as sent.

`stop()` was deprecated in Java 1.2, made to always throw `UnsupportedOperationException` in JDK 20, and removed in JDK 26. Its partners `suspend()` and `resume()` went in JDK 23. In Java, deprecation is a long goodbye.

Old code that still calls `stop()` fails with `NoSuchMethodError` on JDK 26 and later. Strike that one.

The second is to make the relay a **daemon thread**, one the JVM doesn't wait for. When the last non-daemon thread ends, the JVM exits, and daemon threads stop wherever they are, without running their `finally` blocks. A new thread copies the daemon setting of the thread that created it, so you change it yourself, before `start()`:

""" + pair(J_DAEMON, K_DAEMON) + """

A daemon doesn't stop the relay so much as abandon it. The JVM can cut it off between publishing a message and marking it sent. Daemons suit work you can afford to lose halfway: a cache refresher, the metrics flusher in the Try it below, or the JVM's own housekeepers from Threads from zero. For a relay that moves payment events, strike this one too.

The third is a flag of our own, a `running` field that the owner sets to `false` and the loop checks on every pass. (It has to be `volatile`, for reasons the memory model track explains.) A flag works for a busy loop, but it can't wake a sleeping thread.

Our relay would notice the flag only when its current sleep ends, and a relay parked in `queue.take()` would never notice it at all. The executors you'll soon hand your tasks to don't know about your flag either.

The fourth is `interrupt()`, and it's the one Java builds on. `t.interrupt()` sets a flag inside `t`, called the **interrupt flag**. If `t` is blocked in `sleep`, `wait`, `join` or a blocking call such as `BlockingQueue.take()`, that call wakes up and throws `InterruptedException`.

If `t` is busy instead, nothing happens right away: the interrupt flag stays set until the thread looks at it. `ExecutorService.shutdownNow()` stops running tasks this same way.

So stopping a thread in Java is cooperative. The interrupt asks. The thread checks, finishes what it's doing, cleans up and returns, at a moment when its data makes sense.

**Java can't kill a thread. It can only ask, and the thread stops itself.**

The interrupt is the right tool, then. But our relay *was* interrupted, and it carried on. Let's find out where the request went."""

# ---------------------------------------------------------------- section 3
J_SWALLOW = """// Naive: the interrupt is "handled" by logging it
try {
    Thread.sleep(idleMillis);
} catch (InterruptedException e) {
    System.err.println("relay interrupted, carrying on");
}"""
K_SWALLOW = """// Naive: the interrupt is "handled" by logging it
try {
    Thread.sleep(idleMillis)
} catch (e: InterruptedException) {
    System.err.println("relay interrupted, carrying on")
}"""
J_RESTORE = """try {
    Thread.sleep(backoffMillis);
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();   // put the request back
    return;                               // then stop, or throw your own exception
}"""
K_RESTORE = """try {
    Thread.sleep(backoffMillis)           // Kotlin doesn't force this try, so add it on purpose
} catch (e: InterruptedException) {
    Thread.currentThread().interrupt()    // put the request back
    return                                // then stop, or throw your own exception
}"""

S2 = """Here's the part of the relay that answered the shutdown request, straight from the lab's starting code:

""" + pair(J_SWALLOW, K_SWALLOW) + """

The catch block looks harmless: the exception was caught, and a line was logged. But methods that throw `InterruptedException` clear the interrupt flag before they throw. So inside the catch block the flag already reads `false`, which was the warm-up question.

Remember the waiter's line in `ThreadStates`, `flag now false`? That was the same clearing, caught in the act. The relay logs, loops round and calls `sleep` again, and nothing anywhere remembers that someone asked it to stop.

Think of an interrupt as a sticky note on a colleague's screen that says "please wrap up". If they're asleep at their desk, the note wakes them. If they're busy typing, they see it the next time they look up.

The catch is that waking up tears the note off. The note is the interrupt flag, and `sleep` tears it off when it throws.

Once you've caught the exception, then, you hold the only copy of the request. You have two good options. Let the exception propagate, by declaring `throws InterruptedException`. Or stick the note back on, by restoring the flag before you do anything else:

""" + pair(J_RESTORE, K_RESTORE) + """

**Never swallow an interrupt. Rethrow it, or restore it.**

If this feels like an easy mistake, you're in good company. JDK 23 fixed `ImageIcon.loadImage` to restore the flag, and JDK 24 fixed the same bug in `FileSystemPreferences.lockFile()`. From JDK 26, the `Thread` Javadoc has a section on interruption that spells out the rule above.

The relay has a second, quieter way to miss the note. When the outbox is full, it publishes batch after batch and never reaches `sleep`, so no `InterruptedException` ever arrives. A loop like that must look for the note itself, once per batch, with `Thread.currentThread().isInterrupted()`.

Be careful with the static `Thread.interrupted()`, which looks almost the same. It reads the flag *and clears it*, so use it only when you mean to take the note down for good.

With both fixes in place, the relay stops when it's asked to. The code that asks still has one job left: wait for the relay to finish, and not forever."""

ASIDE2 = {
    "title": "Is coroutine cancellation the same thing?",
    "body": "Same idea, separate machinery. Cancelling a Kotlin coroutine is cooperative too: `delay()` and the other suspending functions in kotlinx.coroutines notice it and throw `CancellationException`. A `catch (e: Exception)` that swallows that exception can keep a cancelled coroutine running, much like a swallowed interrupt. But cancelling a coroutine doesn't interrupt the thread it runs on. When a coroutine must call blocking code that only listens to interrupts, wrap the call in `runInterruptible { }`, which turns cancellation into an interrupt. The coroutines track covers this in Cancellation and timeouts."
}

# ---------------------------------------------------------------- section 4
J_SLEEPWAIT = """// Naive: hopes two seconds is enough
relay.interrupt();
Thread.sleep(2_000);     // "should be enough"
producer.close();"""
K_SLEEPWAIT = """// Naive: hopes two seconds is enough
relay.interrupt()
Thread.sleep(2_000)      // "should be enough"
producer.close()"""
J_TIMED = """// Fixed: ask, then wait, but not forever
relay.interrupt();
boolean stopped = relay.join(Duration.ofSeconds(5));   // JDK 19+: true if it ended
if (!stopped) log.warn("outbox relay still running after 5 s");
producer.close();"""
K_TIMED = """// Fixed: ask, then wait, but not forever
relay.interrupt()
val stopped = relay.join(Duration.ofSeconds(5))       // JDK 19+: true if it ended
if (!stopped) log.warn("outbox relay still running after 5 s")
producer.close()"""

S3 = """Now look at the other side of the deploy. The shutdown code did the textbook thing: `relay.interrupt()`, then `relay.join()`, then close the Kafka producer that the relay publishes with. With the old relay, that `join()` waited until the kubelet killed the pod. With the fixed relay, it returns as soon as the relay has finished the batch in hand.

You may be thinking, "Why wait at all? Interrupt it and close the producer." Because the relay may still be publishing, and closing the producer under it makes those sends fail. The next idea is usually this one:

""" + pair(J_SLEEPWAIT, K_SLEEPWAIT) + """

`Thread.sleep(ms)` pauses the current thread for at least that long, and it promises nothing about any other thread. On a quiet laptop the relay stops within a few milliseconds, and the code works. On a node that's busy with three other deploys, two seconds may not be enough.

Even when the relay finishes in time, the shutdown code isn't promised to see what it wrote. The language gives `sleep` no synchronization meaning, so the JIT may compile each thread as if the other didn't exist. It can keep a value in a register instead of memory, or move a read or a write. The memory model track shows a loop that never ends for exactly this reason.

`join()` fixes both problems. It waits for the thread to end, and when it returns, you're guaranteed to see everything that thread wrote. The `java.util.concurrent` docs put it this way: "All actions in a thread happen-before any other thread successfully returns from a join on that thread."

Happens-before is the memory model's name for that guarantee. The same guarantee is why, in Threads from zero, we could read the `partial` array after the joins with no locks at all.

Plain `join()` has one weakness, and the deploy found it: it waits as long as it takes. So give it a limit.

`join(5_000)` waits up to five seconds and returns nothing, so you check `relay.isAlive()` afterwards. Since JDK 19, `join(Duration)` returns `true` if the thread ended:

""" + pair(J_TIMED, K_TIMED) + """

A timed join returns as soon as the thread ends, so it costs nothing when the relay behaves. When it returns `false`, you know the relay is still running, and you can log it and decide what to do.

Keep `sleep` for what it's for: a pause, such as a back-off between retries to the card issuer, or the relay's idle wait between polls. (Since JDK 19 you can write `Thread.sleep(Duration.ofMillis(200))`, if you like the unit in the type.)

**Wait for the thread, not for the clock.**

That completes a thread's life: we can start it, read its state, ask it to stop and wait for it to finish. But all of it is one thread coordinating with another by hand. None of it protects data that two threads change while both are running, and that's where most concurrency bugs live."""

L = {
 "id": "conc-02",
 "title": "A thread's life: start, join, sleep, interrupt",
 "minutes": 35,
 "goal": "By the end you can name the six states a thread lives through and read them in a thread dump, wait for a thread with `join()` instead of `sleep()`, and write a worker that stops cleanly when interrupted without losing the interrupt.",
 "opening": OPENING,
 "warmup": {
  "q": "A worker is inside `Thread.sleep(10_000)`. Another thread calls `worker.interrupt()`. The worker catches the `InterruptedException`. Inside the catch block, what does `Thread.currentThread().isInterrupted()` return?",
  "options": ["true, because it was just interrupted", "false, because the flag was cleared when the exception was thrown", "It throws a second InterruptedException", "It depends on the JVM"],
  "answer": 1,
  "why": "Methods that throw `InterruptedException` clear the interrupt flag first, so inside the catch block the flag already reads false. If the catch only logs, the stop request is gone for good. That's exactly what happened to the relay, and it's why the rule is to rethrow, or to put the flag back with `Thread.currentThread().interrupt()`. The section on where the relay's interrupt went takes it line by line."
 },
 "sections": [
  {
   "h": "The six states a thread lives through",
   "body": S0,
   "figure": {"svg": FIG, "caption": "The relay's life as a map: it starts NEW, lives in RUNNABLE, steps out to wait for a lock, another thread or the clock, and ends TERMINATED."},
   "try": {
    "title": "Put a thread in every state",
    "minutes": 4,
    "steps": [
     "Read `ThreadStates` below. Each `show(...)` call sends a thread somewhere and asks `getState()`. Match each one to a box in the figure.",
     "Run it with the command below, and compare with the output in this section. Then find the extra line the waiter prints when it's interrupted out of `wait()`. It explains the relay's bug, as you'll see in the section on interrupts.",
     "Now give the waiter a time limit: change `monitor.wait()` to `monitor.wait(5_000)`. Predict the `inside wait():` line, then run it again."
    ],
    "code": {"lang": "java", "title": "ThreadStates.java", "src": read(f"{lab}/demo/{P}/ThreadStates.java"),
             "run": demo("ThreadStates"), "file": f"{lab}/demo/{P}/ThreadStates.java", "alt": kt("ThreadStates")},
    "expect": "The first run matches the section line for line: `NEW`, then `TIMED_WAITING` (the sleeper), `RUNNABLE` (the busy loop), `WAITING` (the waiter in `wait()`), `BLOCKED` (main holds `monitor`, so the new thread can't get in) and finally `TERMINATED`. The waiter prints `waiter interrupted, flag now false`: the interrupt woke it, and the flag was cleared on the way out. With `wait(5_000)`, the waiter's line reads `TIMED_WAITING`, after a pause of about two seconds, because `show` keeps polling for a `WAITING` that never comes and then prints what it sees. Same call plus a time limit, and the thread moves to the other box."
   }
  },
  {
   "h": "Reading the states in a thread dump",
   "body": SD
  },
  {
   "h": "Weighing the ways to stop a thread",
   "body": S1,
   "try": {
    "title": "Lose a finally block",
    "minutes": 4,
    "steps": [
     "Run `DaemonDemo`. Count the flushes, and look for the line from the `finally` block.",
     "Change `setDaemon(true)` to `setDaemon(false)` (in Kotlin, `isDaemon = true` to `false`) and run it again. Stop it with Ctrl+C once you've seen enough.",
     "Keep it non-daemon, and add `metrics.interrupt(); metrics.join();` just before main's last `println`. Predict the last two lines, then run it once more."
    ],
    "code": {"lang": "java", "title": "DaemonDemo.java", "src": read(f"{lab}/demo/{P}/DaemonDemo.java"),
             "run": demo("DaemonDemo"), "file": f"{lab}/demo/{P}/DaemonDemo.java", "alt": kt("DaemonDemo")},
    "expect": "As a daemon, you get four flushes and `main: done, returning`, and no `finally block ran`: the JVM exited underneath the thread. As a non-daemon, it flushes forever, because nothing asks it to stop. With the interrupt and the join, it stops at once and prints `metrics: finally block ran` before `main: done, returning`. That's what a clean shutdown looks like: ask, then wait."
   }
  },
  {
   "h": "Where the relay's interrupt went",
   "body": S2,
   "aside": ASIDE2,
   "try": {
    "title": "Watch the flag disappear",
    "minutes": 4,
    "steps": [
     "Run `InterruptFlag` and read the five numbered lines.",
     "Comment out the line `me.interrupt()` in the catch block. Predict lines 2 to 5, then run it again.",
     "Explain to yourself why line 4 prints `true` with the restore in place, and why line 5 then prints `false`."
    ],
    "code": {"lang": "java", "title": "InterruptFlag.java", "src": read(f"{lab}/demo/{P}/InterruptFlag.java"),
             "run": demo("InterruptFlag"), "file": f"{lab}/demo/{P}/InterruptFlag.java", "alt": kt("InterruptFlag")},
    "expect": "With the restore: `false`, `true`, `true`, `true`, `false`. Line 1 is `false` because `sleep` cleared the flag on its way out, and line 2 shows the note stuck back on. Line 4 uses `Thread.interrupted()`, which reads the flag and clears it, so line 5 is `false`. Without the restore, every line prints `false`. The request was lost the moment the exception was caught, exactly as in the relay."
   },
   "refs": [
    {"title": "Thread.java at jdk-27-ga, with the \"Thread Interruption\" section", "url": "https://github.com/openjdk/jdk/blob/jdk-27-ga/src/java.base/share/classes/java/lang/Thread.java", "kind": "docs"},
    {"title": "Interrupts (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/essential/concurrency/interrupt.html", "kind": "read"}
   ]
  },
  {
   "h": "Waiting for the relay to finish",
   "body": S3,
   "try": {
    "title": "Give up waiting, then wait properly",
    "minutes": 3,
    "steps": [
     "Read `JoinWithTimeout`. The worker takes about 500 ms to fetch an FX rate, and `main` waits for it twice. Predict both printed lines.",
     "Run it.",
     "Change the timed join to `fetch.join(Duration.ofSeconds(2))` and run it again. What does `ended` say now, and how long did `main` wait?"
    ],
    "code": {"lang": "java", "title": "JoinWithTimeout.java", "src": read(f"{lab}/demo/{P}/JoinWithTimeout.java"),
             "run": demo("JoinWithTimeout"), "file": f"{lab}/demo/{P}/JoinWithTimeout.java", "alt": kt("JoinWithTimeout")},
    "expect": "First run: `ended=false, alive=true, rate=0`, then `alive=false, rate=10842`. The 100 ms join gave up early, and the plain join waited for the end and saw the rate. With a 2-second limit, `ended=true` and the rate is already there after about 500 ms. A timed join returns as soon as the thread ends; it doesn't sit out the full time."
   }
  }
 ],
 "compare": {
  "title": "An interruptible polling loop in Java and Kotlin",
  "java": {"title": "Java", "src": "Thread relay = new Thread(() -> {\n    Thread me = Thread.currentThread();\n    while (!me.isInterrupted()) {\n        // poll the outbox and publish here\n        try {\n            Thread.sleep(50);        // the compiler forces you to handle the checked exception\n        } catch (InterruptedException e) {\n            me.interrupt();          // restore the flag, so the loop condition sees it\n        }\n    }\n    System.out.println(\"relay stopped, flag = \" + me.isInterrupted());\n}, \"outbox-relay\");\nrelay.start();"},
  "kotlin": {"title": "KotlinRelay.kt", "src": read(f"{lab}/demo/{K}/KotlinRelay.kt")},
  "note": "Both versions follow the same protocol, line for line: loop until the flag is set, sleep, and restore the flag in the catch block. Two things differ. First, Kotlin has no checked exceptions, so `Thread.sleep(50)` compiles with no try at all, and that changes how the bug looks. In Java the usual mistake is a catch that swallows the interrupt. In Kotlin it's often no catch at all: the `InterruptedException` escapes the lambda, the thread dies with a stack trace on standard error, and any cleanup after the loop never runs. Neither is a clean stop. Here Java's checked exception earns its keep: the compiler won't let you forget that interrupts exist, even if it can't make you handle them well. Second, `isInterrupted` reads as a property in Kotlin, while the static `Thread.interrupted()` still reads the flag and clears it."
 },
 "worked": {
  "title": "Make a retrying card-issuer call cancellable",
  "steps": [
   {"say": "Here's a retry loop of the kind most payment services have somewhere. It calls the card issuer and backs off when the call times out. Read it and find the line where a shutdown request disappears.",
    "code": "AuthResult authorize(AuthRequest req) {\n    for (int attempt = 1; ; attempt++) {\n        try {\n            return issuer.authorize(req);\n        } catch (IssuerTimeoutException e) {\n            try {\n                Thread.sleep(200L * attempt);\n            } catch (InterruptedException ie) {\n                log.warn(\"interrupted during back-off\", ie);   // and loop again\n            }\n        }\n    }\n}", "lang": "java",
    "alt_code": "fun authorize(req: AuthRequest): AuthResult {\n    var attempt = 1\n    while (true) {\n        try {\n            return issuer.authorize(req)\n        } catch (e: IssuerTimeoutException) {\n            try {\n                Thread.sleep(200L * attempt)\n            } catch (ie: InterruptedException) {\n                log.warn(\"interrupted during back-off\", ie)   // and loop again\n            }\n        }\n        attempt++\n    }\n}", "alt_lang": "kotlin"},
   {"say": "It's the inner catch. `sleep` cleared the flag before it threw, so after the log line nothing remembers the request, and the loop has no limit. If the issuer is down during a rollout, this thread retries until the pod is killed. It's the relay's bug in a different place. Before you read on, decide what the method should do when it's interrupted.",
    "code": "", "lang": ""},
   {"say": "Put the request back first, then stop retrying and tell the caller why. Wrapping the cause in your own exception is fine, as long as the flag is set before you throw. And while we're here, let's give the retries a limit.",
    "code": "AuthResult authorize(AuthRequest req) {\n    for (int attempt = 1; ; attempt++) {\n        try {\n            return issuer.authorize(req);\n        } catch (IssuerTimeoutException e) {\n            if (attempt == 3) throw e;                          // 1. bounded retries\n            try {\n                Thread.sleep(200L * attempt);\n            } catch (InterruptedException ie) {\n                Thread.currentThread().interrupt();             // 2. restore the request\n                throw new AuthCancelledException(req.id(), ie); // 3. stop, and say why\n            }\n        }\n    }\n}", "lang": "java",
    "alt_code": "fun authorize(req: AuthRequest): AuthResult {\n    var attempt = 1\n    while (true) {\n        try {\n            return issuer.authorize(req)\n        } catch (e: IssuerTimeoutException) {\n            if (attempt == 3) throw e                          // 1. bounded retries\n            try {\n                Thread.sleep(200L * attempt)\n            } catch (ie: InterruptedException) {\n                Thread.currentThread().interrupt()             // 2. restore the request\n                throw AuthCancelledException(req.id, ie)       // 3. stop, and say why\n            }\n        }\n        attempt++\n    }\n}", "alt_lang": "kotlin"},
   {"say": "Now the caller, say an executor that is shutting down, finds the interrupt flag still set on its worker thread, and the payment is reported as cancelled instead of being retried forever. If `authorize` could simply declare `throws InterruptedException`, that would be simpler still: there would be nothing to restore.",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Make the outbox relay stop on interrupt",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/OutboxRelay.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l02.*'",
  "steps": [
   "Run the tests. All five fail, and the run is slow, because each test waits 5 seconds for a relay that never stops. This is the relay from the deploy.",
   "Read `OutboxRelay.run()`. Find the two ways it ignores an interrupt: while sleeping, and while busy with full batches.",
   "Change the loop condition so it checks `Thread.currentThread().isInterrupted()` once per batch. Finish the batch in hand before checking.",
   "Handle the `InterruptedException` from `sleep` by restoring the flag and leaving the loop.",
   "Run the tests until all five pass, then run them once more."
  ],
  "hints": [
   "Put the `try` around the whole `while` loop. Then the catch block runs once, restores the flag, and `run()` returns.",
   "If the loop ends because `isInterrupted()` returned true, the flag is still set. You only need to restore it after an `InterruptedException`.",
   "The \"finishes the batch\" test counts messages: the total must be a multiple of the batch size. Don't check the flag inside the `for` loop over the batch."
  ],
  "done_when": "All five tests in `OutboxRelayTest` pass."
 },
 "drill": {
  "title": "Write an interruptible poller from memory",
  "minutes": 4,
  "prompt": "Close this page. Write a `Runnable` that polls a `Supplier<List<String>>` and prints each item. When the list is empty, it sleeps 100 ms. It must stop when interrupted, whether it's sleeping or busy, and leave the flag set when it returns. Then compare with the answer.",
  "answer": {"lang": "java", "src": "Runnable poller = () -> {\n    try {\n        while (!Thread.currentThread().isInterrupted()) {\n            List<String> batch = source.get();\n            batch.forEach(System.out::println);\n            if (batch.isEmpty()) Thread.sleep(100);\n        }\n    } catch (InterruptedException e) {\n        Thread.currentThread().interrupt();   // sleep cleared it; put it back\n    }\n};", "alt": {"lang": "kotlin", "title": "Kotlin", "src": "val poller = Runnable {\n    try {\n        while (!Thread.currentThread().isInterrupted) {\n            val batch = source.get()\n            batch.forEach(::println)\n            if (batch.isEmpty()) Thread.sleep(100)\n        }\n    } catch (e: InterruptedException) {\n        Thread.currentThread().interrupt()   // sleep cleared it; put it back\n    }\n}"}}
 },
 "recap": [
  "A thread starts NEW, becomes RUNNABLE at `start()`, steps out of RUNNABLE to wait for a lock (BLOCKED), for another thread (WAITING) or for another thread or the clock (TIMED_WAITING), and ends TERMINATED when `run()` returns.",
  "In a thread dump, read the stack as well as the state. RUNNABLE also covers waiting for a core and sitting in native I/O, and a thread parked on a `ReentrantLock` shows WAITING, because BLOCKED is only for `synchronized`.",
  "Java can't kill a thread (`Thread.stop()` was removed in JDK 26), and a daemon is abandoned, not stopped. `interrupt()` sets a flag, and blocking calls like `sleep`, `wait`, `join` and `take` throw `InterruptedException` and clear it.",
  "When you catch `InterruptedException`, rethrow it or call `Thread.currentThread().interrupt()`. A loop that never blocks must check `isInterrupted()` itself.",
  "`join()` waits for a thread to end and makes everything it wrote visible to you; give it a timeout when the wait must end. `sleep()` only passes time.",
  "The limit: start, interrupt and join coordinate one thread with another. They don't protect data that two running threads change at the same time."
 ],
 "closing": "We started with a pod that wouldn't stop and a relay that answered a shutdown request with a log line. We walked the relay through its six states and caught it asleep in a thread dump. Then we struck out `stop()`, daemons and home-made flags, and fixed the relay so the interrupt survives the catch block.\n\nNow search your own code for `catch (InterruptedException`. Every hit should either rethrow or call `Thread.currentThread().interrupt()`. Any hit that only logs is a relay waiting for its deploy.\n\nNext, we'll let two RUNNABLE threads update one counter at the same time, and watch it come out wrong with no exception and no warning.",
 "quiz": [
  {"q": "A thread is stuck inside `ReentrantLock.lock()`, waiting for another thread to release it. What does `getState()` return?",
   "options": ["BLOCKED", "WAITING", "RUNNABLE", "TIMED_WAITING"],
   "answer": 1, "why": "`ReentrantLock` parks its waiting threads with `LockSupport.park()`, and a parked thread is WAITING. BLOCKED is kept for threads trying to enter a `synchronized` block or method. Remember the difference when you scan a thread dump for contention, or you'll miss every explicit lock."},
  {"q": "What does this print?\n\n```java\nThread t = new Thread(() -> {\n    try { Thread.sleep(5_000); }\n    catch (InterruptedException e) {\n        System.out.println(Thread.currentThread().isInterrupted());\n    }\n});\nt.start();\nt.interrupt();\n```",
   "options": ["true", "Nothing: the thread sleeps for 5 s and ends", "false", "It depends on whether interrupt() runs before sleep() starts"],
   "answer": 2, "why": "If the interrupt arrives during the sleep, `sleep` throws and clears the flag. If it arrives before the sleep starts, `sleep` sees the flag, clears it and throws at once. Either way the catch block sees `false`. Timing changes when the exception comes, not what the flag says."},
  {"q": "A Kafka consumer loop wraps its back-off in `try { Thread.sleep(500); } catch (InterruptedException e) { log.warn(\"interrupted\"); }` and keeps looping. What goes wrong at shutdown?",
   "options": ["Nothing, because the exception was logged", "The consumer stops, but its last batch is processed twice", "The JVM throws IllegalMonitorStateException", "`shutdownNow()` interrupts it, the catch clears the request, and the loop keeps running until the process is killed"],
   "answer": 3, "why": "`shutdownNow()` stops tasks by interrupting them. The `InterruptedException` cleared the flag and the catch didn't put it back, so the loop never learns it should stop. It's the relay bug from this lesson in another loop. Logging isn't handling: restore the flag and leave the loop."},
  {"q": "A daemon thread writes audit lines to a file and closes the file in a `finally` block. The last non-daemon thread ends. What happens to the daemon thread?",
   "options": ["The JVM waits for it to finish the current line", "The JVM exits, the daemon stops where it is, and its finally block does not run", "The JVM interrupts it and waits for the finally block", "It becomes a non-daemon thread and keeps the JVM alive"],
   "answer": 1, "why": "The JVM doesn't wait for daemon threads, and it doesn't unwind their stacks when it exits, so their `finally` blocks never run. Audit lines can be lost or cut short. Work that must complete belongs on a non-daemon thread that you stop with an interrupt and then join."},
  {"q": "From Threads from zero: a loop starts each thread and joins it in the same iteration, `t.start(); t.join();`, for four threads. While the loop runs, how many of those four threads are alive at the same time?",
   "options": ["At most one", "All four", "Two: the current one and the next", "None, because join() stops them"],
   "answer": 0, "why": "Each `join()` blocks the loop until that thread is TERMINATED, and only then does the next iteration start a new thread. So at most one of the four is ever alive. Start all four first, then join them in a second loop.",
   "from": "conc-01"}
 ],
 "flashcards": [
  {"front": "A thread waits to enter a `synchronized` block another thread holds. What state is it in?", "back": "BLOCKED."},
  {"front": "A thread waits in `ReentrantLock.lock()`. What state is it in?", "back": "WAITING (or TIMED_WAITING for a timed tryLock). Explicit locks park the thread; BLOCKED is only for monitors."},
  {"front": "Besides waiting, what does `t.join()` guarantee?", "back": "Everything `t` wrote before it ended is visible to the thread whose `join()` returned. `sleep()` gives no such guarantee."},
  {"front": "What happens to the interrupt flag when `sleep()` throws `InterruptedException`?", "back": "It is cleared before the exception is thrown. Inside the catch block, `isInterrupted()` returns false."},
  {"front": "What are the two correct ways to handle a caught `InterruptedException`?", "back": "Rethrow it (declare `throws InterruptedException`), or restore the flag with `Thread.currentThread().interrupt()` and stop what you're doing."},
  {"front": "`isInterrupted()` vs `Thread.interrupted()`?", "back": "`isInterrupted()` only reads the flag. The static `Thread.interrupted()` reads it and clears it."},
  {"front": "What is the status of `Thread.stop()` on JDK 26?", "back": "Removed. It always threw `UnsupportedOperationException` from JDK 20, and old binaries that call it get `NoSuchMethodError` on 26+."}
 ],
 "terms": [
  {"term": "Thread state", "plain": "What a thread is doing right now, one of the six values of `Thread.State`."},
  {"term": "Thread dump", "plain": "A list of every thread in a JVM with its state and stack, taken with `jcmd <pid> Thread.print`."},
  {"term": "join", "plain": "Wait for a thread to end. Afterwards you see everything it wrote."},
  {"term": "Interrupt flag", "plain": "A per-thread boolean that `interrupt()` sets to ask the thread to stop."},
  {"term": "InterruptedException", "plain": "Thrown by blocking calls when the thread is interrupted. The flag is cleared when it is thrown."},
  {"term": "Daemon thread", "plain": "A thread the JVM does not wait for at exit. It can stop mid-work."},
  {"term": "Cooperative cancellation", "plain": "Stopping a thread by asking it, and letting it check and clean up itself."}
 ],
 "explain_back": {
  "prompt": "A teammate asks: \"Why can't I just catch InterruptedException and log it? The thread keeps working, so what's the harm?\" Answer them in your own words.",
  "answer": "An interrupt is how the rest of the system asks your thread to stop: executors, shutdown code and frameworks all use it. When `sleep` or `wait` throws `InterruptedException`, it clears the interrupt flag first. If you only log, the request is gone, and nobody above you can tell it was ever made. So the loop keeps running, and shutdown hangs until the process is killed, just like the outbox relay during the deploy. Either let the exception propagate, or call `Thread.currentThread().interrupt()` to put the flag back, then stop what you're doing."
 },
 "deeper": {
  "minutes": 8,
  "body": "Not every blocking call listens to interrupts, and it's worth knowing which ones don't before you meet them in production.\n\n`sleep`, `wait`, `join`, `BlockingQueue.take` and `Lock.lockInterruptibly` throw `InterruptedException`. A thread blocked on an NIO `InterruptibleChannel` gets different treatment: the Javadoc says the channel is closed, the flag is set and the thread receives a `ClosedByInterruptException`. So interrupting a thread that is writing to a `FileChannel` closes the file for everyone who shares that channel. That one surprises people.\n\nPlain `synchronized` doesn't respond at all. A thread that is BLOCKED waiting for a monitor stays blocked when you interrupt it; only the flag changes. A platform thread reading a classic `java.net.Socket` stream may also sit there until data arrives. For those, give the wait a timeout (a socket read timeout, or `tryLock` with a timeout), so the thread wakes up now and then and can check its flag.\n\nTwo smaller facts to finish. Interrupts are part of the memory model too: if T1 interrupts T2, everything T1 did before the interrupt is visible to T2 once T2 sees it, by catching the exception or by reading the flag. And the JDK 27 Javadoc for `interrupt()` notes that interrupting a thread that isn't alive still records the request in the reference implementation, so don't count on an interrupt sent before `start()` being dropped."
 },
 "sources": [
  {"title": "Thread (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Thread.html"},
  {"title": "java.util.concurrent package summary, Memory Consistency Properties (source at jdk-25-ga)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/package-info.java"},
  {"title": "Interrupts (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/essential/concurrency/interrupt.html"},
  {"title": "Java Concurrency in Practice, Goetz et al., chapter 7", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/conc-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
