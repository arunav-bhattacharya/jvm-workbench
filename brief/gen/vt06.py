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
    '<text class="t-s t-m" x="20" y="90">FX calls in flight: at most 10. Everything waits behind the pool.</text>'
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
    '<text class="t-s t-ok" x="20" y="284">FX calls in flight: about 200. Only the database call waits its turn.</text>'
    '</svg>'
)

S1 = """Here is the quote service from this lesson's lab, as it runs in production today. It handles requests on a fixed pool of 10 platform threads. Nobody remembers exactly why 10, but the database pool has 10 connections.

```kotlin
class QuoteService(private val db: CustomerDb, private val fx: FxApi) : AutoCloseable {
    // 10 platform threads, because the database pool has 10 connections
    private val workers = Executors.newFixedThreadPool(10)

    fun quote(request: QuoteRequest): Quote {
        val tier = db.tier(request.customerId)    // 5 ms on a pooled connection
        val rate = fx.rate(request.pair)          // 100 ms HTTP call
        return Quote(request.customerId, request.pair, rate, fee(tier, request.amount))
    }
}
```

```java
public final class QuoteService implements AutoCloseable {
    // 10 platform threads, because the database pool has 10 connections
    private final ExecutorService workers = Executors.newFixedThreadPool(10);

    public Quote quote(QuoteRequest request) throws Exception {
        String tier = db.tier(request.customerId());    // 5 ms on a pooled connection
        BigDecimal rate = fx.rate(request.pair());      // 100 ms HTTP call
        return new Quote(request.customerId(), request.pair(), rate, fee(tier, request.amount()));
    }
}
```

The obvious migration is one line: replace `newFixedThreadPool(10)` with `newVirtualThreadPerTaskExecutor()`. Do that in the lab and every test fails with `connection pool: no connection after 30 ms`.

The pool did two jobs. It ran the requests, and it made sure that no more than 10 of them could ever reach the database. The second job was never written down anywhere, but it's the reason the connection pool never had to wait. Virtual threads take over the first job and drop the second. In a burst of 300 requests, all 300 now ask for a connection at the same moment, and the pool's 30 ms borrow timeout was tuned for 10 callers.

So put the second job back, explicitly, around the one call that needs it:

```kotlin
private val dbPermits = Semaphore(db.poolSize, true)        // one permit per pooled connection

fun quote(request: QuoteRequest): Quote {
    val tier = withDbPermit { db.tier(request.customerId) }  // only the database call waits its turn
    val rate = fx.rate(request.pair)                         // FX calls now overlap freely
    return Quote(request.customerId, request.pair, rate, fee(tier, request.amount))
}
```

```java
private final Semaphore dbPermits = new Semaphore(db.poolSize(), true);   // one permit per pooled connection

public Quote quote(QuoteRequest request) throws Exception {
    String tier;
    dbPermits.acquire();
    try {
        tier = db.tier(request.customerId());           // only the database call waits its turn
    } finally {
        dbPermits.release();
    }
    BigDecimal rate = fx.rate(request.pair());          // FX calls now overlap freely
    return new Quote(request.customerId(), request.pair(), rate, fee(tier, request.amount()));
}
```

Why not just raise the pool's timeout? You could, and requests would wait inside the pool instead. The semaphore is better for two reasons. Its queue is visible: `queueLength` is a gauge you can put on a dashboard. And the policy is yours: wait, or `tryAcquire` with a deadline that fits the request's budget and fails before any work is done. Meanwhile the FX calls, which never needed a limit, go from 10 in flight to about 200."""

S2 = """Every migration I have seen needed the same handful of changes. Go through them in this order.

1. Run JDK 25 first. On JDK 21 to 23, blocking inside `synchronized` pins the carrier, and JDBC drivers, HTTP clients and logging appenders do exactly that. On JDK 25, only class initializers and native frames still pin. Lesson 4 of this track has the details.
2. Replace the pools that run blocking work with one virtual thread per task, through `newVirtualThreadPerTaskExecutor()` or your framework's switch. Delete the old pool-size setting so nobody tunes it later.
3. For each downstream the old pool protected, write the limit down. That means one shared `Semaphore` per downstream, sized from what that downstream allows, held only around its calls. Also look for downstreams with no limit at all, because now nothing slows the traffic in front of them.
4. Leave the connection pool small. A database runs well with a few connections per CPU core of the database server, and more connections make it slower. Every pod multiplies the number: 30 pods with 20 connections each are 600 sessions on one Oracle instance.
5. Hunt `ThreadLocal`s. Caches become one object per request (lesson 4 of this track), and request context belongs in arguments or scoped values (lesson 5).
6. Keep CPU-heavy steps on a bounded pool of platform threads. Signing a settlement file on a virtual thread holds a carrier for the whole time.
7. Give every wait a deadline. With a pool, a slow downstream filled the queue and callers got rejected. With virtual threads, nothing pushes back, and parked requests pile up in the heap. Use `tryAcquire` with a timeout and HTTP client timeouts, and return a fast 503 when you're over budget.

Item 3 is the one teams skip, because the code still works in tests. It only fails at the first real traffic peak."""

