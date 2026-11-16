import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/concurrency/src"
P = "java/workbench/concurrency/l05"
K = "kotlin/workbench/concurrency/l05"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"./gradlew :concurrency:demo -Pmain=workbench.concurrency.l05.{name}"
def kt(name):
    """The Kotlin twin of a Java demo: Foo.kt with a top-level main, class FooKt."""
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
            "run": demo(f"{name}Kt"), "file": f"{lab}/demo/{K}/{name}.kt"}
def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

FIG = (
    '<svg viewBox="0 0 680 250" role="img" aria-label="A monitor: threads wait in the entry set for the lock, one owner runs the block, wait() moves the owner to the wait set, notify moves waiters back to the entry set">'
    '<rect class="box-bad" x="20" y="60" width="170" height="96" rx="8"/>'
    '<text class="t" x="105" y="86" text-anchor="middle">entry set</text>'
    '<text class="t-s t-code" x="105" y="110" text-anchor="middle">BLOCKED</text>'
    '<text class="t-s t-m" x="105" y="132" text-anchor="middle">wants the lock</text>'
    '<rect class="box-a" x="255" y="60" width="170" height="96" rx="8"/>'
    '<text class="t" x="340" y="86" text-anchor="middle">owner</text>'
    '<text class="t-s t-code" x="340" y="110" text-anchor="middle">RUNNABLE</text>'
    '<text class="t-s t-m" x="340" y="132" text-anchor="middle">holds the monitor</text>'
    '<rect class="box-b" x="490" y="60" width="170" height="96" rx="8"/>'
    '<text class="t" x="575" y="86" text-anchor="middle">wait set</text>'
    '<text class="t-s t-code" x="575" y="110" text-anchor="middle">WAITING</text>'
    '<text class="t-s t-m" x="575" y="132" text-anchor="middle">lock given back</text>'
    '<line class="ln" x1="190" y1="108" x2="253" y2="108" marker-end="url(#arr)"/>'
    '<text class="t-s" x="222" y="98" text-anchor="middle">gets it</text>'
    '<line class="ln" x1="425" y1="108" x2="488" y2="108" marker-end="url(#arr)"/>'
    '<text class="t-s t-code" x="456" y="98" text-anchor="middle">wait()</text>'
    '<line class="ln" x1="340" y1="58" x2="340" y2="24" marker-end="url(#arr)"/>'
    '<text class="t-s" x="350" y="34" text-anchor="start">leaves the block: lock released</text>'
    '<path class="ln-a" d="M575 158 L575 205 L105 205 L105 160" fill="none" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="340" y="228" text-anchor="middle">notify() / notifyAll(): back to the entry set, so it must win the lock again</text>'
    '</svg>'
)

# ---------------------------------------------------------------- code samples in the prose
J_SPIN = """// Naive: asks the empty queue again and again
String nextAuthorization() {
    while (true) {
        synchronized (lock) {
            if (!queue.isEmpty()) return queue.removeFirst();
        }
    }
}"""
K_SPIN = """// Naive: asks the empty queue again and again
fun nextAuthorization(): String {
    while (true) {
        synchronized(lock) {
            if (queue.isNotEmpty()) return queue.removeFirst()
        }
    }
}"""
J_WORKER = """// Fixed: sleeps until a payment arrives
String nextAuthorization() throws InterruptedException {
    synchronized (lock) {
        while (queue.isEmpty()) {
            lock.wait();               // give back the lock, sleep until woken, take it again
        }
        return queue.removeFirst();    // the queue has an item, and we hold the lock
    }
}"""
K_WORKER = """// Fixed: sleeps until a payment arrives
fun nextAuthorization(): String {
    synchronized(lock) {               // lock is a java.lang.Object: Kotlin's Any has no wait()
        while (queue.isEmpty()) {
            lock.wait()                // give back the lock, sleep until woken, take it again
        }
        return queue.removeFirst()     // the queue has an item, and we hold the lock
    }
}"""
J_ADD = """void add(String authorization) {
    synchronized (lock) {
        queue.addLast(authorization);  // change the state first
        lock.notifyAll();              // then wake every thread waiting on lock
    }
}"""
K_ADD = """fun add(authorization: String) {
    synchronized(lock) {
        queue.addLast(authorization)   // change the state first
        lock.notifyAll()               // then wake every thread waiting on lock
    }
}"""
J_IF = """// Naive: checks once, before waiting
synchronized (lock) {
    if (queue.isEmpty()) lock.wait();
    return queue.removeFirst();
}"""
K_IF = """// Naive: checks once, before waiting
synchronized(lock) {
    if (queue.isEmpty()) lock.wait()
    return queue.removeFirst()
}"""
J_FULL = """while (queue.size() == capacity) lock.wait();   // the Kafka thread's guard: "not full\""""
K_FULL = """while (queue.size == capacity) lock.wait()      // the Kafka thread's guard: "not full\""""

