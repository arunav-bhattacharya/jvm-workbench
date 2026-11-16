import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/concurrency/src"
P = "java/workbench/concurrency/l12"
K = "kotlin/workbench/concurrency/l12"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"./gradlew :concurrency:demo -Pmain=workbench.concurrency.l12.{name}"
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
J_ONEPILL = """// Naive: one pill for three cooks
for (Thread w : waiters) w.join();      // every order is on the rail
rail.put(PILL);                          // "kitchen closed"
for (Thread c : cooks) c.join();         // waits for all three cooks"""
K_ONEPILL = """// Naive: one pill for three cooks
waiters.forEach { it.join() }           // every order is on the rail
rail.put(PILL)                           // "kitchen closed"
cooks.forEach { it.join() }              // waits for all three cooks"""

J_PILL = """// each cook
while (true) {
    String ticket = rail.take();          // waits while the rail is empty
    if (ticket == PILL) break;            // identity: a ticket that reads "PILL" is still a ticket
    cook(ticket);
}

// the head chef, after every waiter has finished:
for (int i = 0; i < cooks; i++) rail.put(PILL);   // one pill per cook"""
K_PILL = """// each cook
while (true) {
    val ticket = rail.take()              // waits while the rail is empty
    if (ticket === PILL) break            // identity: a ticket that reads "PILL" is still a ticket
    cook(ticket)
}

// the head chef, after every waiter has finished:
repeat(cooks) { rail.put(PILL) }          // one pill per cook"""

J_ORDER = """int left = seat, right = (seat + 1) % forks.length;
ReentrantLock first = forks[Math.min(left, right)];    // philosopher 4 takes fork 0 first
ReentrantLock second = forks[Math.max(left, right)];"""
K_ORDER = """val left = seat
val right = (seat + 1) % forks.size
val first = forks[minOf(left, right)]     // philosopher 4 takes fork 0 first
val second = forks[maxOf(left, right)]"""
J_WAITER = """Semaphore seats = new Semaphore(forks.length - 1);   // the waiter: one chair short

seats.acquire();
try {
    eatWithBothForks();
} finally {
    seats.release();
}"""
K_WAITER = """val seats = Semaphore(forks.size - 1)                // the waiter: one chair short

seats.acquire()
try {
    eatWithBothForks()
} finally {
    seats.release()
}"""

J_RW = """new ReentrantReadWriteLock();        // non-fair: a new reader waits if a writer is next in line
new ReentrantReadWriteLock(true);    // fair: strict arrival order, less work done per second"""
K_RW = """ReentrantReadWriteLock()        // non-fair: a new reader waits if a writer is next in line
ReentrantReadWriteLock(true)    // fair: strict arrival order, less work done per second"""

J_SHUT = """void closeKitchen() throws InterruptedException {
    open = false;                                      // 1. waiters stop taking new orders
    for (Thread w : waiters) w.join();                 // 2. wait until no waiter can put again
    for (int i = 0; i < cooks.size(); i++) {
        rail.put(PILL);                                // 3. one pill per cook, behind every real ticket
    }
    long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(30);
    for (Thread c : cooks) {
        c.join(Math.max(1, TimeUnit.NANOSECONDS.toMillis(deadline - System.nanoTime())));   // 4. one deadline for all
    }
    for (Thread c : cooks) if (c.isAlive()) c.interrupt();   // 5. still busy: interrupt as a last resort
}"""
K_SHUT = """fun closeKitchen() {
    open = false                                       // 1. waiters stop taking new orders
    waiters.forEach { it.join() }                      // 2. wait until no waiter can put again
    repeat(cooks.size) { rail.put(PILL) }              // 3. one pill per cook, behind every real ticket
    val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(30)
    for (c in cooks) {
        c.join(maxOf(1L, TimeUnit.NANOSECONDS.toMillis(deadline - System.nanoTime())))   // 4. one deadline for all
    }
    cooks.filter { it.isAlive }.forEach { it.interrupt() }   // 5. still busy: interrupt as a last resort
}"""
J_SHUT_BAD = """// Naive: stop now, whatever is on the rail
void closeKitchen() {
    for (Thread c : cooks) c.interrupt();
    for (Thread w : waiters) w.interrupt();
}"""
K_SHUT_BAD = """// Naive: stop now, whatever is on the rail
fun closeKitchen() {
    cooks.forEach { it.interrupt() }
    waiters.forEach { it.interrupt() }
}"""

