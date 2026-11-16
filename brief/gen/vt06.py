import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/vthreads/src"
P = "java/workbench/vthreads/l06"
K = "kotlin/workbench/vthreads/l06"
read = lambda p: (ROOT / p).read_text()


def demo(name):
    """Try-it code for a Java demo plus its Kotlin twin."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": f"./gradlew :vthreads:demo -Pmain=workbench.vthreads.l06.{name}",
            "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": f"./gradlew :vthreads:demo -Pmain=workbench.vthreads.l06.{name}Kt",
                    "file": f"{lab}/demo/{K}/{name}.kt"}}


FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="Where 300 waiting requests queue in three setups. With a fixed pool of 10, they queue for a thread and the database pool never waits. With a plain swap to virtual threads, they all queue inside the database pool and most time out. With virtual threads and a Semaphore of 10, they queue at the semaphore and the database pool never waits.">'
    '<text class="t-s t-m" x="20" y="22">Before: a fixed pool of 10 platform threads</text>'
    '<rect class="box" x="20" y="32" width="150" height="40" rx="8"/>'
    '<text class="t-s" x="95" y="56" text-anchor="middle">300 requests</text>'
    '<line class="ln" x1="170" y1="52" x2="196" y2="52" marker-end="url(#arr)"/>'
    '<rect class="box-dim" x="200" y="32" width="190" height="40" rx="8"/>'
    '<text class="t-s" x="295" y="56" text-anchor="middle">queue for a thread: 290</text>'
    '<line class="ln" x1="390" y1="52" x2="416" y2="52" marker-end="url(#arr)"/>'
    '<rect class="box" x="420" y="32" width="100" height="40" rx="8"/>'
    '<text class="t-s" x="470" y="56" text-anchor="middle">10 threads</text>'
    '<line class="ln" x1="520" y1="52" x2="541" y2="52" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="545" y="32" width="125" height="40" rx="8"/>'
    '<text class="t-s" x="607" y="56" text-anchor="middle">DB pool: no waits</text>'
    '<text class="t-s t-m" x="20" y="90">Rate calls in flight: at most 10. Everything waits behind the pool.</text>'
    '<text class="t-s t-m" x="20" y="118">A plain swap: one virtual thread per request</text>'
    '<rect class="box" x="20" y="128" width="150" height="40" rx="8"/>'
    '<text class="t-s" x="95" y="152" text-anchor="middle">300 virtual threads</text>'
    '<line class="ln-bad" x1="170" y1="148" x2="196" y2="148" marker-end="url(#arr)"/>'
    '<rect class="box-bad" x="200" y="128" width="470" height="40" rx="8"/>'
    '<text class="t-s" x="435" y="152" text-anchor="middle">DB pool: 290 wait inside it, and most time out after 30 ms</text>'
    '<text class="t-s t-bad" x="20" y="186">The limit the old pool gave you is gone.</text>'
    '<text class="t-s t-m" x="20" y="214">Migrated: one virtual thread per request, plus Semaphore(10)</text>'
    '<rect class="box" x="20" y="224" width="150" height="40" rx="8"/>'
    '<text class="t-s" x="95" y="248" text-anchor="middle">300 virtual threads</text>'
    '<line class="ln-a" x1="170" y1="244" x2="196" y2="244" marker-end="url(#arr)"/>'
    '<rect class="box-a" x="200" y="224" width="320" height="40" rx="8"/>'
    '<text class="t-s" x="360" y="248" text-anchor="middle">Semaphore(10): 290 wait, visible and yours</text>'
    '<line class="ln-a" x1="520" y1="244" x2="541" y2="244" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="545" y="224" width="125" height="40" rx="8"/>'
    '<text class="t-s" x="607" y="248" text-anchor="middle">DB pool: no waits</text>'
    '<text class="t-s t-ok" x="20" y="284">Rate calls in flight: about 200. Only the database call waits its turn.</text>'
    '</svg>'
)


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


OPENING = """Picture a small restaurant run the old way, as in the first lesson of this track: each waiter stays with one table until its meal is done. This one has 10 waiters, and the kitchen has 10 burners. Nobody planned it, but with 10 waiters, no more than 10 orders ever reach the burners at once.

Then the owner moves to order slips, cheap enough for one per table. Drinks and bread now come at once. But at the first rush, 300 slips reach the kitchen together, and there are still 10 burners. Most of those orders come back with an apology.

A program moving from a fixed pool to virtual threads meets the same rush. The move looks like one line, and every test with light traffic passes, so the trap is easy to fall into. The old pool was also a limit that nobody wrote down.

Lesson 5 ended by asking which limit that is. In this lesson, we'll move a small service in two steps, write its hidden limit back with a semaphore, work through a checklist, and check the result with Little's law. Before we start, make a guess, and keep it in mind."""

S0 = """Let's meet the service first. Part of the shop answers one question before every checkout: what will this order cost in the customer's own money? The lab calls it `QuoteService`, since a quote is a price offer. For each request it does two things. It looks up the customer's level, gold or standard, in the shop's database, which takes 5 ms on a borrowed **connection**, an open line to the database. Then it asks the exchange-rate service from lesson 4 of this track for today's rate, which takes 100 ms.

The database sits behind a **connection pool**: 10 open connections that requests borrow and give back. A request that finds all 10 in use waits, and this pool gives up after 30 ms. Here is the service as it runs today, on a fixed pool: a team of 10 platform threads, the costly kind that each use a thread of the operating system, taking requests from a queue:

""" + pair(
"""public final class QuoteService implements AutoCloseable {
    // 10 platform threads, because the database pool has 10 connections
    private final ExecutorService workers = Executors.newFixedThreadPool(10);

    public Quote quote(QuoteRequest request) throws Exception {
        String tier = db.tier(request.customerId());    // 5 ms on a borrowed connection
        BigDecimal rate = fx.rate(request.pair());      // 100 ms call to the exchange-rate service
        return new Quote(request.customerId(), request.pair(), rate, fee(tier, request.amount()));
    }
}""",
"""class QuoteService(private val db: CustomerDb, private val fx: FxApi) : AutoCloseable {
    // 10 platform threads, because the database pool has 10 connections
    private val workers = Executors.newFixedThreadPool(10)

    fun quote(request: QuoteRequest): Quote {
        val tier = db.tier(request.customerId)    // 5 ms on a borrowed connection
        val rate = fx.rate(request.pair)          // 100 ms call to the exchange-rate service
        return Quote(request.customerId, request.pair, rate, fee(tier, request.amount))
    }
}""") + """

A virtual thread is the cheap kind: the JDK sets it aside whenever it waits, so a program can have one per request. The obvious move is one line: replace `newFixedThreadPool(10)` with `newVirtualThreadPerTaskExecutor()`. `MigrationDemo`, in the Try it below, sends a burst of 300 requests at once and runs the same handler three ways. Predict line B before you look. On this busy machine it printed:

```text
A: fixed pool of 10                 3,200 ms   ok 300   failed   0   rate calls in flight at peak  10
B: virtual threads                    173 ms   ok  63   failed 237   rate calls in flight at peak  63
```

Line A is slow and safe: 300 requests through 10 threads, at about 105 ms each, take 30 rounds, about 3.2 s. Line B is fast and mostly wrong. Four requests in five failed with `connection pool: no connection after 30 ms`.

The pool did two jobs. It ran the requests, and it made sure that no more than 10 of them ever reached the database. Nobody wrote the second job down, but it's the reason the connection pool never had to make anyone wait. Virtual threads take over the first job and quietly drop the second. In the restaurant, the 10 waiters were the pool's threads and the 10 burners are the connections. The slips are the virtual threads, and nothing stops 300 of them from reaching 10 burners. In the burst, all 300 asked for a connection at the same moment. A pool tuned for 10 callers gave each of the others 30 ms and then said no.

So write the second job back, on purpose, around the one call that needs it. It's the grill tokens from lesson 3 of this track: a `Semaphore`, a counter of permits, with one permit per connection:

""" + pair(
"""private final Semaphore dbPermits = new Semaphore(db.poolSize(), true);   // one permit per connection

public Quote quote(QuoteRequest request) throws Exception {
    String tier;
    dbPermits.acquire();                                // outside the try
    try {
        tier = db.tier(request.customerId());           // only the database call waits its turn
    } finally {
        dbPermits.release();
    }
    BigDecimal rate = fx.rate(request.pair());          // rate calls now overlap freely
    return new Quote(request.customerId(), request.pair(), rate, fee(tier, request.amount()));
}""",
"""private val dbPermits = Semaphore(db.poolSize, true)          // one permit per connection

fun quote(request: QuoteRequest): Quote {
    val tier = withDbPermit { db.tier(request.customerId) }   // only the database call waits its turn
    val rate = fx.rate(request.pair)                          // rate calls now overlap freely
    return Quote(request.customerId, request.pair, rate, fee(tier, request.amount))
}""") + """

The Kotlin version wraps acquire, try and release in a small `inline` function, `withDbPermit`, which the lab asks you to write. The `true` makes the semaphore **fair**: waiting requests get permits in the order they arrived. Line C of the demo runs this version:

```text
C: virtual threads + Semaphore(10)    283 ms   ok 300   failed   0   rate calls in flight at peak 180
```

No failures, and eleven times faster than line A. The 300 requests still met the database 10 at a time, but they waited at the semaphore, where waiting is cheap and has no 30 ms limit, not inside the pool. And the rate calls, which never needed a limit, went from 10 at a time to 180. The old pool deserves one word of credit: it was safe. It was also slow, because it held back calls that needed no limit.

You may wonder why we don't just raise the pool's 30 ms timeout. You could, and requests would wait inside the pool instead. The semaphore is better for two reasons. Its line is visible: `getQueueLength()` says how many requests are waiting, a number you can put on a chart. And the policy is yours: wait, or use `tryAcquire` with a deadline that gives up before any work is done.

**Removing a pool removes a limit. Write it back as one semaphore per resource, sized from that resource.**

Ten permits fit ten connections. So why not give the database 300 connections, one per request, and skip the semaphore?"""

S1 = """A database can run only a few queries truly at the same time, roughly a few per processor core of the computer it runs on. Past that point, more connections don't add speed. They add work inside the database, which switches between more sessions and lets them fight over the same data. So a database often runs slower with 300 connections than with 10, not faster.

Copies make it worse. A busy shop runs several copies of the same service, each with its own pool. Four copies with 20 connections each are 80 sessions on one database, and the database usually serves other programs as well.

So the connection pool stays small, sized from the database, and the waiting moves into your service, in front of the pool. In the restaurant, you don't add burners because you hired cheap waiters. You hang 10 tokens by the burners and let the slips wait on the board.

