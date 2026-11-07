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
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

J_PILL = """// consumer
while (true) {
    String record = queue.take();          // waits while the queue is empty
    if (record == PILL) break;             // identity: a record "PILL" is still a record
    settle(record);
}

// coordinator, after every producer has finished:
for (int i = 0; i < consumers; i++) queue.put(PILL);   // one pill per consumer"""
K_PILL = """// consumer
while (true) {
    val record = queue.take()          // waits while the queue is empty
    if (record === PILL) break         // identity: a record "PILL" is still a record
    settle(record)
}

// coordinator, after every producer has finished:
repeat(consumers) { queue.put(PILL) }  // one pill per consumer"""

J_ORDER = """int left = seat, right = (seat + 1) % n;
ReentrantLock first = forks[Math.min(left, right)];    // the last philosopher reaches right first
ReentrantLock second = forks[Math.max(left, right)];"""
K_ORDER = """val left = seat
val right = (seat + 1) % n
val first = forks[minOf(left, right)]     // the last philosopher reaches right first
val second = forks[maxOf(left, right)]"""
J_WAITER = """seats.acquire();                 // Semaphore(n - 1): one chair short, so someone can always eat
try { eatWithBothForks(); } finally { seats.release(); }"""
K_WAITER = """seats.acquire()                 // Semaphore(n - 1): one chair short, so someone can always eat
try { eatWithBothForks() } finally { seats.release() }"""

J_RW = """new ReentrantReadWriteLock();        // non-fair: a new reader waits if a writer is next in line
new ReentrantReadWriteLock(true);    // fair: strict arrival order, lower throughput"""
K_RW = """ReentrantReadWriteLock()        // non-fair: a new reader waits if a writer is next in line
ReentrantReadWriteLock(true)    // fair: strict arrival order, lower throughput"""

J_SHUT = """void shutdown() throws InterruptedException {
    running = false;                                   // 1. producers stop polling Kafka
    for (Thread p : producers) p.join();               // 2. wait until no producer can put again
    for (int i = 0; i < consumers.size(); i++) {
        queue.put(PILL);                               // 3. one pill per consumer, behind every real record
    }
    long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(30);
    for (Thread c : consumers) {
        c.join(Math.max(1, TimeUnit.NANOSECONDS.toMillis(deadline - System.nanoTime())));   // 4. one deadline for all
    }
    for (Thread c : consumers) if (c.isAlive()) c.interrupt();   // 5. still busy: interrupt; Kafka redelivers
}"""
K_SHUT = """fun shutdown() {
    running = false                                    // 1. producers stop polling Kafka
    producers.forEach { it.join() }                    // 2. wait until no producer can put again
    repeat(consumers.size) { queue.put(PILL) }         // 3. one pill per consumer, behind every real record
    val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(30)
    for (c in consumers) {
        c.join(maxOf(1L, TimeUnit.NANOSECONDS.toMillis(deadline - System.nanoTime())))   // 4. one deadline for all
    }
    consumers.filter { it.isAlive }.forEach { it.interrupt() }   // 5. still busy: interrupt; Kafka redelivers
}"""
J_SHUT_BAD = """void shutdown() {
    for (Thread c : consumers) c.interrupt();   // stop now, whatever is in the queue
    for (Thread p : producers) p.interrupt();
}"""
K_SHUT_BAD = """fun shutdown() {
    consumers.forEach { it.interrupt() }        // stop now, whatever is in the queue
    producers.forEach { it.interrupt() }
}"""

J_DRILL = """static final String PILL = new String("PILL");   // a unique object, compared by identity

static void runPipeline(List<Thread> producers, List<Thread> consumers, BlockingQueue<String> queue)
        throws InterruptedException {
    for (Thread c : consumers) c.start();
    for (Thread p : producers) p.start();
    for (Thread p : producers) p.join();          // every record is in the queue
    for (Thread c : consumers) queue.put(PILL);   // one pill each, behind the records
    for (Thread c : consumers) c.join();
}

// each consumer's loop:
// while (true) { String r = queue.take(); if (r == PILL) return; settle(r); }"""
K_DRILL = """val PILL = String(charArrayOf('P', 'I', 'L', 'L'))   // a unique object, compared by identity

fun runPipeline(producers: List<Thread>, consumers: List<Thread>, queue: BlockingQueue<String>) {
    consumers.forEach { it.start() }
    producers.forEach { it.start() }
    producers.forEach { it.join() }               // every record is in the queue
    consumers.forEach { queue.put(PILL) }         // one pill each, behind the records
    consumers.forEach { it.join() }
}

// each consumer's loop:
// while (true) { val r = queue.take(); if (r === PILL) return; settle(r) }"""

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
 "title": "Three philosophers, three forks, left first",
 "intro": "Each philosopher takes the left fork, then the right one. First let them eat one at a time. Then reset and give each philosopher exactly one step before anyone takes a second.",
 "vars": {"meals": 0},
 "locks": ["f0", "f1", "f2"],
 "threads": [phil(0), phil(1), phil(2)],
 "goal": {"var": "meals", "eq": 3, "say": "All three ate, one after another. Now reset and let each philosopher pick up a left fork first: every fork is held, every philosopher waits for the next one's fork, and the table freezes."}
}

