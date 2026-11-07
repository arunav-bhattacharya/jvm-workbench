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

L = {
 "id": "conc-05",
 "title": "wait, notify and guarded blocks",
 "minutes": 35,
 "goal": "By the end you can write a guarded block with `wait()` in a `while` loop, choose between `notify()` and `notifyAll()`, and build a bounded buffer from scratch.",
 "warmup": {
  "q": "Two consumers wait on an empty queue with `if (queue.isEmpty()) lock.wait(); return queue.removeFirst();`. A producer adds one item and calls `notifyAll()`. What happens?",
  "options": ["One consumer gets the item and the other keeps waiting", "Both wake; one gets the item and the other throws NoSuchElementException", "notifyAll() wakes only one of them, so nothing goes wrong", "Both get the same item"],
  "answer": 1,
  "why": "`notifyAll()` wakes both. They get the lock back one at a time. The first takes the item. The second is already past its `if`, so it calls `removeFirst()` on an empty queue. With `while` instead of `if`, the second would check again and go back to waiting."
 },
 "sections": [
  {
   "h": "A guarded block waits for a condition without burning a core",
   "body": "A consumer thread has nothing to do until a payment arrives. The worst way to wait is to spin:\n\n```java\nwhile (!ready) { }     // checks the flag as fast as the core can go\n```\n\n```kotlin\nwhile (!ready) { }     // the same spin in Kotlin\n```\n\nThe demo below measured it. To wait one second, the spinning thread used about 1,026 ms of CPU: a whole core, doing nothing useful. The thread that waited properly used 0 ms. (The spinner's flag also has to be `volatile`, or the JIT may read it once and loop forever. The memory model track explains why.)\n\nThe proper way is a **guarded block**. You hold the lock, check the condition, and call `wait()` if it doesn't hold yet:\n\n```java\nsynchronized (lock) {\n    while (!ready) {\n        lock.wait();      // give back the lock, sleep until woken, take the lock again\n    }\n    // here ready is true, and we hold the lock\n}\n```\n\n```kotlin\nsynchronized(lock) {   // lock is a java.lang.Object here: Kotlin's Any has no wait()\n    while (!ready) {\n        lock.wait()       // give back the lock, sleep until woken, take the lock again\n    }\n    // here ready is true, and we hold the lock\n}\n```\n\n`wait()` does three things in order. It releases the monitor, so other threads can get in and change the state. It parks the thread in the monitor's **wait set**, in the WAITING state, using no CPU. And when the thread is woken, it takes the monitor back before `wait()` returns.\n\nThe thread that changes the state calls `notifyAll()`, holding the same lock:\n\n```java\nsynchronized (lock) {\n    ready = true;\n    lock.notifyAll();     // wake every thread waiting on lock\n}\n```\n\n```kotlin\nsynchronized(lock) {\n    ready = true\n    lock.notifyAll()      // wake every thread waiting on lock\n}\n```\n\n`notifyAll()` does not hand over the lock. The woken threads move to the monitor's entry set, the threads waiting to get in, where they show as `BLOCKED` and compete for the lock like any newcomer. None of them can run until the notifier leaves its block.\n\nYou must hold the monitor of the object you call `wait()` or `notifyAll()` on. Call them outside `synchronized (lock)` and you get `IllegalMonitorStateException` at once. That rule protects you. The condition can only change while someone holds the lock, so a waiter can't check the flag, miss the change that happens next, and then wait forever.",
   "try": {
    "title": "Spin vs wait",
    "minutes": 4,
    "steps": [
     "Run `BusyWaitDemo`. Both threads wait one second for the same event. Predict the CPU time of each.",
     "In the waiter, delete the `synchronized` line around the `while` loop and its closing brace, so `lock.wait()` runs without the lock. Run it again.",
     "Put it back."
    ],
    "code": {"lang": "java", "title": "BusyWaitDemo.java", "src": read(f"{lab}/demo/{P}/BusyWaitDemo.java"),
             "run": demo("BusyWaitDemo"), "file": f"{lab}/demo/{P}/BusyWaitDemo.java", "alt": kt("BusyWaitDemo")},
    "expect": "The spinner uses about a full second of CPU to wait one second. The waiter uses close to zero. Without the `synchronized` block, the waiter dies at once with `IllegalMonitorStateException`: you can only wait on a monitor you hold."
   }
  },
  {
   "h": "Always wait in a while loop, never an if",
   "body": "When `wait()` returns, the condition you waited for may not hold. There are two reasons.\n\nThe first is in the Javadoc for `Object.wait`: \"A thread can wake up without being notified, interrupted, or timing out, a so-called spurious wakeup.\" It is rare. It is also allowed, and the Javadoc tells you to test the condition again and keep waiting if it is not met.\n\nThe second reason happens all the time. `notifyAll()` wakes every waiter, but they take the lock back one at a time, and other threads may get in first. Two consumers wait on an empty queue. A producer adds one item and calls `notifyAll()`. Consumer 1 gets the lock first and takes the item. Consumer 2 gets the lock next, and the queue is empty again. If consumer 2 checked with `if`, it is already past its check:\n\n```java\nif (queue.isEmpty()) lock.wait();   // checked once, before waiting\nreturn queue.removeFirst();         // NoSuchElementException\n```\n\n```kotlin\nif (queue.isEmpty()) lock.wait()    // checked once, before waiting\nreturn queue.removeFirst()          // NoSuchElementException\n```\n\nWith `while`, consumer 2 checks again, sees the empty queue and goes back to waiting. That is all a guarded block is: a `while` loop around `wait()`, with the condition as the loop test.\n\nThe habit costs nothing, so make it unconditional. Every `wait()` sits inside `while (!condition)`. In a code review, treat an `if` around `wait()` as a bug, even in code that has never failed. It has just never had two waiters at the same time yet.",
   "try": {
    "title": "Steal a wake-up",
    "minutes": 4,
    "steps": [
     "Read `IfInsteadOfWhile`. Both consumers are parked before main adds one item and calls `notifyAll()`.",
     "Run it and read both consumers' lines.",
     "Change `if (queue.isEmpty())` to `while (queue.isEmpty())`. Predict what each consumer prints, then run it again."
    ],
    "code": {"lang": "java", "title": "IfInsteadOfWhile.java", "src": read(f"{lab}/demo/{P}/IfInsteadOfWhile.java"),
             "run": demo("IfInsteadOfWhile"), "file": f"{lab}/demo/{P}/IfInsteadOfWhile.java", "alt": kt("IfInsteadOfWhile")},
    "expect": "With `if`: one consumer takes `auth-1`, the other fails with `java.util.NoSuchElementException`. With `while`: one takes `auth-1`, the other re-checks, waits again, and takes `auth-2` when main gives it a second item. Which consumer wins can change from run to run."
   }
  },
  {
   "h": "Prefer notifyAll, because notify wakes one thread, maybe the wrong one",
   "body": "`notify()` wakes one thread from the wait set, and you don't get to choose which. That is fine when every waiter waits for the same condition and any one of them can use the change. It breaks when one monitor has waiters for different conditions.\n\nA bounded buffer is the classic case. Producers wait for \"not full\", consumers wait for \"not empty\", and with a plain monitor they share one wait set. Picture a buffer with one slot, two producers and two consumers, all using `notify()`:\n\n1. The slot is empty, so both consumers wait.\n2. Producer 1 fills the slot and wakes consumer 1. Before consumer 1 gets the lock, both producers find the slot full and wait. The wait set now holds producer 1, producer 2 and consumer 2.\n3. Consumer 1 empties the slot and calls `notify()`, which happens to wake consumer 2, the wrong kind.\n4. Consumer 2 finds the slot empty and waits again. Consumer 1 loops, finds it empty too, and waits.\n\nNow all four threads wait for a signal nobody will send. No thread holds the lock, so it isn't a deadlock in the textbook sense, but the program has stopped just the same. The demo below gets there within a handful of items.\n\nSo the default is `notifyAll()`. It wakes every waiter, each one re-checks its own condition in its `while` loop, and the ones that can't go on wait again. The price is extra wake-ups when many threads wait, which rarely matters next to a stalled pipeline.\n\nUse `notify()` only when both of these hold: every waiter waits for the same condition, and one change lets at most one of them proceed. If you need precise wake-ups for two kinds of waiters, give each kind its own `Condition` on a `ReentrantLock`. That is lesson 7 of this track.",
   "try": {
    "title": "Stall a pipeline with notify()",
    "minutes": 3,
    "steps": [
     "Run `NotifyStall`. Two producers and two consumers share a one-slot buffer that signals with `notify()`.",
     "Read the thread states it prints when progress stops.",
     "Run it again with `-Pargs=all`, which switches both signals to `notifyAll()`."
    ],
    "code": {"lang": "java", "title": "NotifyStall.java", "src": read(f"{lab}/demo/{P}/NotifyStall.java"),
             "run": demo("NotifyStall"), "file": f"{lab}/demo/{P}/NotifyStall.java", "alt": kt("NotifyStall")},
    "expect": "With `notify()` it stalls almost at once (runs here stopped after 2 or 3 items) with all four threads `WAITING`. With `notifyAll()` it moves tens of thousands of items a second for the full five seconds."
   }
  },
  {
   "h": "A bounded buffer, by hand",
   "body": "Put the three rules together and you get the bounded buffer you'll write in the lab. A bounded buffer sits between producers and consumers. It holds at most `capacity` items, so a fast producer has to wait for slow consumers instead of filling the heap. That waiting is called **backpressure**.\n\n```java\n" + BUFFER + "\n```\n\n```kotlin\n" + KBUFFER + "\n```\n\nEach method has the same three parts. The **guard** is a `while` loop that waits until the method can proceed. The **act** changes the state, safely, because the condition holds and the lock is held. The **signal** wakes the other side, because the state they wait on just changed.\n\nA few choices in there are deliberate.\n\nThe lock is a private object, not `this`. Any code that can reach an object can call `wait()` or `notify()` on it. With a private lock, only the buffer can signal its own waiters.\n\nBoth methods signal with `notifyAll()`, because producers and consumers share one wait set, as the previous section showed.\n\nBoth methods declare `throws InterruptedException`. `wait()` throws it when the waiting thread is interrupted, and the buffer can't know what the caller wants to do about that, so it lets the caller decide. That is the second option from lesson 2 of this track: propagate.\n\nIn production you won't write this class. `ArrayBlockingQueue` does the same job, faster and with timeouts, and lesson 9 of this track covers it. You write it once so that `put` and `take` stop being magic, and so that a thread dump full of threads waiting inside a queue makes sense to you.\n\nCheck your model before the lab. Delete the `notifyAll()` in `take()`. Two producers fill a buffer of capacity 2 and then wait in `put()`. A consumer takes one item. What happens next? (The producers stay in `wait()`: the take made room, but nothing woke them. The consumers drain the buffer and then wait too, until every thread is waiting.)",
   "figure": {"svg": FIG, "caption": "wait() moves the owner to the wait set and gives the lock back. notify moves a waiter back to the entry set, where it must win the lock again, so it must re-check its condition."}
  }
 ],
 "analogy": "A monitor is a meeting room with one key. People who want the room queue in the corridor (the entry set, BLOCKED). The one inside can decide they can't continue yet, hang the key back up and go to the lounge next door (the wait set, WAITING). When someone in the room changes things, they can call into the lounge: `notify()` sends one person back to the corridor, `notifyAll()` sends everyone. Nobody walks from the lounge straight into the room. They queue for the key again, and by the time they get in, the thing they waited for may be gone, which is why they must look again. The analogy breaks at spurious wakeups: people don't leave the lounge for no reason, but a Java thread is allowed to.",
 "in_your_world": "You'll rarely hand-write `wait()` in a payments service, and when you do it should look like the buffer above. You meet guarded blocks all the time inside libraries. A connection pool with 20 connections makes the 21st request wait until a connection is returned. A `KafkaProducer` blocks `send()` for up to `max.block.ms` when its buffer memory is full. A Quarkus worker pool queues requests when every worker is busy. In a thread dump those threads show WAITING or TIMED_WAITING inside the library's code. Reading the stack tells you which condition they wait for, and that usually tells you which resource ran out.",
 "mistake": "The most common real mistake is using `wait()` and `notify()` as a bare signal, with no condition to check: one thread calls `lock.wait()` \"until the result is ready\", another calls `lock.notify()` when it is. If the notify happens before the waiter starts waiting, the signal is lost and the waiter sleeps forever. This is a lost wake-up. It passes tests because the waiter usually gets there first. The fix is to always wait for a state, never for an event: set a field such as `ready = true` under the lock before notifying, and wait with `while (!ready) lock.wait();`. A notify that came early is then harmless, because the waiter sees `ready` and never waits.",
 "compare": {
  "title": "A guarded buffer in Java and Kotlin",
  "java": {"title": "BoundedBuffer.java", "src": BUFFER},
  "kotlin": {"title": "KotlinGuarded.kt", "src": read(f"{lab}/demo/{K}/KotlinGuarded.kt")},
  "note": "Kotlin's `Any` does not expose `wait()`, `notify()` or `notifyAll()`. The Kotlin samples in this lesson get them by using a `java.lang.Object` as the lock, which works but earns a compiler warning that you have to suppress. The idiomatic replacement is a `ReentrantLock` with a `Condition`: `withLock { }` takes and releases the lock, `await()` plays the part of `wait()`, and `signalAll()` the part of `notifyAll()`. The rules don't change. `Condition` allows spurious wakeups too, so you still wait in a `while` loop. As a bonus, one lock can have several conditions, so producers and consumers can wait separately. Lesson 7 of this track builds on exactly that."
 },
 "worked": {
  "title": "Wait for a settlement file, with a deadline",
  "steps": [
   {"say": "A batch job must wait until the settlement file has arrived, but give up after 30 seconds. Here is the first attempt. What can go wrong?",
    "code": "boolean awaitFile() throws InterruptedException {\n    synchronized (lock) {\n        if (!fileArrived) lock.wait(30_000);\n        return fileArrived;\n    }\n}", "lang": "java",
    "alt_code": "fun awaitFile(): Boolean {\n    synchronized(lock) {\n        if (!fileArrived) lock.wait(30_000)\n        return fileArrived\n    }\n}", "alt_lang": "kotlin"},
   {"say": "It is the `if` bug in a new shape. A spurious wakeup, or a `notifyAll()` meant for some other condition on the same lock, returns early with `fileArrived` still false, after 2 seconds instead of 30. Simply putting `wait(30_000)` in a `while` loop is wrong too: every wake-up would start a fresh 30 seconds. The fix is to compute a deadline once and wait for what is left of it.",
    "code": "", "lang": ""},
   {"say": "The guard loop now checks the condition and the clock. Each pass waits only for the remaining time.",
    "code": "boolean awaitFile(Duration timeout) throws InterruptedException {\n    long deadline = System.nanoTime() + timeout.toNanos();     // 1. fix the deadline once\n    synchronized (lock) {\n        while (!fileArrived) {                                  // 2. guard on the condition\n            long leftMillis = (deadline - System.nanoTime()) / 1_000_000;\n            if (leftMillis <= 0) return false;                  // 3. out of time\n            lock.wait(leftMillis);                              // 4. wait only for what's left\n        }\n        return true;\n    }\n}", "lang": "java",
    "alt_code": "fun awaitFile(timeout: Duration): Boolean {\n    val deadline = System.nanoTime() + timeout.toNanos()     // 1. fix the deadline once\n    synchronized(lock) {\n        while (!fileArrived) {                                // 2. guard on the condition\n            val leftMillis = (deadline - System.nanoTime()) / 1_000_000\n            if (leftMillis <= 0) return false                 // 3. out of time\n            lock.wait(leftMillis)                             // 4. wait only for what's left\n        }\n        return true\n    }\n}", "alt_lang": "kotlin"},
   {"say": "The side that receives the file sets the state before it signals, both under the lock. If it runs before anyone waits, nothing is lost: the waiter sees `fileArrived` and never calls `wait()`. Why does the waiter use `System.nanoTime()` and not `System.currentTimeMillis()`?",
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
   "Write `put`: guard with `while (full) lock.wait();`, add at the tail, `notifyAll()`.",
   "Write `take`: guard with `while (empty) lock.wait();`, remove the head, `notifyAll()`, return it. Write `size()` under the lock.",
   "Run the tests until all six pass, then twice more. The 4-producer, 4-consumer test is the one that catches `if` and `notify()` mistakes."
  ],
  "hints": [
   "The blocking tests poll `getState()` until it says WAITING. A thread that sleeps in a loop shows TIMED_WAITING and fails them. Use `wait()` with no timeout.",
   "Call `wait()` and `notifyAll()` on the same object you synchronize on. Calling `wait()` on `this` while holding `lock` throws `IllegalMonitorStateException`.",
   "Don't catch `InterruptedException` inside the buffer. Let it propagate: both methods already declare it."
  ],
  "done_when": "All six tests in `BoundedBufferTest` pass, three runs in a row."
 },
 "drill": {
  "title": "A bounded buffer from memory",
  "minutes": 6,
  "prompt": "Close this page and the lab. In a blank file, write a bounded buffer of `String` with `put` and `take`, using `synchronized`, `wait` and `notifyAll`. Then check: is every `wait()` inside a `while`? Do both methods signal? Did you use a private lock?",
  "answer": {"lang": "java", "src": BUFFER, "alt": {"lang": "kotlin", "title": "Kotlin", "src": KBUFFER}}
 },
 "recap": [
  "A guarded block holds the lock, checks a condition, and calls `wait()` until it holds. `wait()` releases the monitor while it waits and retakes it before returning.",
  "You must hold an object's monitor to call its `wait()`, `notify()` or `notifyAll()`, or you get `IllegalMonitorStateException`.",
  "Always `while (!condition) wait();`. Spurious wakeups are allowed, and another thread may change the state before you get the lock back.",
  "`notify()` wakes one arbitrary waiter. With two kinds of waiters on one monitor it can wake the wrong kind and stall everything. Default to `notifyAll()`.",
  "Wait for a state, not an event: set a field before notifying, so an early signal is never lost."
 ],
 "quiz": [
  {"q": "What happens when this runs on its own?\n\n```java\nObject lock = new Object();\nlock.notifyAll();\n```",
   "options": ["Nothing, since nobody is waiting", "It wakes every thread in the JVM that is waiting on any lock", "It throws IllegalMonitorStateException, because the thread doesn't hold lock's monitor", "It blocks until some thread waits on lock"],
   "answer": 2, "why": "`wait`, `notify` and `notifyAll` require the caller to own the object's monitor, so they must run inside `synchronized (lock)`. It doesn't matter that nobody is waiting. The check comes first."},
  {"q": "A thread wakes up from `lock.wait()` because another thread called `notifyAll()`. When does it run the line after `wait()`?",
   "options": ["Immediately, in parallel with the notifier", "After it gets the monitor back, which is at the earliest when the notifier leaves its synchronized block", "Only after every other woken thread has finished", "Never: it has to call wait() again"],
   "answer": 1, "why": "`notifyAll()` doesn't release the lock. The woken threads move back to competing for the monitor, and `wait()` returns only once this thread owns it again. Other woken threads may get it first and change the state, which is why the condition must be re-checked."},
  {"q": "A one-slot buffer has 2 producers and 2 consumers, and both `put` and `take` call `notify()`. Each `wait()` is correctly inside a `while`. What can happen?",
   "options": ["Nothing bad, because the while loops make it safe", "Two consumers take the same item", "IllegalMonitorStateException", "All four threads end up waiting with nobody left to notify them"],
   "answer": 3, "why": "The `while` loops protect against acting on a false condition, not against lost signals. If a consumer's `notify()` wakes the other consumer instead of a producer, that wake-up is wasted, and soon every thread waits. `notifyAll()`, or one `Condition` per kind of waiter, fixes it."},
  {"q": "A worker calls `lock.wait()` with no condition, \"until the report is done\". The reporting thread calls `lock.notifyAll()` when it finishes. Sometimes the worker waits forever. Why?",
   "options": ["notifyAll() only wakes threads that started waiting before it was called, so an early report is a lost wake-up", "wait() without a timeout is not allowed", "notifyAll() needs a second call to wake a thread", "The worker must call notify() itself"],
   "answer": 0, "why": "A notification wakes only threads that are already waiting. If the report finishes first, the signal goes nowhere, and the worker then waits for a signal that already happened. Wait for a state: `while (!done) lock.wait();`, with `done = true` set before `notifyAll()`."},
  {"q": "From A thread's life: a consumer is parked inside `lock.wait()` and another thread interrupts it. Which is true?",
   "options": ["wait() returns normally and the interrupt flag stays set", "wait() throws InterruptedException at once, without retaking the monitor", "Nothing happens until someone calls notify()", "wait() retakes the monitor, then throws InterruptedException with the interrupt flag cleared"],
   "answer": 3, "why": "Like `sleep`, `wait` reacts to an interrupt by throwing `InterruptedException` and clearing the flag. It retakes the monitor first, so your catch or finally block still runs inside the synchronized block. Restore the flag or let the exception propagate.",
   "from": "conc-02"}
 ],
 "flashcards": [
  {"front": "What three things does `lock.wait()` do?", "back": "It releases lock's monitor, parks the thread in the wait set (WAITING), and retakes the monitor before it returns."},
  {"front": "Why must `wait()` always sit inside `while (!condition)`?", "back": "Spurious wakeups are allowed, and another thread may change the state between the notify and the moment you get the lock back."},
  {"front": "What happens if you call `wait()` or `notify()` without holding that object's monitor?", "back": "`IllegalMonitorStateException`, at once."},
  {"front": "Does `notifyAll()` release the lock?", "back": "No. The woken threads compete for the monitor after the notifier leaves its synchronized block."},
  {"front": "When is `notify()` safe to use instead of `notifyAll()`?", "back": "Only when every waiter waits for the same condition and each change lets at most one waiter proceed."},
  {"front": "What is a lost wake-up?", "back": "A notify that happens before anyone waits. If the waiter has no condition to check, it then waits forever. Fix: wait for a state field, set before notifying."}
 ],
 "terms": [
  {"term": "Guarded block", "plain": "Code that waits, under a lock, until a condition holds: `while (!cond) lock.wait();`."},
  {"term": "Wait set", "plain": "The threads parked in `wait()` on one monitor, waiting to be notified."},
  {"term": "Spurious wakeup", "plain": "A return from `wait()` with no notify, interrupt or timeout. Allowed by the spec."},
  {"term": "notifyAll", "plain": "Wake every thread in the monitor's wait set. They then compete for the lock."},
  {"term": "Lost wake-up", "plain": "A signal sent before anyone waits for it, so the waiter never hears it."},
  {"term": "Backpressure", "plain": "Making a fast producer wait when the consumer can't keep up, instead of buffering without limit."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why a bounded buffer built on one monitor needs `while` loops and `notifyAll()`, and what goes wrong if you use `if` or `notify()` instead.",
  "answer": "Producers wait for \"not full\" and consumers wait for \"not empty\", but with one monitor they share one wait set. When a thread wakes, the state may already have changed again, because other woken threads can get the lock first, and spurious wakeups are allowed. So each waiter must re-check its condition in a `while` loop; with `if`, a consumer can wake up and remove from an empty buffer. `notify()` wakes one arbitrary waiter, which may be the wrong kind: a consumer waking another consumer wastes the only signal, and eventually every thread waits with nobody to wake them. `notifyAll()` wakes everyone, and the loops send the ones that can't proceed back to waiting."
 },
 "deeper": {
  "minutes": 8,
  "body": "Timed waits are the same idea with a clock. `wait(millis)` returns when notified, interrupted, spuriously, or when the time is up, and it does not tell you which. That is why the worked example tracks its own deadline with `System.nanoTime()`.\n\nThe JVM has bugs here too. JDK 26 carries a fix titled \"Notification can be lost due to interrupt in Object.wait\". That is a good reason to use the standard library's queues and synchronizers wherever you can: they are tested far harder than any guarded block you or I will write.\n\nTwo observability notes. JFR has a `jdk.JavaMonitorWait` event, with the monitor's class, the thread that notified, the timeout and whether it timed out, and JDK 25 added a `jdk.JavaMonitorNotify` event. And on virtual threads, `Object.wait()` used to pin the carrier thread. Since JDK 24 (JEP 491) it no longer does in most cases.\n\nFinally, the history. `wait`/`notify` have been in Java since 1.0. `java.util.concurrent` arrived in Java 5 with `Condition`, `BlockingQueue` and friends, built by Doug Lea on a framework called `AbstractQueuedSynchronizer`. When you read the source of `ArrayBlockingQueue`, you'll find the same guard, act and signal parts as in this lesson, written with a `ReentrantLock` and two `Condition`s."
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