BUFFER = """public class BoundedBuffer<T> {
    private final Object lock = new Object();
    private final Deque<T> items = new ArrayDeque<>();
    private final int capacity;

    public void put(T item) throws InterruptedException {
        synchronized (lock) {
            while (items.size() == capacity) {   // 1. guard: re-check after every wake-up
                lock.wait();
            }
            items.addLast(item);                 // 2. act: condition holds, lock held
            lock.notifyAll();                    // 3. signal: the state changed
        }
    }

    public T take() throws InterruptedException {
        synchronized (lock) {
            while (items.isEmpty()) {
                lock.wait();
            }
            T head = items.removeFirst();
            lock.notifyAll();
            return head;
        }
    }
}"""

KBUFFER = """class BoundedBuffer<T>(private val capacity: Int) {
    @Suppress("PLATFORM_CLASS_MAPPED_TO_KOTLIN")
    private val lock = Object()                    // java.lang.Object: Kotlin's Any has no wait()
    private val items = ArrayDeque<T>()

    @Throws(InterruptedException::class)           // so Java callers see it, as in the Java version
    fun put(item: T) {
        synchronized(lock) {
            while (items.size == capacity) {       // 1. guard: re-check after every wake-up
                lock.wait()
            }
            items.addLast(item)                    // 2. act: condition holds, lock held
            lock.notifyAll()                       // 3. signal: the state changed
        }
    }

    @Throws(InterruptedException::class)
    fun take(): T {
        synchronized(lock) {
            while (items.isEmpty()) {
                lock.wait()
            }
            val head = items.removeFirst()
            lock.notifyAll()
            return head
        }
    }
}"""

OPENING = """Picture the settlement queue on a quiet evening. One thread reads card authorizations from Kafka and drops each one into an in-memory queue. A settlement worker takes them off the other end. Between bursts the queue is empty, and the worker waits for the next payment.

So how should it wait? In synchronized and intrinsic locks, we let one thread at a time into the code that touches shared state. That keeps the queue consistent, but a lock says nothing about waiting for the queue to fill. The first versions most of us write either ask the empty queue "anything yet?" millions of times a second, or nap between questions and make each payment wait for the nap to end.

Every Java object has a better answer, built into the monitor that `synchronized` uses. In this lesson, we'll teach the worker to wait without spinning, see why a second worker must check again, watch `notify()` stall a bounded queue, and build that queue by hand. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Let's start with one worker and an empty queue. The quickest code asks again and again, taking the lock for every look, since readers need the lock too:

""" + pair(J_SPIN, K_SPIN) + """

That loop is correct: it never takes a payment that isn't there, and it never misses one. But it's a **busy wait**, or spin. The thread stays `RUNNABLE` and keeps a core busy the whole time it waits, and the Kafka thread has to compete with it for the lock on every add.

The Try it below times a simpler spinner, one that checks a `volatile` flag, against a thread that waits properly. To wait one second, the spinner used about 1,030 ms of CPU. The waiting thread used 0 ms.

A `Thread.sleep(50)` between looks saves the CPU. In exchange, a payment that lands just after a look sits there for up to 50 ms. The outbox relay in A thread's life made the same trade between its polls. A sleep is a guess about when the next item will arrive, and the guess is never quite right.

What we want is a worker that sleeps until the queue changes, and a Kafka thread that wakes it when it does. Every Java object can do that, through its monitor. Here's the worker's side:

""" + pair(J_WORKER, K_WORKER) + """

`wait()` does three things, in order. First, it releases the monitor, so the Kafka thread can get in. Then it parks the worker in the monitor's **wait set**, in the `WAITING` state, using no CPU. Finally, when the worker is woken, it takes the monitor back before `wait()` returns. So the line after `wait()` runs with the lock held, like the line before it.

The Kafka thread does the other half, holding the same lock:

""" + pair(J_ADD, K_ADD) + """

`notifyAll()` doesn't hand over the lock. Each woken thread moves to the monitor's **entry set**, the threads queuing to get in, and shows as `BLOCKED` until the Kafka thread leaves its block. (Its sibling `notify()` wakes just one waiter. Which one it wakes will matter in the third section.)

Picture the monitor as a room with one key. `wait()` hangs the key on its hook and steps into the waiting room next door. `notifyAll()` sends everyone in the waiting room back to the corridor, to queue for the key again. The waiting room is the wait set, and the corridor is the entry set; the figure draws both.

The worker's code is a **guarded block**. The guard is the loop's condition, here "the queue isn't empty", and the thread waits until it holds. Notice that the guard is a `while`, although with one worker an `if` looks just as good. We'll come back to that in the next section.

The order on the Kafka side matters too: state first, then the signal. If a payment arrives before the worker starts waiting, the `notifyAll()` wakes nobody, and that's fine. The worker checks the queue first, finds the payment and never calls `wait()`. Code that waits for a bare signal, with no state to check, sleeps forever when the signal comes first. That's a **lost wake-up**, and it passes tests because the waiter usually gets there first.

**A notification is only a hint. Wait for a state, never for a signal.**

One more rule holds it all together. You must hold the monitor of the object you call `wait()` or `notifyAll()` on, or you get `IllegalMonitorStateException` at once. Since the queue can change only under the lock, no payment can slip in between the worker's check and its wait.

One worker now waits for free and wakes the moment a payment lands. A busy evening needs a second one."""

