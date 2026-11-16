import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/vthreads/src"
P = "java/workbench/vthreads/l03"
K = "kotlin/workbench/vthreads/l03"
read = lambda p: (ROOT / p).read_text()


def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": f"./gradlew :vthreads:demo -Pmain=workbench.vthreads.l03.{name}",
            "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": f"./gradlew :vthreads:demo -Pmain=workbench.vthreads.l03.{name}Kt",
                    "file": f"{lab}/demo/{K}/{name}.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 680 270" role="img" aria-label="Thousands of virtual threads, one per order, wait parked at a Semaphore with 20 permits, like slips waiting for one of 20 tokens. At most 20 calls at a time pass through to the database.">'
    '<text class="t-s t-m" x="95" y="40" text-anchor="middle">one virtual thread per order</text>'
    '<rect class="box-ok" x="20" y="56" width="150" height="34" rx="8"/>'
    '<text class="t-s" x="95" y="78" text-anchor="middle">VT 20: has a permit</text>'
    '<rect class="box-dim" x="20" y="100" width="150" height="34" rx="8"/>'
    '<text class="t-s" x="95" y="122" text-anchor="middle">VT 21: parked</text>'
    '<rect class="box-dim" x="20" y="144" width="150" height="34" rx="8"/>'
    '<text class="t-s" x="95" y="166" text-anchor="middle">VT 22: parked</text>'
    '<text class="t-s t-m" x="95" y="206" text-anchor="middle">4,977 more parked,</text>'
    '<text class="t-s t-m" x="95" y="224" text-anchor="middle">about 2 KB of heap each</text>'
    '<line class="ln-a" x1="170" y1="130" x2="246" y2="130" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="208" y="122" text-anchor="middle">acquire()</text>'
    '<rect class="box-a" x="250" y="56" width="160" height="150" rx="8"/>'
    '<text class="t t-code" x="330" y="98" text-anchor="middle">Semaphore(20)</text>'
    '<text class="t-s" x="330" y="122" text-anchor="middle">the hook of 20 tokens</text>'
    '<text class="t-s" x="330" y="146" text-anchor="middle">no permit: park</text>'
    '<text class="t-s" x="330" y="170" text-anchor="middle">release(): wake one</text>'
    '<line class="ln-a" x1="410" y1="130" x2="476" y2="130" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="443" y="122" text-anchor="middle">20 at once</text>'
    '<rect class="box" x="480" y="56" width="180" height="150" rx="8"/>'
    '<text class="t" x="570" y="100" text-anchor="middle">the database</text>'
    '<text class="t-s" x="570" y="130" text-anchor="middle">20 connections</text>'
    '<text class="t-s" x="570" y="154" text-anchor="middle">50 ms per call</text>'
    '<text class="t-s t-a" x="340" y="254" text-anchor="middle">Little\'s law: 20 permits / 0.05 s = at most 400 calls a second</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Picture the restaurant from How virtual threads work, with four waiters and a board of order slips. Slips cost almost nothing, so the manager writes a fresh one for every table and throws it away after the meal. One evening a tour bus arrives, and 5,000 orders go up on the rail within a minute. The waiters are calm. The grill is not: it has room for 20 pans, and 5,000 orders want it at once.

Our shop has the same evening. It saves every order in a database, where it keeps its data, and the database accepts 20 connections, open lines to it, at a time. With a virtual thread per order, nothing stops all 5,000 from asking at once.

The fix most people reach for is an old friend, a pool of 20 threads. It's a fair choice, because pools kept our numbers in check through the executors track, and it works. It also makes every other part of each order wait in the same line.

In this lesson, we'll start virtual threads, give every task its own, and limit the database alone, with a semaphore. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_WAYS = """// 1. a one-off, no name
Thread a = Thread.startVirtualThread(() -> checkout(basket));

// 2. a builder, when you want a name in thread dumps
Thread b = Thread.ofVirtual().name("checkout-", 0).start(() -> checkout(basket));   // checkout-0

// 3. created now, started later
Thread c = Thread.ofVirtual().unstarted(() -> checkout(basket));
c.start();

// 4. a ThreadFactory, for libraries that ask for one
ThreadFactory receipts = Thread.ofVirtual().name("receipt-", 0).factory();
ExecutorService named = Executors.newThreadPerTaskExecutor(receipts);

// 5. what you'll use most: one new virtual thread per task
ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor();"""
K_WAYS = """// 1. a one-off, no name
val a = Thread.startVirtualThread { checkout(basket) }

// 2. a builder, when you want a name in thread dumps
val b = Thread.ofVirtual().name("checkout-", 0).start { checkout(basket) }   // checkout-0

// 3. created now, started later
val c = Thread.ofVirtual().unstarted { checkout(basket) }
c.start()

// 4. a ThreadFactory, for libraries that ask for one
val receipts = Thread.ofVirtual().name("receipt-", 0).factory()
val named = Executors.newThreadPerTaskExecutor(receipts)