Waiting in your service is cheap, but it isn't free of risk. With a fixed pool, a slow database filled the pool's queue, and the program pushed back on new work. With virtual threads, nothing pushes back. Here the restaurant picture breaks, and the break matters. Real waiters cost wages, so nobody hires 300 by accident, but virtual threads cost almost nothing, so the crowd can grow very large before anyone notices. Parked requests pile up on the heap, the memory where Java keeps its objects, each with its stack, and every one of them is a customer waiting for an answer.

So give every wait a **deadline**: a point after which the request gives up and says so. At the semaphore, `tryAcquire` with a timeout does that:

""" + pair(
"""if (!dbPermits.tryAcquire(200, TimeUnit.MILLISECONDS)) {       // a deadline, not an endless wait
    throw new ShopBusyException("database busy, please try again");   // a fast, honest answer
}
try {
    tier = db.tier(request.customerId());
} finally {
    dbPermits.release();
}""",
"""if (!dbPermits.tryAcquire(200, TimeUnit.MILLISECONDS)) {       // a deadline, not an endless wait
    throw ShopBusyException("database busy, please try again")       // a fast, honest answer
}
val tier = try {
    db.tier(request.customerId)
} finally {
    dbPermits.release()
}""") + """

Turning work away early like this is **load shedding**, from lesson 3 of this track. The pool's own timeout stays as a safety net, but it fires late, after the request has already done part of its work. A deadline at the semaphore fails before any of that. Calls over the network need deadlines too: give the client that calls the exchange-rate service a timeout, so a bad day there can't hold requests forever.

Little's law, from lesson 1, says how long that line can get: requests waiting = arrival rate × time each one waits. At 1,000 requests a second, a 200 ms deadline lets at most about 200 requests wait at once. Pick the deadline from what a customer will accept, and the law tells you what the wait costs in parked requests.

**Keep the connection pool small, and let requests wait in front of it, with a deadline.**

The semaphore and the deadline fix one service. A real move touches more than one pool, so it helps to have a list."""

S2 = """Most moves to virtual threads need the same handful of changes. Go through them in this order:

1. Run JDK 25 first. On JDK 21 to 23, blocking inside `synchronized` pins the carrier: the platform thread that runs the virtual thread blocks too. Database drivers, web clients and logging libraries do exactly that. On JDK 25, only static initializers (the code that sets up a class) and native frames (calls into code written in another language) still pin. Lesson 4 of this track has the details.
2. Replace the pools that run blocking work with one virtual thread per task, through `newVirtualThreadPerTaskExecutor()`. Delete the old pool-size setting, so nobody tunes it later by mistake.
3. For each resource the old pool protected, write the limit down: one shared `Semaphore` per resource, sized from what that resource allows, held only around its calls. Look for resources with no limit at all, too, because now nothing slows the traffic in front of them.
4. Keep the connection pool small, sized from the database and multiplied by the number of copies of the service.
5. Hunt `ThreadLocal`s. A cache becomes one object per request (lesson 4), and a request's details belong in arguments or scoped values (lesson 5).
6. Keep heavy computing on a bounded pool of platform threads. Resizing a photo on a virtual thread holds a carrier for the whole time.
7. Give every wait a deadline: `tryAcquire` with a timeout, a timeout on every network client, and a fast "busy" answer when you're over budget.

Item 3 is the one people skip, because the code still passes every test with light traffic. It fails at the first real rush, exactly as line B did.

The three searches in the Try it below find the first candidates for items 1, 2 and 5 in any codebase. In the lab's own code they find a pool, a `ThreadLocal` and two `synchronized` methods, all from this track. In a real program, expect more pools than you thought, because many sit inside libraries and their settings, not in your own code.

**Switching the executor is one line. Writing down the limits it removed is the real move.**

The checklist gets the move right. To know that it worked, measure it."""

S3 = """Measure before you switch, then again after, with the same **load test**: a program that sends a steady stream of fake requests. You need a baseline of the requests finished per second, the time a typical request takes and the time the slowest one in a hundred takes (often called the p99). Add the error rate, the processor use, the heap and the time spent in garbage collection. Without a baseline, "it feels faster" is all you'll have.

After the switch, one number stops meaning anything: the thread count. Fifty thousand virtual threads is normal and tells you nothing. Watch where requests wait instead, with a few **gauges**, numbers that show a current value and go up and down, like the fuel gauge in a car:

- the requests in flight in the service
- the queue length on each semaphore
- the connection pool's waiting and active counts
- `jdk.VirtualThreadPinned` events from a recording of JFR, the JVM's built-in flight recorder, as in lesson 4 of this track

**Little's law** ties these together: requests in flight = throughput × time in the system, where throughput is the requests finished per second. Use it both ways. To predict, multiply. `MeasureDemo`, in the Try it below, sends 400 requests a second, and each spends about 120 ms inside: 20 ms on the database, holding one of 10 permits, then 100 ms with the exchange-rate service. So about 400 × 0.12 = 48 should be in flight. One run printed a line every 250 ms (two of them here) and a summary:

```text
t=  590 ms   in flight   48   waiting for a db permit    0
t=1,102 ms   in flight   48   waiting for a db permit    0
throughput 378/s, mean time in system 124 ms
Little's law: throughput x time = 46.7; measured average in flight = 47.0
```

The prediction held, and the last two numbers agree, as the law says they must. Both sit a little under 48, because the averages include the start and the end of the run, when fewer requests are inside.

To find a bottleneck, divide a limit by the time each request holds it. Ten permits, each held for 20 ms, serve at most 10 / 0.02 s = 500 requests a second. Below that rate the semaphore's line stays near zero. So what happens at 600 a second? Predict both gauges, then look:

```text
t=  268 ms   in flight  102   waiting for a db permit   45
t=  822 ms   in flight  164   waiting for a db permit  104
t=1,336 ms   in flight  229   waiting for a db permit  169
t=1,851 ms   in flight  281   waiting for a db permit  221
throughput 462/s, mean time in system 380 ms
```

The line at the semaphore grew on every sample, the time in the system tripled, and throughput stayed under 500 however many requests arrived. A rising queue with flat throughput is what a full resource looks like, and it's the alert to set up. The thread count would have said nothing, while the queue gauge named the database.

Roll out like any risky change. Switch one copy of the service first, send it real traffic, and compare its numbers with the copies still on the old pool. Look at the slowest requests and the error rate first. Then check that heap and garbage collection didn't jump, because parked virtual threads keep their stacks on the heap.

**Count where requests wait, not how many threads you have. A growing queue with flat throughput names the full resource.**

That's the whole move: a new executor, the limits written down, and the numbers that prove it. The lab does it to `QuoteService`."""

CLOSING = """We started with a restaurant whose 10 waiters quietly protected 10 burners. The quote service had the same hidden deal: 10 threads kept the database at 10 callers. One line of code removed it, one semaphore wrote it back, and the rate calls could overlap. Little's law showed where requests wait.

Now look in your own code for a fixed pool whose size matches something else, such as a connection count. Write that limit down as a semaphore before you touch the pool.

Next, we'll start the capstone with Design the ledger and make it correct: a small bank ledger that must stay right under load. Before any thread runs, what must always be true of its balances?"""