FIG = (
    '<svg viewBox="0 0 680 230" role="img" aria-label="Two producers put records into a bounded queue; three consumers take them. After the producers finish, three pills follow the last record, one for each consumer">'
    '<rect class="box-a" x="20" y="40" width="120" height="44" rx="8"/><text class="t" x="80" y="67" text-anchor="middle">producer 1</text>'
    '<rect class="box-a" x="20" y="130" width="120" height="44" rx="8"/><text class="t" x="80" y="157" text-anchor="middle">producer 2</text>'
    '<line class="ln" x1="140" y1="62" x2="196" y2="98" marker-end="url(#arr)"/>'
    '<line class="ln" x1="140" y1="152" x2="196" y2="118" marker-end="url(#arr)"/>'
    '<rect class="box" x="200" y="84" width="280" height="46" rx="8"/>'
    + "".join(f'<rect class="{c}" x="{212 + 44 * k}" y="95" width="36" height="24" rx="6"/>' for k, c in enumerate(["box-bad", "box-bad", "box-bad", "box-ok", "box-ok", "box-ok"]))
    + '<text class="t-s t-bad" x="274" y="148" text-anchor="middle">3 pills, last</text>'
    '<text class="t-s t-ok" x="406" y="148" text-anchor="middle">records first</text>'
    '<text class="t-s t-m" x="340" y="76" text-anchor="middle">bounded queue: put waits when full</text>'
    '<line class="ln" x1="480" y1="100" x2="536" y2="56" marker-end="url(#arr)"/>'
    '<line class="ln" x1="480" y1="107" x2="536" y2="107" marker-end="url(#arr)"/>'
    '<line class="ln" x1="480" y1="114" x2="536" y2="158" marker-end="url(#arr)"/>'
    + "".join(f'<rect class="box-b" x="540" y="{y}" width="120" height="40" rx="8"/><text class="t" x="600" y="{y + 25}" text-anchor="middle">consumer {n}</text>' for n, y in ((1, 36), (2, 87), (3, 138)))
    + '<text class="t-s t-m" x="340" y="210" text-anchor="middle">each consumer stops at its own pill, after every real record</text>'
    '</svg>'
)