J_DRILL = """static final String PILL = new String("PILL");   // a unique object, compared by identity

static void runPipeline(List<Thread> producers, List<Thread> consumers, BlockingQueue<String> queue)
        throws InterruptedException {
    for (Thread c : consumers) c.start();
    for (Thread p : producers) p.start();
    for (Thread p : producers) p.join();          // every item is in the queue
    for (Thread c : consumers) queue.put(PILL);   // one pill each, behind the items
    for (Thread c : consumers) c.join();
}

// each consumer's loop:
// while (true) { String item = queue.take(); if (item == PILL) return; process(item); }"""
K_DRILL = """val PILL = String(charArrayOf('P', 'I', 'L', 'L'))   // a unique object, compared by identity

fun runPipeline(producers: List<Thread>, consumers: List<Thread>, queue: BlockingQueue<String>) {
    consumers.forEach { it.start() }
    producers.forEach { it.start() }
    producers.forEach { it.join() }               // every item is in the queue
    consumers.forEach { queue.put(PILL) }         // one pill each, behind the items
    consumers.forEach { it.join() }
}

// each consumer's loop:
// while (true) { val item = queue.take(); if (item === PILL) return; process(item) }"""

def phil(i):
    left, right = f"f{i}", f"f{(i + 1) % 3}"
    return {"name": f"P{i}", "steps": [
        {"op": "lock", "lock": left, "code": f"left.lock();     // fork {i}"},
        {"op": "lock", "lock": right, "code": f"right.lock();    // fork {(i + 1) % 3}"},
        {"op": "read", "var": "meals", "reg": "r", "code": "int r = meals;"},
        {"op": "add", "reg": "r", "n": 1, "code": "r = r + 1;       // eat"},
        {"op": "write", "var": "meals", "reg": "r", "code": "meals = r;"},
        {"op": "unlock", "lock": right, "code": "right.unlock();"},
        {"op": "unlock", "lock": left, "code": "left.unlock();"}]}

SIM = {
 "title": "Three philosophers, three forks, left fork first",
 "intro": "Each philosopher takes the left fork, then the right one. First let them eat one at a time. Then reset and give each philosopher exactly one step before anyone takes a second.",
 "vars": {"meals": 0},
 "locks": ["f0", "f1", "f2"],
 "threads": [phil(0), phil(1), phil(2)],
 "goal": {"var": "meals", "eq": 3, "say": "All three ate, one after another. Now reset and let each philosopher pick up a left fork first: every fork is held, every philosopher waits for the next one's fork, and the table freezes."}
}

FIG = (
    '<svg viewBox="0 0 680 230" role="img" aria-label="Two waiters put orders on a bounded rail; three cooks take them. After the waiters finish, three pills follow the last order, one for each cook">'
    '<rect class="box-a" x="20" y="40" width="120" height="44" rx="8"/><text class="t" x="80" y="67" text-anchor="middle">waiter 1</text>'
    '<rect class="box-a" x="20" y="130" width="120" height="44" rx="8"/><text class="t" x="80" y="157" text-anchor="middle">waiter 2</text>'
    '<line class="ln" x1="140" y1="62" x2="196" y2="98" marker-end="url(#arr)"/>'
    '<line class="ln" x1="140" y1="152" x2="196" y2="118" marker-end="url(#arr)"/>'
    '<rect class="box" x="200" y="84" width="280" height="46" rx="8"/>'
    + "".join(f'<rect class="{c}" x="{212 + 44 * k}" y="95" width="36" height="24" rx="6"/>' for k, c in enumerate(["box-bad", "box-bad", "box-bad", "box-ok", "box-ok", "box-ok"]))
    + '<text class="t-s t-bad" x="274" y="148" text-anchor="middle">3 pills, last</text>'
    '<text class="t-s t-ok" x="406" y="148" text-anchor="middle">orders first</text>'
    '<text class="t-s t-m" x="340" y="76" text-anchor="middle">bounded rail: put waits when full</text>'
    '<line class="ln" x1="480" y1="100" x2="536" y2="56" marker-end="url(#arr)"/>'
    '<line class="ln" x1="480" y1="107" x2="536" y2="107" marker-end="url(#arr)"/>'
    '<line class="ln" x1="480" y1="114" x2="536" y2="158" marker-end="url(#arr)"/>'
    + "".join(f'<rect class="box-b" x="540" y="{y}" width="120" height="40" rx="8"/><text class="t" x="600" y="{y + 25}" text-anchor="middle">cook {n}</text>' for n, y in ((1, 36), (2, 87), (3, 138)))
    + '<text class="t-s t-m" x="340" y="210" text-anchor="middle">each cook stops at its own pill, after every real order</text>'
    '</svg>'
)

