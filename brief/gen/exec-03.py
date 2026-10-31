import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/executors/src"
P = "java/workbench/executors/l03"
read = lambda p: (ROOT / p).read_text()
KP = "kotlin/workbench/executors/l03"
def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l03.{name}",
            "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{KP}/{name}.kt"),
                    "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l03.{name}Kt",
                    "file": f"{lab}/demo/{KP}/{name}.kt"}}

SVG = (
    '<svg viewBox="0 0 640 220" role="img" aria-label="Little\'s law: 400 requests per second arrive, each stays 250 ms, so 100 are inside on average">'
    '<text class="t t-code" x="105" y="92" text-anchor="middle">λ = 400 / s</text>'
    '<line class="ln-a" x1="30" y1="108" x2="196" y2="108" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="105" y="130" text-anchor="middle">arrivals</text>'
    '<rect class="box-a" x="200" y="45" width="240" height="120" rx="8"/>'
    '<text class="t" x="320" y="80" text-anchor="middle">in the system</text>'
    '<text class="t t-code" x="320" y="110" text-anchor="middle">L = λ × W</text>'
    '<text class="t-s t-code" x="320" y="138" text-anchor="middle">= 400 × 0.25 s = 100</text>'
    '<line class="ln-a" x1="440" y1="108" x2="606" y2="108" marker-end="url(#arr)"/>'
    '<text class="t t-code" x="525" y="92" text-anchor="middle">400 / s</text>'
    '<text class="t-s t-m" x="525" y="130" text-anchor="middle">completions</text>'
    '<line class="ln-d" x1="200" y1="185" x2="440" y2="185"/>'
    '<text class="t-s t-m" x="320" y="205" text-anchor="middle">W = 250 ms from arrival to completion</text>'
    '</svg>'
)

