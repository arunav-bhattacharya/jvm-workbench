import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/vthreads/src"
P = "java/workbench/vthreads/l01"
K = "kotlin/workbench/vthreads/l01"
read = lambda p: (ROOT / p).read_text()

FIG = (
    '<svg viewBox="0 0 640 236" role="img" aria-label="Timeline of one 200 ms payment authorization: about 5 ms on the CPU and 195 ms blocked waiting for the fraud service, the card issuer and the ledger">'
    '<text class="t" x="40" y="26">One authorization: 200 ms on one thread</text>'
    '<text class="t-s t-m" x="43" y="62" text-anchor="middle">parse</text>'
    '<text class="t-s t-m" x="596" y="62" text-anchor="middle">reply</text>'
    '<rect class="box-a" x="40" y="70" width="6" height="44" rx="3"/>'
    '<rect class="box-dim" x="46" y="70" width="112" height="44" rx="8"/>'
    '<text class="t-s" x="102" y="96" text-anchor="middle">fraud 40 ms</text>'
    '<rect class="box-dim" x="158" y="70" width="336" height="44" rx="8"/>'
    '<text class="t-s" x="326" y="96" text-anchor="middle">card issuer 120 ms</text>'
    '<rect class="box-dim" x="494" y="70" width="98" height="44" rx="8"/>'
    '<text class="t-s" x="543" y="96" text-anchor="middle">ledger 35 ms</text>'
    '<rect class="box-a" x="592" y="70" width="8" height="44" rx="3"/>'
    '<line class="ln" x1="40" y1="128" x2="600" y2="128"/>'
    '<text class="t-s t-m" x="40" y="146" text-anchor="middle">0</text>'
    '<text class="t-s t-m" x="320" y="146" text-anchor="middle">100 ms</text>'
    '<text class="t-s t-m" x="600" y="146" text-anchor="middle">200 ms</text>'
    '<rect class="box-a" x="40" y="164" width="16" height="16" rx="3"/>'
    '<text class="t-s" x="64" y="177">running on a CPU: 5 ms</text>'
    '<rect class="box-dim" x="260" y="164" width="16" height="16" rx="3"/>'
    '<text class="t-s" x="284" y="177">blocked, still holding its thread: 195 ms</text>'
    '<text class="t-s t-a" x="320" y="220" text-anchor="middle">200 threads / 0.2 s per request = at most 1,000 requests per second</text>'
    '</svg>'
)