OPENING = """Picture the kitchen from wait, notify and guarded blocks at closing time. The waiters have stopped taking orders. A few tickets are still on the rail, and three cooks are working through them. (In code, each cook is a thread, one path of work running beside the others, and the rail is a queue.) When the rail is empty, each cook waits for the next ticket. Tonight there won't be one.

How does a cook know it's time to go home? An empty rail can mean the evening is over, or just that the next ticket is late. The quickest answers both go wrong. Tell every cook to stop at once, and the tickets still on the rail are never cooked. Put one "kitchen closed" card on the rail, and one cook goes home while two wait by the empty rail all night.

Don't share ended with the state you can't take away. This lesson puts the whole track's tools to work on three classic problems: closing the kitchen, five philosophers sharing forks at a round table, and a price board that many read and one person changes. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Let's name the parts first. A thread that puts work into a queue is a **producer**, and a thread that takes work out is a **consumer**. Our waiters are producers and our cooks are consumers, and the whole shape is called producer-consumer. Most concurrent programs have one somewhere: something makes work at one speed, and something else does it at another.

In Java, the rail is a `BlockingQueue` from Concurrent collections. `put` adds a ticket, and `take` removes one, waiting while the queue is empty. Give the queue a limit, as the rail in wait, notify and guarded blocks had. A bounded queue, one with a fixed capacity, makes `put` wait while it's full, so a fast waiter slows to the cooks' pace instead of piling up tickets until memory runs out. That's **backpressure**: a full queue pushing back on whoever fills it.

The hard part is stopping. A cook waits in `take()`, and `take()` never returns from an empty queue. Inside, it parks (sleeps until woken) on the queue's own "not empty" condition, a wait set like the one from guarded blocks, and only a `put` wakes it. Once the waiters have gone home, nothing ever will.

There are three ways out. Interrupting the cooks, that is, asking each thread to stop, is fast. But it drops whatever is still queued: `take()` checks the interrupt flag before it looks at the queue, so it throws even when tickets are waiting. Polling with a timeout, `poll(1, SECONDS)` in a loop that checks a stop flag, works too. But every cook can wait up to one timeout before it notices, and every loop has to check the flag correctly. The clean answer is a **poison pill**: a special item that means "no more work", put on the rail like any other ticket. A cook that takes it stops.

Here's the naive version, with one pill for the whole kitchen:

""" + pair(J_ONEPILL, K_ONEPILL) + """

The Try it runs two waiters, three cooks and a rail with room for four tickets. With `-Pargs=onepill` it printed:

```text
cook-1 got its pill after 1004 orders
cooks still waiting: 2 (WAITING in take)
```

A pill is just an item, so the first cook to take it removes it from the rail and goes home. The other two find an empty rail and wait in `take()`, all night. Anything that waits for them to finish, such as the program's own shutdown, hangs with them.

Three rules make pills work:

- Put the pills only after every producer has finished, so they land behind every real ticket.
- Put one pill per consumer, because each pill is taken once.
- Compare against the pill by identity, with `==`. A pill made with `new String("PILL")` is an object of its own, so a real ticket that happens to read `PILL` is still a ticket.

""" + pair(J_PILL, K_PILL) + """

The same run with one pill per cook printed:

```text
cook-1 got its pill after 511 orders
cook-2 got its pill after 177 orders
cook-0 got its pill after 1312 orders
cooks still waiting: 0
```

The three counts add up to 2,000, every order the waiters put, and no cook was left waiting. The split changes from run to run, because whichever cook is free takes the next ticket. The figure shows the rail at closing time: the last real orders, then the pills.

**One pill stops one consumer. Put one per consumer, after the last producer.**

The kitchen now closes without losing an order. The next problem has no queue at all, just five threads, five locks and a table."""

ASIDE0 = {
 "title": "Why are these three called classic?",
 "body": "Because people have argued about them for over fifty years. Edsger Dijkstra set the dining philosophers as an exam problem in 1965, with five computers competing for shared tape drives, and Tony Hoare soon retold it with philosophers and forks. The readers-writers problem got its name in a 1971 paper by Courtois, Heymans and Parnas. They have lasted because nearly every concurrency bug you'll meet is one of the three in another setting. It's a queue that won't stop, locks taken in a circle, or a thread that never gets its turn."
}