S3 = """Most services don't create their request threads themselves. The framework does, so the switch is in the framework.

**Quarkus** has no global switch. You opt in per endpoint, or per class, with `@RunOnVirtualThread`, and Quarkus then runs each call on a new virtual thread:

```java
@Path("/quotes")
public class QuoteResource {
    @Inject QuoteService quotes;

    @POST
    @RunOnVirtualThread                       // each call runs on a new virtual thread
    public Quote quote(QuoteRequest request) {
        return quotes.quote(request);         // plain blocking code: JDBC, REST client, Kafka producer
    }
}
```

```kotlin
@Path("/quotes")
class QuoteResource(private val quotes: QuoteService) {

    @POST
    @RunOnVirtualThread                       // each call runs on a new virtual thread
    fun quote(request: QuoteRequest): Quote =
        quotes.quote(request)                 // plain blocking code: JDBC, REST client, Kafka producer
}
```

The annotation is `io.smallrye.common.annotation.RunOnVirtualThread`. The same annotation works on Reactive Messaging `@Incoming` methods, which is how a Kafka consumer handles records on virtual threads. Opting in one endpoint at a time is a good fit for a migration: you move the busiest blocking endpoint first and compare.

**Spring Boot** 3.2 and later has one property for the whole application:

```properties
spring.threads.virtual.enabled=true
```

With it, the embedded web server handles requests on virtual threads, and Spring's own task executors use them too.

Neither framework adds the limits from the checklist. That's still your code. They also change what an old setting means. `quarkus.thread-pool.max-threads` sizes the worker pool, which `@RunOnVirtualThread` endpoints don't use, so it no longer caps them. If you relied on it as your database limit, that limit is gone, exactly like the pool in the lab.

The Quarkus guide lists the traps it sees most, and you know all of them by now: libraries that pin on JDK 21, CPU-heavy endpoints that monopolize a carrier, and libraries that pool objects in `ThreadLocal`s."""

S4 = """Measure before you switch, then again after, with the same load test. You need a baseline of throughput, p50 and p99 latency, error rate, CPU, heap and GC time. Without it, "it feels faster" is all you'll have.

After the switch, one number stops meaning anything: the thread count. Fifty thousand virtual threads is normal and tells you nothing. Watch where requests wait instead:

- requests in flight in the service
- the queue length on each downstream semaphore
- the connection pool's pending and active counts (HikariCP's Micrometer metrics are `hikaricp.connections.pending` and `hikaricp.connections.active`)
- `jdk.VirtualThreadPinned` events from a JFR recording, as in lesson 4 of this track

**Little's law** ties these together: requests in flight = throughput × time in the system. Use it both ways. To predict, multiply: 400 requests per second that spend 120 ms in the service means about 48 in flight. To find a bottleneck, divide a limit by the time each request holds it. Ten database permits held for 20 ms each serve at most 10 / 0.02 s = 500 requests per second. Below that rate the semaphore's queue stays near zero. Above it, the queue grows every second, latency grows with it, and throughput stays flat at about 500. A rising queue gauge with flat throughput is what a saturated downstream looks like, and it is the alert to set up.

Roll out like any risky change. Switch one pod (or one endpoint in Quarkus), send it real traffic, and compare its numbers with the pods still on the old pool. Look at p99 latency and error rate first. Then check that heap and GC didn't jump, because parked virtual threads keep their stacks on the heap."""