ASIDE0 = {
    "title": "Why do the Kotlin samples lock on Object()?",
    "body": "Kotlin's `Any` stands for `java.lang.Object`, but it doesn't expose `wait()`, `notify()` or `notifyAll()`. To call them, the Kotlin samples in this lesson declare the lock as a `java.lang.Object` itself, `private val lock = Object()`, which earns a compiler warning that the demos silence with `@Suppress(\"PLATFORM_CLASS_MAPPED_TO_KOTLIN\")`. The idiomatic Kotlin guarded block uses a `ReentrantLock` and a `Condition` instead: `await()` plays the part of `wait()`, and `signalAll()` the part of `notifyAll()`. Every rule in this lesson holds there unchanged, and lesson 7 of this track covers it."
}

# ---------------------------------------------------------------- section 1
S1 = """Remember the `while` in the worker's guard? With one worker, an `if` seems to do the same job: check once, wait if the queue is empty, then take the payment. Plenty of first versions look exactly like this:

""" + pair(J_IF, K_IF) + """

With one worker, that passes every test. So let's give it a second worker and a single payment. The Try it below parks two consumers in `wait()`, adds one authorization and calls `notifyAll()`. Here's what it printed:

```text
consumer-2 failed: java.util.NoSuchElementException
consumer-1 took auth-1
```

`notifyAll()` woke two workers for one payment, and the second one found the queue empty. Let's trace it, one thread at a time:

1. Both workers find the queue empty and call `wait()`, so both sit in the wait set.
2. The Kafka thread adds `auth-1` and calls `notifyAll()`. Both workers move to the entry set.
3. Consumer 1 gets the lock first. Its `wait()` returns, it takes `auth-1`, and it leaves.
4. Consumer 2 gets the lock next, and its `wait()` returns too. Its `if` ran long ago, before it waited, so it goes straight to `removeFirst()` on an empty queue.

Which worker wins, and which line prints first, changes from run to run. The ending doesn't.

With `while`, consumer 2 checks the queue again after waking, finds it empty and goes back to waiting. Change that one word in the Try it, and the second worker waits quietly until main gives it `auth-2`.

**Being woken doesn't mean the state is right. Check again, in a while loop.**

There's a second reason for the loop, in the Javadoc for `Object.wait`: "A thread can wake up without being notified, interrupted, or timing out, a so-called spurious wakeup." It's rare, but it's allowed, and the Javadoc tells you to test the condition again and keep waiting. In the waiting-room picture, nobody walks out for no reason; a Java thread is allowed to. So even a lone worker needs the loop. A second worker just makes the bug show up on the first busy evening.

The loop costs nothing, so use it every time. In a code review, treat an `if` around `wait()` as a bug, even in code that has never failed. It just hasn't had two waiters at once yet.

Two workers now share the queue safely. But nothing stops the Kafka thread from adding payments faster than the workers can settle them. Next, we'll give the queue a limit, and the waiting starts on the other side too."""