L = {
 "id": "conc-12",
 "title": "Classic problems: producer-consumer, philosophers, readers-writers",
 "minutes": 38,
 "goal": "By the end you can build a producer-consumer pipeline that shuts down cleanly with poison pills, fix the dining philosophers deadlock two ways, and explain who starves under each readers-writers policy.",
 "warmup": {
  "q": "Three consumer threads take from a `BlockingQueue`. When the producers are done, the coordinator puts ONE poison pill, and each consumer stops when it takes a pill. What happens?",
  "options": ["All three consumers stop: they all see the pill", "One consumer stops; the other two wait in `take()` forever", "The queue throws, because a pill can only be taken once", "Nothing stops until the queue is garbage collected"],
  "answer": 1,
  "why": "A pill is just an element: the first consumer to take it removes it from the queue and stops. The other two find an empty queue and wait in `take()` forever. Anything that joins the consumers, such as a shutdown hook, hangs too. You need one pill per consumer."
 },
 "sections": [
  {
   "h": "Producer-consumer: a bounded queue between two speeds",
   "body": "Most of the concurrent code in a backend is this shape. Something produces work at one speed, such as a Kafka consumer polling records or request threads accepting payments, and something else processes it at another speed, such as a writer that inserts into Oracle. A `BlockingQueue` sits between them.\n\nBound the queue. A bounded queue is how a slow consumer pushes back on a fast producer: `put` waits when the queue is full, so the producer slows to the consumer's pace instead of filling memory. Lesson 9 of this track showed what the unbounded default does during an incident.\n\nThe hard part is stopping. Consumers wait in `take()`, and `take()` never returns on an empty queue. The standard answer is a **poison pill**: a special element that means \"no more work\". Three rules make it work:\n\n- Put the pills only after every producer has finished, so they land behind every real record.\n- Put one pill per consumer. A pill is taken once.\n- Compare against the pill by identity. A pill made with `new String(\"PILL\")` is a unique object, so a real record that happens to read `PILL` is still a record.\n\n" + pair(J_PILL, K_PILL) + "\n\nThe figure shows the queue at shutdown: the last real records, then the pills. Each consumer drains records until it hits a pill, so no record is left behind and no consumer is left waiting.\n\nThere are other ways to stop: interrupt the consumers, or have them `poll` with a timeout and check a flag. Interrupting is fast but drops whatever is still queued. Polling adds latency and a flag to get right. Pills are the clean choice when every queued record must be processed. The lab builds the whole pipeline.",
   "figure": {"svg": FIG, "caption": "Records first, pills last, one pill per consumer. Each consumer stops at its own pill, after every real record has been taken."},
   "try": {
    "title": "One pill per consumer, or not",
    "minutes": 3,
    "steps": [
     "Read `PoisonPills`. Two producers put 1,000 records each into a queue of 4; three consumers take them. After the producers finish, `main` puts the pills.",
     "Run it. Note how many records each consumer handled.",
     "Run it with `-Pargs=onepill`. Predict how many consumers are still waiting after one second, and in which thread state."
    ],
    "code": code("PoisonPills"),
    "expect": "With one pill each, all three consumers report their pill, their counts add up to 2,000, and `consumers still waiting: 0`. The split changes from run to run. With `onepill`, one consumer stops and two are still waiting: `consumers still waiting: 2 (WAITING in take)`. In a real service, that is a shutdown that never finishes."
   }
  },
  {
   "h": "Dining philosophers: five threads, five locks, one cycle",
   "body": "Five philosophers sit at a round table with one fork between each pair. To eat, a philosopher needs both neighbouring forks. Each one picks up the left fork, then the right.\n\nIt works most of the time. Then, one day, all five pick up their left fork at the same moment. Each now waits for the right fork, which the next philosopher holds as a left fork. Nobody puts a fork down. That is the deadlock from lesson 6 of this track, with five locks instead of two: mutual exclusion, hold and wait, no preemption, and a circular wait around the table. It is also what transfers look like when each one locks two of many accounts.\n\nThe simulator has three philosophers. Let them eat one at a time, then reset and give each one a single step first.\n\nThere are two standard fixes, and each removes a different condition.\n\n**Resource ordering** removes the circular wait. Number the forks and always take the lower-numbered one first. Philosophers 0 to 3 still take left then right, but philosopher 4 needs forks 4 and 0, so it takes fork 0 first. The cycle can't close.\n\n" + pair(J_ORDER, K_ORDER) + "\n\nA waiter removes the chance that everyone holds one fork. Only four of the five may sit down at once, so at least one seated philosopher can always get both forks. A `Semaphore(n - 1)` is the waiter:\n\n" + pair(J_WAITER, K_WAITER) + "\n\nA third fix, `tryLock` on the second fork with a random back-off, removes no-preemption, but brings back the livelock risk from lesson 6. Ordering is the one to use when you can number your resources. The waiter fits when you can't, or when you want to cap how many workers compete at all.",
   "sim": SIM,
   "try": {
    "title": "Freeze the table, then fix it two ways",
    "minutes": 4,
    "steps": [
     "Read `Philosophers`. Five philosophers try to eat 200 meals each, pausing 1 ms between their two forks. After 3 seconds, the demo asks the JVM which threads are deadlocked.",
     "Run it as is. Then run it with `-Pargs=ordered` and with `-Pargs=waiter`.",
     "Compare the meal counts and times. Why can the waiter version be faster than the ordered one?"
    ],
    "code": code("Philosophers"),
    "expect": "As is: almost no meals (0 or 1 in runs here) and `deadlocked philosophers: 5`, found by `ThreadMXBean` because the forks are `ReentrantLock`s. Ordered and waiter: all 1,000 meals in about a second, and no deadlock. The waiter version was a little faster here, because with ordering two philosophers both start by reaching for fork 0, which serializes them more."
   }
  },
  {
   "h": "Readers-writers: decide who waits",
   "body": "Many threads read a shared table and a few write it: BIN ranges read on every payment, refreshed once an hour. Readers can share; a writer needs the table to itself. The question is what happens when both are waiting, and each answer starves somebody.\n\nReaders first lets a new reader in whenever no writer is inside. With a steady stream of overlapping readers, the reader count never drops to zero, so the writer never gets in. The refresh starves.\n\nWriters first makes new readers wait as soon as a writer is waiting. The refresh gets in quickly, but under a stream of writers, readers starve.\n\nA fair policy serves threads in arrival order. Nobody starves, and throughput drops, because readers that could have shared now wait behind a writer that arrived first.\n\nThe JDK's `ReentrantReadWriteLock` picks a middle path. In its default non-fair mode it doesn't promise an order, but a thread that asks for the read lock waits if the thread at the head of the queue wants to write. In practice that keeps a writer from being starved by a stream of new readers. Fair mode gives strict arrival order:\n\n" + pair(J_RW, K_RW) + "\n\nThe Try it shows the difference. A textbook readers-first lock, written with `synchronized`, makes a writer wait as long as the readers keep coming, while `ReentrantReadWriteLock` lets it in within a couple of milliseconds.\n\nBefore choosing a policy, ask whether readers need a lock at all. If the writer replaces the whole table, the snapshot pattern from lesson 11 of this track lets readers read an immutable map with no lock and no waiting, and the question of who starves goes away. Oracle takes the same approach with multiversion reads: readers see a consistent older version and don't wait for writers.",
   "try": {
    "title": "Starve a writer",
    "minutes": 3,
    "steps": [
     "Read `ReadersWriters`. Four readers hold the lock for 2 ms at a time, overlapping, for 1.5 seconds. 100 ms in, one writer asks for the lock. The demo measures how long it waits, first with a hand-written readers-first lock, then with `ReentrantReadWriteLock`.",
     "Predict both waits.",
     "Run it."
    ],
    "code": code("ReadersWriters"),
    "expect": "Readers-first: the writer waits about 1,400 ms, until the readers stop on their own. `ReentrantReadWriteLock`: about 1 to 2 ms, because new readers queue behind the waiting writer instead of overtaking it."
   },
   "refs": [
    {"title": "jcstress samples, including Classic_01_DiningPhilosophers and Classic_02_ProducerConsumerProblem", "url": "https://github.com/openjdk/jcstress/tree/master/jcstress-samples", "kind": "read"}
   ]
  }
 ],
 "analogy": "Producer-consumer is a kitchen pass: cooks put plates on a shelf with room for eight, and waiters take them. When the shelf is full the cooks wait, and at closing time the head chef puts one \"kitchen closed\" card on the shelf for each waiter. Dining philosophers is five people sharing five chopsticks; numbering the chopsticks and always grabbing the lower number first stops the standoff. Readers-writers is a museum room: visitors can share it, but the restorer needs it empty, and someone has to decide whether new visitors may keep walking in while the restorer waits at the door. The analogy breaks at the closing card: a waiter who finds it would tell the others. A consumer that takes a pill just stops, and the other consumers learn nothing.",
 "in_your_world": "The Kafka-to-Oracle path in a payment service is producer-consumer: a poll loop produces records, a worker pool settles them, and a bounded queue between them is what keeps a slow database from turning into an out-of-memory crash. Shutdown is where it usually goes wrong. On SIGTERM, Quarkus gives the application a grace period, and the pipeline has to stop polling, drain what is queued, commit offsets for what it finished, and stop. The worked example shows that order. Dining philosophers is any job that locks several resources at once: transfers that lock two accounts, a netting run that locks a merchant and a settlement batch. Readers-writers is every reference table you refresh while serving traffic.",
 "mistake": "The most common mistake is getting the poison pills wrong at shutdown: putting a single pill for several consumers, or putting the pills before every producer has finished. With one pill, the other consumers wait in `take()` forever and the shutdown hangs until the platform kills the pod, so whatever they were holding is lost. With pills sent too early, consumers stop while producers are still putting, the bounded queue fills, and the producers block forever instead. Both bugs pass every test that never shuts the pipeline down. The fix is the order in this lesson: stop the producers, join them, put one pill per consumer, then join the consumers with a deadline.",
 "compare": {
  "title": "Stopping consumers: pills in Java, a closed channel in Kotlin coroutines",
  "java": {"title": "Java, BlockingQueue", "src": """for (int i = 0; i < 4; i++) {
    pool.add(start(() -> {
        while (true) {
            String r = queue.take();
            if (r == PILL) return;            // each consumer needs its own pill
            settle(r);
        }
    }));
}
for (Thread p : producers) p.join();
for (int i = 0; i < 4; i++) queue.put(PILL);   // 4 consumers, 4 pills
for (Thread c : pool) c.join();"""},
  "kotlin": {"title": "Kotlin, kotlinx.coroutines Channel", "src": """// a Channel can be closed, so there are no pills
coroutineScope {
    val records = Channel<String>(capacity = 8)
    val producers = sources.map { src -> launch { for (r in src) records.send(r) } }
    repeat(4) { launch { for (r in records) settle(r) } }   // each loop ends when the channel is closed AND empty
    producers.joinAll()
    records.close()                                          // "no more records": consumers drain, then stop
}"""},
  "note": "With threads and a `BlockingQueue`, Kotlin code looks just like the Java version: the queue has no notion of \"closed\", so you still need one pill per consumer, compared with `===`. The real difference comes with coroutines. A `Channel` can be closed: `close()` means no more elements, and every `for (r in records)` loop ends once the channel is closed and empty, however many consumers there are. That removes the whole class of pill-counting bugs. `coroutineScope` also waits for every consumer it launched, so there is no join loop to forget. The coroutines track covers channels properly."
 },
 "worked": {
  "title": "Shut a Kafka-to-database pipeline down without losing records",
  "steps": [
   {"say": "A pipeline polls Kafka on two producer threads and settles records on four consumer threads, through a bounded queue. On SIGTERM, someone wrote this. What happens to the records already in the queue, and to the batch a consumer is halfway through?",
    "code": J_SHUT_BAD, "lang": "java", "alt_code": K_SHUT_BAD, "alt_lang": "kotlin"},
   {"say": "Interrupting a consumer that waits in `take()` stops it at once, so everything still queued is dropped. A consumer in the middle of a database call may abort it halfway. And a producer may have polled records it never put. Because offsets were committed only for processed records, Kafka will redeliver what was lost, but the shutdown did a lot of work for nothing, and only idempotent settlement (lesson 3 of this track) keeps the redelivery safe.", "code": "", "lang": ""},
   {"say": "The orderly version, with subgoal labels. `running` is a `volatile` flag the producers check in their poll loops.",
    "code": J_SHUT, "lang": "java", "alt_code": K_SHUT, "alt_lang": "kotlin"},
   {"say": "Before reading on, explain to yourself: why must step 2 finish before step 3 starts? Answer: a pill put while a producer is still running can land in front of that producer's last records. A consumer that takes the pill stops; with all consumers stopped and the queue bounded, the producer then blocks in `put` forever, and the shutdown hangs on step 2 of the next attempt. Joining the producers first guarantees that every real record is already ahead of the pills.", "code": "", "lang": ""},
   {"say": "Step 5 is the safety net. If the database is down, the consumers can't drain the queue within the grace period. Interrupting them is then the right call: the records they didn't finish were never committed to Kafka, so another instance will process them after a rebalance. Orderly shutdown and idempotent processing work together; neither is enough alone.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A pipeline that stops cleanly, and a table that can't deadlock",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/SettlementPipeline.java", f"{lab}/main/{P}/DiningTable.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l12.*'",
  "steps": [
   "Run the tests. All six fail. The three pipeline tests hit `UnsupportedOperationException`. The three `DiningTable` tests time out after 15 seconds: the philosophers deadlocked.",
   "Part 1: write `SettlementPipeline.run`. Create an `ArrayBlockingQueue` of `capacity` and a unique pill (`new String(\"PILL\")`). Start the consumers: each loops on `take()`, stops at the pill (compared with `==`), and otherwise calls `process` and counts.",
   "Start one producer thread per inner list. Join all producers, then put one pill per consumer, then join all consumers, then return the count.",
   "Part 2: fix `DiningTable.dine` so every philosopher takes the lower-numbered fork first. Keep `reachForTheOtherFork()` between the two forks.",
   "Run the tests until all six pass, then twice more."
  ],
  "hints": [
   "Count processed records with an `AtomicInteger`: several consumers increment it at once.",
   "The second pipeline test checks that `process` is never called after `run` returns. If it fails, you return before joining every consumer.",
   "For the table, compute `a = seat` and `b = (seat + 1) % seats`, then lock `forks[min(a, b)]` before `forks[max(a, b)]`. Only the last philosopher's order actually changes, and that is enough to break the cycle."
  ],
  "done_when": "All six tests in `ClassicProblemsTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Poison-pill shutdown from memory",
  "minutes": 4,
  "prompt": "Close this page. Given started-but-not-yet-running producer and consumer threads and their shared `BlockingQueue<String>`, write the coordinator that runs the pipeline to completion with poison pills, plus the consumer's loop. Check: when are the pills put, how many, and how does a consumer recognize one?",
  "answer": {"lang": "java", "src": J_DRILL, "alt": {"lang": "kotlin", "title": "Kotlin", "src": K_DRILL}}
 },
 "recap": [
  "Producer-consumer: a bounded `BlockingQueue` between two speeds; `put` waiting on a full queue is back-pressure.",
  "Poison pills: put them only after every producer has finished, one per consumer, and compare by identity.",
  "Dining philosophers is a circular wait. Take resources in one global order, or limit the competitors to n - 1 with a semaphore.",
  "Readers-first starves writers, writers-first starves readers, fair order starves no one and costs throughput.",
  "`ReentrantReadWriteLock` makes new readers wait behind a queued writer; fair mode gives strict arrival order.",
  "If writers replace the whole table, an immutable snapshot removes the readers-writers problem entirely."
 ],
 "quiz": [
  {"q": "A coordinator puts the poison pills for 4 consumers right after starting the producers, without waiting for them. The queue is bounded. What can happen?",
   "options": ["Nothing: the pills wait at the back of the queue", "The consumers take the pills early and stop, the queue fills, and the producers block in `put` forever", "The pills are rejected because the queue is full", "Each consumer processes exactly one record"],
   "answer": 1, "why": "Pills are ordinary elements in arrival order. Put early, they sit in front of records that producers add later. Consumers stop at them, nothing drains the queue any more, and the producers block once it is full. Join the producers first."},
  {"q": "Five philosophers each take the left fork, then the right one, and sometimes all deadlock. Which change removes the deadlock?",
   "options": ["Make every fork a fair `ReentrantLock`", "Add a random sleep before picking up the left fork", "Always take the lower-numbered fork first, so the last philosopher reaches right first", "Use `synchronized` instead of `ReentrantLock`"],
   "answer": 2, "why": "With one global order, no cycle of waiting can form, so circular wait is gone. Fair locks change who gets a free fork next, not the cycle. A random sleep only makes the bad timing rarer. `synchronized` deadlocks exactly the same way."},
  {"q": "A hand-written readers-first lock protects a BIN table. Readers arrive constantly and overlap. The hourly refresh calls `writeLock()`. What happens?",
   "options": ["The refresh waits until the readers stop arriving, which may be never: writer starvation", "The refresh gets in within one read's duration", "The refresh throws `IllegalStateException`", "Readers and the writer take turns"],
   "answer": 0, "why": "Readers-first admits a new reader whenever no writer is inside, so the reader count never reaches zero while readers overlap. The writer waits for a moment that never comes. `ReentrantReadWriteLock` makes new readers queue behind a waiting writer, and a snapshot avoids locking reads at all."},
  {"q": "From synchronizers: the waiter fix for five philosophers uses a `Semaphore`. Why `new Semaphore(4)` and not `new Semaphore(5)`?",
   "options": ["To save one thread", "With 4 seated, at least one of them can always pick up both forks, so the cycle can't involve all five", "A semaphore can't have more permits than threads", "Fairness requires one fewer permit than threads"],
   "answer": 1, "why": "With five permits, all five can sit, each take a left fork and deadlock as before. With four, at most four hold a fork, and five forks between four people means at least one of them can take both. Permits limit how many compete, which is what breaks the cycle here.",
   "from": "conc-10"},
  {"q": "A consumer checks `if (record.equals(\"POISON\")) break;`, and the pill is the literal `\"POISON\"`. What is the risk?",
   "options": ["`equals` is too slow for a hot loop", "None: a real record never contains that text", "The pill might be garbage collected", "A real record with that text stops a consumer early and is never processed"],
   "answer": 3, "why": "Merchant references and free-text fields can contain anything, including the pill's text. With `equals`, such a record shuts a consumer down and is silently dropped. A pill created as a unique object and compared with `==` (or `===` in Kotlin) can't be confused with data."}
 ],
 "flashcards": [
  {"front": "Poison pills: how many, and when do you put them?", "back": "One per consumer, and only after every producer has finished putting."},
  {"front": "Why compare a poison pill with `==` rather than `equals`?", "back": "So a real record with the same text isn't mistaken for the pill. Make the pill a unique object, such as `new String(\"PILL\")`."},
  {"front": "Why bound the queue between producers and consumers?", "back": "So `put` makes producers wait when consumers fall behind (back-pressure), instead of buffering until memory runs out."},
  {"front": "Which deadlock condition does \"always take the lower-numbered fork first\" remove?", "back": "Circular wait: with one global order, no cycle of waiting threads can form."},
  {"front": "How does a `Semaphore(n - 1)` \"waiter\" prevent the dining philosophers deadlock?", "back": "At most n - 1 philosophers compete for n forks, so at least one can always get both."},
  {"front": "Readers-first lock: who starves?", "back": "Writers. With overlapping readers the reader count never reaches zero, so the writer never gets in."},
  {"front": "What does non-fair `ReentrantReadWriteLock` do when a writer is waiting and a new reader arrives?", "back": "The reader usually waits if the writer is at the head of the queue, so a stream of readers doesn't starve the writer."}
 ],
 "terms": [
  {"term": "Producer-consumer", "plain": "Threads that create work hand it to threads that process it, usually through a queue."},
  {"term": "Poison pill", "plain": "A special queue element that tells one consumer to stop."},
  {"term": "Back-pressure", "plain": "A full bounded queue making producers wait, so they slow to the consumers' pace."},
  {"term": "Dining philosophers", "plain": "The classic deadlock: each thread holds one resource and waits for its neighbour's."},
  {"term": "Resource ordering", "plain": "Taking locks in one global order so no cycle of waiting can form."},
  {"term": "Readers-writers", "plain": "Sharing data between many readers and a few writers, and deciding who waits."},
  {"term": "Writer starvation", "plain": "A writer that never gets in because readers keep holding the lock."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate how you would shut down a pipeline of 2 producers and 4 consumers so that no queued record is lost and no thread is left waiting.",
  "answer": "First stop the producers from taking new work and wait for them to finish, so every real record is already in the queue. Then put four poison pills, one per consumer, behind those records. Each consumer keeps taking records until it takes a pill, so the queue drains completely and each one stops exactly once. The pill is a unique object compared with `==`, so no real record can look like one. Finally, join the consumers with an overall deadline, and interrupt any that are still busy when it passes; whatever they didn't finish was never acknowledged, so it will be redelivered and must be processed idempotently."
 },
 "deeper": {
  "minutes": 10,
  "body": "Poison pills are one of several ways to stop consumers. Executors use interruption: `shutdownNow()` interrupts every worker, and tasks are expected to stop when interrupted, as lesson 2 of this track described. A `poll(timeout)` loop that checks a `volatile` flag is simple but makes shutdown wait for up to one timeout, and adds a flag that every loop must check. Kotlin channels and reactive streams have completion built in, which is why they need no pills. Kafka's own consumer has `wakeup()`, which makes a blocked `poll()` throw `WakeupException`, the usual way to stop a poll loop from another thread.\n\nThe dining philosophers problem has more solutions than the two here. Chandy and Misra's solution passes \"dirty\" and \"clean\" forks between neighbours with requests, which avoids both deadlock and starvation and works across machines, at the cost of messages. A plain `tryLock` with back-off works, but needs randomness to avoid livelock. All of them are ways of removing one of the four conditions from lesson 6.\n\nReaders-writers shows up all over databases. Oracle uses multiversion read consistency: a query reads the version of each block as of when the query started, so readers don't wait for writers and writers don't wait for readers. That is the immutable-snapshot idea from lesson 11 applied to storage, and it's why the problem rarely appears at the SQL level. Writers still wait for other writers on the same rows.\n\nIf you want to see these problems under a real stress harness, the jcstress samples include `Classic_01_DiningPhilosophers` and `Classic_02_ProducerConsumerProblem`. The next lesson shows how to run jcstress and read its results."
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