// 5. what you'll use most: one new virtual thread per task
val perTask = Executors.newVirtualThreadPerTaskExecutor()"""

S0 = f"""Before we give every order its own thread, we need a way to make one. A **virtual thread** is a Java thread that the JDK runs on a few platform threads, called carriers. (A platform thread is one thread of the operating system.) The JDK sets a virtual thread aside whenever it blocks, so it's cheap enough to have one per task. JDK 21 has no `new VirtualThread()`. You start one through `Thread.Builder`, a small object that collects settings such as a name and then makes threads, or through an executor. Both lists below show the same five ways:

{pair(J_WAYS, K_WAYS)}

Read them in order. The first starts a thread at once, with no name. The second gives it a name, and `name("checkout-", 0)` numbers its threads: the first is `checkout-0`, the next `checkout-1`. The third makes the thread now and starts it later. The fourth hands out a `ThreadFactory`, an object that makes threads on request, for code that wants one. A builder isn't safe to share between threads, so set it up in one place. The factory it returns is safe, so share that.

The fifth is the one for normal code. It gives you a `Future` for each task, a handle on its result, its `close()` waits for every task, and most libraries already know how to take an `ExecutorService`. Use a builder when you start one long-lived thread, such as a helper that emails receipts all day, and want a name you can find in a thread dump, the list of every thread a running program has. Virtual threads have no name by default, which makes a dump of 50,000 of them hard to read.

All five give you ordinary `Thread` objects. `join`, `interrupt` and `isAlive` work as usual, and `isVirtual()` tells you which kind you have. `BuildersDemo`, in the Try it below, starts one of each and lets each one print from inside itself. Its run here began:

```text
Thread.startVirtualThread          name=''           virtual=true  daemon=true
Thread.ofVirtual().name().start    name='checkout-7' virtual=true  daemon=true
Thread.ofVirtual().unstarted       name=''           virtual=true  daemon=true
```

Every line says `daemon=true`. A **daemon** thread is one the JVM doesn't wait for when the program ends, and a virtual thread is always one. You can't change that, as the Try it shows.

We can make one thread now. The next step is to make one for every order."""

# ---------------------------------------------------------------- section 1
J_FAN = """List<Receipt> saveAll(List<Order> orders) throws InterruptedException, ExecutionException {
    try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
        // 1. fork: start every save before waiting for any
        List<Future<Receipt>> futures = new ArrayList<>();
        for (Order order : orders) futures.add(perTask.submit(() -> database.save(order)));
        // 2. join: collect the answers in input order
        List<Receipt> receipts = new ArrayList<>();
        for (Future<Receipt> f : futures) receipts.add(f.get());
        return receipts;
    }   // 3. close(): waits for any task still running
}"""
K_FAN = """fun saveAll(orders: List<Order>): List<Receipt> =
    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->
        // 1. fork: start every save before waiting for any
        val futures = orders.map { order -> perTask.submit(Callable { database.save(order) }) }
        // 2. join: collect the answers in input order
        futures.map { it.get() }
    }   // 3. close(): waits for any task still running"""

S1 = f"""`newVirtualThreadPerTaskExecutor()` starts a brand-new virtual thread for every task you submit. It keeps no threads around and has no queue. Its Javadoc says it plainly: the number of threads it creates is unbounded.

Since JDK 19, `ExecutorService` is `AutoCloseable`, so it works in try-with-resources. `close()` shuts the executor down and then waits until every submitted task has finished. That makes a **fan-out**, starting many calls at once and then collecting all their results, the size of one block. Both versions save every order on its own virtual thread:

{pair(J_FAN, K_FAN)}

Let's walk through it. First we submit every order, so all the saves start before we wait for any of them. Then we call `get()` on each future in the order we submitted them, so the receipts come back in the orders' order. Finally `close()`, at the end of the block, waits for anything still running. Read aloud, the method says: give every order its own thread, then collect the answers in order.

Create the executor where the work starts, and let it end where the work ends. An executor per batch costs almost nothing, because it owns no threads. And when the method returns, no thread it started is still running. That promise gets a name and an API of its own in lesson 5 of this track.

Two details trip people up. First, start every task before you call `get()` on any of them. A loop that submits one order and then waits for it saves the batch one order at a time, on 5,000 threads. With a 35 ms save, that's almost three minutes (5,000 × 0.035 s = 175 s) with one call in flight. That's Little's law from The thread-per-request wall (inside at once = arrival rate × time inside) with only one order ever inside, and 5,000 virtual threads didn't help at all.

Second, `get()` reports a failed task as an `ExecutionException` whose cause is the real exception. The other tasks keep running when one fails, and `close()` still waits for them. Stopping them is also lesson 5's topic.

Now look at what our fan-out does to the database. Nothing in the block limits how many orders are saved at once. A copy of the lab's test that prints its count sent 5,000 orders through it, at 10 ms per save. In one run, 3,069 of them were inside the fake database at the same moment, and in another, 4,772. The real database accepts 20.

The executor isn't broken. It does exactly what it promises: one thread per task, no limit. The limit belongs somewhere else, and the first place people put it is the wrong one."""