# ---------------------------------------------------------------- section 2
S2 = """So far only the workers wait. When the card network slows down, the workers fall behind, the Kafka thread keeps adding, and an unbounded queue grows until the heap runs out. So let's give the queue a capacity, and make the Kafka thread wait while it's full:

""" + pair(J_FULL, K_FULL) + """

Making a fast producer wait for a slow consumer like this is called **backpressure**. It also gives the monitor two kinds of waiters. The Kafka thread waits for "not full", and the workers wait for "not empty". A monitor has only one wait set, so they all wait in the same place.

With `notifyAll()`, that's harmless: everyone wakes, and each `while` loop sends back the threads that can't go on. With `notify()`, it isn't. `notify()` wakes one waiter, and it doesn't take requests: the JVM picks which one. Here's what that does to a one-slot queue with two producers and two consumers, where every signal is a `notify()`:

1. The slot is empty, so both consumers wait.
2. Producer 1 fills the slot, and its `notify()` wakes consumer 1. Before consumer 1 gets the lock, both producers find the slot full and wait. The wait set now holds producer 1, producer 2 and consumer 2.
3. Consumer 1 empties the slot and calls `notify()`, which happens to wake consumer 2, the wrong kind.
4. Consumer 2 finds the slot empty and waits again. Consumer 1 loops back, finds it empty too, and waits.

Now all four threads wait for a signal nobody is left to send. No thread holds the lock, so this isn't a deadlock in the textbook sense (the next lesson has those), but the pipeline has stopped just the same. The Try it below gets there fast. One run printed:

```text
using notify()
after 1 s: 5 items moved
stalled after 5 items. Thread states:
  producer-0: WAITING
  producer-1: WAITING
  consumer-0: WAITING
  consumer-1: WAITING
```

Across runs here it stalled after 1 to 5 items. With both signals switched to `notifyAll()`, the same four threads moved about 139,000 items in five seconds and never stalled. Each thread of the wrong kind checks its guard and goes back to waiting, so the right kind always gets a turn. The price is some extra wake-ups, which is cheap next to a stalled pipeline.

**Two kinds of waiters on one monitor need notifyAll(). Wake them all, and let each loop decide.**

`notify()` is safe only when every waiter waits for the same condition and one change lets at most one of them go on. Our unbounded queue from the first two sections qualified: only workers waited, and one payment let one worker go. A bounded queue never does. For a precise wake-up per kind of waiter, give each kind its own `Condition` on a `ReentrantLock`, as lesson 7 of this track shows.

We now have all three pieces: a loop around every `wait()`, a change of state before every signal, and `notifyAll()` when the waiters differ. Let's put them together."""

# ---------------------------------------------------------------- section 3
S3 = """Put the three pieces together and you get the class you'll write in the lab: a **bounded buffer**, which is the settlement queue with a capacity. The Kafka thread waits in `put()` when the workers fall behind, and the workers wait in `take()` when there's nothing to settle:

""" + pair(BUFFER, KBUFFER) + """

`put()` and `take()` have the same three parts. The **guard** is the `while` loop that waits until the method can go on. The **act** changes the queue, safely, because the condition holds and the lock is held. The **signal** wakes the other side, because the state it waits on just changed. Read `put()` aloud and it says: while there's no room, wait; add the item; tell everyone something changed.

Three smaller choices are deliberate, and each comes from an earlier lesson. The lock is a private object, as synchronized and intrinsic locks recommended, so only the buffer can wait on it or signal it. Both methods signal with `notifyAll()`, because producers and consumers share one wait set. And both declare `throws InterruptedException`. The buffer can't know what its caller wants to do about an interrupt, so it lets the exception propagate, one of the two good answers from A thread's life.

Now the honest part. In production you won't write this class: `ArrayBlockingQueue` does the same job, with timeouts, and lesson 9 of this track covers it. Our buffer also has a cost built in. With one wait set, every `notifyAll()` wakes producers and consumers alike, and most of them check their guard and go straight back to waiting. A `Condition` gives one lock a separate wait set per condition, and lesson 7 of this track builds on that.

Why build it, then? Because you meet guarded blocks every day, inside libraries. A connection pool with 20 connections makes the 21st request wait. A `KafkaProducer` blocks `send()` for up to `max.block.ms` when its buffer is full. In a thread dump, those threads show `WAITING` or `TIMED_WAITING` inside the library's code. Once you've written `put()` and `take()` yourself, the stack tells you which condition they wait for.

Check your model before you start the lab. Delete the `notifyAll()` in `take()`. Two producers fill a buffer of capacity 2 and then wait in `put()`. A consumer takes one item. What happens next? (The producers stay in `wait()`: the take made room, but nothing woke them. The consumers drain the buffer and then wait too, until every thread is waiting.)"""

