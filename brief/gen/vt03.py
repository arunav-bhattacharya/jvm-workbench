import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/vthreads/src"
P = "java/workbench/vthreads/l03"
K = "kotlin/workbench/vthreads/l03"
read = lambda p: (ROOT / p).read_text()

FIG = (
    '<svg viewBox="0 0 680 270" role="img" aria-label="Thousands of virtual threads, one per payment, wait parked at a Semaphore with 20 permits. At most 20 calls at a time pass through to the card issuer API.">'
    '<text class="t-s t-m" x="95" y="40" text-anchor="middle">one virtual thread per payment</text>'
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
    '<text class="t t-code" x="330" y="104" text-anchor="middle">Semaphore(20)</text>'
    '<text class="t-s" x="330" y="134" text-anchor="middle">no permit: park</text>'
    '<text class="t-s" x="330" y="158" text-anchor="middle">release(): wake one</text>'
    '<line class="ln-a" x1="410" y1="130" x2="476" y2="130" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="443" y="122" text-anchor="middle">20 at once</text>'
    '<rect class="box" x="480" y="56" width="180" height="150" rx="8"/>'
    '<text class="t" x="570" y="100" text-anchor="middle">card issuer API</text>'
    '<text class="t-s" x="570" y="130" text-anchor="middle">at most 20 in flight</text>'
    '<text class="t-s" x="570" y="154" text-anchor="middle">120 ms per call</text>'
    '<text class="t-s t-a" x="340" y="254" text-anchor="middle">Little\'s law: 20 permits / 0.12 s = at most 167 calls per second</text>'
    '</svg>'
)