# ---------------------------------------------------------------- section 1
S1 = """Here's the most famous puzzle in concurrency, and it needs only a table. Five philosophers sit around a round table, with one fork between each pair of neighbours, so five forks in all. A philosopher thinks for a while, then gets hungry. To eat, each one needs both forks next to them, the one on the left and the one on the right, and each picks up the left fork first.

In code, each philosopher is a thread and each fork is a lock, a `ReentrantLock` from Explicit locks: an object a thread takes with `lock()` and gives back with `unlock()`. It works most of the time. Then, one day, all five get hungry at the same moment and each picks up a left fork. Let's trace the smallest version, with three philosophers:

1. Philosopher 0 takes fork 0. At the same moment, philosopher 1 takes fork 1 and philosopher 2 takes fork 2.
2. Philosopher 0 reaches for fork 1, which philosopher 1 holds. Philosopher 1 reaches for fork 2, held by philosopher 2.
3. Philosopher 2 reaches for fork 0, held by philosopher 0. Every fork is in a hand, and nobody can eat.

Nobody puts a fork down, because the code never says to. That's the deadlock from Deadlock, livelock and starvation, threads that wait for each other forever, with three locks instead of two. All four of its conditions hold. Each fork has one owner (mutual exclusion). Each philosopher holds one fork while waiting for another (hold and wait). Nobody takes a fork from a neighbour (no preemption). And the waiting goes all the way round the table (circular wait). It's also what the bank's transfers look like when each one locks two of many accounts.

The simulator below has three philosophers. First let them eat one at a time. Then reset it and give each philosopher a single step before anyone takes a second.

The Try it runs five philosophers, 200 meals each, with a 1 ms pause between the two forks to make the bad moment likely. Left fork first, it printed:

```text
naive: 0 of 1,000 meals in 3045 ms, deadlocked philosophers: 5
```

Zero meals, and the JVM itself, the program that runs your Java code, names all five philosophers as deadlocked, because forks that are `ReentrantLock`s have owners its deadlock detector can follow. There are two standard fixes, and each removes a different condition.

**Resource ordering** removes the circular wait. Number the forks and always take the lower-numbered one first. Philosophers 0 to 3 still take left, then right. Philosopher 4 needs forks 4 and 0, so it takes fork 0 first:

""" + pair(J_ORDER, K_ORDER) + """

Now a philosopher who holds a fork and waits always wants a higher-numbered one. A cycle would need someone, somewhere, to wait for a lower number than the one they hold, so the cycle can't close, however many forks or accounts there are. It's the lock order from the bank's transfers, applied to a table.

**A waiter** removes the moment when everyone holds one fork. Only four of the five may sit down at once. Four philosophers share five forks. Even if each seated one holds a fork, one fork is still free, and the seated philosopher next to it can pick it up and eat. A `Semaphore(n - 1)` from Synchronizers is the waiter, one chair short:

""" + pair(J_WAITER, K_WAITER) + """

Both fixes served all 1,000 meals in the Try it, in about 1.2 seconds, with no deadlock. A third fix, `tryLock` on the second fork with a random back-off, removes no preemption, but it brings back the livelock risk of the two polite diners in Deadlock, livelock and starvation. Use ordering when you can number your resources. Use the waiter when you can't, or when you want to cap how many threads compete at all.

**Any number of locks can freeze in a circle. Take them in one global order.**

A table of philosophers needs every lock to itself. The last problem is gentler, because most of its threads are happy to share."""

# ---------------------------------------------------------------- section 2
S2 = """The last puzzle brings back the price board from Don't share, with one change: this time the shop updates its prices in place, so readers and the writer have to take turns. Many threads at the tills (the cash registers) read prices all day, and readers can share, because two readers never get in each other's way. Now and then the owner changes the prices, and the writer needs the board to itself, so that no reader sees half a change. That's the readers-writers problem. Its real question is what happens when both are waiting, and every answer makes somebody wait longer than they'd like.

**Readers first** lets a new reader in whenever no writer is inside. It looks generous. But with a steady stream of readers that overlap, the reader count never drops to zero, so the writer never gets in. That's **starvation**: the program makes progress, but one thread never does.

**Writers first** makes new readers wait as soon as a writer is waiting. The owner gets in quickly, but with a stream of writers, the readers starve instead.

**Fair order** serves threads in the order they arrived. Nobody starves, and throughput, the work done per second, drops, because readers that could have shared now wait behind a writer who came first.

Let's watch the first policy fail. The Try it has four readers, each holding the read side for 2 ms at a time, overlapping, for one and a half seconds. After 100 ms, the owner asks for the write side. A textbook readers-first lock, written with `synchronized` and `wait()`, let the owner in only when the readers stopped on their own:

```text
readers-first lock:     writer waited 1379 ms
ReentrantReadWriteLock: writer waited 2 ms
```

The new prices waited in the owner's hand until the shop went quiet. The second line is Java's own `ReentrantReadWriteLock` from Explicit locks, a lock with a read side that many threads can hold together and a write side for one. In its default, non-fair mode it promises no order, but a thread asking for the read side waits if the thread at the head of the queue wants to write. In practice, that keeps a stream of new readers from starving a writer. Fair mode gives strict arrival order:

""" + pair(J_RW, K_RW) + """

**A lock that lets new readers pass a waiting writer can starve the writer. Make them queue behind it.**

Before you choose a policy, ask whether the readers need a lock at all. If the writer replaces the whole board, the snapshot from Don't share lets readers read an immutable map with no lock and no waiting, and the question of who starves goes away. Many databases, the programs that store data for other programs, do something similar, which they call multiversion reads: a reader sees a complete older version while a writer works on the new one.

That's also where this lesson's tools stop. A pill, a lock order and a read-write lock each solve one shape of problem. None of them tells you whether your version works on a busy day. For that you need a test that makes threads collide on purpose, and that's where the next lesson goes."""