L = {
 "id": "conc-05",
 "title": "wait, notify and guarded blocks",
 "minutes": 35,
 "goal": "By the end you can write a guarded block with `wait()` in a `while` loop, choose between `notify()` and `notifyAll()`, and build a bounded buffer from scratch.",
 "opening": OPENING,
 "warmup": {
  "q": "Two settlement workers wait on an empty queue with `if (queue.isEmpty()) lock.wait(); return queue.removeFirst();`. The Kafka thread adds one payment and calls `notifyAll()`. What happens?",
  "options": ["One worker gets the payment and the other keeps waiting", "Both wake; one gets the payment and the other throws NoSuchElementException", "notifyAll() wakes only one of them, so nothing goes wrong", "Both get the same payment"],
  "answer": 1,
  "why": "`notifyAll()` wakes both workers, and they take the lock back one at a time. The first one takes the payment. The second one checked its `if` before it went to sleep, so it calls `removeFirst()` on an empty queue. With `while` instead of `if`, it would check again and go back to waiting. The second section runs exactly this program."
 },
 "sections": [
  {
   "h": "Waiting for the queue without spinning: the guarded block",
   "body": S0,
   "aside": ASIDE0,
   "figure": {"svg": FIG, "caption": "wait() moves the owner to the wait set and gives the lock back. notify moves a waiter back to the entry set, where it must win the lock again, so it must re-check its condition."},
   "try": {
    "title": "Spin vs wait",
    "minutes": 4,
    "steps": [
     "Read `BusyWaitDemo`. Both threads wait one second for the same event: the spinner checks a `volatile` flag, and the waiter sits in a guarded block. Write down your guess for each thread's CPU time.",
     "Run it and compare.",
     "In the waiter, delete the `synchronized` line around the `while` loop and its closing brace, so `lock.wait()` runs without the lock. Predict what happens, run it, then put the lines back."
    ],
    "code": {"lang": "java", "title": "BusyWaitDemo.java", "src": read(f"{lab}/demo/{P}/BusyWaitDemo.java"),
             "run": demo("BusyWaitDemo"), "file": f"{lab}/demo/{P}/BusyWaitDemo.java", "alt": kt("BusyWaitDemo")},
    "expect": "The spinner uses about a full second of CPU to wait one second (runs here printed 1,022 to 1,037 ms). The waiter uses 0 ms. Without the `synchronized` block, the waiter dies at once with `IllegalMonitorStateException`: you can only wait on a monitor you hold."
   }
  },
  {
   "h": "A second worker, and why every wait sits in a while loop",
   "body": S1,
   "try": {
    "title": "Steal a wake-up",
    "minutes": 4,
    "steps": [
     "Read `IfInsteadOfWhile`. Both consumers are parked in `wait()` before main adds one item and calls `notifyAll()`.",
     "Run it and read both consumers' lines.",
     "Change `if (queue.isEmpty())` to `while (queue.isEmpty())`. Write down what you expect each consumer to print, then run it again."
    ],
    "code": {"lang": "java", "title": "IfInsteadOfWhile.java", "src": read(f"{lab}/demo/{P}/IfInsteadOfWhile.java"),
             "run": demo("IfInsteadOfWhile"), "file": f"{lab}/demo/{P}/IfInsteadOfWhile.java", "alt": kt("IfInsteadOfWhile")},
    "expect": "With `if`: one consumer takes `auth-1` and the other fails with `java.util.NoSuchElementException`. With `while`: one consumer takes `auth-1`, the other checks again and goes back to waiting, main prints `one consumer is still waiting; giving it a second item`, and that consumer takes `auth-2`. Which consumer wins can change from run to run."
   }
  },
  {
   "h": "A limit on the queue, and why notify() can stall it",
   "body": S2,
   "try": {
    "title": "Stall a pipeline with notify()",
    "minutes": 3,
    "steps": [
     "Run `NotifyStall`. Two producers and two consumers share a one-slot buffer, and every signal is a `notify()`.",
     "When progress stops, read the thread states it prints and match them against the four steps in this section.",
     "Predict whether it stalls with `notifyAll()`. Then run it again with `-Pargs=all`, which switches both signals to `notifyAll()`."
    ],
    "code": {"lang": "java", "title": "NotifyStall.java", "src": read(f"{lab}/demo/{P}/NotifyStall.java"),
             "run": demo("NotifyStall"), "file": f"{lab}/demo/{P}/NotifyStall.java", "alt": kt("NotifyStall")},
    "expect": "With `notify()` it stalls almost at once (after 1 to 5 items in runs here), with all four threads `WAITING`. With `notifyAll()` it never stalls, and moves roughly 28,000 items a second for the full five seconds. Your counts will differ. On a rare run `notify()` survives the five seconds; run it again and it won't be so lucky."
   }
  },
  {
   "h": "The bounded buffer, built by hand, and where it stops",
   "body": S3
  }
 ],
 "compare": {
  "title": "A guarded buffer in Java and Kotlin",
  "java": {"title": "BoundedBuffer.java", "src": BUFFER},
  "kotlin": {"title": "KotlinGuarded.kt", "src": read(f"{lab}/demo/{K}/KotlinGuarded.kt")},
  "note": "Both versions are the same guarded buffer: the same `while` guard, the same act, and the same signal to every waiter. Three things changed in the Kotlin one. `lock.withLock { }` takes and releases a `ReentrantLock` where Java writes `synchronized`. `changed.await()` stands in for `wait()`. And `changed.signalAll()` stands in for `notifyAll()`. The Java version uses the monitor that every object has carried since Java 1.0, and it needs nothing else. The Kotlin version reaches for a `Condition` because Kotlin's `Any` doesn't expose `wait()`. The rules don't change with the tool: `Condition` allows spurious wakeups too, so the `while` stays. What the `Condition` adds is room to grow, because one lock can have several conditions, so producers and consumers could wait separately. Lesson 7 of this track builds exactly that."
 },
 "worked": {
  "title": "Wait for a settlement file, with a deadline",
  "steps": [
   {"say": "A batch job must wait until the card network's settlement file has arrived, and give up after 30 seconds. Here is the first attempt. Before you read on, find what can go wrong.",
    "code": "boolean awaitFile() throws InterruptedException {\n    synchronized (lock) {\n        if (!fileArrived) lock.wait(30_000);\n        return fileArrived;\n    }\n}", "lang": "java",
    "alt_code": "fun awaitFile(): Boolean {\n    synchronized(lock) {\n        if (!fileArrived) lock.wait(30_000)\n        return fileArrived\n    }\n}", "alt_lang": "kotlin"},
   {"say": "It's the `if` bug in a new shape. A spurious wakeup, or a `notifyAll()` meant for some other condition on the same lock, makes `wait()` return early with `fileArrived` still false: after 2 seconds, say, instead of 30. Just moving `wait(30_000)` into a `while` loop is wrong too, because every wake-up would start a fresh 30 seconds. The fix is to fix the deadline once and wait only for what's left of it.",
    "code": "", "lang": ""},
   {"say": "The guard loop now checks two things: the condition and the clock. Each pass waits only for the time that's left.",
    "code": "boolean awaitFile(Duration timeout) throws InterruptedException {\n    long deadline = System.nanoTime() + timeout.toNanos();     // 1. fix the deadline once\n    synchronized (lock) {\n        while (!fileArrived) {                                  // 2. guard on the condition\n            long leftMillis = (deadline - System.nanoTime()) / 1_000_000;\n            if (leftMillis <= 0) return false;                  // 3. out of time\n            lock.wait(leftMillis);                              // 4. wait only for what's left\n        }\n        return true;\n    }\n}", "lang": "java",
    "alt_code": "fun awaitFile(timeout: Duration): Boolean {\n    val deadline = System.nanoTime() + timeout.toNanos()     // 1. fix the deadline once\n    synchronized(lock) {\n        while (!fileArrived) {                                // 2. guard on the condition\n            val leftMillis = (deadline - System.nanoTime()) / 1_000_000\n            if (leftMillis <= 0) return false                 // 3. out of time\n            lock.wait(leftMillis)                             // 4. wait only for what's left\n        }\n        return true\n    }\n}", "alt_lang": "kotlin"},
   {"say": "The thread that receives the file sets the state before it signals, both under the lock, just as the Kafka thread did. If it runs before anyone waits, nothing is lost: the waiter sees `fileArrived` and never calls `wait()`. One question before the last step: why does the waiter use `System.nanoTime()` and not `System.currentTimeMillis()`?",
    "code": "void onFileArrived() {\n    synchronized (lock) {\n        fileArrived = true;      // state first\n        lock.notifyAll();        // then the signal\n    }\n}", "lang": "java",
    "alt_code": "fun onFileArrived() {\n    synchronized(lock) {\n        fileArrived = true      // state first\n        lock.notifyAll()        // then the signal\n    }\n}", "alt_lang": "kotlin"},
   {"say": "`nanoTime()` only ever moves forward, so it measures elapsed time. `currentTimeMillis()` is wall-clock time, and NTP can move it backwards or forwards, which would stretch or cut the timeout.",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Build a bounded buffer with wait and notifyAll",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/BoundedBuffer.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l05.*'",
  "steps": [
   "Run the tests. All six fail, some only after a few seconds, because the threads that should wait die instead.",
   "Add the fields: a private lock object, an `ArrayDeque` for the items, the capacity. Reject a capacity below 1 in the constructor.",
   "Write `put`: guard with `while (full) lock.wait();`, add at the tail, then `notifyAll()`.",
   "Write `take`: guard with `while (empty) lock.wait();`, remove the head, `notifyAll()`, and return it. Write `size()` under the lock.",
   "Run the tests until all six pass, then twice more. The test with four producers and four consumers is the one that catches `if` and `notify()` mistakes."
  ],
  "hints": [
   "The blocking tests poll `getState()` until it says `WAITING`. A thread that sleeps in a loop shows `TIMED_WAITING` and fails them. Use `wait()` with no timeout.",
   "Call `wait()` and `notifyAll()` on the same object you synchronize on. Calling `wait()` on `this` while holding `lock` throws `IllegalMonitorStateException`.",
   "Don't catch `InterruptedException` inside the buffer. Let it propagate: both methods already declare it."
  ],
  "done_when": "All six tests in `BoundedBufferTest` pass, three runs in a row."
 },
 "drill": {
  "title": "A bounded buffer from memory",
  "minutes": 6,
  "prompt": "Close this page and the lab. In a blank file, write a bounded buffer of `String` with `put` and `take`, using `synchronized`, `wait` and `notifyAll`. Then check your work: is every `wait()` inside a `while`? Do both methods signal? Did you lock on a private object?",
  "answer": {"lang": "java", "src": BUFFER, "alt": {"lang": "kotlin", "title": "Kotlin", "src": KBUFFER}}
 },
 "recap": [
  "A guarded block holds the lock, checks a condition, and calls `wait()` until the condition holds. `wait()` gives the monitor back while it waits and takes it again before it returns.",
  "Call `wait()`, `notify()` or `notifyAll()` only while holding that object's monitor, or you get `IllegalMonitorStateException`.",
  "Always `while (!condition) wait();`. Another woken thread may change the state before you get the lock back, and spurious wakeups are allowed.",
  "Change the state, then notify. Wait for a state, never for a bare signal, so an early notification is never lost.",
  "`notify()` wakes one waiter of the JVM's choosing. With two kinds of waiters on one monitor it can wake the wrong kind and stall everything, so default to `notifyAll()`.",
  "The limit: a monitor has one wait set, so every `notifyAll()` wakes every kind of waiter. A `Condition` gives each kind its own (lesson 7), and `ArrayBlockingQueue` does the whole job for you (lesson 9)."
 ],
 "closing": "We started with a settlement worker that had nothing to do but wait. We gave it a guarded block, a `while` loop for the second worker and `notifyAll()` for the bounded queue, and built the buffer that holds all three.\n\nNow search your own code for `.wait(` and `.await(`. Each one should sit in a `while` loop that tests a state. An `if`, or a wait with no condition, is a bug waiting for its first busy evening.\n\nHere, the stalled threads waited with the lock free. Next, we'll meet threads that stop while holding locks: two ledger transfers, each holding one account and waiting for the other. How does that happen, and how do you make sure it can't?",
 "quiz": [
  {"q": "What happens when this runs on its own?\n\n```java\nObject lock = new Object();\nlock.notifyAll();\n```",
   "options": ["Nothing, since nobody is waiting", "It wakes every thread in the JVM that is waiting on any lock", "It throws IllegalMonitorStateException, because the thread doesn't hold lock's monitor", "It blocks until some thread waits on lock"],
   "answer": 2, "why": "`wait`, `notify` and `notifyAll` need the caller to own the object's monitor, so they belong inside `synchronized (lock)`. The JVM checks ownership first, so it doesn't matter that nobody is waiting. \"Nothing\" would be the right answer for the same call made inside the lock."},
  {"q": "A thread wakes up from `lock.wait()` because another thread called `notifyAll()`. When does it run the line after `wait()`?",
   "options": ["Immediately, in parallel with the notifier", "After it gets the monitor back, which is at the earliest when the notifier leaves its synchronized block", "Only after every other woken thread has finished", "Never: it has to call wait() again"],
   "answer": 1, "why": "`notifyAll()` doesn't release the lock. The woken thread moves to the entry set and competes for the monitor, and `wait()` returns only once this thread owns it again. Running \"immediately\" would put two threads inside one monitor, which a monitor never allows. Other woken threads may get the lock first and change the state, which is why the guard checks again."},
  {"q": "A one-slot buffer has 2 producers and 2 consumers, and both `put` and `take` call `notify()`. Each `wait()` is correctly inside a `while`. What can happen?",
   "options": ["Nothing bad, because the while loops make it safe", "Two consumers take the same item", "IllegalMonitorStateException", "All four threads end up waiting with nobody left to notify them"],
   "answer": 3, "why": "The `while` loops stop a thread from acting on a false condition. They can't bring back a signal that went to the wrong thread. If a consumer's `notify()` wakes the other consumer instead of a producer, that wake-up is wasted, and soon every thread waits. `notifyAll()`, or one `Condition` per kind of waiter, fixes it."},
  {"q": "A worker calls `lock.wait()` with no condition, \"until the report is done\". The reporting thread calls `lock.notifyAll()` when it finishes. Sometimes the worker waits forever. Why?",
   "options": ["notifyAll() only wakes threads that started waiting before it was called, so an early report is a lost wake-up", "wait() without a timeout is not allowed", "notifyAll() needs a second call to wake a thread", "The worker must call notify() itself"],
   "answer": 0, "why": "A notification wakes only threads that are already waiting. If the report finishes first, the signal goes nowhere, and the worker then waits for a signal that already happened. Wait for a state instead: `while (!done) lock.wait();`, with `done = true` set before `notifyAll()`. A timeout would only hide the bug."},
  {"q": "From A thread's life: a consumer is parked inside `lock.wait()` and another thread interrupts it. Which is true?",
   "options": ["wait() returns normally and the interrupt flag stays set", "wait() throws InterruptedException at once, without retaking the monitor", "Nothing happens until someone calls notify()", "wait() retakes the monitor, then throws InterruptedException with the interrupt flag cleared"],
   "answer": 3, "why": "Like `sleep`, `wait` reacts to an interrupt by throwing `InterruptedException` and clearing the flag. It takes the monitor back first, so your catch or finally block still runs inside the synchronized block. The tempting \"at once\" answer misses that step: `wait()` never returns or throws without the lock. Restore the flag or let the exception propagate.",
   "from": "conc-02"}
 ],
 "flashcards": [
  {"front": "What three things does `lock.wait()` do?", "back": "It releases lock's monitor, parks the thread in the wait set (WAITING), and retakes the monitor before it returns."},
  {"front": "Why must `wait()` always sit inside `while (!condition)`?", "back": "Another woken thread may change the state before you get the lock back, and spurious wakeups are allowed."},
  {"front": "What happens if you call `wait()` or `notify()` without holding that object's monitor?", "back": "`IllegalMonitorStateException`, at once."},
  {"front": "Does `notifyAll()` release the lock?", "back": "No. The woken threads compete for the monitor after the notifier leaves its synchronized block."},
  {"front": "When is `notify()` safe to use instead of `notifyAll()`?", "back": "Only when every waiter waits for the same condition and each change lets at most one waiter proceed."},
  {"front": "What is a lost wake-up?", "back": "A notify that happens before anyone waits. If the waiter has no condition to check, it then waits forever. Fix: wait for a state field, set before notifying."}
 ],
 "terms": [
  {"term": "Busy wait", "plain": "Waiting by checking a condition over and over in a loop. The thread stays RUNNABLE and keeps a core busy."},
  {"term": "Guarded block", "plain": "Code that waits, under a lock, until a condition holds: `while (!cond) lock.wait();`."},
  {"term": "Wait set", "plain": "The threads parked in `wait()` on one monitor, waiting to be notified."},
  {"term": "Entry set", "plain": "The threads waiting to enter a monitor (BLOCKED), including woken threads that must win the lock back."},
  {"term": "Spurious wakeup", "plain": "A return from `wait()` with no notify, interrupt or timeout. Allowed by the spec."},
  {"term": "Lost wake-up", "plain": "A signal sent before anyone waits for it, so the waiter never hears it."},
  {"term": "Backpressure", "plain": "Making a fast producer wait when the consumer can't keep up, instead of buffering without limit."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why a bounded buffer built on one monitor needs `while` loops and `notifyAll()`, and what goes wrong if you use `if` or `notify()` instead.",
  "answer": "Producers wait for \"not full\" and consumers wait for \"not empty\", but with one monitor they share one wait set. When a thread wakes, the state may already have changed again, because other woken threads can get the lock first, and spurious wakeups are allowed. So each waiter must check its condition again in a `while` loop. With `if`, a consumer can wake up and remove from an empty buffer. `notify()` wakes one waiter of the JVM's choosing, which may be the wrong kind: a consumer waking another consumer wastes the only signal, and soon every thread waits with nobody left to wake them. `notifyAll()` wakes everyone, and the loops send the ones that can't go on back to waiting."
 },
 "deeper": {
  "minutes": 8,
  "body": "Timed waits are the same idea with a clock. `wait(millis)` returns when it's notified, interrupted, woken spuriously, or when the time is up, and it doesn't tell you which. That's why the worked example tracks its own deadline with `System.nanoTime()`.\n\nThe JVM has had bugs here too. JDK 26 carries a fix titled \"Notification can be lost due to interrupt in Object.wait\". That's one more reason to use the standard library's queues and synchronizers wherever you can: they are tested far harder than any guarded block you or I will write.\n\nTwo notes on observing waits. JFR has a `jdk.JavaMonitorWait` event, with the monitor's class, the thread that notified, the timeout and whether it timed out, and JDK 25 added a `jdk.JavaMonitorNotify` event. And on virtual threads, `Object.wait()` used to pin the carrier thread. Since JDK 24 (JEP 491) it no longer does in most cases.\n\nFinally, the history. `wait` and `notify` have been in Java since 1.0. `java.util.concurrent` arrived in Java 5 with `Condition`, `BlockingQueue` and friends, built by Doug Lea on a framework called `AbstractQueuedSynchronizer`. Read the source of `ArrayBlockingQueue` and you'll find the same guard, act and signal as in this lesson, written with a `ReentrantLock` and two `Condition`s."
 },
 "sources": [
  {"title": "Object.wait and notify (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Object.html"},
  {"title": "Object.java at jdk-25-ga (wait() Javadoc on spurious wakeups)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/lang/Object.java"},
  {"title": "Guarded blocks (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/essential/concurrency/guardmeth.html"},
  {"title": "Java Concurrency in Practice, Goetz et al., section 14.2, Condition queues", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/conc-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