# ---------------------------------------------------------------- section 2
J_POOL = """// Naive: keeps the database at 20, and everything else too
ExecutorService pool = Executors.newFixedThreadPool(20, Thread.ofVirtual().factory());
pool.execute(() -> {
    Stock stock = warehouse.check(order);    // 60 ms, needs no limit, but waits for a pool thread anyway
    database.save(order, stock);             // 10 ms, the only call that needs the limit
});"""
K_POOL = """// Naive: keeps the database at 20, and everything else too
val pool = Executors.newFixedThreadPool(20, Thread.ofVirtual().factory())
pool.execute {
    val stock = warehouse.check(order)       // 60 ms, needs no limit, but waits for a pool thread anyway
    database.save(order, stock)              // 10 ms, the only call that needs the limit
}"""

S2 = f"""Thread pools exist for two reasons. Platform threads are costly to start, so a pool reuses them, and a fixed pool caps how much work runs at once. Neither reason survives virtual threads.

A virtual thread costs about as much to make as a small object, so reusing one saves almost nothing. And a pool is the wrong place for a cap, because it caps everything the task does, not just the one call that needs a limit.

Here's the habit, in code that compiles and runs fine. Each order asks the stock service, which needs no limit, and then saves the order in the database, which accepts 20 at once:

{pair(J_POOL, K_POOL)}

In the restaurant, this is keeping only 20 slips and making each new table wait for a used one. The grill never holds more than 20 pans. Neither does the coffee machine, or the salad bar.

Let's measure the cost. `PoolVsSemaphoreDemo`, in the Try it below, runs 1,000 such orders. Predict the pool's time first: each task holds a pool thread for 70 ms, so 1,000 tasks take 1,000 / 20 × 70 ms = 3.5 s. One run on this busy machine printed:

```text
pool of 20 virtual threads:        3,628 ms
```

The prediction held. To give the pool its due, the database never saw more than 20, and nothing broke. But the stock checks needed no limit, and they waited in line anyway. If only the save were limited, all 1,000 stock checks would overlap. The batch would take about 60 ms plus 1,000 / 20 × 10 ms, about 0.56 s. The demo's second line tries exactly that, and the next section explains how.

A reused thread brings one more problem. A `ThreadLocal`, a variable with a separate value for each thread, survives from one task to the next on a pooled thread. Lesson 4 of this track covers that trap.

JEP 444, the design document behind virtual threads, gives the rule in a few words.

**Never pool virtual threads. Create one per task, and put the limit on the resource.**

Pools are still the right tool for platform threads that compute. A `newFixedThreadPool(cores)` for checksums or image resizing keeps that work bounded, and off the virtual thread scheduler. The rule is about virtual threads only.

So the limit moves to the database itself. We need something that lets 20 orders in, makes the rest wait, and makes waiting cheap."""

# ---------------------------------------------------------------- section 3
J_STORE = """final class OrderStore {
    private final Semaphore connections = new Semaphore(20);   // 1. one per resource, shared by all callers
    private final Database database;

    OrderStore(Database database) { this.database = database; }

    Receipt save(Order order) throws InterruptedException {
        connections.acquire();                               // 2. acquire on the line before the try
        try {
            return database.save(order);                     // only the call that needs the limit
        } finally {
            connections.release();                           // 3. always give it back
        }
    }
}"""
K_STORE = """class OrderStore(private val database: Database) {
    private val connections = Semaphore(20)                  // 1. one per resource, shared by all callers

    fun save(order: Order): Receipt {
        connections.acquire()                                // 2. acquire on the line before the try
        try {
            return database.save(order)                      // only the call that needs the limit
        } finally {
            connections.release()                            // 3. always give it back
        }
    }
}"""