L = {
 "id": "conc-12",
 "title": "Classic problems: producer-consumer, philosophers, readers-writers",
 "minutes": 38,
 "goal": "By the end you can stop a producer-consumer pipeline cleanly with poison pills, fix the dining philosophers deadlock two ways, and say who starves under each readers-writers policy.",
 "opening": OPENING,
 "warmup": {
  "q": "Three cook threads take orders from a `BlockingQueue`, a queue whose `take()` waits while it's empty. At closing time, the head chef puts ONE special \"kitchen closed\" item in the queue, and each cook stops when it takes that item. What happens?",
  "options": ["All three cooks stop, because they all see the item", "One cook stops; the other two wait in `take()` forever", "The queue throws, because the item can only be taken once", "Nothing stops until the queue is garbage collected"],
  "answer": 1,
  "why": "The special item, a poison pill, is just an element: the first cook to take it removes it from the queue and stops. The other two find an empty queue and wait in `take()` forever, and anything that waits for them, such as the program's shutdown, hangs too. You need one pill per cook. The first section runs exactly this."
 },
 "sections": [
  {
   "h": "Closing the kitchen: a bounded queue and one poison pill per cook",
   "body": S0,
   "aside": ASIDE0,
   "figure": {"svg": FIG, "caption": "Orders first, pills last, one pill per cook. Each cook stops at its own pill, after every real order has been taken."},
   "try": {
    "title": "One pill per cook, or not",
    "minutes": 3,
    "steps": [
     "Read `PoisonPills`. Two waiters put 1,000 orders each on a rail with room for 4, and three cooks take them. After the waiters finish, `main` puts the pills.",
     "Run it. Note how many orders each cook handled.",
     "Run it with `-Pargs=onepill`. Predict how many cooks are still waiting after one second, and in which thread state."
    ],
    "code": code("PoisonPills"),
    "expect": "With one pill each, all three cooks report their pill, their counts add up to 2,000, and `cooks still waiting: 0`. The split changes from run to run. With `onepill`, one cook stops and two are still waiting: `cooks still waiting: 2 (WAITING in take)`. In a real program, that's a shutdown that never finishes."
   }
  },
  {
   "h": "Five philosophers, five forks: the table that freezes, and two fixes",
   "body": S1,
   "sim": SIM,
   "try": {
    "title": "Freeze the table, then fix it two ways",
    "minutes": 4,
    "steps": [
     "Read `Philosophers`. Five philosophers try to eat 200 meals each, pausing 1 ms between their two forks. After 3 seconds, the demo asks the JVM which threads are deadlocked.",
     "Run it as it is. Then run it with `-Pargs=ordered` and with `-Pargs=waiter`.",
     "Compare the meal counts, the times and the deadlock counts."
    ],
    "code": code("Philosophers"),
    "expect": "As it is: no meals at all in runs here (a lucky run may get one) and `deadlocked philosophers: 5`, found by `ThreadMXBean`, the JDK's window onto the JVM's threads, because the forks are `ReentrantLock`s. Ordered and waiter: all 1,000 meals in about 1.2 seconds, and `deadlocked philosophers: 0`."
   }
  },
  {
   "h": "Many readers, one writer: who waits at the price board",
   "body": S2,
   "try": {
    "title": "Starve a writer",
    "minutes": 3,
    "steps": [
     "Read `ReadersWriters`. Four readers hold the read side for 2 ms at a time, overlapping, for 1.5 seconds. After 100 ms, one writer asks for the lock. The demo measures how long it waits, first with a hand-written readers-first lock, then with `ReentrantReadWriteLock`.",
     "Predict both waits.",
     "Run it."
    ],
    "code": code("ReadersWriters"),
    "expect": "Readers-first: the writer waits about 1,400 ms (1,379 and 1,362 ms in runs here), until the readers stop on their own. `ReentrantReadWriteLock`: 0 to 2 ms, because new readers queue behind the waiting writer instead of passing it."
   },
   "refs": [
    {"title": "jcstress samples, including Classic_01_DiningPhilosophers and Classic_02_ProducerConsumerProblem", "url": "https://github.com/openjdk/jcstress/tree/master/jcstress-samples", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "Stopping consumers: pills in Java, a closed channel in Kotlin coroutines",
  "java": {"title": "Java, BlockingQueue", "src": """for (int i = 0; i < 4; i++) {
    cooks.add(start(() -> {
        while (true) {
            String ticket = rail.take();
            if (ticket == PILL) return;        // each cook needs its own pill
            cook(ticket);
        }
    }));
}
for (Thread w : waiters) w.join();
for (int i = 0; i < 4; i++) rail.put(PILL);   // 4 cooks, 4 pills
for (Thread c : cooks) c.join();"""},
  "kotlin": {"title": "Kotlin, kotlinx.coroutines Channel", "src": """// a Channel can be closed, so there are no pills
coroutineScope {
    val rail = Channel<String>(capacity = 8)
    val waiters = tables.map { table -> launch { for (t in table) rail.send(t) } }
    repeat(4) { launch { for (t in rail) cook(t) } }   // each loop ends when the channel is closed AND empty
    waiters.joinAll()
    rail.close()                                        // "no more tickets": cooks finish the rail, then stop
}"""},
  "note": "With threads and a `BlockingQueue`, Kotlin code looks just like the Java version: the queue has no idea of \"closed\", so you still need one pill per consumer, compared with `===`. Java's queue does its job well, and the pill is a small, honest workaround for what it lacks. The real difference comes with coroutines, Kotlin's lightweight tasks that the coroutines track covers. A `Channel` is a queue for coroutines, and it can be closed: `close()` means no more items, and every `for (t in rail)` loop ends once the channel is closed and empty, however many consumers there are. That removes the whole family of pill-counting bugs. `coroutineScope` also waits for every coroutine it launched, so there is no join loop to forget."
 },
 "worked": {
  "title": "Close the kitchen without losing an order",
  "steps": [
   {"say": "The kitchen's program has two waiter threads that take orders from the tables and four cook threads, with a bounded rail between them. At closing time, someone wrote this. What happens to the tickets still on the rail, and to the dish a cook is halfway through?",
    "code": J_SHUT_BAD, "lang": "java", "alt_code": K_SHUT_BAD, "alt_lang": "kotlin"},
   {"say": "Interrupting a cook that waits in `take()` stops it at once, so every ticket still on the rail is dropped. A cook in the middle of a dish may stop halfway and leave it unfinished. And a waiter interrupted inside `put` loses the order it was holding. Nothing throws, and nothing tells the customers.", "code": "", "lang": ""},
   {"say": "Here's the orderly version, with a label on each step. `open` is a `volatile` flag the waiters check before they take each new order.",
    "code": J_SHUT, "lang": "java", "alt_code": K_SHUT, "alt_lang": "kotlin"},
   {"say": "Before reading on, explain to yourself why step 2 must finish before step 3 starts. Answer: a pill put while a waiter is still working can land in front of that waiter's last tickets. A cook that takes the pill goes home. With every cook gone and the rail bounded, the waiter then waits in `put` forever, and the shutdown hangs in step 2. Joining the waiters first means every real ticket is already ahead of the pills.", "code": "", "lang": ""},
   {"say": "Step 5 is the safety net. If the oven breaks, the cooks can't finish the rail before the deadline, and interrupting them is then the right call. The orders they didn't finish were never marked as served. A program that records each finished order, as the bank recorded each payment in Race conditions, knows exactly which ones to pick up when it starts again.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A pipeline that stops cleanly, and a table that can't deadlock",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/SettlementPipeline.java", f"{lab}/main/{P}/DiningTable.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l12.*'",
  "steps": [
   "Meet the two classes. `SettlementPipeline` is this lesson's kitchen in general form: producer threads put records (plain strings) into one bounded queue, and consumer threads take them and call `process` on each. `DiningTable` is the philosophers' table: `dine(seat, meals, eat)` has the philosopher in `seat` take two forks and eat, `meals` times.",
   "Run the tests. All six fail. The three pipeline tests hit `UnsupportedOperationException`. The three `DiningTable` tests time out after 15 seconds each: the philosophers deadlocked.",
   "Part 1: write `SettlementPipeline.run`. Create an `ArrayBlockingQueue` of `capacity` and a unique pill (`new String(\"PILL\")`). Start the consumers: each loops on `take()`, stops at the pill (compared with `==`), and otherwise calls `process` and counts.",
   "Start one producer thread per inner list. Join all producers, then put one pill per consumer, then join all consumers, then return the count.",
   "Part 2: fix `DiningTable.dine` so every philosopher takes the lower-numbered fork first. Keep `reachForTheOtherFork()` between the two forks.",
   "Run the tests until all six pass, then twice more."
  ],
  "hints": [
   "Count processed records with an `AtomicInteger`, because several consumers add to it at once.",
   "The second pipeline test checks that `process` is never called after `run` returns. If it fails, you return before joining every consumer.",
   "For the table, compute `a = seat` and `b = (seat + 1) % seats`, then lock `forks[min(a, b)]` before `forks[max(a, b)]`. Only the last philosopher's order actually changes, and that's enough to break the cycle."
  ],
  "done_when": "All six tests in `ClassicProblemsTest` pass, three runs in a row."
 },
 "drill": {
  "title": "A poison-pill shutdown from memory",
  "minutes": 4,
  "prompt": "Close this page. You're given producer and consumer threads that are created but not yet started, and their shared `BlockingQueue<String>`. Write the code that runs them to completion with poison pills, plus the consumer's loop. Then check: when are the pills put, how many, and how does a consumer recognize one?",
  "answer": {"lang": "java", "src": J_DRILL, "alt": {"lang": "kotlin", "title": "Kotlin", "src": K_DRILL}}
 },
 "recap": [
  "Producer-consumer: a bounded `BlockingQueue` between two speeds. A full queue that makes `put` wait is backpressure.",
  "Poison pills: put them only after every producer has finished, one per consumer, and compare them by identity.",
  "Dining philosophers is a circular wait. Take resources in one global order, or let at most n - 1 threads compete with a semaphore.",
  "Readers first starves writers, writers first starves readers, and fair order starves nobody but gets less done per second.",
  "`ReentrantReadWriteLock` makes new readers wait behind a queued writer, and fair mode gives strict arrival order. If writers replace the whole thing, an immutable snapshot removes the problem.",
  "The limit: these tools fix the shape of a problem. Only a test that makes threads collide shows that your version works."
 ],
 "closing": "We started at closing time, with three cooks by an empty rail who couldn't tell the evening was over. One pill per cook sent them home after the last order. Then we unfroze a table of philosophers with one fork order, and let the owner change prices without waiting for the shop to empty.\n\nNow search your own code for loops around `take()`, and ask how each one ends. If it's an interrupt, check what happens to the work still queued. If it's a pill, count the pills.\n\nEvery fix here passed its demo. Next, we'll ask how you know a fix really works: how do you write a test that makes threads collide, and what do you do when a program hangs anyway?",
 "quiz": [
  {"q": "The head chef puts the poison pills for 4 cooks right after starting the waiters, without waiting for them to finish. The rail is bounded. What can happen?",
   "options": ["Nothing: the pills wait at the back of the queue", "The cooks take the pills early and stop, the rail fills up, and the waiters wait in `put` forever", "The pills are rejected because the queue is full", "Each cook cooks exactly one order"],
   "answer": 1, "why": "Pills are ordinary elements, taken in arrival order. Put early, they sit in front of tickets that the waiters add later. The cooks stop at them, nothing drains the rail any more, and the waiters block once it's full. Join the producers first."},
  {"q": "Five philosophers each take the left fork, then the right one, and sometimes they all freeze. Which change removes the deadlock?",
   "options": ["Make every fork a fair `ReentrantLock`", "Add a random sleep before picking up the left fork", "Always take the lower-numbered fork first, so the last philosopher reaches right first", "Use `synchronized` instead of `ReentrantLock`"],
   "answer": 2, "why": "With one global order, no cycle of waiting can form, so circular wait is gone. Fair locks change who gets a free fork next, not the cycle. A random sleep only makes the bad timing rarer. `synchronized` deadlocks in exactly the same way."},
  {"q": "A hand-written readers-first lock protects the shop's price table. Readers arrive all the time and overlap. Once an hour, the owner calls `writeLock()` to change the prices. What happens?",
   "options": ["The owner waits until the readers stop arriving, which may be never: writer starvation", "The owner gets in within one read's duration", "The owner's call throws `IllegalStateException`", "Readers and the writer take turns"],
   "answer": 0, "why": "Readers first lets a new reader in whenever no writer is inside, so the reader count never reaches zero while readers overlap. The writer waits for a moment that never comes. `ReentrantReadWriteLock` makes new readers queue behind a waiting writer, and a snapshot avoids locking reads at all."},
  {"q": "From Synchronizers: the waiter fix for five philosophers uses a `Semaphore`. Why `new Semaphore(4)` and not `new Semaphore(5)`?",
   "options": ["To save one thread", "With at most 4 seated, at least one of them can always pick up both forks, so the cycle can't involve everyone", "A semaphore can't have more permits than threads", "Fairness needs one permit fewer than there are threads"],
   "answer": 1, "why": "With five permits, all five can sit, each take a left fork and freeze as before. With four, at most four hold a fork, and five forks between four people means at least one of them can take both. The permits limit how many compete, and that's what breaks the cycle here.",
   "from": "conc-10"},
  {"q": "A cook checks `if (ticket.equals(\"POISON\")) break;`, and the pill is the string literal `\"POISON\"`. What's the risk?",
   "options": ["`equals` is too slow for a busy loop", "None: a real ticket never contains that text", "The pill might be garbage collected", "A real ticket with that text stops a cook early and is never cooked"],
   "answer": 3, "why": "A ticket's text can be anything a waiter types, including the pill's text. With `equals`, such a ticket sends a cook home and is silently dropped. A pill created as a unique object and compared with `==` (or `===` in Kotlin) can't be confused with real data."}
 ],
 "flashcards": [
  {"front": "Poison pills: how many, and when do you put them?", "back": "One per consumer, and only after every producer has finished putting."},
  {"front": "Why compare a poison pill with `==` rather than `equals`?", "back": "So a real item with the same text isn't mistaken for the pill. Make the pill a unique object, such as `new String(\"PILL\")`."},
  {"front": "Why bound the queue between producers and consumers?", "back": "So `put` makes producers wait when consumers fall behind (backpressure), instead of filling memory."},
  {"front": "Which deadlock condition does \"always take the lower-numbered fork first\" remove?", "back": "Circular wait: with one global order, no cycle of waiting threads can form."},
  {"front": "How does a `Semaphore(n - 1)` \"waiter\" prevent the dining philosophers deadlock?", "back": "At most n - 1 philosophers compete for n forks, so at least one can always get both."},
  {"front": "Readers-first lock: who starves?", "back": "Writers. With overlapping readers the reader count never reaches zero, so the writer never gets in."},
  {"front": "What does non-fair `ReentrantReadWriteLock` do when a writer is waiting and a new reader arrives?", "back": "The reader usually waits if the writer is at the head of the queue, so a stream of readers doesn't starve the writer."}
 ],
 "terms": [
  {"term": "Producer-consumer", "plain": "Threads that make work hand it to threads that do it, usually through a queue."},
  {"term": "Poison pill", "plain": "A special queue item that tells one consumer to stop."},
  {"term": "Backpressure", "plain": "A full bounded queue making producers wait, so they slow to the consumers' pace."},
  {"term": "Dining philosophers", "plain": "The classic deadlock: each thread holds one resource and waits for its neighbour's."},
  {"term": "Resource ordering", "plain": "Taking locks in one global order so that no cycle of waiting can form."},
  {"term": "Readers-writers", "plain": "Sharing data between many readers and a few writers, and deciding who waits."},
  {"term": "Writer starvation", "plain": "A writer that never gets in because readers keep holding the lock."}
 ],
 "explain_back": {
  "prompt": "Explain to a friend how you'd close a kitchen with 2 waiter threads and 4 cook threads so that no order on the rail is lost and no thread is left waiting.",
  "answer": "First stop the waiters from taking new orders and wait for them to finish, so every real ticket is already on the rail. Then put four poison pills, one per cook, behind those tickets. Each cook keeps taking tickets until it takes a pill, so the rail empties completely and each cook stops exactly once. The pill is a unique object compared with `==`, so no real ticket can look like one. Finally, wait for the cooks with one overall deadline, and interrupt any that are still busy when it passes. Whatever they didn't finish was never marked as served, so it can be picked up again later."
 },
 "deeper": {
  "minutes": 10,
  "body": "Poison pills are one of several ways to stop consumers. Thread pools use interruption: `shutdownNow()` interrupts every worker, and tasks are expected to stop when interrupted, as A thread's life described. A `poll(timeout)` loop that checks a `volatile` flag is simple, but it makes shutdown wait for up to one timeout, and every loop must check the flag. Kotlin channels and reactive streams have completion built in, which is why they need no pills.\n\nThe dining philosophers problem has more solutions than the two here. Chandy and Misra's solution passes \"dirty\" and \"clean\" forks between neighbours on request, which avoids both deadlock and starvation and works across machines, at the cost of messages. A plain `tryLock` with back-off works too, but it needs randomness to avoid livelock. All of them remove one of the four conditions from Deadlock, livelock and starvation.\n\nReaders-writers shows up all over databases. Many of them use multiversion reads: a query reads each row as it was when the query started, so readers don't wait for writers and writers don't wait for readers. That is the immutable-snapshot idea from Don't share applied to storage, and it's why you rarely meet this problem in plain database queries. Writers still wait for other writers on the same rows.\n\nIf you want to see these problems under a real stress harness, the jcstress samples include `Classic_01_DiningPhilosophers` and `Classic_02_ProducerConsumerProblem`. The next lesson shows how to run jcstress and read its results."
 },
 "sources": [
  {"title": "BlockingQueue (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/BlockingQueue.html"},
  {"title": "ReentrantReadWriteLock (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantReadWriteLock.html"},
  {"title": "jcstress samples (classic problems, mutual exclusion)", "url": "https://github.com/openjdk/jcstress/tree/master/jcstress-samples"},
  {"title": "Java Concurrency in Practice, Goetz et al., chapters 5 and 7", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/conc-12.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