L = {
 "id": "vt-03",
 "title": "Using virtual threads: one per task, limits with semaphores",
 "minutes": 35,
 "goal": "By the end you can start virtual threads the right way, fan out thousands of blocking calls with one virtual thread per task, and cap what a downstream system sees with a shared Semaphore instead of a pool.",
 "warmup": {
  "q": "The card issuer allows 20 concurrent calls from your service. You move a 10,000-payment batch to virtual threads. What is the right way to stay under the issuer's limit?",
  "options": [
   "`Executors.newFixedThreadPool(20, Thread.ofVirtual().factory())`: a pool of 20 virtual threads",
   "`Executors.newVirtualThreadPerTaskExecutor()`, and one shared `Semaphore(20)` acquired around the issuer call",
   "`Executors.newVirtualThreadPerTaskExecutor()` on its own, since virtual threads limit themselves to the core count",
   "A new `Semaphore(20)` inside each payment's task"
  ],
  "answer": 1,
  "why": "Limit the resource, not the threads. A pool of 20 also limits everything else each task does, so work that needs no limit waits too. The per-task executor has no limit at all: it will start 10,000 virtual threads. A semaphore created per task gives every task its own 20 permits, which limits nothing. One shared semaphore around the call is the only option that caps the issuer at 20."
 },
 "sections": [
  {
   "h": "Five ways to start a virtual thread",
   "body": "JDK 21 has no `new VirtualThread()`. You start virtual threads through the `Thread.Builder` API or through an executor:\n\n```java\n// 1. a one-off, no name\nThread a = Thread.startVirtualThread(() -> settle(p));\n\n// 2. a builder, when you want a name in thread dumps\nThread b = Thread.ofVirtual().name(\"auth-\", 0).start(() -> settle(p));   // auth-0\n\n// 3. created now, started later\nThread c = Thread.ofVirtual().unstarted(() -> settle(p));\nc.start();\n\n// 4. a ThreadFactory, for libraries and frameworks that take one\nThreadFactory vtf = Thread.ofVirtual().name(\"ledger-\", 0).factory();\nExecutorService named = Executors.newThreadPerTaskExecutor(vtf);\n\n// 5. what you'll use most: one new virtual thread per task\nExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor();\n```\n\n```kotlin\n// 1. a one-off, no name\nval a = Thread.startVirtualThread { settle(p) }\n\n// 2. a builder, when you want a name in thread dumps\nval b = Thread.ofVirtual().name(\"auth-\", 0).start { settle(p) }   // auth-0\n\n// 3. created now, started later\nval c = Thread.ofVirtual().unstarted { settle(p) }\nc.start()\n\n// 4. a ThreadFactory, for libraries and frameworks that take one\nval vtf = Thread.ofVirtual().name(\"ledger-\", 0).factory()\nval named = Executors.newThreadPerTaskExecutor(vtf)\n\n// 5. what you'll use most: one new virtual thread per task\nval perTask = Executors.newVirtualThreadPerTaskExecutor()\n```\n\nThe builder with `name(\"auth-\", 0)` numbers its threads: the first is `auth-0`, the next `auth-1`. A builder object is not thread safe, so build it in one place. The factory it returns is thread safe, so share that.\n\nUse the executor in normal code. It gives you `Future`s, it has a `close()` that waits, and every framework already knows how to take an `ExecutorService`. Use the builder when you start a single long-lived thread, such as a Kafka poll loop, and want a name you can find in a thread dump. Virtual threads have no name by default, which makes a dump of 50,000 of them hard to read.\n\nAll of these return ordinary `Thread` objects. `join`, `interrupt` and `isAlive` work as usual, and `isVirtual()` tells you which kind you have.",
   "try": {
    "title": "Start one of each",
    "minutes": 3,
    "steps": [
     "Run `BuildersDemo`. Each line is printed from inside the new thread.",
     "Predict before you look: which ones have a name, and what is `isDaemon()` for each?",
     "Add `.daemon(false)` before `.start(...)` on the `ofVirtual()` line (in either file) and run again. What happens?"
    ],
    "code": {"lang": "java", "title": "BuildersDemo.java", "src": read(f"{lab}/demo/{P}/BuildersDemo.java"),
             "run": "./gradlew :vthreads:demo -Pmain=workbench.vthreads.l03.BuildersDemo",
             "file": f"{lab}/demo/{P}/BuildersDemo.java",
             "alt": {"lang": "kotlin", "title": "BuildersDemo.kt", "src": read(f"{lab}/demo/{K}/BuildersDemo.kt"),
                     "run": "./gradlew :vthreads:demo -Pmain=workbench.vthreads.l03.BuildersDemoKt",
                     "file": f"{lab}/demo/{K}/BuildersDemo.kt"}},
    "expect": "Only `auth-7`, `ledger-0` and `ledger-1` have names; the rest print an empty name. Every line says `virtual=true daemon=true`. The `.daemon(false)` edit doesn't compile, in Java or in Kotlin: `Thread.ofVirtual()` returns a `Thread.Builder.OfVirtual`, which has no `daemon` method, because virtual threads are always daemon threads."
   }
  },
  {
   "h": "One task, one virtual thread, one try block",
   "body": "`newVirtualThreadPerTaskExecutor()` starts a brand-new virtual thread for every task you submit. It keeps no threads around and has no queue. Its Javadoc says it plainly: the number of threads it creates is unbounded.\n\nSince JDK 19, `ExecutorService` is `AutoCloseable`. `close()` shuts the executor down and then waits until every submitted task has finished. So the shape of a fan-out is one try-with-resources block:\n\n```java\nList<Receipt> authorizeAll(List<Payment> batch) throws InterruptedException, ExecutionException {\n    try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {\n        // 1. fork: start every call before waiting for any\n        List<Future<Receipt>> futures = new ArrayList<>();\n        for (Payment p : batch) futures.add(perTask.submit(() -> issuer.authorize(p)));\n        // 2. join: collect in input order\n        List<Receipt> receipts = new ArrayList<>();\n        for (Future<Receipt> f : futures) receipts.add(f.get());\n        return receipts;\n    }   // 3. close(): waits for any task still running\n}\n```\n\n```kotlin\nfun authorizeAll(batch: List<Payment>): List<Receipt> =\n    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->\n        // 1. fork: start every call before waiting for any\n        val futures = batch.map { p -> perTask.submit(Callable { issuer.authorize(p) }) }\n        // 2. join: collect in input order\n        futures.map { it.get() }\n    }   // 3. close(): waits for any task still running\n```\n\nCreate the executor where the work starts, and let it end where the work ends. A short-lived executor per request or per batch costs almost nothing, because it doesn't own any threads. It also means that when this method returns, no thread it started is still running. That property gets a name and a whole API in lesson 5 of this track.\n\nIn a Kafka consumer the natural unit is the poll batch: one executor block per batch, one virtual thread per record, and the offset commit after the block closes, when every record has finished. Do this only for topics where records with the same key don't have to be processed in order, because the virtual threads finish in any order.\n\nTwo details trip people up. Start every task before you call `get()` on any of them. A loop that submits one task and then waits on it runs your batch one call at a time, on 5,000 threads. And `get()` reports a failed task as an `ExecutionException` whose cause is the real exception. The other tasks keep running when one fails, and `close()` still waits for them. Cancelling them is also lesson 5's topic.\n\nThis executor has no limit, and that is deliberate. A limit belongs somewhere else, which the next two sections show."
  },
  {
   "h": "Don't pool virtual threads",
   "body": "Thread pools exist for two reasons: platform threads are expensive to create, so you reuse them, and a fixed pool caps how much work runs at once. Neither reason survives virtual threads.\n\nCreating a virtual thread costs about as much as creating a small object, so reuse saves almost nothing. And a pool is the wrong place for a cap, because it caps everything the task does, not just the one call that needs it.\n\nHere is the mistake, in code that compiles and runs fine:\n\n```java\n// anti-pattern: a pool of 20 virtual threads to protect a 20-connection database\nExecutorService pool = Executors.newFixedThreadPool(20, Thread.ofVirtual().factory());\npool.execute(() -> {\n    Risk risk = fraud.check(p);      // 60 ms, needs no limit, but waits for a pool slot anyway\n    ledger.record(p, risk);          // 10 ms, the only call that needs the limit\n});\n```\n\n```kotlin\n// anti-pattern: a pool of 20 virtual threads to protect a 20-connection database\nval pool = Executors.newFixedThreadPool(20, Thread.ofVirtual().factory())\npool.execute {\n    val risk = fraud.check(p)        // 60 ms, needs no limit, but waits for a pool slot anyway\n    ledger.record(p, risk)           // 10 ms, the only call that needs the limit\n}\n```\n\nEach task holds a pool slot for 70 ms, so 1,000 payments take 1,000 / 20 × 70 ms = 3.5 s. If only the ledger call is limited, the fraud calls all overlap. The batch then takes about 60 ms plus 1,000 / 20 × 10 ms, about 0.56 s. Same database limit, six times faster.\n\nPooled threads bring a second problem with them: `ThreadLocal`s survive from one task to the next on a reused thread. Lesson 4 of this track covers that.\n\nThe rule from JEP 444 is short. Never pool virtual threads. Create one per task, and put the limit on the resource.\n\nPools are still the right tool for platform threads doing CPU work. A `newFixedThreadPool(cores)` for hashing, PDF rendering or signature checks keeps that work bounded and off the virtual thread scheduler. The rule is about virtual threads only.",
   "try": {
    "title": "A pool vs a semaphore, same limit",
    "minutes": 4,
    "steps": [
     "Read `PoolVsSemaphoreDemo`. Each request makes a 60 ms fraud call and a 10 ms ledger call, and the ledger allows 20 at once.",
     "Predict both times with the arithmetic above, then run it.",
     "Change `DB_LIMIT` to 50 and predict again. Which version speeds up more?"
    ],
    "code": {"lang": "java", "title": "PoolVsSemaphoreDemo.java", "src": read(f"{lab}/demo/{P}/PoolVsSemaphoreDemo.java"),
             "run": "./gradlew :vthreads:demo -Pmain=workbench.vthreads.l03.PoolVsSemaphoreDemo",
             "file": f"{lab}/demo/{P}/PoolVsSemaphoreDemo.java",
             "alt": {"lang": "kotlin", "title": "PoolVsSemaphoreDemo.kt", "src": read(f"{lab}/demo/{K}/PoolVsSemaphoreDemo.kt"),
                     "run": "./gradlew :vthreads:demo -Pmain=workbench.vthreads.l03.PoolVsSemaphoreDemoKt",
                     "file": f"{lab}/demo/{K}/PoolVsSemaphoreDemo.kt"}},
    "expect": "The pool takes about 3.5 s (one run here: 3,584 ms) and the semaphore version about 0.6 s (586 ms). With a limit of 50 the pool drops to about 1.4 s and the semaphore version to about 0.26 s. Both respect the database limit; only the pool also slows down the work that has no limit."
   }
  },
  {
   "h": "Limit the resource with a shared Semaphore",
   "body": "A `Semaphore` holds a number of permits. `acquire()` takes one, and waits if none are left. `release()` gives one back and wakes a waiter. On a virtual thread, waiting in `acquire()` parks the thread, so 5,000 waiters cost 5,000 small heap objects and no OS threads.\n\nThe pattern has three rules:\n\n```java\nfinal class IssuerClient {\n    private final Semaphore inFlight = new Semaphore(20);   // 1. one per resource, shared by all callers\n    private final IssuerHttp http;\n\n    IssuerClient(IssuerHttp http) { this.http = http; }\n\n    Auth authorize(Payment p) throws InterruptedException {\n        inFlight.acquire();                               // 2. acquire outside the try\n        try {\n            return http.authorize(p);                     // only the call that needs the limit\n        } finally {\n            inFlight.release();                           // 3. always give it back\n        }\n    }\n}\n```\n\n```kotlin\nclass IssuerClient(private val http: IssuerHttp) {\n    private val inFlight = Semaphore(20)                 // 1. one per resource, shared by all callers\n\n    fun authorize(p: Payment): Auth {\n        inFlight.acquire()                               // 2. acquire outside the try\n        try {\n            return http.authorize(p)                     // only the call that needs the limit\n        } finally {\n            inFlight.release()                           // 3. always give it back\n        }\n    }\n}\n```\n\nThe semaphore lives with the resource, as a field on the client that every request uses. A semaphore created inside a request handler gives each request its own 20 permits and limits nothing. `acquire()` sits before the `try`, so a thread interrupted while waiting never releases a permit it didn't get. If it did, the limit would quietly grow to 21, then 22.\n\nPick the number from the downstream side: the issuer's documented concurrency limit, or the size of the database connection pool. Then check it with Little's law. Twenty permits on a 120 ms call give at most 20 / 0.12 s = 167 calls per second. If payments arrive faster than that, the waiters pile up, and each one waits longer than the last.\n\nWaiting forever is rarely what you want in a payment API. `tryAcquire(200, MILLISECONDS)` returns `false` if no permit came in time, so you can answer with a fast 503 or a retry hint instead of a slow timeout. This pattern is usually called a **bulkhead**, after the walls that stop one flooded section from sinking a ship.\n\nA request that calls two limited downstreams uses two semaphores: take the issuer permit, release it, then take the ledger permit. Don't hold one permit while you wait for another. It ties up the first resource for nothing, and two code paths that take them in opposite orders can deadlock exactly like two locks.",
   "figure": {"svg": FIG, "caption": "Thousands of virtual threads park cheaply at the semaphore. Only 20 at a time reach the issuer, and Little's law gives the resulting throughput."},
   "try": {
    "title": "Shed load instead of queueing forever",
    "minutes": 4,
    "steps": [
     "`ShedLoadDemo` sends 1,000 requests at once through a `Semaphore(20)` guarding a 50 ms call. Each request waits at most 200 ms for a permit.",
     "Predict how many get served. Hint: in 200 ms each permit can serve about 200 / 50 = 4 calls, plus the first round.",
     "Run it, then try `-Pargs='20 50 2000'` and `-Pargs='100 50 200'`, predicting each first."
    ],
    "code": {"lang": "java", "title": "ShedLoadDemo.java", "src": read(f"{lab}/demo/{P}/ShedLoadDemo.java"),
             "run": "./gradlew :vthreads:demo -Pmain=workbench.vthreads.l03.ShedLoadDemo",
             "file": f"{lab}/demo/{P}/ShedLoadDemo.java",
             "alt": {"lang": "kotlin", "title": "ShedLoadDemo.kt", "src": read(f"{lab}/demo/{K}/ShedLoadDemo.kt"),
                     "run": "./gradlew :vthreads:demo -Pmain=workbench.vthreads.l03.ShedLoadDemoKt",
                     "file": f"{lab}/demo/{K}/ShedLoadDemo.kt"}},
    "expect": "With the defaults, about 100 requests are served (20 permits × 5 rounds; one run here served 94) and the rest are shed in about a third of a second. A 2 s wait serves about 20 × 41 = 820. With 100 permits and 200 ms, about 500 are served. Served requests = permits × (max wait / call time + 1), which is Little's law turned around."
   },
   "refs": [
    {"title": "Semaphore (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Semaphore.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A semaphore is the stack of visitor badges at a building's front desk. The building (the card issuer) has room for 20 visitors, so there are 20 badges. Visitors who arrive when the stack is empty sit in the lobby, which is cheap, and the next one in line gets a badge when someone hands theirs back on the way out. A pool of 20 virtual threads is like hiring 20 escorts who each walk one visitor through the whole day, the coffee shop included, so visitors who only want coffee wait for an escort too. The analogy breaks at the lobby: a real lobby fills up, but parked virtual threads only cost heap, so the line can grow far longer than you'd want. That is why you set a wait limit.",
 "in_your_world": "Every downstream in a payment flow has a concurrency contract: the card network's API allows a fixed number of calls in flight per merchant, your Oracle pool has 20 connections, the fraud vendor rate-limits by client. On platform threads the request pool size was hiding those limits. On virtual threads, each one needs its own shared semaphore (or a library bulkhead, such as Resilience4j's, if you already use one) on the client object. In a Kafka consumer that fans out one virtual thread per record in a poll batch, the semaphore is what keeps a 500-record batch from opening 500 calls to the issuer at once.",
 "mistake": "The most common mistake is keeping the old habit of a fixed pool and just giving it virtual threads: `newFixedThreadPool(20, Thread.ofVirtual().factory())`. It looks like a cheap upgrade and it does limit the database. It also limits every other part of each task, keeps an unbounded queue in front of the pool, and reuses threads, so `ThreadLocal` state leaks between tasks. The second most common is the opposite: dropping the limit entirely because \"virtual threads are cheap\", and then sending 5,000 concurrent calls to a downstream that allows 20. Use one virtual thread per task and one shared semaphore per scarce resource.",
 "compare": {
  "title": "Fan out with a shared limit in Java and Kotlin",
  "java": {"title": "FanOut.java + Bulkhead.java (lab solution, trimmed)", "src": "public final class Bulkhead {\n    private final Semaphore permits;\n\n    public Bulkhead(int maxConcurrent) { permits = new Semaphore(maxConcurrent); }\n\n    public <T> T call(Callable<T> work) throws Exception {\n        permits.acquire();\n        try { return work.call(); }\n        finally { permits.release(); }\n    }\n}\n\nstatic final Bulkhead ISSUER = new Bulkhead(20);\n\nList<String> authorizeAll(List<String> ids) throws Exception {\n    try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {\n        List<Future<String>> fs = new ArrayList<>();\n        for (String id : ids) fs.add(perTask.submit(() -> ISSUER.call(() -> authorize(id))));\n        List<String> out = new ArrayList<>();\n        for (Future<String> f : fs) out.add(f.get());\n        return out;\n    }\n}"},
  "kotlin": {"title": "FanOutKotlin.kt", "src": read(f"{lab}/demo/{K}/FanOutKotlin.kt")},
  "note": "The Kotlin version is the same design: `use {}` is Kotlin's try-with-resources and works because `ExecutorService` is `AutoCloseable` since JDK 19, and an `inline` extension gives `Semaphore` a `withPermit` block. `Callable { ... }` picks the `submit` overload that returns a value; a bare lambda can be read as a `Runnable`. Watch the name clash: kotlinx.coroutines has its own `Semaphore` with a suspending `withPermit`, built for coroutines. Inside coroutines use that one, because `java.util.concurrent.Semaphore.acquire()` blocks the thread. On virtual threads, use the JDK semaphore. Run the Kotlin file with `./gradlew :vthreads:demo -Pmain=workbench.vthreads.l03.FanOutKotlinKt`."
 },
 "worked": {
  "title": "Send a payout batch to the bank, 20 at a time",
  "steps": [
   {"say": "The bank's payout API allows 20 concurrent calls per client and takes about 150 ms. A batch has 3,000 payouts, and each one also needs an account lookup that has no limit. Start with the limit, as a field on the client that every caller shares.", "code": "final class BankClient {\n    // one limit for the whole service, from the bank's API contract\n    private final Semaphore inFlight = new Semaphore(20);\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class BankClient {\n    // one limit for the whole service, from the bank's API contract\n    private val inFlight = Semaphore(20)\n}"},
   {"say": "Guard only the bank call. The account lookup happens before `acquire()`, so 3,000 lookups overlap freely.", "code": "PayoutResult send(Payout p) throws Exception {\n    Account acct = accounts.lookup(p.accountId());   // 1. unlimited work first\n    inFlight.acquire();                               // 2. wait for a slot (parks a virtual thread)\n    try {\n        return bank.payout(acct, p);                  // 3. the only limited call\n    } finally {\n        inFlight.release();                           // 4. always give the slot back\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "fun send(p: Payout): PayoutResult {\n    val acct = accounts.lookup(p.accountId)   // 1. unlimited work first\n    inFlight.acquire()                        // 2. wait for a slot (parks a virtual thread)\n    try {\n        return bank.payout(acct, p)           // 3. the only limited call\n    } finally {\n        inFlight.release()                    // 4. always give the slot back\n    }\n}"},
   {"say": "Fan out one virtual thread per payout, and collect in order. The executor block guarantees that no payout is still running when the method returns.", "code": "List<PayoutResult> sendAll(List<Payout> batch) throws Exception {\n    try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {\n        List<Future<PayoutResult>> fs = new ArrayList<>();\n        for (Payout p : batch) fs.add(perTask.submit(() -> send(p)));   // 5. fork all\n        List<PayoutResult> results = new ArrayList<>();\n        for (Future<PayoutResult> f : fs) results.add(f.get());          // 6. join in order\n        return results;\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "fun sendAll(batch: List<Payout>): List<PayoutResult> =\n    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->\n        val fs = batch.map { p -> perTask.submit(Callable { send(p) }) }   // 5. fork all\n        fs.map { it.get() }                                                 // 6. join in order\n    }"},
   {"say": "Check the timing with Little's law before you ship it. The bank stage caps you at 20 / 0.15 s = 133 payouts per second, so 3,000 payouts take about 22.5 s no matter how many threads you start. If that is too slow, the fix is a higher limit agreed with the bank, not more threads."}
  ]
 },
 "lab": {
  "title": "Fan out 5,000 calls, never more than 20 in flight",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/FanOut.java", f"{lab}/main/{P}/Bulkhead.java", f"{lab}/main/{P}/BlockingCall.java"],
  "run": "./gradlew :vthreads:test --tests 'workbench.vthreads.l03.*'",
  "steps": [
   "Run the tests once. All six fail.",
   "Write `FanOut.callAll`: open `Executors.newVirtualThreadPerTaskExecutor()` in try-with-resources, submit one task per input (`perTask.submit(() -> call.call(input))`), then call `get()` on each future in order and collect the results.",
   "Write `Bulkhead`: a `Semaphore` field built in the constructor, `call` with `acquire()` before the `try` and `release()` in `finally`, and `available()` from `availablePermits()`.",
   "Run the tests. The bulkhead test sends 5,000 calls through `Bulkhead(20)` and records the most calls that were inside the fake issuer at once. It must be at most 20, and at least 10 to prove the calls overlap.",
   "Read the shared-limit test: two fan-outs run at the same time through one `Bulkhead`. Think about what would happen if each fan-out made its own."
  ],
  "hints": [
   "Inside a lambda, `input` must be effectively final. The enhanced `for` loop variable is, so `for (I input : inputs)` works directly.",
   "`Future.get()` already throws `ExecutionException` with the task's exception as the cause, which is exactly what the failure test expects. You don't need to wrap anything.",
   "If the 5,000-call test takes minutes, you are probably waiting on each future right after submitting it. Submit all of them first."
  ],
  "done_when": "All six tests in `FanOutTest` pass."
 },
 "drill": {
  "title": "The bulkhead from memory",
  "minutes": 4,
  "prompt": "Close this page. Write a class `FraudClient` whose `check(Payment p)` method lets at most 50 calls reach `http.check(p)` at once across the whole service, and gives up with a `RejectedExecutionException` if no slot frees up within 100 ms. Then compare with the answer: where is `acquire` relative to the `try`?",
  "answer": {"lang": "java", "src": "final class FraudClient {\n    private final Semaphore inFlight = new Semaphore(50);   // shared by every caller\n    private final FraudHttp http;\n\n    FraudClient(FraudHttp http) { this.http = http; }\n\n    Risk check(Payment p) throws InterruptedException {\n        if (!inFlight.tryAcquire(100, TimeUnit.MILLISECONDS)) {\n            throw new RejectedExecutionException(\"fraud service busy\");   // fail fast\n        }\n        try {\n            return http.check(p);\n        } finally {\n            inFlight.release();   // only reached if we got a permit\n        }\n    }\n}",
            "alt": {"lang": "kotlin", "src": "class FraudClient(private val http: FraudHttp) {\n    private val inFlight = Semaphore(50)   // shared by every caller\n\n    fun check(p: Payment): Risk {\n        if (!inFlight.tryAcquire(100, TimeUnit.MILLISECONDS)) {\n            throw RejectedExecutionException(\"fraud service busy\")   // fail fast\n        }\n        try {\n            return http.check(p)\n        } finally {\n            inFlight.release()   // only reached if we got a permit\n        }\n    }\n}"}}
 },
 "recap": [
  "Start virtual threads with `Thread.ofVirtual()`, `Thread.startVirtualThread`, a `factory()`, or, most often, `Executors.newVirtualThreadPerTaskExecutor()`.",
  "The per-task executor creates a new, unbounded virtual thread for every task. Open it in try-with-resources: `close()` waits for every task.",
  "Fork all tasks first, then `get()` them in order. A failure comes back as an `ExecutionException` carrying the real cause.",
  "Never pool virtual threads. A pool caps the whole task, keeps a queue, and leaks `ThreadLocal` state between tasks.",
  "Limit a scarce resource with one shared `Semaphore`: `acquire()` before the `try`, `release()` in `finally`, and only around the call that needs it.",
  "Little's law sizes the limit: permits / call time = maximum calls per second. Use `tryAcquire` with a timeout to shed load instead of queueing forever."
 ],
 "quiz": [
  {"q": "10,000 concurrent requests each call a fraud API that allows 50 concurrent calls. Which design is right?",
   "options": ["`newFixedThreadPool(50)` of platform threads for all request handling", "`newFixedThreadPool(50, Thread.ofVirtual().factory())`", "A virtual thread per request, and one shared `Semaphore(50)` around the fraud call", "A virtual thread per request, and a `new Semaphore(50)` created inside each request handler"], "answer": 2,
   "why": "The limit belongs to the fraud API, so put one semaphore on the client and share it. Both pools limit all request handling, not just the fraud call. A semaphore created per request gives every request its own 50 permits, which limits nothing at all."},
  {"q": "What does this print?\n\n```java\ntry (var perTask = Executors.newVirtualThreadPerTaskExecutor()) {\n    for (int i = 0; i < 3; i++)\n        perTask.submit(() -> System.out.println(Thread.currentThread().getName().isEmpty()));\n}\nSystem.out.println(\"done\");\n```",
   "options": ["`true` three times, then `done`", "`done` first, then `true` three times", "`false` three times, then `done`, because each thread is named `pool-1-thread-N`", "Nothing: the tasks are cancelled when the block ends"], "answer": 0,
   "why": "Virtual threads have no name by default, so `getName()` is empty. `close()` at the end of the try block waits for all three tasks before `done` runs. The `pool-1-thread-N` names belong to the platform threads of `newFixedThreadPool`."},
  {"q": "A `Semaphore(20)` guards a 50 ms call. 1,000 virtual threads reach `acquire()` at the same moment. About how long until the last one gets a permit?",
   "options": ["About 50 ms", "About 2.5 s", "About 50 s", "Never: 980 threads fail with an exception"], "answer": 1,
   "why": "Twenty permits on a 50 ms call serve 400 calls per second, so 1,000 calls need about 2.5 s, and the last thread waits for nearly all of it. Nothing fails: `acquire()` waits as long as it takes. Use `tryAcquire` with a timeout if that wait is too long."},
  {"q": "You submit 1 million tasks to `Executors.newVirtualThreadPerTaskExecutor()`. How many threads can it create?",
   "options": ["As many as there are cores", "256, the scheduler's maximum", "A pool the JVM sizes from the workload", "Up to 1 million: one new virtual thread per task, with no limit"], "answer": 3,
   "why": "The Javadoc says the number of threads it creates is unbounded. The core count and the 256 cap describe carrier threads, which run the virtual threads. They don't limit how many virtual threads exist."},
  {"q": "From the lesson \"Synchronizers: latch, barrier, semaphore, phaser\": a developer writes `try { sem.acquire(); call(); } finally { sem.release(); }`. A thread is interrupted while it waits inside `acquire()`. What happens to the semaphore?",
   "options": ["Nothing: `release()` ignores threads that hold no permit", "`acquire()` retries automatically after the interrupt", "It gains a permit it never handed out, so the limit quietly grows by one", "`release()` throws `IllegalMonitorStateException`"], "answer": 2,
   "why": "A `Semaphore` doesn't track who holds permits. `release()` always adds one, even from a thread that never acquired. Every interrupted waiter raises the limit by one. Put `acquire()` before the `try` so `finally` only runs after a permit was really taken.", "from": "conc-10"}
 ],
 "flashcards": [
  {"front": "Which executor gives every task its own new virtual thread?", "back": "`Executors.newVirtualThreadPerTaskExecutor()`. It has no pool, no queue and no limit."},
  {"front": "What does `close()` on an `ExecutorService` do (JDK 19+)?", "back": "It calls `shutdown()` and then waits until every submitted task has finished."},
  {"front": "Should you pool virtual threads?", "back": "No. Create one per task, and limit the scarce resource with a shared `Semaphore`."},
  {"front": "Where does the `Semaphore` for a downstream API belong?", "back": "One per resource, shared by all callers, for example a field on the API client. One per request limits nothing."},
  {"front": "`Semaphore(20)` guards a call that takes 100 ms. Maximum calls per second?", "back": "200 (20 / 0.1 s)."},
  {"front": "Why put `acquire()` before the `try` and `release()` in `finally`?", "back": "So a thread that fails to acquire never releases a permit it didn't get, and a thread whose call throws always gives its permit back."},
  {"front": "How do you make a semaphore wait fail fast?", "back": "`tryAcquire(timeout, unit)` returns `false` if no permit arrives in time, so you can reject the request."}
 ],
 "terms": [
  {"term": "Thread.Builder", "plain": "The JDK 21 API for creating threads: `Thread.ofVirtual()` and `Thread.ofPlatform()`."},
  {"term": "Thread-per-task executor", "plain": "An executor that starts a new thread for every task and never reuses one."},
  {"term": "Fan-out", "plain": "Starting many calls at once and then collecting all their results."},
  {"term": "Semaphore", "plain": "A counter of permits. `acquire` takes one or waits, `release` gives one back."},
  {"term": "Bulkhead", "plain": "A limit on how many calls may be inside one downstream at once, so one slow dependency can't use up everything."},
  {"term": "Load shedding", "plain": "Rejecting work quickly when you're over capacity, instead of letting it queue."}
 ],
 "explain_back": {
  "prompt": "A teammate proposes `Executors.newFixedThreadPool(20, Thread.ofVirtual().factory())` for a batch job \"to protect the database, which has 20 connections\". Explain why you'd do it differently, and what you'd write instead.",
  "answer": "A pool of 20 caps the whole task, not just the database call. Each payout also does lookups and HTTP calls that don't touch the database, and all of that would wait for one of the 20 pool slots too, so the batch runs far slower than it needs to. It also reuses threads, so anything left in a `ThreadLocal` leaks into the next task. I'd use `newVirtualThreadPerTaskExecutor()` in a try-with-resources block, one virtual thread per payout, and one shared `Semaphore(20)` that the database code acquires right around its query, with `release()` in `finally`. The database still never sees more than 20 queries, and everything else overlaps freely. Little's law tells us the database stage caps throughput at 20 divided by the query time."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Concurrency limits and rate limits are different things.** A semaphore limits how many calls are in flight. Many APIs instead publish a rate, such as 300 requests per second. Little's law connects the two only if the latency is stable: 20 in flight at 100 ms is 200 per second, but if the API slows to 400 ms, the same 20 permits give 50 per second, while a rate limiter would happily let 300 per second through and pile them up inside the API. If the contract is a rate, use a rate limiter. If it's connections or concurrent calls, use a semaphore. Some teams use both.\n\n**Fair or not.** `new Semaphore(20)` is non-fair: a thread that calls `acquire()` just as a permit is released can take it ahead of threads that have waited longer. That gives better throughput. `new Semaphore(20, true)` hands permits out in arrival order, which keeps the worst-case wait lower. For a payment API, where a few very slow requests hurt more than a little lost throughput, fair is often the better default.\n\n**Very many waiters.** Thousands of virtual threads parked on one semaphore are fine. Each `release()` wakes one waiter, and each waiter costs a parked virtual thread. With hundreds of thousands of waiters, the bigger problem is latency: the last waiter waits for everyone ahead of it. A bounded wait with `tryAcquire` keeps that under control and turns overload into fast, honest errors.\n\n**Structured fan-out.** The try-with-resources block guarantees that every thread the method started has finished when it returns. What it doesn't do is stop the other tasks when one fails. Lesson 5 of this track builds that behavior with plain executors, and then shows the JDK's own API for it."
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