L = {
 "id": "vt-01",
 "title": "The thread-per-request wall",
 "minutes": 35,
 "goal": "By the end you can use Little's law to say how many threads a blocking service needs, explain why platform threads cap its throughput, and say what virtual threads change and what they don't.",
 "warmup": {
  "q": "A payments API runs on a pool of 200 worker threads. Each authorization takes 200 ms, almost all of it waiting on the card issuer. Traffic rises from 800 to 1,500 requests per second. What happens?",
  "options": [
   "CPU climbs to 100% and every request gets a little slower",
   "Throughput stops near 1,000 requests per second and latency keeps growing, while CPU stays low",
   "The pool starts more threads to absorb the extra load",
   "Nothing: 200 threads can handle any rate as long as requests are short"
  ],
  "answer": 1,
  "why": "Each request holds a thread for 200 ms, so one thread finishes 5 requests per second and 200 threads finish 1,000. The other 500 requests per second wait in the pool's queue, and the queue grows every second. The CPU is idle most of that time, because the threads are blocked, not computing. A fixed pool never grows on its own."
 },
 "sections": [
  {
   "h": "A platform thread is an OS thread, and you only get thousands",
   "body": "Before JDK 21, every `java.lang.Thread` was a thin wrapper around one operating system thread. The JDK now calls these **platform threads**. The mapping is one to one: `new Thread(r).start()` asks the kernel for a thread, and the kernel schedules it.\n\nThat costs real resources. Each platform thread reserves a stack up front: 1 MB by default on 64-bit Linux (`-Xss`, or `ThreadStackSize` in `java -XX:+PrintFlagsFinal`). The kernel commits the pages lazily, but it still keeps the reservation, guard pages and its own bookkeeping per thread. Starting a thread is a system call. Switching between thousands of runnable threads costs the kernel time and costs you CPU caches.\n\nSo a JVM is comfortable with hundreds of platform threads, and survives a few thousand. Push to tens of thousands and you start fighting ulimits, memory and the scheduler. A million is out of reach.\n\nServers have used one style for decades anyway: **thread-per-request**. Tomcat, the Quarkus worker pool, and every JDBC-based service give each request one thread for its whole life. The code is easy to read. A stack trace tells you the whole story of a request. A debugger steps through it line by line. `ThreadLocal` context such as the logging MDC or the current transaction just works, because the request never changes threads.\n\nThe catch is in the phrase \"whole life\". The thread stays assigned to the request while the request waits for the database, the fraud service and the card issuer. A blocked thread does no work, but nobody else can use it. You run out of threads long before you run out of CPU.",
   "try": {
    "title": "Count what a thread costs",
    "minutes": 4,
    "steps": [
     "Run `ThreadCostDemo` with the command below. It starts 4,000 platform threads that all stay alive until it releases them, then does the same with 100,000 virtual threads.",
     "Before you look at the output, guess which run finishes first: 4,000 platform threads or 25 times as many virtual threads?",
     "Try `-Pargs='5000 1000000'` for a million virtual threads. Leave the platform count at 5,000 or less on a laptop."
    ],
    "code": {"lang": "java", "title": "ThreadCostDemo.java", "src": read(f"{lab}/demo/{P}/ThreadCostDemo.java"),
             "run": "./gradlew :vthreads:demo -Pmain=workbench.vthreads.l01.ThreadCostDemo",
             "file": f"{lab}/demo/{P}/ThreadCostDemo.java",
             "alt": {"lang": "kotlin", "title": "ThreadCostDemo.kt", "src": read(f"{lab}/demo/{K}/ThreadCostDemo.kt"),
                     "run": "./gradlew :vthreads:demo -Pmain=workbench.vthreads.l01.ThreadCostDemoKt",
                     "file": f"{lab}/demo/{K}/ThreadCostDemo.kt"}},
    "expect": "Each platform thread costs tens to hundreds of microseconds to start (one busy run here printed about 900 us per thread). Each virtual thread costs a few microseconds, so 100,000 of them finish sooner than 4,000 platform threads. A million virtual threads take a second or two and some heap. Nothing crashes."
   }
  },
  {
   "h": "Little's law tells you how many threads you need",
   "body": "One formula explains the wall. **Little's law** says that in any stable system:\n\n```text\nL = λ × W\nrequests in flight = arrival rate × time each request spends inside\n```\n\nIt holds for supermarkets, call centers and servers, whatever the details. With thread-per-request, every request in flight holds one thread, so L is also the number of threads you need.\n\nTake a payment authorization. It parses the request (2 ms of CPU), calls the fraud service (40 ms), calls the card issuer (120 ms), writes to the ledger (35 ms) and replies (3 ms). That is 200 ms per request, and only 5 ms of it uses a CPU. The figure below shows the shape.\n\nAt peak the service gets 1,500 authorizations per second:\n\n```text\nL = 1,500/s × 0.2 s = 300 requests in flight = 300 threads\n```\n\nThe worker pool has 200 threads. Turn the formula around to get the most it can serve:\n\n```text\nλ max = L / W = 200 / 0.2 s = 1,000 requests per second\n```\n\nThe other 500 requests per second wait in the pool's queue. The queue grows every second, so latency grows every second, and CPU sits at a few percent. Dashboards show a slow service with idle machines.\n\nNow the issuer has a bad day and its calls take 1,200 ms. W becomes 1.28 s and the same 200 threads cap you at 156 requests per second. A slow dependency shrinks your throughput even though your own code did not change. That is how one slow downstream service takes down a whole thread-per-request fleet.\n\nYou have two ways out. Make W smaller, which you often can't, because the issuer is not yours. Or make L cheaper: hold the request somewhere other than an expensive OS thread while it waits.",
   "figure": {"svg": FIG, "caption": "The thread is busy for 5 ms and blocked for 195 ms, but it belongs to this one request for all 200 ms."},
   "try": {
    "title": "Predict the wall, then hit it",
    "minutes": 5,
    "steps": [
     "`WallDemo` runs 2,000 fake authorizations that each block for 100 ms, first on a fixed pool of 100 threads. Use Little's law to predict the pool's time before you run it.",
     "Run it with the command below. Ignore the virtual thread line for now.",
     "Predict again for a pool of 200, then run with `-Pargs='200 2000 100'`. Then try a 300 ms latency: `-Pargs='100 2000 300'`."
    ],
    "code": {"lang": "java", "title": "WallDemo.java", "src": read(f"{lab}/demo/{P}/WallDemo.java"),
             "run": "./gradlew :vthreads:demo -Pmain=workbench.vthreads.l01.WallDemo",
             "file": f"{lab}/demo/{P}/WallDemo.java",
             "alt": {"lang": "kotlin", "title": "WallDemo.kt", "src": read(f"{lab}/demo/{K}/WallDemo.kt"),
                     "run": "./gradlew :vthreads:demo -Pmain=workbench.vthreads.l01.WallDemoKt",
                     "file": f"{lab}/demo/{K}/WallDemo.kt"}},
    "expect": "100 threads at 100 ms finish at most 1,000 requests per second, so 2,000 requests take about 2 s (one run here: 2,050 ms). 200 threads halve that to about 1 s. Tripling the latency to 300 ms triples the pool's time to about 6 s. The pool's throughput is threads divided by latency, exactly as the formula says."
   },
   "refs": [
    {"title": "JEP 444: Virtual Threads (see the Little's law discussion in its motivation)", "url": "https://openjdk.org/jeps/444", "kind": "read"}
   ]
  },
  {
   "h": "The async workaround, and what it costs",
   "body": "The industry's first answer was to stop holding a thread while waiting. Async code hands the thread back at every wait and continues later on whatever thread is free:\n\n```java\n// blocking: one thread per request, held for all 200 ms\nReceipt authorize(Payment p) {\n    Risk risk = fraud.check(p);              // 40 ms\n    Auth auth = issuer.authorize(p, risk);   // 120 ms\n    return ledger.record(p, auth);           // 35 ms\n}\n\n// async: the thread goes back to the pool at every wait\nCompletableFuture<Receipt> authorizeAsync(Payment p) {\n    return fraud.checkAsync(p)\n        .thenCompose(risk -> issuer.authorizeAsync(p, risk))\n        .thenCompose(auth -> ledger.recordAsync(p, auth));\n}\n```\n\n```kotlin\n// blocking: one thread per request, held for all 200 ms\nfun authorize(p: Payment): Receipt {\n    val risk = fraud.check(p)                // 40 ms\n    val auth = issuer.authorize(p, risk)     // 120 ms\n    return ledger.record(p, auth)            // 35 ms\n}\n\n// async: the thread goes back to the pool at every wait\nfun authorizeAsync(p: Payment): CompletableFuture<Receipt> =\n    fraud.checkAsync(p)\n        .thenCompose { risk -> issuer.authorizeAsync(p, risk) }\n        .thenCompose { auth -> ledger.recordAsync(p, auth) }\n```\n\n`CompletableFuture`, Reactor's `Mono` and `Flux`, Vert.x and Quarkus's reactive stack all work this way. A handful of event-loop threads, about one per core, can keep thousands of requests in flight. It works, and it is why reactive stacks became popular.\n\nYou pay for it in the code.\n\nEvery library on the request path must be async too. JDBC is blocking, so you need a reactive driver. One blocking call on an event-loop thread stalls every request that shares that loop, and nothing warns you.\n\nThe call stack stops meaning anything. When `issuer.authorizeAsync` fails, the stack trace shows pool worker frames and lambda names, not `authorize` calling `issuer.authorize`. A debugger can't step from one stage to the next. A profiler shows time in the event loop.\n\nControl flow turns into operators. A `try/catch` becomes `exceptionally` or `onErrorResume`. A loop with an early exit becomes a recursive chain. `ThreadLocal` context (the MDC, the security context, the transaction) does not follow the request from thread to thread, so you need a context propagation library.\n\nKotlin coroutines get closest to the blocking style: a `suspend` function reads top to bottom. They still need suspend-aware libraries, though. A blocking JDBC call inside a coroutine blocks a real thread, and you are back to pool sizing with `Dispatchers.IO`.\n\nIf your code is already reactive and works, keep it. Most payment services are plain blocking code on a pool, and rewriting them as async chains to save threads is a poor trade."
  },
  {
   "h": "Virtual threads: cheap threads, same blocking code",
   "body": "JDK 21 took the other way out: make threads cheap. **Virtual threads** became a final feature in JDK 21 (JEP 444). A virtual thread is a normal `java.lang.Thread`, but the JDK schedules it, not the OS. It runs on a small pool of platform threads, about one per core. When it blocks on a socket read, a sleep or a lock, the JDK parks it, saves its stack on the heap, and lets another virtual thread use that platform thread. Lesson 2 of this track shows how.\n\nA virtual thread starts in a few microseconds and needs a small heap object that grows with its stack. A million of them fit on a laptop. So you keep the blocking `authorize` method and give every request its own virtual thread:\n\n```java\ntry (ExecutorService perRequest = Executors.newVirtualThreadPerTaskExecutor()) {\n    for (Payment p : incoming) {\n        perRequest.submit(() -> authorize(p));   // blocking code, cheap thread\n    }\n}   // close() waits for every task\n```\n\n```kotlin\nExecutors.newVirtualThreadPerTaskExecutor().use { perRequest ->\n    for (p in incoming) {\n        perRequest.submit(Callable { authorize(p) })   // blocking code, cheap thread\n    }\n}   // use {} closes the executor, and close() waits for every task\n```\n\nLittle's law still holds. At 1,500 requests per second and 200 ms you still have 300 requests in flight. They just don't cost 300 OS threads anymore. If the issuer slows to 1.2 s, you have 1,920 in flight, and that is fine too.\n\nBe clear about what virtual threads do not change:\n\n- One request is not faster. It still waits 200 ms. Virtual threads give you scale (more requests in flight), not speed.\n- CPU-bound work gains nothing. With 8 cores, at most 8 virtual threads compute at once.\n- Downstream limits stay. Your ledger database pool still has 20 connections. With the thread cap gone, 300 requests reach that pool at once, and the bottleneck moves there. Lessons 3 and 6 of this track deal with it.\n\nThe lab makes the wall measurable: the same blocking handler on a fixed pool and on one virtual thread per task.",
   "try": {
    "title": "Run the same wall on virtual threads",
    "minutes": 3,
    "steps": [
     "Run `WallDemo` again and look at the second line this time.",
     "Run `-Pargs='100 2000 300'`. Predict first: does the virtual thread time triple like the pool's did?",
     "Run `-Pargs='100 5000 100'`. Predict both lines before you look."
    ],
    "expect": "The virtual line finishes 2,000 requests in a little over 100 ms (one run here: 165 ms), because all 2,000 sleep at the same time. With 300 ms latency it takes a little over 300 ms: the time follows the latency of one request, not the number of requests. With 5,000 requests the pool needs about 5 s and the virtual run still takes well under a second."
   }
  }
 ],
 "analogy": "Picture a restaurant where each waiter is assigned to one table from the moment guests sit down until they pay. While the kitchen cooks, the waiter stands at the table and does nothing. With 20 waiters you serve 20 tables at once, however many seats are empty, and guests queue at the door. Async code is one waiter running between many tables with a notepad of what each table needs next. It works, but the notepad gets complicated. Virtual threads give every table its own waiter, and waiters cost almost nothing to hire. The analogy breaks in one place: the kitchen is still the kitchen. If the slow part is the cooking itself (CPU work) or a pantry with room for only 20 cooks (a connection pool), more waiters don't help.",
 "in_your_world": "Your Quarkus REST endpoints run on a worker pool with a fixed maximum size (`quarkus.thread-pool.max-threads`), and Little's law decides when it fills up. A card issuer that slows from 120 ms to 1.2 s during an incident cuts that pool's throughput by about ten times, even though your code didn't change. The same math applies to a Kafka consumer that calls a fraud API per record, and to Temporal activity workers, which run each activity on a thread from a fixed number of slots. When you see latency climbing with CPU at 5%, compute L = λ × W before you add pods.",
 "mistake": "The most common mistake is reading \"slow and idle\" as a CPU or code problem. Latency climbs, throughput flattens, CPU is at 5%, so the team adds pods or raises the pool to 2,000 threads. More threads does lift the cap for a while, but each one reserves 1 MB of stack and adds scheduling work, and the extra requests often just pile up on the database pool instead. Do the arithmetic first: measure W, compute L = λ × W for the peak rate, and compare L with your thread pool and with every pool behind it. Then fix the resource that is actually full.",
 "compare": {
  "title": "Blocking code that scales: virtual threads vs coroutines",
  "java": {"title": "Java 21+: virtual threads", "src": "// plain blocking code, one cheap virtual thread per payment\nList<Receipt> authorizeAll(List<Payment> batch) throws Exception {\n    try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {\n        List<Future<Receipt>> futures = new ArrayList<>();\n        for (Payment p : batch) futures.add(perTask.submit(() -> authorize(p)));\n        List<Receipt> receipts = new ArrayList<>();\n        for (Future<Receipt> f : futures) receipts.add(f.get());\n        return receipts;\n    }\n}\n\nReceipt authorize(Payment p) {\n    Risk risk = fraud.check(p);              // ordinary blocking HTTP call\n    Auth auth = issuer.authorize(p, risk);\n    return ledger.record(p, auth);           // ordinary JDBC\n}"},
  "kotlin": {"title": "Kotlin: kotlinx.coroutines", "src": "// suspend functions: the compiler turns them into state machines\nsuspend fun authorizeAll(batch: List<Payment>): List<Receipt> = coroutineScope {\n    batch.map { p -> async { authorize(p) } }.awaitAll()\n}\n\nsuspend fun authorize(p: Payment): Receipt {\n    val risk = fraud.check(p)                // must itself suspend to free the thread\n    val auth = issuer.authorize(p, risk)\n    return ledger.record(p, auth)            // blocking JDBC here would block a real thread\n}"},
  "note": "Both read top to bottom, and both keep thousands of payments in flight on a few OS threads. The difference is where the magic lives. Kotlin does it in the compiler: only `suspend` functions can give the thread back, so every waiting call on the path has to be suspend-aware, and a blocking JDBC call needs `withContext(Dispatchers.IO)`, which is a thread pool again. Virtual threads do it in the JDK at run time: any blocking JDK call (sockets, `sleep`, locks, `BlockingQueue`) parks the virtual thread, so existing JDBC drivers and HTTP clients work unchanged. You can mix the two: `Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher()` runs coroutines on virtual threads, which helps when they call blocking libraries."
 },
 "worked": {
  "title": "Size the authorization service with Little's law",
  "steps": [
   {"say": "Write down W for one request, stage by stage. Use p50 numbers from your traces for a first pass, and redo it with p99 for the bad day.", "code": "parse        2 ms  (CPU)\nfraud       40 ms  (HTTP, waiting)\nissuer     120 ms  (HTTP, waiting)\nledger      35 ms  (JDBC, waiting)\nreply        3 ms  (CPU)\nW          200 ms", "lang": "text"},
   {"say": "Compute L at the peak rate. This is how many requests are in flight, so it is how many threads thread-per-request needs.", "code": "L = λ × W = 1,500/s × 0.200 s = 300 threads", "lang": "text"},
   {"say": "Compare with the pool you have. 200 threads cap the service at 1,000 requests per second. At 1,500 arriving, the queue grows by 500 every second. After 10 s, 5,000 requests are queued, and a new one waits about 5 s before a thread even picks it up.", "code": "λ max = 200 / 0.200 s = 1,000/s\nqueue growth = 1,500 - 1,000 = 500 per second\nwait after 10 s = 5,000 / 1,000/s = 5 s", "lang": "text"},
   {"say": "Apply the same law to every resource a request holds, not just threads. The ledger stage holds a database connection for 35 ms. With a pool of 20 connections, that stage alone caps you at 571 requests per second. Fixing the thread pool, with more platform threads or with virtual threads, would only move the queue to the connection pool.", "code": "connections needed = 1,500/s × 0.035 s = 53\nλ max (ledger)     = 20 / 0.035 s = 571/s   <- the real bottleneck", "lang": "text"},
   {"say": "Decide. Raise the connection pool only if the database can take 53 concurrent writes. Then make threads cheap with virtual threads, and keep an explicit limit in front of the issuer and the database. Lesson 3 of this track shows that limit."}
  ]
 },
 "lab": {
  "title": "Measure the wall: fixed pool vs a virtual thread per task",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/LittlesLaw.java", f"{lab}/main/{P}/BlockingRunner.java"],
  "run": "./gradlew :vthreads:test --tests 'workbench.vthreads.l01.*'",
  "steps": [
   "Run the tests once. All five fail with `UnsupportedOperationException`.",
   "Write `LittlesLaw.inFlight` (L = λ × W) and `LittlesLaw.maxThroughput` (λ = L / W). Convert the `Duration` to seconds as a `double` first.",
   "Write `BlockingRunner.runOnFixedPool`: open `Executors.newFixedThreadPool(poolSize)` in try-with-resources, `execute` the handler `tasks` times, and count each finished task in an `AtomicInteger`. Return the count after the try block.",
   "Write `runOnVirtualThreads` the same way with `Executors.newVirtualThreadPerTaskExecutor()`.",
   "Run the tests again. The last one takes about 2.5 s: it runs 2,000 tasks of 100 ms on a 100-thread pool, then on virtual threads. Read its assertions to see why the pool can never beat 2 s."
  ],
  "hints": [
   "`close()` on an `ExecutorService` (JDK 19+) calls `shutdown()` and then waits for every task. That is why the try-with-resources block makes your method wait.",
   "Count with an `AtomicInteger`, not an `int`: the tasks finish on many threads at once. The lesson \"Race conditions: why count++ lies\" shows what `count++` does there.",
   "`Duration.toNanos() / 1_000_000_000.0` gives seconds as a `double` without losing the milliseconds."
  ],
  "done_when": "All five tests in `ThreadPerRequestTest` pass, two runs in a row."
 },
 "drill": {
  "title": "Little's law and the per-task executor, from memory",
  "minutes": 4,
  "prompt": "Close this page. A Kafka consumer service handles 600 records per second, and each record waits 250 ms on a fraud API. (1) How many records are in flight? (2) A pool of 64 threads processes them: what is the most it can handle per second? (3) Write a method that runs a `Runnable` once per record, each on its own virtual thread, and returns when all are done.",
  "answer": {"lang": "java", "src": "// (1) L = 600/s × 0.25 s = 150 in flight\n// (2) λ max = 64 / 0.25 s = 256 records per second, far below 600\n// (3)\nstatic void runAll(List<Runnable> perRecord) {\n    try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {\n        for (Runnable r : perRecord) perTask.execute(r);\n    }   // close() waits for all of them\n}",
            "alt": {"lang": "kotlin", "src": "// (1) L = 600/s × 0.25 s = 150 in flight\n// (2) λ max = 64 / 0.25 s = 256 records per second, far below 600\n// (3)\nfun runAll(perRecord: List<Runnable>) {\n    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->\n        perRecord.forEach { perTask.execute(it) }\n    }   // close() waits for all of them\n}"}}
 },
 "recap": [
  "A platform thread is one OS thread with a 1 MB stack reserved by default on 64-bit Linux. A JVM handles thousands of them, not millions.",
  "Little's law: requests in flight = arrival rate × latency. With thread-per-request, that is also the number of threads you need.",
  "A blocking service is capped at threads / latency requests per second. A slow dependency lowers that cap while CPU stays idle.",
  "Async and reactive code free the thread while waiting, at the price of async-only libraries, broken stack traces and lost `ThreadLocal` context.",
  "Virtual threads (final in JDK 21, JEP 444) make threads cheap, so plain blocking code can keep thousands of requests in flight.",
  "They give scale, not speed: one request is no faster, CPU-bound work gains nothing, and downstream pools become the new limit."
 ],
 "quiz": [
  {"q": "A service receives 3,000 requests per second and each one takes 50 ms. How many requests are in flight on average?",
   "options": ["60", "150", "600", "3,000"], "answer": 1,
   "why": "L = λ × W = 3,000/s × 0.05 s = 150. Dividing instead of multiplying gives 60, a common slip. The 3,000 figure is a rate per second, not a count of requests in flight at one moment."},
  {"q": "A 200-thread pool serves 1,000 requests per second at 200 ms each. The card issuer slows down and each request now takes 2 s. CPU drops to 3%. What is the most the service can finish per second now?",
   "options": ["Still 1,000, since the CPU is idle", "500", "100", "20"], "answer": 2,
   "why": "λ max = threads / W = 200 / 2 s = 100 requests per second. Idle CPU doesn't help: the limit is threads held while waiting, not computation. That is why one slow dependency can take down a thread-per-request service."},
  {"q": "You move a blocking handler from a 200-thread pool to one virtual thread per request. At low traffic, how does one request's latency change? It spends 120 ms waiting on the issuer.",
   "options": ["About the same: it still waits 120 ms for the issuer", "It drops to a few milliseconds, because virtual threads don't really block", "It halves, because virtual threads switch faster", "It doubles, because of the scheduling overhead"], "answer": 0,
   "why": "Virtual threads give scale, not speed. The request still waits for the issuer. What changes is how many requests can wait at once without running out of threads, so at high traffic the queueing delay disappears."},
  {"q": "Which workload gains the most from virtual threads?",
   "options": ["A batch job that computes HMACs over 50 million ledger rows on 8 cores", "A low-traffic admin API that serves 5 requests per second", "A report that is slow because one SQL query takes 30 s", "A payments API that waits on HTTP and database calls for 190 ms of every 200 ms request"], "answer": 3,
   "why": "Virtual threads help when many tasks are in flight and most of their time is spent blocked. The HMAC batch job is CPU-bound, so 8 cores is the limit either way. The admin API never runs out of threads. The slow query is one request that is still slow on any thread."},
  {"q": "From the executors track: `Executors.newFixedThreadPool(200)` receives 1,500 tasks per second that each block for 200 ms. What happens to the tasks it can't start right away?",
   "options": ["They are rejected with RejectedExecutionException", "The pool adds threads up to its maximum", "They wait in an unbounded queue, so the queue and the latency keep growing", "They run on the submitting thread"], "answer": 2,
   "why": "`newFixedThreadPool` uses an unbounded `LinkedBlockingQueue`, and core and maximum size are both 200. Nothing is rejected and no thread is added. Tasks queue without limit, which is exactly the growing latency Little's law predicts.", "from": "exec-02"}
 ],
 "flashcards": [
  {"front": "State Little's law.", "back": "L = λ × W: the number of requests in flight equals the arrival rate times the time each request spends in the system."},
  {"front": "1,500 requests per second, 200 ms each. How many threads does thread-per-request need?", "back": "300 (1,500 × 0.2)."},
  {"front": "200 threads, each request holds one for 200 ms. What is the maximum throughput?", "back": "1,000 requests per second (200 / 0.2 s). Above that the queue grows, even with idle CPU."},
  {"front": "What is a platform thread?", "back": "A `java.lang.Thread` backed one to one by an OS thread, with its own stack (1 MB reserved by default on 64-bit Linux)."},
  {"front": "Do virtual threads make a single request faster?", "back": "No. They give scale (more requests in flight at once), not speed. Each request waits just as long."},
  {"front": "In which JDK did virtual threads become final, and under which JEP?", "back": "JDK 21, JEP 444."},
  {"front": "What happens when a handler on an event-loop thread makes a blocking JDBC call?", "back": "It blocks the event-loop thread, so every other request on that loop stalls until the call returns."}
 ],
 "terms": [
  {"term": "Platform thread", "plain": "A Java thread that is one OS thread. Expensive, so you get thousands."},
  {"term": "Virtual thread", "plain": "A Java thread scheduled by the JDK on a few OS threads. Cheap, so you can have millions."},
  {"term": "Thread-per-request", "plain": "A server style where each request gets one thread for its whole life."},
  {"term": "Little's law", "plain": "In flight = arrival rate × time inside. L = λ × W."},
  {"term": "Throughput", "plain": "How many requests finish per second."},
  {"term": "Latency", "plain": "How long one request takes from start to end."},
  {"term": "Event loop", "plain": "A thread that runs many requests' callbacks in turn and must never block."}
 ],
 "explain_back": {
  "prompt": "Your manager asks why the payments API tops out at about 1,000 requests per second while CPU sits at 5%. Explain it with Little's law, and say what virtual threads would change and what they would not.",
  "answer": "Each authorization takes about 200 ms, and almost all of that is waiting on the fraud service, the issuer and the ledger. With thread-per-request, a request holds a thread the whole time, so 200 threads can finish at most 200 / 0.2 s = 1,000 requests per second. Above that, requests queue for a thread, so latency climbs, while the CPU has almost nothing to do because the threads are blocked. Virtual threads make threads cheap, so we could keep 300 or 3,000 requests in flight without 3,000 OS threads, and the thread cap goes away. They would not make any single request faster, and the next limit would be the database pool and the issuer's own capacity, so we'd need explicit limits there."
 },
 "deeper": {
  "minutes": 10,
  "body": "Little's law needs only one assumption: the system is stable, meaning requests leave as fast as they arrive over the long run. It says nothing about the shape of the traffic or the order of service, which is why it works for a payments API as well as for a supermarket.\n\nIt does not tell you what happens near the limit. As a pool approaches 100% busy, the queue does not grow smoothly. Short bursts above the average rate make requests wait, and the waits add up faster than the load. A pool that is busy 95% of the time has much longer queues than one at 80%, even though it is only a little busier. That is why capacity planning leaves headroom.\n\nIt also explains why thread-per-request held on for so long. If W is 5 ms (an in-memory lookup), 200 threads give you 40,000 requests per second, and nobody needs async code. The wall only appears when W is dominated by waiting on other systems, which describes most microservices. JEP 444's motivation section makes this exact argument: the number of threads limits throughput long before CPU or network do.\n\nOne honest question remains: why not shrink `-Xss` and run 20,000 platform threads? Some teams did. You still pay a system call per thread start, the kernel still schedules 20,000 threads, and too small a stack turns deep call chains into `StackOverflowError`. A virtual thread's stack lives on the heap and grows only as deep as the code actually goes, so you don't have to guess a size."
 },
 "sources": [
  {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444"},
  {"title": "Virtual Threads (Java SE 21 Core Libraries guide)", "url": "https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html"},
  {"title": "Executors.newVirtualThreadPerTaskExecutor (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Executors.html"},
  {"title": "Thread (Java SE 25 API): platform and virtual threads", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Thread.html"}
 ]
}
out = ROOT / "content/lessons/vt-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