S3 = f"""Back to the restaurant. The grill has room for 20 pans, so a hook beside it holds 20 metal tokens. Before an order goes on the grill, it takes a token, and when it comes off, the token goes back on the hook. An order that finds the hook empty waits on the board, which costs a slip of paper and no waiter. The rest of the kitchen carries on without tokens.

In Java, the hook is a **Semaphore**, the car park from Synchronizers. It holds a number of **permits**, here 20: the tokens. `acquire()` takes a permit, and waits if none is left. `release()` gives one back and wakes one waiting thread. On a virtual thread, waiting in `acquire()` parks the thread, that is, sets it aside until a permit comes free. So 5,000 waiting orders cost 5,000 small heap objects and no platform threads.

The pattern has three rules, numbered in the code:

{pair(J_STORE, K_STORE)}

First, the semaphore lives with the resource, as one field on the object every order uses. Second, `acquire()` sits on the line before the `try`, so a thread that is interrupted while it waits never releases a permit it didn't get. Third, `release()` sits in the `finally`, so a save that throws still gives its permit back.

`PoolVsSemaphoreDemo`'s second line runs the same 1,000 orders, with one virtual thread each and a `Semaphore(20)` around the save alone:

```text
pool of 20 virtual threads:        3,628 ms
virtual thread per task + Semaphore(20):   604 ms
```

Same database limit, six times faster, because all 1,000 stock checks overlapped.

Here the restaurant picture breaks, and the break matters. A real token is a thing you can hold; a permit is only a count. The semaphore never checks who hands one back, so a `release()` from a thread that never acquired adds a 21st permit, as Synchronizers showed. That's why rule two keeps `acquire()` outside the `try`.

Rule one fails just as quietly. Picture a handler that creates `new Semaphore(20)` for each request. Every request gets its own hook with 20 tokens, which is generous, and limits nothing: no thread ever waits, and all 5,000 reach the database.

Pick the number from the resource's side, such as the database's connection count. Then check it with Little's law. Twenty permits on a 50 ms call allow at most 20 / 0.05 s = 400 calls a second. So 1,000 orders take about 2.5 s, however many threads you start. `FanOutKotlin`, in the compare block, took 2,639 ms. If orders arrive faster than 400 a second, the line of waiters grows without end.

Waiting forever is rarely what a customer wants. `tryAcquire(200, MILLISECONDS)` returns `false` if no permit came in time, so the shop can answer "busy, try again" at once instead of after a long wait. That's **load shedding**, turning work away early when you're over capacity. A limit like this, one per slow thing your program calls, is the bulkhead from Sizing a pool.

One last trap: an order that needs two limited things uses two semaphores, one after the other. Don't hold one permit while you wait for another. It ties up the first resource for nothing, and two code paths that take them in opposite orders can deadlock, each waiting forever for the other, exactly like two locks.

**Threads are cheap, and the database is not. Give every task its own virtual thread, and every scarce resource one shared semaphore.**

That's the whole pattern. The lab builds it from scratch and proves the limit with 5,000 calls."""

ASIDE3 = {
    "title": "What if my code runs in Kotlin coroutines?",
    "body": "Then use the coroutine library's own semaphore. kotlinx.coroutines has `kotlinx.coroutines.sync.Semaphore`, whose `acquire()` is a `suspend` function, and a `withPermit { }` block that releases the permit for you. A coroutine waiting there suspends and frees its thread. The JDK's `Semaphore.acquire()` inside a coroutine would block the thread the coroutine runs on, and every other coroutine waiting for that thread. On virtual threads, use the JDK's semaphore, as this lesson does.",
}

# ---------------------------------------------------------------- closing
CLOSING = """We started with free slips and a grill with room for 20 pans. One virtual thread per order made 5,000 orders cheap to hold. A pool of 20 kept the grill safe but made the coffee wait too, and one shared semaphore kept the grill at 20 while everything else ran free.

Now search your own code for `Thread.ofVirtual().factory()` passed to a fixed pool, and for `new Semaphore(` inside a method that runs once per request. The first is a pool doing a semaphore's job. The second limits nothing.

Next, we'll look at the traps that remain. What can still stop a virtual thread from letting go of its carrier, and what happens to a `ThreadLocal` cache with a million threads?"""