L = {
 "id": "vt-06",
 "title": "Moving a blocking service to virtual threads",
 "minutes": 35,
 "goal": "By the end you can move a pool-based blocking service to one virtual thread per request without overloading what sits behind it, work through the checklist that move needs, and use Little's law to check that it worked.",
 "opening": OPENING,
 "warmup": {
  "q": "A service handles requests on a fixed pool of 20 threads. Its database has a connection pool of 20 connections (open lines to the database that requests borrow and give back), which gives up after waiting 250 ms, and in two years it has never timed out. You switch request handling to one virtual thread per request. At the next busy hour, what happens first?",
  "options": [
   "Nothing changes: the connection pool still caps the database at 20",
   "Connection timeouts: every request in the rush now asks for one of 20 connections at once",
   "The JVM runs out of memory creating virtual threads",
   "Throughput drops, because virtual threads run code more slowly than platform threads"
  ],
  "answer": 1,
  "why": "The fixed pool was a limit nobody wrote down: it never let more than 20 requests near the database. With a virtual thread each, every request in the rush reaches the connection pool together, and those that wait longer than 250 ms fail. The first option is tempting and half right: the pool still caps the database at 20 connections, but the waiting moved into the pool, where it turns into errors. A few thousand parked virtual threads fit easily in the heap, and virtual threads run code at the same speed."
 },
 "sections": [
  {
   "h": "The old pool's second job: a database limit nobody wrote down",
   "body": S0,
   "figure": {"svg": FIG, "caption": "The same burst of 300 requests in three setups. What matters isn't how many threads you have, but where the waiting requests line up."},
   "try": {
    "title": "Migrate in two steps",
    "minutes": 4,
    "steps": [
     "Read `MigrationDemo`. 300 requests arrive at once. Each borrows one of 10 connections for a 5 ms query (the pool gives up after 30 ms), then makes a 100 ms call to the exchange-rate service.",
     "Predict, for A (the old pool), B (a plain swap to virtual threads) and C (virtual threads plus a `Semaphore(10)`): the total time, the failed requests, and the most rate calls in flight at once.",
     "Run it. Then change C's semaphore to `new Semaphore(3, true)` (in Kotlin, `Semaphore(3, true)`) and predict the new time before you run it again."
    ],
    "code": demo("MigrationDemo"),
    "expect": "A takes about 3,200 ms with no failures, and rate calls peak at exactly 10 (3,200 and 3,196 ms in runs here). B is fast, but most requests fail (63 ok and 237 failed in one run, 60 and 240 in another, 71 and 229 in the run the video shows), because they all waited inside the pool. C takes about 260 to 290 ms with no failures, and rate calls peak near 200 (180 and 195 here). With 3 permits (the label still says 10), C takes about 600 ms: 300 queries × 5 ms / 3 permits is 500 ms, plus one 100 ms rate call (644 ms here), and rate calls peak near 60. The database part of the request decides the time, and the semaphore is where you choose it."
   }
  },
  {
   "h": "Where the waiting belongs: a small connection pool and a deadline on every wait",
   "body": S1,
   "refs": [
    {"title": "About Pool Sizing (the HikariCP connection pool's wiki)", "url": "https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing", "kind": "read"}
   ]
  },
  {
   "h": "A checklist for the move, in the order to do it",
   "body": S2,
   "aside": {
    "title": "What if my service runs on a web framework?",
    "body": "A web framework is the library that receives each request and calls your code, so it also picks the request's thread, and the switch lives there. Spring Boot 3.2 and later switch with one setting, `spring.threads.virtual.enabled=true`: the web server and Spring's own task executors then use virtual threads. Quarkus has no global switch. You mark an endpoint, one address that requests arrive at, or a whole class with `@RunOnVirtualThread`, which lets you move the busiest endpoint first and compare. Neither framework adds the limits from item 3, so those are still your semaphores. And an old setting can quietly lose its meaning: in Quarkus, `quarkus.thread-pool.max-threads` sizes a pool that `@RunOnVirtualThread` endpoints don't use, so it no longer caps them."
   },
   "try": {
    "title": "Audit a codebase",
    "minutes": 3,
    "steps": [
     "From `labs/`, run the three searches below on the vthreads exercises. Each one looks for one checklist item.",
     "For each hit, name the checklist item and the fix.",
     "Run the same searches on a program of your own (change the path), and sort the hits: request handling, heavy computing, or a request's details."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "# 2. pools that run blocking work\ngrep -rnE \"newFixedThreadPool|newCachedThreadPool|new ThreadPoolExecutor\" --include=*.java --include=*.kt vthreads/src/main\n# 5. ThreadLocal caches and request details\ngrep -rnE \"ThreadLocal\" --include=*.java --include=*.kt vthreads/src/main\n# 1. monitors around slow calls (matters on JDK 21 to 23)\ngrep -rnE \"synchronized\" --include=*.java --include=*.kt vthreads/src/main", "run": ""},
    "expect": "Unless you already fixed them, the searches find this lesson's `QuoteService` with its `newFixedThreadPool(10)`, the `ThreadLocal<SimpleDateFormat>` in lesson 4's `ReceiptStamp`, and the `synchronized` methods in lesson 4's `FxRateCache`, plus a comment or two that mention them. In a real program, expect more pools than you thought: many of them sit inside libraries and their settings, not in your own code."
   }
  },
  {
   "h": "Measuring the move: Little's law finds the full resource",
   "body": S3,
   "try": {
    "title": "Watch a resource fill up",
    "minutes": 5,
    "steps": [
     "Read `MeasureDemo`. Requests arrive at a steady rate. Each holds one of 10 database permits for 20 ms, then makes a 100 ms call to the exchange-rate service. A sampler prints two gauges every 250 ms.",
     "Use Little's law to predict the requests in flight at 400 a second. Run it.",
     "Work out the database's capacity from the permits and the query time. Then run it at 600 a second with `-Pargs='600 2'`, and predict what the two gauges do first."
    ],
    "code": demo("MeasureDemo"),
    "expect": "At 400 a second, requests in flight sit near 48 (400 × 0.12 s) and nobody waits for a permit. The summary's two Little's law numbers agree (46.7 and 47.0 in a run here; a little under 48, because the averages include the start and the end). The database's capacity is 10 / 0.02 s = 500 a second, so at 600 a second the permit queue grows on every line (45, 80, 104 and on past 200 in one run), the time in the system climbs to around 400 ms (380 ms here), and throughput stays under 500 (462 a second here). The thread count would have told you nothing; the queue gauge told you which resource is full."
   }
  }
 ],
 "compare": {
  "title": "The migrated QuoteService in Java and Kotlin",
  "java": {"title": "QuoteService.java", "src": "public final class QuoteService implements AutoCloseable {\n    private final CustomerDb db;\n    private final FxApi fx;\n    // 1. one new virtual thread per request: no size to pick\n    private final ExecutorService requests = Executors.newVirtualThreadPerTaskExecutor();\n    // 2. the limit the old pool gave you by accident, now written down\n    private final Semaphore dbPermits;\n\n    public QuoteService(CustomerDb db, FxApi fx) {\n        this.db = db;\n        this.fx = fx;\n        this.dbPermits = new Semaphore(db.poolSize(), true);   // one permit per pooled connection\n    }\n\n    public Quote quote(QuoteRequest r) throws Exception {\n        String tier;\n        dbPermits.acquire();                                    // outside the try\n        try {\n            tier = db.tier(r.customerId());                     // only the database call holds a permit\n        } finally {\n            dbPermits.release();\n        }\n        BigDecimal rate = fx.rate(r.pair());                    // rate calls overlap freely\n        return new Quote(r.customerId(), r.pair(), rate, fee(tier, r.amount()));\n    }\n\n    // 3. a gauge for the chart\n    public int dbWaiting() {\n        return dbPermits.getQueueLength();\n    }\n\n    @Override\n    public void close() {\n        requests.close();                                       // 4. waits for requests in flight\n    }\n}"},
  "kotlin": {"title": "QuoteService.kt (the lab's solution)", "src": "class QuoteService(private val db: CustomerDb, private val fx: FxApi) : AutoCloseable {\n    // 1. one new virtual thread per request: no size to pick\n    private val requests = Executors.newVirtualThreadPerTaskExecutor()\n    // 2. the limit the old pool gave you by accident, now written down\n    private val dbPermits = Semaphore(db.poolSize, true)       // one permit per pooled connection\n\n    fun quote(r: QuoteRequest): Quote {\n        val tier = withDbPermit { db.tier(r.customerId) }      // only the database call holds a permit\n        val rate = fx.rate(r.pair)                             // rate calls overlap freely\n        return Quote(r.customerId, r.pair, rate, fee(tier, r.amount))\n    }\n\n    // 3. a gauge for the chart\n    fun dbWaiting(): Int = dbPermits.queueLength\n\n    override fun close() = requests.close()                    // 4. waits for requests in flight\n\n    private inline fun <T> withDbPermit(block: () -> T): T {\n        dbPermits.acquire()                                    // outside the try\n        try {\n            return block()\n        } finally {\n            dbPermits.release()\n        }\n    }\n}"},
  "note": "The move is the same in both: the executor changes, and the limit becomes a semaphore around one call. Kotlin's version reads better, because a small `inline` function that takes a lambda wraps the acquire, the try and the release, and inlining means the lambda costs nothing at run time. Java has no way to say that without a functional interface, so the try and finally sit in the method. Watch for two Kotlin traps. `kotlinx.coroutines.sync.Semaphore` has a `withPermit` too, but it suspends a coroutine and isn't the `java.util.concurrent.Semaphore` your threads need. And Kotlin doesn't check exceptions, so nothing reminds you that `acquire()` can throw `InterruptedException`. It still can, and it must still sit outside the `try`."
 },
 "worked": {
  "title": "Size every limit with Little's law before the switch",
  "steps": [
   {"say": "The shop's checkout runs as 4 copies of the same service behind one address, and each copy gets 200 checkouts a second at the busiest hour. A checkout spends 200 ms in the service: 40 ms asking the stock service, 120 ms waiting for the bank, 35 ms on a database connection and 5 ms computing. The bank allows the shop 150 calls in flight at once, across all copies. Today each copy has a fixed pool of 30 threads and 10 connections. First question: is the thread pool the bottleneck today?", "code": "time in the service   W = 40 + 120 + 35 + 5 ms = 200 ms\nthreads needed        L = 200/s x 0.2 s       = 40\nthe pool has 30, so at the busiest hour checkouts queue for a thread\npool capacity             30 / 0.2 s          = 150 checkouts/s", "lang": "text"},
   {"say": "Yes. The pool tops out at 150 checkouts a second, below the 200 that arrive, so checkouts queue at the busiest hour. Virtual threads remove that limit. Now check each resource with the same formula, because nothing caps them any more.", "code": "database connections busy   200/s x 0.035 s = 7     pool of 10: fine\nbank calls in flight        200/s x 0.120 s = 24    limit 150 / 4 copies = 37 per copy\nstock calls in flight       200/s x 0.040 s = 8     no published limit: ask the stock team\nvirtual threads             40 at a time, a little heap", "lang": "text"},
   {"say": "Write the limits in code: one shared semaphore per resource, sized per copy, held only around that resource's calls.", "code": "final class Limits {\n    // 1. the bank: 150 calls in flight for the shop, shared by 4 copies\n    final Semaphore bank = new Semaphore(150 / 4, true);\n    // 2. the database: one permit per pooled connection\n    final Semaphore db = new Semaphore(10, true);\n    // 3. the stock service: no limit yet; add one when its team gives you a number\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class Limits {\n    // 1. the bank: 150 calls in flight for the shop, shared by 4 copies\n    val bank = Semaphore(150 / 4, true)\n    // 2. the database: one permit per pooled connection\n    val db = Semaphore(10, true)\n    // 3. the stock service: no limit yet; add one when its team gives you a number\n}"},
   {"say": "Predict where each limit starts to bite, by dividing the permits by the time each checkout holds one. The bank semaphore starts to queue at 37 / 0.12 s, about 308 checkouts a second per copy, and the database at 10 / 0.035 s, about 285. If one copy stops, the other 3 get about 267 a second each, just under both. So the first alert to set is the queue length of the database semaphore, and each copy can now serve about 285 checkouts a second instead of 150."}
  ]
 },
 "lab": {
  "title": "Migrate the quote service",
  "minutes": 12,
  "files": [f"{lab}/main/{K}/QuoteService.kt", f"{lab}/main/{K}/QuoteModel.kt"],
  "run": "./gradlew :vthreads:test --tests 'workbench.vthreads.l06.*'",
  "steps": [
   "This lab is in Kotlin. `QuoteService` prices an order in the customer's own money: a 5 ms database lookup, then a 100 ms call to the exchange-rate service (`FxApi`). Run the tests once. Four of five fail. The burst test passes, because the old pool of 10 keeps the database safe by accident.",
   "TODO 1: replace `Executors.newFixedThreadPool(10)` with `Executors.newVirtualThreadPerTaskExecutor()`. Run the tests again. Now the burst test fails too, with `connection pool: no connection after 30 ms`. That's the limit you just removed.",
   "TODO 2: add `private val dbPermits = Semaphore(db.poolSize, true)` and hold a permit around the `db.tier(...)` call and nothing else: `acquire()` before a `try`, `release()` in its `finally`. A small `private inline fun <T> withDbPermit(block: () -> T): T` keeps `quote` easy to read.",
   "TODO 3 and 4: `dbWaiting()` returns `dbPermits.queueLength`, and `close()` calls `close()` on the new executor.",
   "Run the tests until all five pass. Then read the pool-size test: it builds a pool of 3 connections. Explain why `Semaphore(10)` would fail it."
  ],
  "hints": [
   "Keep the rate call outside the permit. If the permit covers the whole request, you have rebuilt the old 10-thread limit, and the test about rate calls fails.",
   "`acquire()` goes before the `try`. If it sat inside, a thread interrupted while waiting would `release()` a permit it never got, and the limit would quietly grow.",
   "Import `java.util.concurrent.Semaphore`, not `kotlinx.coroutines.sync.Semaphore`. The coroutine one suspends coroutines and doesn't work from a plain thread.",
   "`Semaphore.queueLength` is an estimate while threads come and go, but it's exact when nothing changes, which is what the gauge test waits for."
  ],
  "done_when": "All five tests in `QuoteServiceTest` pass."
 },
 "drill": {
  "title": "Write the limited client from memory",
  "minutes": 4,
  "prompt": "Close the lab. Write an `OrderStore` that many virtual threads call at once through `save(order)`, and that never lets more than `connections` of them inside `db.insert(order)` at the same time. Callers that can't get in within 200 ms should fail fast with an exception. Then name the one number you would put on a chart.",
  "answer": {"lang": "java", "src": "final class OrderStore {\n    private final OrderDb db;\n    private final Semaphore permits;                       // one per pooled connection, shared by all callers\n\n    OrderStore(OrderDb db, int connections) {\n        this.db = db;\n        this.permits = new Semaphore(connections, true);\n    }\n\n    void save(Order order) throws InterruptedException {\n        if (!permits.tryAcquire(200, TimeUnit.MILLISECONDS)) {   // a deadline, not an endless wait\n            throw new ShopBusyException(\"no database connection within 200 ms\");\n        }\n        try {\n            db.insert(order);                              // only this call holds a permit\n        } finally {\n            permits.release();\n        }\n    }\n\n    int waiting() {                                        // the number: callers queued right now\n        return permits.getQueueLength();\n    }\n}",
             "alt": {"lang": "kotlin", "src": "class OrderStore(private val db: OrderDb, connections: Int) {\n    private val permits = Semaphore(connections, true)     // one per pooled connection, shared by all callers\n\n    fun save(order: Order) {\n        if (!permits.tryAcquire(200, TimeUnit.MILLISECONDS)) {   // a deadline, not an endless wait\n            throw ShopBusyException(\"no database connection within 200 ms\")\n        }\n        try {\n            db.insert(order)                               // only this call holds a permit\n        } finally {\n            permits.release()\n        }\n    }\n\n    fun waiting(): Int = permits.queueLength               // the number: callers queued right now\n}"}}
 },
 "recap": [
  "A fixed thread pool limits every resource its threads touch. Moving to virtual threads removes that limit together with the pool.",
  "Write each limit back: one shared `Semaphore` per resource, sized from that resource, held only around its calls.",
  "Don't grow connection pools to match thread counts. The database decides how many connections help, and every copy of the service multiplies them.",
  "Give every wait a deadline, such as `tryAcquire` with a timeout, and answer \"busy\" fast when you're over budget.",
  "Checklist: JDK 25 first, one virtual thread per task, limits written down, `ThreadLocal` caches and details, heavy computing on a bounded pool, a deadline on every wait.",
  "The limit: virtual threads remove the cap on threads, not the caps on resources. Measure in-flight requests and queue lengths; a growing queue with flat throughput marks the full resource."
 ],
 "quiz": [
  {"q": "After the switch to virtual threads, the slowest requests take twice as long at the busiest hour, while throughput stays flat. Which number tells you whether the database is the bottleneck?",
   "options": ["The number of live virtual threads", "The queue length on the database semaphore (or the pool's waiting count), climbing at the busiest hour", "The processor use of the carrier threads", "The number of `ForkJoinPool` worker threads"], "answer": 1,
   "why": "A full resource shows up as a queue that grows while throughput stays flat. The count of virtual threads grows with any slowdown and doesn't say where the time goes, which is why it's tempting and useless. Carrier processor use is low when everybody waits, and the scheduler's worker count stays near the core count."},
  {"q": "One copy of a service handles 300 requests a second, and each request holds a database connection for 25 ms. On average, about how many connections are busy?",
   "options": ["About 8", "About 25", "About 75", "About 300"], "answer": 0,
   "why": "Little's law: busy connections = arrival rate × holding time = 300/s × 0.025 s = 7.5. A pool of 10 is close to its limit at this rate, and 10 / 0.025 s = 400 requests a second is where it fills up. The other options mix up the holding time with a count, or assume every request holds a connection the whole time."},
  {"q": "After the move, a `new Semaphore(10, true)` guards the database calls, and the database has 10 connections with a short borrow timeout. To make the service faster, a teammate raises the semaphore to 300 permits. What happens in a burst of 300 requests?",
   "options": ["It gets faster: 300 requests reach the database at once", "Nothing changes: the size of a semaphore never matters", "Most requests time out inside the connection pool again, as before the semaphore", "The JVM refuses to create more permits than there are connections"], "answer": 2,
   "why": "The semaphore's size is the limit. With 300 permits, 300 callers reach a pool of 10 connections, and those that wait longer than the pool's timeout fail: that's line B of `MigrationDemo` again. Size the semaphore from the resource, one permit per connection. The JVM doesn't know what the permits stand for, so it allows any number."},
  {"q": "After the move, the connection pool reports timeouts at every busy hour. Which fix is right?",
   "options": ["Raise the pool's maximum size to 1,000 connections", "Go back to a fixed pool of 20 platform threads for all request handling", "Raise the pool's connection timeout to 5 minutes", "Put a shared `Semaphore` sized to the pool around the database work, and use `tryAcquire` with a deadline that fits the request's time budget"], "answer": 3,
   "why": "The semaphore restores the limit the old pool gave you, only around the database work, with a queue you can see and a deadline you choose. A huge pool overloads the database for every program that shares it. A fixed pool brings back the cap on everything, including calls that never needed it. A 5-minute timeout hides overload as very slow requests."},
  {"q": "From the lesson \"Pinning, ThreadLocals and other traps\": your service runs on JDK 21, and its database driver (the library that talks to the database) holds a `synchronized` lock while it reads from the network. You move request handling to virtual threads. What is the main risk, and the simplest fix?",
   "options": [
    "Pinning: queries block their carriers, and a few slow ones can stall every virtual thread. Upgrade to JDK 25, or to a driver version that uses `ReentrantLock`",
    "Data races inside the driver, because virtual threads ignore `synchronized`. Wrap every call in your own lock",
    "A `ThreadLocal` leak in the driver. Call `remove()` after each query",
    "No risk: a database driver never blocks while it holds a lock"
   ], "answer": 0, "from": "vt-04",
   "why": "On JDK 21 to 23, blocking while holding a monitor pins the carrier, and with as many carriers as cores, a few slow queries can hold all of them. JEP 491 fixed this in JDK 24, so JDK 25 is the cleanest fix. `synchronized` still lets one thread in at a time on virtual threads, so there is no new race."}
 ],
 "flashcards": [
  {"front": "What limit does a fixed thread pool give you without saying so?", "back": "No more than N requests can reach any resource at once. Moving to virtual threads removes it."},
  {"front": "Where does the semaphore go when you move to virtual threads?", "back": "Around the one call that needs the limit, as one object shared by all requests, sized from that resource."},
  {"front": "Should you grow the connection pool to match the number of virtual threads?", "back": "No. The database decides how many connections help, roughly a few per database processor core, and every copy of the service multiplies the pool. Queue in front of the pool instead."},
  {"front": "Why give every semaphore wait a deadline after the move?", "back": "With virtual threads nothing pushes back, so parked requests pile up. `tryAcquire` with a timeout turns overload into a fast \"busy\" answer instead of a long wait."},
  {"front": "10 permits, each held for 20 ms. What is the most requests a second they can serve?", "back": "500 (10 / 0.02 s). Above that, the semaphore's queue grows while throughput stays flat."},
  {"front": "Little's law in one line?", "back": "Requests in flight = throughput × time in the system (L = λW)."},
  {"front": "Which gauge shows a full resource after the move?", "back": "The queue on its semaphore (or the pool's waiting count) growing while throughput stays flat."}
 ],
 "terms": [
  {"term": "Implicit limit", "plain": "A cap on how much runs at once that nobody set on purpose, such as a thread pool's size protecting a database."},
  {"term": "Connection pool", "plain": "A fixed set of open database connections that callers borrow and give back. Callers wait, or time out, when all are in use."},
  {"term": "Fair semaphore", "plain": "A semaphore that hands out permits in the order the waiters arrived (`new Semaphore(n, true)`)."},
  {"term": "Deadline", "plain": "A point in time after which a waiting request gives up and says so."},
  {"term": "Little's law", "plain": "In a stable system, requests in flight = throughput × average time in the system."},
  {"term": "Load shedding", "plain": "Turning work away quickly, with a \"busy\" answer, when a limit is full, instead of letting it wait without end."}
 ],
 "explain_back": {
  "prompt": "A manager asks why the team can't just flip the virtual threads switch tomorrow. Explain what the switch changes, what can break, and how you would roll it out and measure it.",
  "answer": "The switch gives every request its own virtual thread, so blocking calls stop tying up a limited pool and many more requests can be in flight. That is the point, and it is also the risk: the old pool also limited how many requests reached the database and the other services we call, without anyone writing that down. After the switch, a busy hour sends all of them at once, and the connection pool starts timing out, or the bank's service starts turning us away. So before the switch I'd run JDK 25 to avoid `synchronized` pinning, add a shared semaphore per resource sized from its real limit, keep the connection pool small, replace `ThreadLocal` caches, keep heavy computing on a bounded pool, and give every wait a deadline. For the rollout I'd take a baseline with a load test, switch one copy of the service, and compare its slowest requests, error rate, heap and garbage collection with the others. I'd also watch the semaphore queues and the pool's waiting count, and use Little's law to predict the rate at which each one fills up."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Admission control at the door.** The lab's semaphore waits without a deadline, deep inside the request. In a busy shop it's often better to decide at the start: try to take every permit the request will need, or a single \"requests in progress\" permit sized with Little's law, with a short `tryAcquire` deadline, and answer \"busy\" at once if you can't. Then you never call the bank for a request that would later time out at the database.\n\n**Pool timeouts and semaphore waits.** A pool's borrow timeout and a semaphore's deadline look alike, but they sit in different places. The pool timeout fires after the request has done part of its work and may already hold other resources. A deadline at the semaphore, at the start of the call, fails before any of that. Keep the pool's timeout too, as a safety net for bugs in your own limits.\n\n**Fairness and the slowest requests.** A fair semaphore serves waiters in arrival order. That costs a little throughput and keeps the slowest requests close to the typical ones during a burst. A non-fair one lets a newcomer grab a permit that was just released, which helps the average and hurts the unlucky waiters. For a checkout, the slowest customers matter more.\n\n**Thread dumps after the move.** `jstack` shows the carriers, not the thousands of parked virtual threads. `jcmd <pid> Thread.dump_to_file -format=json dump.json` writes all of them, grouped by the executor or scope that owns them. Before you need it in a hurry, practise finding the stack of one stuck request in such a dump.\n\n**When not to move.** A service that mostly computes, or that already runs fully asynchronous code on a few event-loop threads, gains little. The win is largest for services that block on the network and are limited by their thread pool today. Little's law tells you which kind yours is: compare the threads you need (rate × time) with the threads you have."
 },
 "closing": CLOSING,
 "sources": [
  {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444"},
  {"title": "Semaphore (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Semaphore.html"},
  {"title": "About Pool Sizing (HikariCP wiki)", "url": "https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing"},
  {"title": "Virtual thread support reference (Quarkus guide)", "url": "https://quarkus.io/guides/virtual-threads"}
 ]
}
out = ROOT / "content/lessons/vt-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