L = {
 "id": "exec-03",
 "title": "Sizing a pool: CPU-bound, IO-bound and Little's law",
 "minutes": 35,
 "goal": "By the end you can size a pool from measurements: one thread per core for CPU work, Goetz's formula for work that waits, Little's law for traffic, and the smallest downstream limit as the ceiling.",
 "warmup": {
  "q": "Your service gets 400 authorizations a second, and each one takes 250 ms from start to finish, mostly waiting on the card issuer. With one thread per request, about how many threads are busy at any moment?",
  "options": [
   "About 4, one per core",
   "About 100",
   "About 400, one per request each second",
   "About 1,600"
  ],
  "answer": 1,
  "why": "Little's law: requests in flight = arrival rate x time in system = 400 x 0.25 s = 100. Core count only matters for work that computes. Each request is in the system for a quarter of a second, so at any moment about a quarter of one second's arrivals are inside."
 },
 "sections": [
  {
   "h": "CPU-bound work wants about one thread per core",
   "body": "Here is `CpuBoundDemo` on a 4-core machine. The job is 32 SHA-256 tasks with no I/O and no locks, run on pools of different sizes:\n\n```text\navailableProcessors() = 4\n 1 threads:   359 ms\n 2 threads:   171 ms\n 4 threads:    92 ms\n 8 threads:    96 ms\n16 threads:    98 ms\n```\n\nDoubling the threads halves the time until the thread count reaches the core count. After that, nothing improves. A core runs one thread at a time, so a fifth thread on four cores only gets CPU by taking it from one of the other four. You pay for context switches and colder caches and get no extra work done.\n\nSo for CPU-bound work, size the pool to `Runtime.getRuntime().availableProcessors()`. Goetz suggests one more than that, so the CPUs stay busy when a thread stalls on a page fault. Either is fine. Fifty threads for hashing is not.\n\nAsk the JVM, not the hardware spec. Inside a container, `availableProcessors()` reports the CPU limit of the container, so a pod with a 2-CPU limit on a 64-core node sees 2. That is the number you want, because it's all the CPU the pod gets. You can override it with `-XX:ActiveProcessorCount=N`.\n\nIn a payment service, CPU-bound work is the minority: signing and verifying, encrypting card data, parsing a large settlement file, scoring a fraud model in-process. Most request handling spends its time waiting, and that needs a different rule.",
   "try": {
    "title": "Find where the curve goes flat",
    "minutes": 3,
    "steps": [
     "Check how many cores your machine has. Predict the pool size after which `CpuBoundDemo` stops getting faster.",
     "Run it with the command below."
    ],
    "code": demo("CpuBoundDemo"),
    "expect": "The time roughly halves from 1 to 2 threads and from 2 to the core count, then stays flat or gets a little worse. If other programs are busy on the machine, or the laptop has slower efficiency cores, the curve flattens earlier: the pool only gets the CPU nobody else is using."
   }
  },
  {
   "h": "Work that waits: N × U × (1 + W/C)",
   "body": "Most backend tasks compute briefly and then wait: for the database, the card issuer, a Kafka acknowledgement. A waiting thread uses no CPU, so while it waits, another thread can use the core. That is why pools for I/O work need more threads than cores. Goetz's formula from *Java Concurrency in Practice* says how many:\n\n```text\nthreads = cores x target CPU utilization x (1 + wait time / compute time)\n```\n\nTake 8 cores, a target of 80 percent CPU, and an authorization that computes for 20 ms (parsing, validation, signing) and then waits 180 ms for the issuer: 8 x 0.8 x (1 + 180/20) = 64 threads. The ratio is what matters. A task that waits nine times longer than it computes leaves room for about ten such tasks per core.\n\nThe formula is a starting point, and it can mislead you in three ways.\n\nFirst, you have to measure W and C. A timer around the downstream call gives you W, and the rest of the task's time is roughly C. JFR shows the same split. A guess like \"it's mostly I/O\" gives a number that looks precise and isn't.\n\nSecond, it assumes waiting is free. Waiting on a remote call is. Waiting for a lock, or for a connection that every other thread also needs, is not: more threads just make a longer line for the same lock.\n\nThird, it sizes for CPU and knows nothing else. It can't tell that the issuer accepts only 50 concurrent connections from you, or that your database pool has 20. Those limits often decide the answer, and the last section of this lesson is about them.",
   "try": {
    "title": "Size two pools by hand",
    "minutes": 3,
    "steps": [
     "A refund service runs on 4 cores, targets 50 percent CPU, and each refund computes for 5 ms and waits 95 ms on the ledger. Work out the pool size.",
     "A report job on the same box computes for 40 ms and waits 10 ms per row. Work out its pool size too, then check both with `PoolSizing.ioBound` once you've done the lab."
    ],
    "expect": "Refunds: 4 x 0.5 x (1 + 95/5) = 40 threads. Reports: 4 x 0.5 x (1 + 10/40) = 2.5, rounded up to 3. The report job is mostly CPU, so it gets about as many threads as the cores you're willing to give it."
   }
  },
  {
   "h": "Little's law: in flight = arrival rate × time in system",
   "body": "Goetz's formula starts from CPUs. Little's law starts from traffic. It holds for any stable system, a supermarket or a thread pool:\n\n```text\nL = λ x W\n```\n\nL is the average number of requests inside, λ (lambda) is the arrival rate and W is the average time each request spends inside. Your payment API gets 400 authorizations a second at peak, and each takes 250 ms end to end, so 400 x 0.25 = 100 requests are in flight on average. With one thread per request, that is 100 busy threads. If you have fewer, the extra requests wait somewhere.\n\nTurn it around to see what a pool can do. Solve for λ: 50 threads at 250 ms each finish at most 50 / 0.25 = 200 requests a second. If 400 arrive, 200 a second pile up in the queue. The waiting adds to W, so the queue grows without limit until memory or patience runs out. That is the unbounded-queue story from lesson 2 of this track, with numbers.\n\n`LittlesLawDemo` checks the law with 200 requests that each wait 50 ms:\n\n```text\n 5 threads:   97 req/s measured,  100 predicted by threads / W\n10 threads:  191 req/s measured,  200 predicted by threads / W\n20 threads:  376 req/s measured,  400 predicted by threads / W\n```\n\nWhen the work is waiting, throughput is threads divided by latency. Faster CPUs would not help. More threads would, for as long as threads are the scarce thing. That argument, made in JEP 444, is why virtual threads exist, and the \"Virtual threads\" track picks it up.",
   "figure": {"svg": SVG, "caption": "Little's law: if 400 requests arrive each second and each stays 250 ms, about 100 are inside at any moment."},
   "try": {
    "title": "Check Little's law",
    "minutes": 3,
    "steps": [
     "Read `LittlesLawDemo`. Predict the throughput for 40 threads before you run it.",
     "Run it with the command below and compare each row with its prediction."
    ],
    "code": demo("LittlesLawDemo"),
    "expect": "5, 10 and 20 threads land within a few percent of 100, 200 and 400 requests a second. 40 threads falls short of 800 (about 630 here), because 200 requests are only five rounds for 40 threads and the pool's start-up time is now a large part of the run."
   }
  },
  {
   "h": "The downstream decides: connection pools and bulkheads",
   "body": "Little's law counts threads, but a request in flight holds other things too. Say every authorization writes to the ledger and holds one of your 20 database connections for 10 ms. The database path then tops out at 20 / 0.01 = 2,000 writes a second, whatever your thread count. Threads beyond that line up for a connection instead of a CPU. Run the demo with `db` and you see it: with only 10 connections, 20 and 40 threads are no faster than 10.\n\nSo size from the scarcest resource backwards: the database pool, the issuer's contract (say 50 concurrent connections per merchant client), a fraud API's rate limit. HikariCP's wiki page on pool sizing makes the same point for databases. It starts from a small formula, connections = (cores x 2) + effective spindle count, and tells you to load-test from there, because more connections than the database can serve make every query slower.\n\nLimits also need isolation. Say authorizations, refunds and balance lookups share one pool of 64 threads, and the issuer slows from 120 ms to 3 s. Little's law fills all 64 threads with stuck issuer calls within seconds. Balance lookups, which never touch the issuer, now time out too.\n\nA **bulkhead** stops that. It is a separate limit per dependency, named after the walls that keep one flooded compartment from sinking a ship. It can be a separate pool per downstream, or a `Semaphore` around the call, which is what you build in the lab. The issuer gets 50 permits. When they are gone, new issuer calls fail fast, and the rest of the service keeps its threads.",
   "try": {
    "title": "Hit the connection ceiling",
    "minutes": 2,
    "steps": [
     "Predict the four rows of `LittlesLawDemo` when every request also needs one of 10 connections.",
     "Run the demo again with `-Pargs=db`."
    ],
    "expect": "5 threads still give about 100 requests a second and 10 threads about 200. 20 and 40 threads also stay near 200: ten connections at 50 ms each allow 10 / 0.05 = 200 a second, and the extra threads just wait in `connections.acquire()`."
   },
   "refs": [
    {"title": "About Pool Sizing (HikariCP wiki)", "url": "https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing", "kind": "read"}
   ]
  }
 ],
 "analogy": "Little's law is a supermarket. If 120 customers walk in every hour and each one spends half an hour inside, there are about 60 people in the shop at any moment. To serve more customers per hour without making anyone shop faster, you need room for more people inside, which for a pool means more threads. The checkouts are the downstream limit: add aisles all you like, and if there are four tills, people queue at the tills. The analogy breaks at the door. Shoppers who see a packed shop walk away. An unbounded queue in front of a pool never turns anyone away, so it fills up instead.",
 "in_your_world": "Write down the three numbers for your busiest path before you touch a pool setting: peak arrivals per second, average time per request, and the smallest limit it passes through. For card authorizations that is usually the issuer connection limit or the database pool, not CPU. Check what your Quarkus worker pool is set to (`quarkus.thread-pool.max-threads`) and what your datasource allows, and make sure the second is not far smaller than the first, or the extra worker threads only queue for connections. Temporal workers have a maximum number of concurrent activity executions. That is a pool size by another name, and the same arithmetic applies: activities per second times average duration. Put issuer calls behind their own bulkhead, so a slow issuer costs you authorizations and nothing else.",
 "mistake": "Raising the thread count when the bottleneck is downstream. Authorizations slow down, someone doubles the pool from 64 to 128 threads, and latency gets worse: the database pool still has 20 connections, so 108 threads now queue for them, each holding a request in memory. It happens because thread count is the knob that's easy to turn. Look at the scarce resource first (Hikari's pending-connections metric, the issuer's error rate), size the pool to that limit, and put a bulkhead in front of the slow dependency.",
 "compare": {
  "title": "A bulkhead in Java and with coroutines",
  "java": {"title": "Bulkhead.java (solution, core of call)", "src": "public <T> T call(Callable<T> work) throws Exception {\n    // a waiting caller blocks its platform thread here\n    if (!permits.tryAcquire(maxWait.toNanos(), TimeUnit.NANOSECONDS)) {\n        throw new BulkheadFullException(\"bulkhead '\" + name + \"' is full\");\n    }\n    try {\n        return work.call();\n    } finally {\n        permits.release();\n    }\n}"},
  "kotlin": {"title": "Bulkhead.kt (kotlinx.coroutines)", "src": "import kotlinx.coroutines.sync.Semaphore\nimport kotlinx.coroutines.sync.withPermit\n\nclass Bulkhead(private val name: String, maxConcurrent: Int) {\n    private val permits = Semaphore(maxConcurrent)\n\n    // fail fast, like Duration.ZERO in the Java version\n    suspend fun <T> tryCall(work: suspend () -> T): T {\n        if (!permits.tryAcquire()) throw BulkheadFullException(\"bulkhead '$name' is full\")\n        try {\n            return work()\n        } finally {\n            permits.release()\n        }\n    }\n\n    // wait for a permit: the coroutine suspends and holds no thread while it waits\n    suspend fun <T> call(work: suspend () -> T): T = permits.withPermit { work() }\n}"},
  "note": "Both protect the issuer the same way: at most N calls in flight. The difference is what waiting costs. The Java version blocks a platform thread in `tryAcquire`, so a thousand waiting callers are a thousand parked threads, which is why it needs a short `maxWait`. The coroutine `Semaphore` suspends, so a thousand waiting callers are a thousand small objects. kotlinx's `Semaphore` has no timed acquire; wrap the waiting call in `withTimeout` if you need a deadline."
 },
 "worked": {
  "title": "Size the authorization pool from measurements",
  "steps": [
   {"say": "Measure first. Under a load test at the expected peak, the authorization path shows these numbers. Before reading on, estimate the pool size.",
    "code": "peak arrivals        400 / s\nCPU per request      10 ms   (parse, validate, sign)\nwait per request     140 ms  (issuer call)\ncores                8\nissuer contract      50 concurrent connections", "lang": "text"},
   {"say": "Little's law gives the concurrency the traffic needs: L = 400 x (0.010 + 0.140) = 400 x 0.15 = 60 requests in flight, so 60 threads if each request holds a thread for its whole life.",
    "code": "", "lang": ""},
   {"say": "Check the CPU. 400 requests x 10 ms = 4 CPU-seconds every second, so 4 of the 8 cores are busy: 50 percent. Goetz's formula at that utilization agrees: 8 x 0.5 x (1 + 140/10) = 60. The box can carry the load.",
    "code": "", "lang": ""},
   {"say": "Now the downstream. The issuer allows 50 concurrent connections, and each call holds one for 140 ms, so the issuer path tops out at 50 / 0.14 = 357 authorizations a second. That is below the 400 peak. A pool of 60 would leave 10 threads queued on the issuer's connections.",
    "code": "", "lang": ""},
   {"say": "So the real answer is: put issuer calls behind a bulkhead of 50, size the pool near 60 so the non-issuer work keeps moving, and treat 357 a second as the service's real capacity. Getting to 400 is now a business question (a bigger contract with the issuer, or a second merchant client), not a pool setting.",
    "code": "Bulkhead issuer = new Bulkhead(\"issuer\", 50, Duration.ofMillis(100));\nExecutorService auth = Executors.newFixedThreadPool(60);", "lang": "java",
    "alt_code": "val issuer = Bulkhead(\"issuer\", 50, Duration.ofMillis(100))\nval auth = Executors.newFixedThreadPool(60)", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Pool arithmetic and a bulkhead",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/PoolSizing.java", f"{lab}/main/{P}/Bulkhead.java"],
  "run": "./gradlew :executors:test --tests 'workbench.executors.l03.*'",
  "steps": [
   "Run the tests. All nine fail.",
   "Write the four `PoolSizing` methods. Each is one or two lines. Convert durations with `d.toNanos() / 1e9` to get seconds as a `double`.",
   "Write `Bulkhead.call`: `tryAcquire` with the max wait, throw `BulkheadFullException` if that fails, otherwise run the work and release the permit in a `finally`.",
   "Run the tests until all nine pass."
  ],
  "hints": [
   "One test expects `ioBound(3, 0.5, 10 ms, 30 ms)` to be 2. In floating point, 3 x 0.5 x (1 + 10/30) comes out as 2.0000000000000004, and `Math.ceil` turns that into 3. Subtract a tiny amount (say 1e-9) before rounding up.",
   "`Semaphore.tryAcquire(long timeout, TimeUnit unit)` with a zero timeout returns at once. It throws `InterruptedException`, which `call` may simply let through.",
   "Don't wrap the work's exception. The test checks it gets the very same `IOException` back."
  ],
  "done_when": "All nine tests in `SizingTest` pass."
 },
 "drill": {
  "title": "Both laws from memory",
  "minutes": 4,
  "prompt": "Close this page. Write Goetz's formula and Little's law. Then answer: (a) balance lookups arrive at 1,200 a second and take 40 ms; how many are in flight? (b) the lookup pool has 32 threads; what is its maximum throughput? (c) each lookup holds one of 20 database connections for 25 ms; what is the database path's limit?",
  "answer": {"lang": "text", "src": "threads = cores x utilization x (1 + W/C)\nL = lambda x W\n\n(a) L = 1,200 x 0.040 = 48 in flight\n(b) lambda = L / W = 32 / 0.040 = 800 per second  (less than 1,200: the pool is too small)\n(c) 20 / 0.025 = 800 per second  (the database caps you at the same rate)\n\nSo 48 threads would not help on their own: raise the connection limit too, or cut the 25 ms."}
 },
 "recap": [
  "CPU-bound pools want about one thread per core, from `availableProcessors()`, which respects container CPU limits.",
  "Pools for work that waits use threads = cores x utilization x (1 + W/C), with W and C measured, not guessed.",
  "Little's law, L = λ x W, gives the concurrency your traffic needs. Turned around, threads / latency is the most a pool can finish per second.",
  "Every request also holds downstream resources. The smallest limit on the path (database pool, issuer connections, rate limit) is the real ceiling.",
  "A bulkhead gives each dependency its own limit, so one slow dependency can't take every thread."
 ],
 "quiz": [
  {
   "q": "A fraud-scoring job is pure CPU and runs on a pod with an 8-CPU limit. Someone raises its pool from 8 to 32 threads. What happens to throughput?",
   "options": [
    "It roughly quadruples",
    "About the same, or a little worse from context switching",
    "It doubles",
    "It deadlocks"
   ],
   "answer": 1,
   "why": "Eight CPUs can run eight threads at a time. The other 24 threads only take turns on the same CPUs. For work that waits, more threads help; for pure computation they don't."
  },
  {
   "q": "A refunds endpoint receives 300 requests a second, and each takes 400 ms. How many requests are in flight on average?",
   "options": [
    "75",
    "750",
    "120",
    "40"
   ],
   "answer": 2,
   "why": "L = λ x W = 300 x 0.4 = 120. Dividing 300 by 4, or multiplying by 2.5, are the tempting slips. Write the units down: requests per second times seconds gives requests."
  },
  {
   "q": "A service runs on 4 cores, aims for full CPU use, and each task computes for 10 ms and then waits 90 ms. What does Goetz's formula give?",
   "options": [
    "40",
    "4",
    "36",
    "400"
   ],
   "answer": 0,
   "why": "4 x 1.0 x (1 + 90/10) = 4 x 10 = 40. The tempting 36 comes from using W/C alone instead of 1 + W/C; the 1 accounts for the time each task spends on the CPU."
  },
  {
   "q": "Authorizations, refunds and balance lookups share one pool of 64 threads. When the card issuer slows down, balance lookups, which never call the issuer, start timing out. What is the best fix?",
   "options": [
    "Double the pool to 128 threads",
    "Switch the pool to an unbounded queue",
    "Use CallerRunsPolicy",
    "Put issuer calls behind their own limit (a bulkhead), so they can't use every thread"
   ],
   "answer": 3,
   "why": "Slow issuer calls fill every shared thread, so unrelated work starves. A bulkhead caps how many threads issuer calls may hold. Doubling the pool only delays the problem: Little's law fills 128 threads as surely as 64 when each call takes 3 s."
  },
  {
   "q": "From \"Inside ThreadPoolExecutor: core, max, queue, rejection\": a pool is `new ThreadPoolExecutor(20, 200, 60, SECONDS, new LinkedBlockingQueue<>())`. Traffic is 400 requests a second at 250 ms each. What happens?",
   "options": [
    "It grows to 200 threads, which is plenty",
    "It stays at 20 threads, finishes at most 80 a second, and the queue grows without limit",
    "It grows to exactly the 100 threads Little's law asks for",
    "It rejects the excess requests"
   ],
   "answer": 1,
   "why": "With an unbounded queue the pool never grows past core, so 20 threads at 250 ms finish 20 / 0.25 = 80 a second. Little's law needs 100 in flight. The other 320 a second pile up in the queue, which never refuses, so nothing is ever rejected either.",
   "from": "exec-02"
  }
 ],
 "flashcards": [
  {"front": "How many threads for a pool doing pure CPU work?", "back": "About one per core: `Runtime.getRuntime().availableProcessors()` (Goetz suggests one more)."},
  {"front": "Goetz's pool-size formula for tasks that wait?", "back": "threads = cores x target utilization x (1 + wait time / compute time)."},
  {"front": "State Little's law.", "back": "L = λ x W: requests in flight = arrival rate x average time in the system."},
  {"front": "50 threads, each request holds a thread for 250 ms. Maximum throughput?", "back": "50 / 0.25 = 200 requests per second."},
  {"front": "Why don't threads beyond the database pool size speed up database-bound requests?", "back": "Each request needs a connection. The extra threads just wait in line for one."},
  {"front": "What is a bulkhead?", "back": "A separate concurrency limit per dependency (its own pool or a Semaphore), so one slow dependency can't take every thread."},
  {"front": "What does `availableProcessors()` return in a pod with a 2-CPU limit?", "back": "2. The JVM reads the container's CPU limit, not the host's core count."}
 ],
 "terms": [
  {"term": "CPU-bound", "plain": "Work limited by computation. More threads than cores don't help."},
  {"term": "I/O-bound", "plain": "Work that mostly waits on the network or disk, so one core can serve many such tasks."},
  {"term": "Little's law", "plain": "Requests in flight equal arrival rate times time spent in the system."},
  {"term": "Throughput", "plain": "Work finished per unit of time, such as requests per second."},
  {"term": "Latency", "plain": "How long one request takes from arrival to completion."},
  {"term": "Bulkhead", "plain": "A per-dependency limit that keeps one slow dependency from using all the threads."},
  {"term": "Wait/compute ratio", "plain": "How long a task waits divided by how long it computes. It decides how many threads one core can feed."}
 ],
 "explain_back": {
  "prompt": "Your manager asks why you can't just set every pool to 500 threads \"to be safe\". Explain, using the core count, Little's law and the database pool.",
  "answer": "Threads only help while threads are the scarce thing. For CPU work the limit is the cores: beyond one thread per core, threads just take turns and add switching costs. For work that waits, Little's law tells us how many requests are in flight: arrival rate times latency. At 400 a second and 250 ms that is 100, so 500 threads would mostly sit idle, each with its own stack. And every request also needs things like a database connection. If the pool has 20 connections, threads beyond what 20 connections can serve just queue for them, holding memory and adding latency. So I size from the measured traffic, check CPU, cap it by the smallest downstream limit, and give slow dependencies their own bulkhead."
 },
 "deeper": {
  "minutes": 8,
  "body": "Why aim for 80 percent CPU and not 100? Queueing theory has a short answer. In the simplest model of a single server with random arrivals (M/M/1), the average time in the system is W = S / (1 - ρ), where S is the service time and ρ is utilization. At 50 percent busy, a request spends 2 x S in the system. At 80 percent, 5 x S. At 90 percent, 10 x S. At 99 percent, 100 x S. Real systems are not M/M/1, but the shape holds: latency grows slowly at first and then very fast as you approach full use. Headroom is what keeps the 99th percentile sane during a burst.\n\nLittle's law has a subtle side that this lesson glossed over. The W in L = λ x W is the measured time in the system, including time spent queuing. If you add threads and requests now queue for a database connection instead of for a thread, W grows and throughput doesn't. That is exactly the debate on the loom-dev list before JEP 444 was finalized: more threads raise the ceiling only while threads are what requests wait for. Once the bottleneck moves downstream, the downstream sets λ.\n\nThe last tool is measurement. Time the queue wait and the run time of each task separately (lesson 9 of this track does this with `beforeExecute` and `afterExecute`). If queue wait dominates, the pool is too small for its traffic. If run time grew, look downstream."
 },
 "sources": [
  {"title": "Java Concurrency in Practice, Goetz et al., section 8.2 (sizing thread pools)", "url": "https://jcip.net/"},
  {"title": "About Pool Sizing (HikariCP wiki)", "url": "https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing"},
  {"title": "JEP 444: Virtual Threads (section on Little's law)", "url": "https://openjdk.org/jeps/444"}
 ]
}
out = ROOT / "content/lessons/exec-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