L = {
 "id": "vt-03",
 "title": "Using virtual threads: one per task, limits with semaphores",
 "minutes": 35,
 "goal": "By the end you can start virtual threads the right way, fan out thousands of blocking calls with one virtual thread per task, and cap what a scarce resource sees with a shared Semaphore instead of a pool.",
 "opening": OPENING,
 "warmup": {
  "q": "The shop's database accepts 20 connections at once. You move a batch of 10,000 orders to virtual threads. What is the right way to stay under the database's limit?",
  "options": [
   "`Executors.newFixedThreadPool(20, Thread.ofVirtual().factory())`: a pool of 20 virtual threads",
   "`Executors.newVirtualThreadPerTaskExecutor()`, and one shared `Semaphore(20)` acquired around the database call",
   "`Executors.newVirtualThreadPerTaskExecutor()` on its own, since virtual threads limit themselves to the number of cores",
   "A new `Semaphore(20)` inside each order's task"
  ],
  "answer": 1,
  "why": "Limit the resource, not the threads. A pool of 20 also limits everything else each task does, so work that needs no limit waits too. The per-task executor has no limit at all: it will start 10,000 virtual threads. A semaphore created inside each task gives every task its own 20 permits, which limits nothing. One shared semaphore around the call is the only option that keeps the database at 20."
 },
 "sections": [
  {
   "h": "Five ways to start a virtual thread, and the one you'll use most",
   "body": S0,
   "try": {
    "title": "Start one of each",
    "minutes": 3,
    "steps": [
     "Run `BuildersDemo`. Each line is printed from inside the new thread.",
     "Predict before you look: which ones have a name, and what does `isDaemon()` say for each?",
     "Add `.daemon(false)` before `.start(...)` on the `Thread.ofVirtual().name(\"checkout-7\")` line (in either file) and run again. What happens?"
    ],
    "code": demo("BuildersDemo"),
    "expect": "Only `checkout-7`, `receipt-0` and `receipt-1` have names; the rest print an empty name. Every line says `virtual=true  daemon=true`. The `.daemon(false)` edit doesn't compile, in Java or in Kotlin: `Thread.ofVirtual()` returns a `Thread.Builder.OfVirtual`, which has no `daemon` method, because virtual threads are always daemon threads."
   }
  },
  {
   "h": "One order, one virtual thread: a fan-out in one try block",
   "body": S1
  },
  {
   "h": "The old habit fails: a pool of 20 virtual threads, and what it costs",
   "body": S2,
   "try": {
    "title": "A pool vs a semaphore, same limit",
    "minutes": 4,
    "steps": [
     "Read `PoolVsSemaphoreDemo`. Each order makes a 60 ms stock check and a 10 ms save, and the database allows 20 saves at once.",
     "Predict both times with the arithmetic above, then run it.",
     "Change `DB_LIMIT` to 50 and predict again. Which version speeds up more?"
    ],
    "code": demo("PoolVsSemaphoreDemo"),
    "expect": "The pool takes about 3.5 s (3,610 to 3,736 ms in busy runs here) and the semaphore version about 0.6 s (604 to 622 ms). With a limit of 50, the pool drops to about 1.4 s (1,000 / 50 × 70 ms) and the semaphore version to about 0.26 s (60 ms + 1,000 / 50 × 10 ms). Both keep the database at its limit; only the pool also slows down the work that needs no limit."
   }
  },
  {
   "h": "Twenty tokens at the grill: one shared Semaphore in front of the database",
   "body": S3,
   "figure": {"svg": FIG, "caption": "Thousands of virtual threads park cheaply at the semaphore, like slips waiting for a token. Only 20 at a time reach the database, and Little's law gives the throughput that follows."},
   "aside": ASIDE3,
   "try": {
    "title": "Shed load instead of queueing forever",
    "minutes": 4,
    "steps": [
     "`ShedLoadDemo` sends 1,000 requests at once through a `Semaphore(20)` guarding a 50 ms database call. Each request waits at most 200 ms for a permit, then gives up.",
     "Predict how many get served. Hint: in 200 ms each permit can serve about 200 / 50 = 4 calls, plus the first round.",
     "Run it, then try `-Pargs='20 50 2000'` and `-Pargs='100 50 200'`, predicting each first."
    ],
    "code": demo("ShedLoadDemo"),
    "expect": "With the defaults, about 100 requests are served (20 permits × 5 rounds; runs here served exactly 100) and the other 900 are turned away in about a third of a second. A 2 s wait serves about 20 × 41 = 820 on an idle machine (746 on this busy one). With 100 permits and 200 ms, about 500 are served (492 here). Served requests = permits × (max wait / call time + 1), which is Little's law turned around."
   },
   "refs": [
    {"title": "Semaphore (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Semaphore.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "Fan out with a shared limit in Java and Kotlin",
  "java": {"title": "FanOut.java + Bulkhead.java (lab solution, trimmed)", "src": "public final class Bulkhead {\n    private final Semaphore permits;\n\n    public Bulkhead(int maxConcurrent) { permits = new Semaphore(maxConcurrent); }\n\n    public <T> T call(Callable<T> work) throws Exception {\n        permits.acquire();\n        try { return work.call(); }\n        finally { permits.release(); }\n    }\n}\n\nstatic final Bulkhead DATABASE = new Bulkhead(20);\n\nList<String> saveAll(List<String> ids) throws Exception {\n    try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {\n        List<Future<String>> fs = new ArrayList<>();\n        for (String id : ids) fs.add(perTask.submit(() -> DATABASE.call(() -> saveOrder(id))));\n        List<String> out = new ArrayList<>();\n        for (Future<String> f : fs) out.add(f.get());\n        return out;\n    }\n}"},
  "kotlin": {"title": "FanOutKotlin.kt", "src": read(f"{lab}/demo/{K}/FanOutKotlin.kt")},
  "note": "The Kotlin version is the same design. `use {}` is Kotlin's try-with-resources, and it works because `ExecutorService` is `AutoCloseable` since JDK 19. An `inline` extension function gives `Semaphore` a `withPermit` block, so the try and finally are written once. `Callable { ... }` picks the `submit` overload that returns a value; a bare lambda could be read as a `Runnable`. Watch one name: kotlinx.coroutines has a `Semaphore` of its own, built for coroutines (see the box in the last section). On virtual threads, use the JDK's. Run the Kotlin file with `./gradlew :vthreads:demo -Pmain=workbench.vthreads.l03.FanOutKotlinKt`: 1,000 orders through 20 permits at 50 ms each take about 2.5 s."
 },
 "worked": {
  "title": "Send the night's orders to the delivery company, 20 at a time",
  "steps": [
   {"say": "Every night the shop sends 3,000 orders to a delivery company. Its web service allows 20 calls at once from each shop and takes about 150 ms per call. Each order also needs an address lookup in the shop's own data, which has no limit. Start with the limit, as a field on the client that every caller shares.",
    "code": "final class DeliveryClient {\n    // one limit for the whole program, from the delivery company's rules\n    private final Semaphore inFlight = new Semaphore(20);\n}",
    "lang": "java",
    "alt_lang": "kotlin",
    "alt_code": "class DeliveryClient {\n    // one limit for the whole program, from the delivery company's rules\n    private val inFlight = Semaphore(20)\n}"},
   {"say": "Guard only the delivery call. The address lookup happens before `acquire()`, so 3,000 lookups overlap freely.",
    "code": "Booking send(Order order) throws Exception {\n    Address to = addresses.lookup(order.customerId());   // 1. unlimited work first\n    inFlight.acquire();                                   // 2. wait for a permit (parks a virtual thread)\n    try {\n        return delivery.book(order, to);                  // 3. the only limited call\n    } finally {\n        inFlight.release();                               // 4. always give the permit back\n    }\n}",
    "lang": "java",
    "alt_lang": "kotlin",
    "alt_code": "fun send(order: Order): Booking {\n    val to = addresses.lookup(order.customerId)   // 1. unlimited work first\n    inFlight.acquire()                            // 2. wait for a permit (parks a virtual thread)\n    try {\n        return delivery.book(order, to)           // 3. the only limited call\n    } finally {\n        inFlight.release()                        // 4. always give the permit back\n    }\n}"},
   {"say": "Fan out one virtual thread per order, and collect in order. The executor block makes sure no order is still being sent when the method returns.",
    "code": "List<Booking> sendAll(List<Order> orders) throws Exception {\n    try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {\n        List<Future<Booking>> fs = new ArrayList<>();\n        for (Order o : orders) fs.add(perTask.submit(() -> send(o)));   // 5. fork all\n        List<Booking> bookings = new ArrayList<>();\n        for (Future<Booking> f : fs) bookings.add(f.get());             // 6. join in order\n        return bookings;\n    }\n}",
    "lang": "java",
    "alt_lang": "kotlin",
    "alt_code": "fun sendAll(orders: List<Order>): List<Booking> =\n    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->\n        val fs = orders.map { o -> perTask.submit(Callable { send(o) }) }   // 5. fork all\n        fs.map { it.get() }                                                 // 6. join in order\n    }"},
   {"say": "Check the timing with Little's law before you rely on it. The delivery step caps you at 20 / 0.15 s = 133 orders a second, so 3,000 orders take about 22.5 s, however many threads you start. If that's too slow, the fix is a higher limit agreed with the delivery company, not more threads."}
  ]
 },
 "lab": {
  "title": "Fan out 5,000 calls, never more than 20 in flight",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/FanOut.java", f"{lab}/main/{P}/Bulkhead.java", f"{lab}/main/{P}/BlockingCall.java"],
  "run": "./gradlew :vthreads:test --tests 'workbench.vthreads.l03.*'",
  "steps": [
   "Run the tests once. All six fail. The tests use `FakeDatabase`, a fake that sleeps on every call like a slow database and counts how many calls are inside it at once.",
   "Write `FanOut.callAll`: open `Executors.newVirtualThreadPerTaskExecutor()` in try-with-resources, submit one task per input (`perTask.submit(() -> call.call(input))`), then call `get()` on each future in order and collect the results.",
   "Write `Bulkhead`, a shared limit for one scarce resource: a `Semaphore` field built in the constructor, `call` with `acquire()` before the `try` and `release()` in `finally`, and `available()` from `availablePermits()`.",
   "Run the tests. The bulkhead test sends 5,000 calls through `Bulkhead(20)` and records the most calls that were inside the fake database at once. It must be at most 20, and at least 10 to prove the calls overlap.",
   "Read the shared-limit test: two fan-outs run at the same time through one `Bulkhead`. Think about what would happen if each fan-out made its own."
  ],
  "hints": [
   "Inside a lambda, `input` must be effectively final. The variable of an enhanced `for` loop is, so `for (I input : inputs)` works directly.",
   "`Future.get()` already throws `ExecutionException` with the task's exception as the cause, which is exactly what the failure test expects. You don't need to wrap anything.",
   "If the 5,000-call test takes minutes, you are probably waiting on each future right after submitting it. Submit all of them first."
  ],
  "done_when": "All six tests in `FanOutTest` pass."
 },
 "drill": {
  "title": "The shared limit from memory",
  "minutes": 4,
  "prompt": "Close this page. Write a class `StockClient` whose `check(Order order)` method lets at most 50 calls reach `http.check(order)` at once across the whole program, and gives up with a `RejectedExecutionException` if no permit frees up within 100 ms. Then compare with the answer: where is `acquire` relative to the `try`?",
  "answer": {"lang": "java", "src": "final class StockClient {\n    private final Semaphore inFlight = new Semaphore(50);   // shared by every caller\n    private final StockHttp http;\n\n    StockClient(StockHttp http) { this.http = http; }\n\n    Stock check(Order order) throws InterruptedException {\n        if (!inFlight.tryAcquire(100, TimeUnit.MILLISECONDS)) {\n            throw new RejectedExecutionException(\"stock service busy\");   // fail fast\n        }\n        try {\n            return http.check(order);\n        } finally {\n            inFlight.release();   // only reached if we got a permit\n        }\n    }\n}",
             "alt": {"lang": "kotlin", "src": "class StockClient(private val http: StockHttp) {\n    private val inFlight = Semaphore(50)   // shared by every caller\n\n    fun check(order: Order): Stock {\n        if (!inFlight.tryAcquire(100, TimeUnit.MILLISECONDS)) {\n            throw RejectedExecutionException(\"stock service busy\")   // fail fast\n        }\n        try {\n            return http.check(order)\n        } finally {\n            inFlight.release()   // only reached if we got a permit\n        }\n    }\n}"}}
 },
 "recap": [
  "Start virtual threads with `Thread.ofVirtual()`, `Thread.startVirtualThread`, a `factory()`, or, most often, `Executors.newVirtualThreadPerTaskExecutor()`.",
  "The per-task executor creates a new virtual thread for every task, with no limit. Open it in try-with-resources: `close()` waits for every task.",
  "Fork all tasks first, then `get()` them in order. A failure comes back as an `ExecutionException` that carries the real cause.",
  "Never pool virtual threads. A pool caps the whole task, keeps a queue, and leaks `ThreadLocal` values from one task to the next.",
  "Limit a scarce resource with one shared `Semaphore`: `acquire()` before the `try`, `release()` in `finally`, and only around the call that needs it.",
  "The limit of the limit: permits / call time is the most calls per second you'll get, and waiters pile up beyond it. Use `tryAcquire` with a timeout to turn work away instead of queueing forever."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "10,000 checkouts at once each call a stock service that allows 50 calls at once. Which design is right?",
   "options": ["`newFixedThreadPool(50)` of platform threads for all checkout handling", "`newFixedThreadPool(50, Thread.ofVirtual().factory())`", "A virtual thread per checkout, and one shared `Semaphore(50)` around the stock call", "A virtual thread per checkout, and a `new Semaphore(50)` created inside each checkout's handler"],
   "answer": 2,
   "why": "The limit belongs to the stock service, so put one semaphore on its client and share it. Both pools limit all of the checkout handling, not just the stock call. A semaphore created per checkout gives every checkout its own 50 permits, which limits nothing at all."},
  {"q": "What does this print?\n\n```java\ntry (var perTask = Executors.newVirtualThreadPerTaskExecutor()) {\n    for (int i = 0; i < 3; i++)\n        perTask.submit(() -> System.out.println(Thread.currentThread().getName().isEmpty()));\n}\nSystem.out.println(\"done\");\n```",
   "options": ["`true` three times, then `done`", "`done` first, then `true` three times", "`false` three times, then `done`, because each thread is named `pool-1-thread-N`", "Nothing: the tasks are cancelled when the block ends"],
   "answer": 0,
   "why": "Virtual threads have no name by default, so `getName()` is empty. `close()` at the end of the try block waits for all three tasks before `done` runs. The `pool-1-thread-N` names belong to the platform threads of `newFixedThreadPool`."},
  {"q": "A `Semaphore(20)` guards a 50 ms call. 1,000 virtual threads reach `acquire()` at the same moment. About how long until the last one gets a permit?",
   "options": ["About 50 ms", "About 2.5 s", "About 50 s", "Never: 980 threads fail with an exception"],
   "answer": 1,
   "why": "Twenty permits on a 50 ms call serve 400 calls a second, so 1,000 calls need about 2.5 s, and the last thread waits for nearly all of it. Nothing fails: `acquire()` waits as long as it takes. Use `tryAcquire` with a timeout if that wait is too long."},
  {"q": "You submit 1 million tasks to `Executors.newVirtualThreadPerTaskExecutor()`. How many threads can it create?",
   "options": ["As many as there are cores", "256, the scheduler's maximum", "A pool the JVM sizes from the workload", "Up to 1 million: one new virtual thread per task, with no limit"],
   "answer": 3,
   "why": "The Javadoc says the number of threads it creates is unbounded. The core count and the 256 cap describe carrier threads, the platform threads that run the virtual threads. They don't limit how many virtual threads exist."},
  {"q": "From the lesson \"Synchronizers: latch, barrier, semaphore, phaser\": a developer writes `try { sem.acquire(); call(); } finally { sem.release(); }`. A thread is interrupted while it waits inside `acquire()`. What happens to the semaphore?",
   "options": ["Nothing: `release()` ignores threads that hold no permit", "`acquire()` retries automatically after the interrupt", "It gains a permit it never handed out, so the limit quietly grows by one", "`release()` throws `IllegalMonitorStateException`"],
   "answer": 2,
   "why": "A `Semaphore` doesn't track who holds its permits. `release()` always adds one, even from a thread that never acquired, so every interrupted waiter raises the limit by one. Put `acquire()` on the line before the `try`, so `finally` runs only after a permit was really taken.",
   "from": "conc-10"}
 ],
 "flashcards": [
  {"front": "Which executor gives every task its own new virtual thread?", "back": "`Executors.newVirtualThreadPerTaskExecutor()`. It has no pool, no queue and no limit."},
  {"front": "What does `close()` on an `ExecutorService` do (JDK 19 and later)?", "back": "It calls `shutdown()` and then waits until every submitted task has finished."},
  {"front": "Should you pool virtual threads?", "back": "No. Create one per task, and limit the scarce resource with a shared `Semaphore`."},
  {"front": "Where does the `Semaphore` that protects a database belong?", "back": "One per resource, shared by all callers, for example a field on the object that talks to the database. One per request limits nothing."},
  {"front": "`Semaphore(20)` guards a call that takes 100 ms. What is the most calls per second?", "back": "200 (20 / 0.1 s)."},
  {"front": "Why put `acquire()` before the `try` and `release()` in `finally`?", "back": "So a thread that fails to acquire never releases a permit it didn't get, and a thread whose call throws always gives its permit back."},
  {"front": "How do you make a wait at a semaphore fail fast?", "back": "`tryAcquire(timeout, unit)` returns `false` if no permit arrives in time, so you can turn the request away."}
 ],
 "terms": [
  {"term": "Thread.Builder", "plain": "The JDK 21 API that makes threads: `Thread.ofVirtual()` and `Thread.ofPlatform()`."},
  {"term": "Thread-per-task executor", "plain": "An executor that starts a new thread for every task and never reuses one."},
  {"term": "Fan-out", "plain": "Starting many calls at once, then collecting all their results."},
  {"term": "Semaphore", "plain": "A counter of permits. `acquire` takes one or waits, `release` gives one back."},
  {"term": "Permit", "plain": "One unit of a semaphore's count: the right for one thread to be inside the guarded code."},
  {"term": "Bulkhead", "plain": "A limit on how many calls may be inside one slow service at once, so it can't use up everything."},
  {"term": "Load shedding", "plain": "Turning work away quickly when you're over capacity, instead of letting it queue."}
 ],
 "explain_back": {
  "prompt": "A teammate proposes `Executors.newFixedThreadPool(20, Thread.ofVirtual().factory())` for the nightly order batch, \"to protect the database, which has 20 connections\". Explain why you'd do it differently, and what you'd write instead.",
  "answer": "A pool of 20 caps the whole task, not just the database call. Each order also checks the stock and looks up an address, and none of that touches the database, but all of it would wait for one of the 20 pool threads too, so the batch runs far slower than it needs to. The pool also reuses threads, so anything left in a `ThreadLocal` leaks into the next task. I'd use `newVirtualThreadPerTaskExecutor()` in a try-with-resources block, one virtual thread per order, and one shared `Semaphore(20)` that the database code acquires right around its call, with `release()` in `finally`. The database still never sees more than 20 calls, and everything else overlaps freely. Little's law says the database step caps throughput at 20 divided by the time of one call."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Limits on calls at once and limits on calls per second are different things.** A semaphore limits how many calls are in flight. Many web services instead publish a rate, such as 300 requests a second. Little's law connects the two only while the latency stays the same. Twenty in flight at 100 ms is 200 a second, but if the service slows to 400 ms, the same 20 permits give 50 a second, while a rate limiter would happily let 300 a second through and pile them up inside the slow service. If the rule is a rate, use a rate limiter. If it's connections or calls at once, use a semaphore. Some programs use both.\n\n**Fair or not.** `new Semaphore(20)` is not fair: a thread that calls `acquire()` just as a permit comes free can take it ahead of threads that have waited longer. That gives a little more throughput. `new Semaphore(20, true)` hands permits out in arrival order, which keeps the worst wait shorter. For a checkout, where a few very slow customers hurt more than a little lost throughput, fair is often the better choice.\n\n**Very many waiters.** Thousands of virtual threads parked on one semaphore are fine. Each `release()` wakes one waiter, and each waiter costs one parked virtual thread. With hundreds of thousands of waiters, the bigger problem is time: the last waiter waits for everyone ahead of it. A bounded wait with `tryAcquire` keeps that under control and turns overload into fast, honest errors.\n\n**Structured fan-out.** The try-with-resources block makes sure that every thread the method started has finished when it returns. What it doesn't do is stop the other tasks when one fails. Lesson 5 of this track builds that behavior with plain executors, and then shows the JDK's own API for it."
 },
 "sources": [
  {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444"},
  {"title": "Executors (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Executors.html"},
  {"title": "Thread.Builder (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Thread.Builder.html"},
  {"title": "Semaphore (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Semaphore.html"}
 ]
}
out = ROOT / "content/lessons/vt-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