L = {
 "id": "vt-06",
 "title": "Moving a blocking service to virtual threads",
 "minutes": 35,
 "goal": "By the end you can migrate a pool-based blocking service to one virtual thread per request without overloading what sits behind it, switch it on in Quarkus or Spring Boot, and use Little's law to check that it worked.",
 "warmup": {
  "q": "A service handles requests on a fixed pool of 20 threads. Its database pool has 20 connections and a connection timeout of 250 ms, and in two years it has never timed out. You switch request handling to one virtual thread per request. At the next traffic peak, what happens first?",
  "options": [
   "Nothing changes: the connection pool still caps the database at 20",
   "Connection timeouts: every request in the peak now asks for one of 20 connections at once",
   "The JVM runs out of memory creating virtual threads",
   "Throughput drops, because virtual threads run code more slowly than platform threads"
  ],
  "answer": 1,
  "why": "The fixed pool was a limit nobody wrote down: it never let more than 20 requests near the database. With a virtual thread each, every request in the peak reaches the connection pool together, and those that wait longer than 250 ms fail. The first option is half right: the pool still caps the database at 20 connections, but the waiting moved into the pool, where it turns into errors. A few thousand parked virtual threads fit easily in the heap, and virtual threads run code at the same speed."
 },
 "sections": [
  {
   "h": "The old pool was a limit you never wrote down",
   "body": S1,
   "figure": {"svg": FIG, "caption": "The same burst in three setups. The question is not how many threads you have but where the waiting requests queue."},
   "try": {
    "title": "Migrate in two steps",
    "minutes": 4,
    "steps": [
     "Read `MigrationDemo`. 300 requests arrive at once. Each borrows one of 10 connections for a 5 ms query (the pool gives up after 30 ms), then makes a 100 ms FX call.",
     "Predict, for A (the old pool), B (a plain swap to virtual threads) and C (virtual threads plus a `Semaphore(10)`): total time, failed requests, and peak FX calls in flight.",
     "Run it. Then change C's semaphore to `new Semaphore(3, true)` (in Kotlin, `Semaphore(3, true)`) and predict the new time before running again."
    ],
    "code": demo("MigrationDemo"),
    "expect": "A takes about 3,200 ms with no failures, and FX peaks at exactly 10. B is fast but most requests fail (one run here: 71 ok, 229 failed), because they all waited inside the pool. C takes about 260 ms with no failures, and FX peaks near 200. With 3 permits (the label still says 10), C takes about 600 ms: 300 queries × 5 ms / 3 permits is 500 ms, plus one 100 ms FX call, and FX peaks lower, near 60. The database part of the request decides the time, and the semaphore is where you choose it."
   }
  },
  {
   "h": "A migration checklist",
   "body": S2,
   "try": {
    "title": "Audit a codebase",
    "minutes": 3,
    "steps": [
     "From `labs/`, run the three searches below on the vthreads exercises. Each one looks for one checklist item.",
     "For each hit, name the checklist item and the fix.",
     "Run the same searches on a service you own (change the path), and note which hits are request handling, which are CPU work, and which are context."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "# 2. pools that run blocking work\ngrep -rnE \"newFixedThreadPool|newCachedThreadPool|new ThreadPoolExecutor\" --include=*.java --include=*.kt vthreads/src/main\n# 5. ThreadLocal caches and context\ngrep -rnE \"ThreadLocal\" --include=*.java --include=*.kt vthreads/src/main\n# 1. monitors around I/O (matters on JDK 21 to 23)\ngrep -rnE \"synchronized\" --include=*.java --include=*.kt vthreads/src/main", "run": ""},
    "expect": "Unless you already fixed them, the searches find this lesson's `QuoteService` with its `newFixedThreadPool(10)`, the `ThreadLocal<SimpleDateFormat>` in `ReceiptStamp` and the `synchronized` methods in `FxRateCache` from lesson 4, plus a comment or two. In a real service, expect more pools than you thought: many of them sit inside libraries and framework config, not in your own code."
   }
  },
  {
   "h": "Quarkus and Spring Boot: the switch is one line",
   "body": S3,
   "refs": [
    {"title": "Virtual thread support reference (Quarkus guide)", "url": "https://quarkus.io/guides/virtual-threads", "kind": "docs"}
   ]
  },
  {
   "h": "Measure it, and let Little's law find the bottleneck",
   "body": S4,
   "try": {
    "title": "Watch a downstream saturate",
    "minutes": 5,
    "steps": [
     "Read `MeasureDemo`. Requests arrive at a steady rate. Each holds one of 10 database permits for 20 ms, then makes a 100 ms FX call. A sampler prints two gauges every 250 ms.",
     "Use Little's law to predict the requests in flight at 400 per second. Run it.",
     "Work out the database's capacity from the permits and the query time. Then run it at 600 per second with `-Pargs='600 2'`, and predict what the two gauges do first."
    ],
    "code": demo("MeasureDemo"),
    "expect": "At 400 per second, requests in flight sit near 48 (400 × 0.12 s) and nobody waits for a permit. The summary's two Little's law numbers agree (45.7 and 45.7 in one run; they are a little below 48 because the averages include the start and the drain). The database's capacity is 10 / 0.02 s = 500 per second, so at 600 per second the permit queue grows on every line (44, 80, 113 and on to more than 200 in one run), time in the system climbs to around 400 ms, and throughput stays near 460 to 500. The thread count would have told you nothing; the queue gauge told you which downstream is full."
   },
   "refs": [
    {"title": "About Pool Sizing (HikariCP wiki)", "url": "https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing", "kind": "read"}
   ]
  }
 ],
 "analogy": "The old pool is a restaurant with 10 waiters and a kitchen with 10 burners. Nobody planned it, but with 10 waiters there are never more than 10 orders at the kitchen at once. Moving to virtual threads is like giving every table its own waiter the moment it's seated. Drinks and bread arrive at once, which is the FX call overlapping. But at a peak, 300 waiters crowd the kitchen door. The semaphore is a ticket machine at that door with 10 tickets: waiters queue in an orderly line you can count, and the kitchen works at its pace. The analogy breaks on cost. Real waiters are paid, so nobody would hire 300 by accident. Virtual threads cost almost nothing, so the crowd at the door can grow very large before anyone notices.",
 "in_your_world": "In a Quarkus service the datasource is an Agroal pool sized by `quarkus.datasource.jdbc.max-size`, and with `@RunOnVirtualThread` the worker pool no longer stands in front of it. Before you annotate the busiest endpoint, find out what used to cap it, and write that cap down as a semaphore. Do the same for each REST client: a card issuer that allows 150 calls in flight for your merchant, shared across 4 pods, means `Semaphore(37)` per pod. Size the Oracle side from the database, not from the thread count, and multiply by the number of pods. For a Kafka consumer moved to virtual threads, check how many records your framework now processes at once, and whether records with the same key still need to be handled in order. In a Temporal worker, the maximum number of concurrent activity executions is already an explicit limit. Size it from the downstreams the activities call, not from CPU.",
 "mistake": "The most common mistake is growing the connection pool to match the new concurrency: \"we have 2,000 virtual threads now, so set the pool to 2,000\". The database can only run a limited number of queries at once, roughly a few per CPU core of the database server. Past that point, more connections add context switching and lock contention inside the database, and every pod multiplies the session count. The result is a slower database and, at a peak, a database that refuses new sessions for every service that shares it. Keep the pool small and put an explicit semaphore in front of it. Then let requests queue in your service, where you can see the queue and shed load with a deadline.",
 "compare": {
  "title": "The migrated QuoteService in Java and Kotlin",
  "java": {"title": "QuoteService.java", "src": "public final class QuoteService implements AutoCloseable {\n    private final CustomerDb db;\n    private final FxApi fx;\n    // 1. one new virtual thread per request: no size to pick\n    private final ExecutorService requests = Executors.newVirtualThreadPerTaskExecutor();\n    // 2. the limit the old pool gave you by accident, now explicit\n    private final Semaphore dbPermits;\n\n    public QuoteService(CustomerDb db, FxApi fx) {\n        this.db = db;\n        this.fx = fx;\n        this.dbPermits = new Semaphore(db.poolSize(), true);   // one permit per pooled connection\n    }\n\n    public Quote quote(QuoteRequest r) throws Exception {\n        String tier;\n        dbPermits.acquire();                                    // outside the try\n        try {\n            tier = db.tier(r.customerId());                     // only the database call holds a permit\n        } finally {\n            dbPermits.release();\n        }\n        BigDecimal rate = fx.rate(r.pair());                    // FX calls overlap freely\n        return new Quote(r.customerId(), r.pair(), rate, fee(tier, r.amount()));\n    }\n\n    // 3. a gauge for the dashboard\n    public int dbWaiting() {\n        return dbPermits.getQueueLength();\n    }\n\n    @Override\n    public void close() {\n        requests.close();                                       // 4. waits for requests in flight\n    }\n}"},
  "kotlin": {"title": "QuoteService.kt (the lab's solution)", "src": "class QuoteService(private val db: CustomerDb, private val fx: FxApi) : AutoCloseable {\n    // 1. one new virtual thread per request: no size to pick\n    private val requests = Executors.newVirtualThreadPerTaskExecutor()\n    // 2. the limit the old pool gave you by accident, now explicit\n    private val dbPermits = Semaphore(db.poolSize, true)       // one permit per pooled connection\n\n    fun quote(r: QuoteRequest): Quote {\n        val tier = withDbPermit { db.tier(r.customerId) }      // only the database call holds a permit\n        val rate = fx.rate(r.pair)                             // FX calls overlap freely\n        return Quote(r.customerId, r.pair, rate, fee(tier, r.amount))\n    }\n\n    // 3. a gauge for the dashboard\n    fun dbWaiting(): Int = dbPermits.queueLength\n\n    override fun close() = requests.close()                    // 4. waits for requests in flight\n\n    private inline fun <T> withDbPermit(block: () -> T): T {\n        dbPermits.acquire()                                    // outside the try\n        try {\n            return block()\n        } finally {\n            dbPermits.release()\n        }\n    }\n}"},
  "note": "The migration is the same in both: the executor changes, and the limit becomes a semaphore around one call. Kotlin's version reads better because a small `inline` function with a lambda wraps acquire, try and release, and inlining means the lambda costs nothing at run time. Java has no equivalent without a functional interface, so the try/finally sits in the method. Two Kotlin traps: `kotlinx.coroutines.sync.Semaphore` has a `withPermit` too, but it suspends a coroutine and is not the `java.util.concurrent.Semaphore` your threads need. And Kotlin doesn't check exceptions, so nothing reminds you that `acquire()` can throw `InterruptedException`. It still can, and it must still sit outside the `try`."
 },
 "worked": {
  "title": "Size every limit with Little's law before the switch",
  "steps": [
   {"say": "A card authorization service runs on 4 pods, and each pod gets 200 requests per second at peak. A request holds a database connection for 15 ms, calls the fraud API for 200 ms, and calls the card issuer for 120 ms. The issuer allows 150 calls in flight for your merchant, across all pods. Today each pod has a fixed pool of 50 threads and 10 connections. First question: is the thread pool the bottleneck today?",
    "code": "time in the system   W = 15 + 200 + 120 ms = 335 ms\nthreads needed       L = 200/s x 0.335 s  = 67\nthe pool has 50, so at peak requests queue for a thread\npool capacity            50 / 0.335 s     = about 149 requests/s", "lang": "text"},
   {"say": "Yes. The pool tops out near 149 requests per second, below the 200 that arrive, so requests queue at peak. Virtual threads remove that limit. Now check each downstream with the same formula, because nothing caps them any more.",
    "code": "database connections busy   200/s x 0.015 s = 3      pool of 10: fine\nissuer calls in flight      200/s x 0.120 s = 24     limit 150 / 4 pods = 37 per pod\nfraud calls in flight       200/s x 0.200 s = 40     no published limit: ask the fraud team\nvirtual threads             67 at a time, a small amount of heap", "lang": "text"},
   {"say": "Write the limits in code: one shared semaphore per downstream, sized per pod, held only around that downstream's calls.",
    "code": "final class Downstreams {\n    // 1. issuer: 150 calls in flight for the merchant, shared by 4 pods\n    final Semaphore issuer = new Semaphore(150 / 4, true);\n    // 2. database: one permit per pooled connection\n    final Semaphore db = new Semaphore(10, true);\n    // 3. fraud: no limit yet; add one when the fraud team gives you a number\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class Downstreams {\n    // 1. issuer: 150 calls in flight for the merchant, shared by 4 pods\n    val issuer = Semaphore(150 / 4, true)\n    // 2. database: one permit per pooled connection\n    val db = Semaphore(10, true)\n    // 3. fraud: no limit yet; add one when the fraud team gives you a number\n}"},
   {"say": "Predict where each limit starts to bite, by dividing permits by the time each request holds one. The issuer semaphore starts to queue at 37 / 0.12 s, about 308 requests per second per pod, and the database at 10 / 0.015 s, about 666. If one pod dies, the other 3 get about 267 per second each, still under 308. So the first alert to set is the issuer semaphore's queue length, and the capacity of the service is now about 300 requests per second per pod instead of 149."}
  ]
 },
 "lab": {
  "title": "Migrate the quote service",
  "minutes": 12,
  "files": [f"{lab}/main/{K}/QuoteService.kt", f"{lab}/main/{K}/QuoteModel.kt"],
  "run": "./gradlew :vthreads:test --tests 'workbench.vthreads.l06.*'",
  "steps": [
   "This lab is in Kotlin. Run the tests once. Four of five fail. The burst test passes, because the old pool of 10 keeps the database safe by accident.",
   "TODO 1: replace `Executors.newFixedThreadPool(10)` with `Executors.newVirtualThreadPerTaskExecutor()`. Run the tests again. Now all five fail with `connection pool: no connection after 30 ms`. That's the limit you just removed.",
   "TODO 2: add `private val dbPermits = Semaphore(db.poolSize, true)` and hold a permit around the `db.tier(...)` call and nothing else: `acquire()` before a `try`, `release()` in its `finally`. A small `private inline fun <T> withDbPermit(block: () -> T): T` keeps `quote` readable.",
   "TODO 3 and 4: `dbWaiting()` returns `dbPermits.queueLength`, and `close()` calls `close()` on the new executor.",
   "Run the tests until all five pass. Then read the pool-size test: it builds a pool of 3 connections. Explain why `Semaphore(10)` would fail it."
  ],
  "hints": [
   "Keep the FX call outside the permit. If the permit covers the whole request, you have rebuilt the old 10-thread limit, and the FX test fails.",
   "`acquire()` goes before the `try`. If it sat inside, a thread interrupted while waiting would `release()` a permit it never got, and the limit would quietly grow.",
   "Import `java.util.concurrent.Semaphore`, not `kotlinx.coroutines.sync.Semaphore`. The coroutine one suspends coroutines and doesn't work from a plain thread.",
   "`Semaphore.queueLength` is an estimate while threads come and go, but it is exact when nothing changes, which is what the gauge test waits for."
  ],
  "done_when": "All five tests in `QuoteServiceTest` pass."
 },
 "drill": {
  "title": "Write the migrated client from memory",
  "minutes": 4,
  "prompt": "Close the lab. Write a `LedgerClient` that many virtual threads call at once through `post(entry)`, and that never lets more than `connections` of them inside `ledgerDb.insert(entry)` at the same time. Callers that can't get in within 200 ms should fail fast with an exception. Then name the one metric you would export from it.",
  "answer": {"lang": "java", "src": "final class LedgerClient {\n    private final LedgerDb ledgerDb;\n    private final Semaphore permits;                       // one per pooled connection, shared by all callers\n\n    LedgerClient(LedgerDb ledgerDb, int connections) {\n        this.ledgerDb = ledgerDb;\n        this.permits = new Semaphore(connections, true);\n    }\n\n    void post(Entry entry) throws InterruptedException {\n        if (!permits.tryAcquire(200, TimeUnit.MILLISECONDS)) {   // a deadline, not an endless wait\n            throw new LedgerBusyException(\"no ledger connection within 200 ms\");\n        }\n        try {\n            ledgerDb.insert(entry);                        // only this call holds a permit\n        } finally {\n            permits.release();\n        }\n    }\n\n    int waiting() {                                        // the metric: callers queued right now\n        return permits.getQueueLength();\n    }\n}",
             "alt": {"lang": "kotlin", "src": "class LedgerClient(private val ledgerDb: LedgerDb, connections: Int) {\n    private val permits = Semaphore(connections, true)     // one per pooled connection, shared by all callers\n\n    fun post(entry: Entry) {\n        if (!permits.tryAcquire(200, TimeUnit.MILLISECONDS)) {   // a deadline, not an endless wait\n            throw LedgerBusyException(\"no ledger connection within 200 ms\")\n        }\n        try {\n            ledgerDb.insert(entry)                         // only this call holds a permit\n        } finally {\n            permits.release()\n        }\n    }\n\n    fun waiting(): Int = permits.queueLength               // the metric: callers queued right now\n}"}}
 },
 "recap": [
  "A fixed thread pool limits every downstream its threads touch. Moving to virtual threads removes that limit together with the pool.",
  "Write each limit down: one shared `Semaphore` per downstream, sized from that downstream, held only around its calls.",
  "Don't grow connection pools to match thread counts. The database decides how many connections help, and every pod multiplies them.",
  "Checklist: JDK 25 first, one virtual thread per task, explicit limits, ThreadLocal caches and context, CPU work on a bounded pool, a deadline on every wait.",
  "Quarkus opts in per endpoint with `@RunOnVirtualThread`; Spring Boot 3.2+ switches with `spring.threads.virtual.enabled=true`. Neither adds your limits.",
  "Measure before and after. In-flight = throughput × time (Little's law), and a growing queue gauge with flat throughput marks the saturated downstream."
 ],
 "quiz": [
  {"q": "After the switch to virtual threads, p99 latency doubles at peak while throughput stays flat. Which metric tells you whether the database is the bottleneck?",
   "options": [
    "The number of live virtual threads",
    "The queue length on the database semaphore (or the pool's pending count), climbing at peak",
    "CPU usage of the carrier threads",
    "The number of `ForkJoinPool` worker threads"
   ], "answer": 1,
   "why": "A saturated downstream shows up as a queue that grows while throughput stays flat. Virtual thread counts grow with any slowdown and don't say where the time goes. Carrier CPU is low when everybody waits, and the scheduler's worker count stays near the core count."},
  {"q": "A pod handles 300 requests per second, and each request holds a database connection for 25 ms. On average, about how many connections are busy?",
   "options": ["About 8", "About 25", "About 75", "About 300"], "answer": 0,
   "why": "Little's law: busy connections = arrival rate × holding time = 300/s × 0.025 s = 7.5. A pool of 10 is close to its limit at this rate, and 10 / 0.025 s = 400 requests per second is where it saturates. The other options mix up the holding time with a count, or assume every request holds a connection the whole time."},
  {"q": "In a Quarkus service, how do you run one blocking REST endpoint on virtual threads?",
   "options": [
    "Raise `quarkus.thread-pool.max-threads` to 10,000",
    "Set `spring.threads.virtual.enabled=true`",
    "Annotate the endpoint method with `@RunOnVirtualThread`",
    "Return a `Uni` from the method"
   ], "answer": 2,
   "why": "Quarkus opts in per method or class with `@RunOnVirtualThread`, and each call then runs on a new virtual thread. The thread pool setting sizes platform worker threads. The `spring.threads` property is Spring Boot's global switch. Returning a `Uni` makes the endpoint reactive and runs it on the event loop, which must never block."},
  {"q": "After the migration, the connection pool reports timeouts at every peak. Which fix is right?",
   "options": [
    "Raise the pool's maximum size to 1,000 connections",
    "Go back to a fixed pool of 20 platform threads for all request handling",
    "Raise the pool's connection timeout to 5 minutes",
    "Put a shared `Semaphore` sized to the pool around the database work, and use `tryAcquire` with a deadline that fits the request's budget"
   ], "answer": 3,
   "why": "The semaphore restores the limit the old pool gave you, only around the database work, with a queue you can see and a deadline you choose. A huge pool overloads the database for every service that shares it. A fixed pool brings back the cap on everything, including calls that never needed it. A 5-minute timeout hides overload as very slow requests."},
  {"q": "From the lesson \"Pinning, ThreadLocals and other traps\": your service runs on JDK 21, and its JDBC driver holds a `synchronized` lock while it reads from the socket. You move request handling to virtual threads. What is the main risk, and the simplest fix?",
   "options": [
    "Pinning: queries block their carriers, and a few slow ones can stall every virtual thread. Upgrade to JDK 25, or to a driver version that uses `ReentrantLock`",
    "Data races inside the driver, because virtual threads don't respect `synchronized`. Wrap every call in your own lock",
    "A `ThreadLocal` leak in the driver. Call `remove()` after each query",
    "No risk: a JDBC driver never blocks while it holds a lock"
   ], "answer": 0, "from": "vt-04",
   "why": "On JDK 21 to 23, blocking while holding a monitor pins the carrier, and with as many carriers as cores, a few slow queries can hold all of them. JEP 491 fixed this in JDK 24, so JDK 25 is the cleanest fix. `synchronized` still gives mutual exclusion on virtual threads, so there is no new race."}
 ],
 "flashcards": [
  {"front": "What limit does a fixed thread pool give you without saying so?", "back": "No more than N requests can reach any downstream at once. Moving to virtual threads removes it."},
  {"front": "Where does the semaphore go when you migrate to virtual threads?", "back": "Around the one downstream call that needs the limit, as one object shared by all requests, sized from that downstream."},
  {"front": "Should you grow the connection pool to match the number of virtual threads?", "back": "No. The database decides how many connections help, roughly a few per database CPU core, and every pod multiplies the pool. Queue in front of the pool instead."},
  {"front": "How do you run a Quarkus REST endpoint on virtual threads?", "back": "Annotate the method or class with `@RunOnVirtualThread`. Quarkus has no global switch."},
  {"front": "How do you switch a Spring Boot 3.2+ application to virtual threads?", "back": "`spring.threads.virtual.enabled=true`"},
  {"front": "Little's law in one line?", "back": "Requests in flight = throughput × time in the system (L = λW)."},
  {"front": "Which gauge shows a saturated downstream after the move?", "back": "The queue on its semaphore (or the pool's pending count) growing while throughput stays flat."}
 ],
 "terms": [
  {"term": "Implicit limit", "plain": "A cap on concurrency that nobody configured on purpose, such as a thread pool's size protecting a database."},
  {"term": "Bulkhead", "plain": "An explicit limit on calls to one downstream, usually a shared Semaphore, so it can't be overloaded."},
  {"term": "Connection pool", "plain": "A fixed set of open database connections that callers borrow and return. Callers wait, or time out, when all are in use."},
  {"term": "Little's law", "plain": "In a stable system, requests in flight = throughput × average time in the system."},
  {"term": "@RunOnVirtualThread", "plain": "The annotation that makes Quarkus run an endpoint or message handler on a new virtual thread per call."},
  {"term": "Load shedding", "plain": "Rejecting work quickly, for example with a 503, when a limit is full, instead of letting it wait without end."}
 ],
 "explain_back": {
  "prompt": "Your manager asks why the team can't just flip the virtual threads switch in production tomorrow. Explain what the switch changes, what can break, and how you would roll it out and measure it.",
  "answer": "The switch gives every request its own virtual thread, so blocking calls stop tying up a limited pool and many more requests can be in flight. That is the point, and it is also the risk: the old pool also limited how many requests reached the database and the other downstreams, without anyone writing that down. After the switch, a peak sends all of them at once, and the connection pool starts timing out or a partner API starts rejecting us. So before the switch I'd run JDK 25 to avoid `synchronized` pinning, add a shared semaphore per downstream sized from its real limit, keep the connection pool small, replace ThreadLocal caches, and keep CPU-heavy work on a bounded pool. For the rollout I'd take a baseline under a load test, switch one pod or one endpoint, and compare p99, error rate, heap and GC with the others. I'd also watch the semaphore queues and the pool's pending count, and use Little's law to predict at what rate each one saturates."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Admission control at the door.** The lab's semaphore waits without a deadline, deep inside the request. In a payment API it's often better to decide at the start: try to take every permit the request will need, or a single \"requests in progress\" permit sized from Little's law, with a short `tryAcquire` deadline, and answer 503 at once if you can't. Then you never call the fraud API for a request that would later time out at the database.\n\n**Pool timeouts versus semaphore waits.** A pool's borrow timeout and a semaphore's deadline look alike, but they sit at different places. The pool timeout fires after the request has done part of its work and maybe holds other resources. A deadline at the semaphore, at the start of the call, fails before any of that. Keep the pool's timeout too, as a safety net for bugs in your own limits.\n\n**Fairness and the tail.** A fair semaphore serves waiters in arrival order. That costs a little throughput and keeps p99 close to p50 during a burst. A non-fair one lets a newcomer grab a permit that was just released, which helps the average and hurts the unlucky waiters. For payment latency the tail matters more.\n\n**Thread dumps after the move.** `jstack` shows carriers, not the thousands of parked virtual threads. `jcmd <pid> Thread.dump_to_file -format=json dump.json` writes all of them, grouped by the executor or scope that owns them. Before an incident, practise finding the stack of one stuck request in such a dump.\n\n**When not to migrate.** A service that is CPU-bound, or that already runs fully reactive code on a few event-loop threads, gains little. The win is largest for services that block on I/O and are limited by their thread pool today. Little's law tells you which kind yours is: compare the threads you need (rate × time) with the threads you have."
 },
 "sources": [
  {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444"},
  {"title": "Virtual thread support reference (Quarkus guide)", "url": "https://quarkus.io/guides/virtual-threads"},
  {"title": "About Pool Sizing (HikariCP wiki)", "url": "https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing"},
  {"title": "Semaphore (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Semaphore.html"}
 ]
}
out = ROOT / "content/lessons/vt-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
