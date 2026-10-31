import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/vthreads/src"
P = "java/workbench/vthreads/l04"
K = "kotlin/workbench/vthreads/l04"
read = lambda p: (ROOT / p).read_text()


def demo(name, title_java=None):
    """Try-it code for a Java demo plus its Kotlin twin."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": f"./gradlew :vthreads:demo -Pmain=workbench.vthreads.l04.{name}",
            "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": f"./gradlew :vthreads:demo -Pmain=workbench.vthreads.l04.{name}Kt",
                    "file": f"{lab}/demo/{K}/{name}.kt"}}


FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="JDK 21 to 23: all four carrier threads are held by virtual threads pinned while entering a synchronized block. The virtual thread that should take the lock next sits in the ready queue and can never get a carrier.">'
    '<text class="t-s t-m" x="150" y="38" text-anchor="middle">carrier threads (4 cores)</text>'
    '<rect class="box-bad" x="20" y="50" width="260" height="44" rx="8"/>'
    '<text class="t-s" x="150" y="68" text-anchor="middle">worker-1: pinned by VT 31</text>'
    '<text class="t-s t-bad" x="150" y="86" text-anchor="middle">blocked entering synchronized</text>'
    '<rect class="box-bad" x="20" y="102" width="260" height="44" rx="8"/>'
    '<text class="t-s" x="150" y="120" text-anchor="middle">worker-2: pinned by VT 44</text>'
    '<text class="t-s t-bad" x="150" y="138" text-anchor="middle">blocked entering synchronized</text>'
    '<rect class="box-bad" x="20" y="154" width="260" height="44" rx="8"/>'
    '<text class="t-s" x="150" y="172" text-anchor="middle">worker-3: pinned by VT 58</text>'
    '<text class="t-s t-bad" x="150" y="190" text-anchor="middle">blocked entering synchronized</text>'
    '<rect class="box-bad" x="20" y="206" width="260" height="44" rx="8"/>'
    '<text class="t-s" x="150" y="224" text-anchor="middle">worker-4: pinned by VT 63</text>'
    '<text class="t-s t-bad" x="150" y="242" text-anchor="middle">blocked entering synchronized</text>'
    '<text class="t-s t-m" x="530" y="38" text-anchor="middle">ready queue</text>'
    '<rect class="box" x="400" y="50" width="260" height="200" rx="8"/>'
    '<rect class="box-b" x="415" y="78" width="230" height="60" rx="8"/>'
    '<text class="t-s" x="530" y="102" text-anchor="middle">VT 7: next to take the lock</text>'
    '<text class="t-s" x="530" y="122" text-anchor="middle">needs a carrier to run</text>'
    '<rect class="box-dim" x="415" y="160" width="230" height="60" rx="8"/>'
    '<text class="t-s" x="530" y="184" text-anchor="middle">VT 90, 91, ...: new requests</text>'
    '<text class="t-s" x="530" y="204" text-anchor="middle">also waiting for a carrier</text>'
    '<line class="ln-bad" x1="413" y1="108" x2="284" y2="108" marker-end="url(#arr)"/>'
    '<text class="t-s t-bad" x="345" y="98" text-anchor="middle">no free carrier</text>'
    '<text class="t-s t-bad" x="340" y="284" text-anchor="middle">JDK 21 to 23: the carriers wait for the lock, and the lock waits for a carrier</text>'
    '</svg>'
)

L = {
 "id": "vt-04",
 "title": "Pinning, ThreadLocals and other traps",
 "minutes": 35,
 "goal": "By the end you can say what pins a virtual thread on JDK 21 and on JDK 25, find pinning with JFR, and fix the two classic migration traps: a monitor held around I/O and a ThreadLocal used as a cache.",
 "warmup": {
  "q": "On JDK 25, a virtual thread runs `synchronized (cache) { rate = fxApi.fetch(pair); }`, where `fetch` is an 80 ms HTTP call. What happens to its carrier thread during those 80 ms?",
  "options": [
   "It is pinned: the carrier blocks for 80 ms, because `synchronized` always pins a virtual thread",
   "It is free: since JDK 24 the virtual thread unmounts while it waits, even inside `synchronized`",
   "The JVM throws, because blocking inside `synchronized` is not allowed on a virtual thread",
   "The JVM converts the virtual thread into a platform thread for the duration of the block"
  ],
  "answer": 1,
  "why": "JDK 24 (JEP 491) changed how monitors work, so a virtual thread can hold a monitor and still unmount. \"synchronized pins\" was true on JDK 21 to 23, and a lot of articles from that time still say it. The lock still serializes the callers, though: only one of them can fetch at a time."
 },
 "sections": [
  {
   "h": "Pinning: when a virtual thread can't let go",
   "body": "A virtual thread is **pinned** when it reaches a blocking call but can't unmount. It stays on its carrier, and the carrier blocks with it. For that time the carrier is a plain platform thread again, and you have one carrier fewer for everybody else.\n\nOn JDK 21 to 23 the most common cause is a monitor. The JVM tracked monitor ownership per OS thread, so a virtual thread holding a `synchronized` lock could not leave its carrier. Here is the shape that hurts, from this lesson's lab:\n\n```java\npublic synchronized BigDecimal rate(String pair) {   // a monitor\n    BigDecimal r = rates.get(pair);\n    if (r == null) {\n        r = ratesService.fetch(pair);   // 100 ms socket read while holding the monitor\n        rates.put(pair, r);\n    }\n    return r;\n}\n```\n\n```kotlin\n@Synchronized                                     // a monitor, exactly like Java's synchronized\nfun rate(pair: String): BigDecimal =\n    rates.getOrPut(pair) { ratesService.fetch(pair) }   // 100 ms socket read while holding the monitor\n```\n\nOn JDK 21 the thread holding the monitor pins its carrier for 100 ms. Every other caller that blocks trying to enter the monitor pins its carrier too. With 4 carriers, 4 waiting callers are enough to stop every virtual thread in the JVM, including requests that never touch the cache.\n\nIt can get worse than slow. In 2024 Netflix described services on Java 21 that stopped answering completely. Every carrier was held by a virtual thread pinned in `synchronized` code, waiting for a lock. The virtual thread that had to run next to move things along was unmounted, waiting for a free carrier, and there never was one. The figure shows the shape.\n\n**JDK 24 fixed this** (JEP 491). Monitors were reworked so that a virtual thread can acquire, hold and release them independently of its carrier. `synchronized` and `Object.wait()` now unmount like `ReentrantLock` does. JDK 25 is the first LTS with the fix.\n\nSo the advice depends on your JDK. On JDK 25, leave working `synchronized` code alone. On JDK 21, replace `synchronized` around blocking calls with a `ReentrantLock`, which has always parked virtual threads properly. That is the first half of the lab.",
   "figure": {"svg": FIG, "caption": "On JDK 21 to 23, pinned virtual threads can hold every carrier while they wait for a lock, and the thread that needs to run next to release them never gets a carrier."},
   "try": {
    "title": "Pin the only carrier",
    "minutes": 4,
    "steps": [
     "Read `PinningDemo`. It runs with one carrier. A ticker wants to tick every 50 ms, while three virtual threads each block for 100 ms: inside `synchronized`, inside a `ReentrantLock`, or inside a class initializer.",
     "Check your JDK with `java -version`. Predict the longest gap between ticks and the number of pinned events for each scenario on that JDK.",
     "Run it. If you have both JDK 21 and JDK 25 installed, run it on both (point `JAVA_HOME` at each)."
    ],
    "code": demo("PinningDemo"),
    "expect": "On JDK 21: `synchronized` leaves a gap of about 300 ms between ticks and 3 pinned events (the three sleepers run one after another on the only carrier, and nothing else runs). `ReentrantLock` keeps the ticker at about 50 ms with 0 events. On JDK 25 `synchronized` behaves like `ReentrantLock`: about 50 ms, 0 events. The class initializer pins on both JDKs: a gap of about 200 ms and 1 event, and on JDK 25 JFR even names the reason (`VM call to ...SlowRatesTable.<clinit> on stack`)."
   },
   "refs": [
    {"title": "JEP 491: Synchronize Virtual Threads without Pinning", "url": "https://openjdk.org/jeps/491", "kind": "read"}
   ]
  },
  {
   "h": "What still pins on JDK 25, and how to see it",
   "body": "JEP 491 removed the big case. Two smaller ones remain:\n\n- **Native frames.** If a virtual thread calls native code (a JNI method, or a downcall through the Foreign Function and Memory API), and that native code calls back into Java code that blocks, the virtual thread is pinned. The JVM can't move native frames to the heap.\n- **Class initializers.** A virtual thread that blocks while running a `static {}` block (or a Kotlin `object`'s `init`) is pinned, because the JVM runs class initialization through its own frames.\n\nThe second one is easy to write by accident:\n\n```java\nclass FeeTable {\n    // runs inside <clinit>: an HTTP call here pins the first virtual thread that touches FeeTable\n    static final Map<String, BigDecimal> FEES = loadFromConfigService();\n}\n```\n\n```kotlin\nobject FeeTable {\n    // runs inside <clinit>: an HTTP call here pins the first virtual thread that touches FeeTable\n    val fees: Map<String, BigDecimal> = loadFromConfigService()\n}\n```\n\nMove slow loading out of static initialization, into an explicit startup step or a lazily filled cache.\n\nFile I/O is a related case that isn't called pinning. A file read blocks inside the OS, so the virtual thread keeps its carrier, and the scheduler adds a temporary carrier to make up for it.\n\nTo find pinning, use **JFR**. The `jdk.VirtualThreadPinned` event is on by default in both built-in settings files, with a 20 ms threshold, and it records the stack of the pinned thread. On JDK 25 it also records the reason, the blocking operation and the carrier.\n\n```bash\njava -XX:StartFlightRecording=filename=pin.jfr,settings=profile -jar payments.jar\njfr print --events jdk.VirtualThreadPinned pin.jfr\n```\n\nIn a running service, `jcmd <pid> JFR.start settings=profile` does the same. To catch shorter pins, add `jdk.VirtualThreadPinned#threshold=5ms` to the `-XX:StartFlightRecording` options.\n\nYou'll find older advice to use `-Djdk.tracePinnedThreads=full`. That property worked on JDK 21 to 23 and was removed in JDK 24. On JDK 25 it is silently ignored, so a clean run with it proves nothing.",
   "try": {
    "title": "Read a pinned event",
    "minutes": 4,
    "steps": [
     "Run `PinningDemo` once through Gradle (previous Try it) so its class is compiled.",
     "From `labs/`, run the class initializer scenario with a JFR recording, then print the pinned events with the commands below.",
     "Find the stack frame that names `SlowRatesTable`. On JDK 25, also read the `pinnedReason` and `carrierThread` fields."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "java -XX:StartFlightRecording=filename=pin.jfr,settings=profile \\\n     -cp vthreads/build/classes/java/demo workbench.vthreads.l04.PinningDemo init\njfr print --events jdk.VirtualThreadPinned pin.jfr", "run": ""},
    "expect": "One `jdk.VirtualThreadPinned` event of about 200 ms. Its stack shows `Thread.sleep` called from the static initializer of `PinningDemo$SlowRatesTable`. On JDK 25 the event also says `blockingOperation = \"LockSupport.park\"`, `pinnedReason = \"VM call to ...SlowRatesTable.<clinit> on stack\"` and which `ForkJoinPool-1-worker` was blocked. On JDK 21 you only get the stack, which is still enough."
   },
   "refs": [
    {"title": "jdk.jfr.Recording (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/jdk.jfr/jdk/jfr/Recording.html", "kind": "docs"}
   ]
  },
  {
   "h": "ThreadLocal caches stop caching",
   "body": "`ThreadLocal` works on virtual threads. Each virtual thread has its own values, exactly like a platform thread. The trap is a `ThreadLocal` used as a cache:\n\n```java\n// SimpleDateFormat isn't thread-safe, so keep one per thread\nstatic final ThreadLocal<SimpleDateFormat> FORMAT =\n        ThreadLocal.withInitial(() -> new SimpleDateFormat(\"yyyy-MM-dd'T'HH:mm:ss.SSS'Z'\"));\n```\n\n```kotlin\n// SimpleDateFormat isn't thread-safe, so keep one per thread\nval FORMAT: ThreadLocal<SimpleDateFormat> =\n    ThreadLocal.withInitial { SimpleDateFormat(\"yyyy-MM-dd'T'HH:mm:ss.SSS'Z'\") }\n```\n\nOn a pool of 200 platform threads this builds 200 formatters, once, and reuses them for millions of requests. With one virtual thread per request, every request is a new thread with an empty map. The \"cache\" builds a formatter, uses it once, and throws it away. A million requests now build a million formatters. Nothing fails. You see it as allocation and GC time.\n\nPer-thread buffers are worse, because they cost memory for as long as the thread lives. A 64 KB `ThreadLocal<byte[]>` scratch buffer was 13 MB on 200 threads. On 100,000 live virtual threads it is 6.4 GB.\n\nThe fixes are ordinary:\n\n- Use an immutable, thread-safe object and share it. `DateTimeFormatter` replaces `SimpleDateFormat`. This is the second half of the lab.\n- If the object is expensive and not thread-safe, use a real cache or pool for that object (a `ConcurrentHashMap`, a small object pool), not one per thread.\n- If it is cheap, just create it where you need it.\n\n`ThreadLocal` for request context (an MDC entry, a tenant id) still works within one virtual thread, but it doesn't flow into threads you start, and it never gets wiped unless you call `remove()`. Scoped values, final in JDK 25, are the cleaner tool for that, and lesson 5 of this track covers them.\n\nTo find thread-local use in a migrated service, run it with `-Djdk.traceVirtualThreadLocals=true`. That is an unsupported diagnostic property, but it exists on JDK 21 and 25, and it prints a stack trace whenever a virtual thread sets a thread local.",
   "try": {
    "title": "Count the formatters",
    "minutes": 3,
    "steps": [
     "Read `ThreadLocalCostDemo`. It formats 100,000 timestamps with a `ThreadLocal<SimpleDateFormat>` on a pool of 8 platform threads, then with one virtual thread per task, then with one shared `DateTimeFormatter`.",
     "Predict the three \"formatters built\" numbers before you run it.",
     "Run it, and compare the times too."
    ],
    "code": demo("ThreadLocalCostDemo"),
    "expect": "8, then 100,000, then 1. The pool built one formatter per thread and reused it. With virtual threads every task built its own and threw it away. The shared `DateTimeFormatter` is also the fastest line (one run here: 958 ms, 1,074 ms and 253 ms), though times swing a lot on a busy machine."
   }
  },
  {
   "h": "CPU-bound work gains nothing",
   "body": "Virtual threads make waiting cheap. They do nothing for computing. There are as many carriers as cores, so at most that many virtual threads compute at once, which is exactly what a fixed pool of that size gives you.\n\nIt is worse than \"no gain\", because there is no time slicing. A virtual thread that signs a large settlement batch for 3 seconds keeps its carrier for 3 seconds. Put four of those on a 4-core pod, and every HTTP request handled on virtual threads waits until one of them finishes, even requests that only need a millisecond of CPU.\n\nKeep heavy CPU work on a bounded pool of platform threads, and let the virtual thread wait for it:\n\n```java\nprivate final ExecutorService cpu = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());\n\nReceipt settle(Batch b) throws Exception {\n    Signature sig = cpu.submit(() -> signer.sign(b)).get();   // heavy CPU on a bounded platform pool\n    return ledger.record(b, sig);                              // blocking I/O stays on the virtual thread\n}\n```\n\n```kotlin\nprivate val cpu = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors())\n\nfun settle(b: Batch): Receipt {\n    val sig = cpu.submit(Callable { signer.sign(b) }).get()   // heavy CPU on a bounded platform pool\n    return ledger.record(b, sig)                              // blocking I/O stays on the virtual thread\n}\n```\n\nThe virtual thread parks in `get()`, so it holds no carrier while the signing runs. The CPU pool keeps the heavy work to its own threads, and the OS time-slices those threads against the carriers, so request handling keeps moving.\n\nThe line is fuzzy for work that is a little of both. Parsing a 2 KB JSON body is fine on a virtual thread. Anything that runs for tens of milliseconds without blocking (hashing, compression, PDF rendering, big XML transforms) belongs on the CPU pool.",
   "try": {
    "title": "Hash on virtual threads",
    "minutes": 3,
    "steps": [
     "Read `CpuBoundDemo`. Each of 64 tasks hashes a 1 MB buffer 20 times: a fixed amount of pure CPU work.",
     "Predict which line finishes first: a pool sized to your cores, or one virtual thread per task.",
     "Run it, then run `-Pargs='256 20'` and predict again."
    ],
    "code": demo("CpuBoundDemo"),
    "expect": "Both lines take about the same time (around 1 s on 4 cores in one run here), and the virtual thread line is never meaningfully faster. On a busy machine it can even be slower. Four times the tasks take about four times as long on both. The work is limited by cores, and both setups use all of them."
   }
  }
 ],
 "analogy": "Back to the office from the lesson on carriers: desks are carriers, and workers pack their papers into a briefcase and free the desk whenever they wait. Pinning is a worker who is handcuffed to the desk while waiting. On JDK 21 to 23, holding a `synchronized` lock was such a handcuff, and a few handcuffed workers waiting on each other could block every desk in the building. JDK 24 removed that handcuff. A `ThreadLocal` cache is a drawer in the desk that each worker fills with their own stationery: fine when the same 200 people work there every day, useless when every visitor is new. The analogy breaks for CPU work: a worker who is busy at the desk is not stuck, they are working. They just never get up, because nobody tells them to.",
 "in_your_world": "If your Quarkus services still run on JDK 21, check before you turn on `@RunOnVirtualThread`: JDBC drivers, HTTP clients and logging appenders that use `synchronized` around socket I/O pin on JDK 21 to 23. Many libraries have since switched to `ReentrantLock`, but trust a JFR recording under load more than a changelog. On JDK 25 that whole class of problem is gone, which is the best argument for upgrading first. The `ThreadLocal` trap applies on every JDK: look for `ThreadLocal.withInitial` caches of formatters, `MessageDigest`, `Cipher` or buffers in payment code, and for CPU-heavy steps such as signing settlement files or generating statements, which belong on a bounded platform pool.",
 "mistake": "The most common mistake today is following advice written for JDK 21 on JDK 25. Teams rewrite every `synchronized` block in the codebase as `ReentrantLock`, which is churn with no benefit on JDK 24 and later, and they \"check\" for pinning with `-Djdk.tracePinnedThreads=full`, which JDK 24 removed, so it prints nothing and looks like a clean bill of health. Know which JDK you run. On JDK 25, keep `synchronized`, keep a JFR recording with `jdk.VirtualThreadPinned` in staging and production, and fix the pins it actually reports, which are mostly slow static initializers and native code.",
 "compare": {
  "title": "Taking the monitor out of the slow path",
  "java": {"title": "Java: synchronized becomes ReentrantLock", "src": "// JDK 21 to 23: this pins for the whole fetch\npublic synchronized BigDecimal rate(String pair) {\n    return rates.computeIfAbsent(pair, ratesService::fetch);\n}\n\n// any JDK: a j.u.c lock parks a waiting virtual thread instead\nprivate final ReentrantLock lock = new ReentrantLock();\n\npublic BigDecimal rate(String pair) {\n    lock.lock();\n    try {\n        return rates.computeIfAbsent(pair, ratesService::fetch);   // rates is a plain HashMap\n    } finally {\n        lock.unlock();\n    }\n}"},
  "kotlin": {"title": "Kotlin: @Synchronized becomes withLock", "src": "// JDK 21 to 23: @Synchronized and synchronized(lock) {} are monitors, and pin the same way\n@Synchronized\nfun rate(pair: String): BigDecimal = rates.getOrPut(pair) { ratesService.fetch(pair) }\n\n// any JDK: kotlin.concurrent.withLock does lock / try / finally / unlock for you\nprivate val lock = ReentrantLock()\n\nfun rate(pair: String): BigDecimal = lock.withLock {\n    rates.getOrPut(pair) { ratesService.fetch(pair) }   // rates is a plain HashMap\n}"},
  "note": "Kotlin has no `synchronized` keyword, but `@Synchronized` and the `synchronized(lock) { }` function both compile to the same JVM monitor instructions as Java, so they pin on JDK 21 to 23 in exactly the same way. The Kotlin fix is shorter, because the standard library's `withLock` extension writes the `lock()`, `try` and `finally { unlock() }` for you, and it is inline, so it costs nothing. Note what neither version does: it doesn't let two different pairs load in parallel. That needs a lock per key, and on JDK 25 it is the only reason left to change this code."
 },
 "worked": {
  "title": "Find and fix a pin from a JFR recording (JDK 21)",
  "steps": [
   {"say": "The quote service runs on JDK 21 with virtual threads. Under load, p99 latency jumps from 150 ms to several seconds while CPU stays low. Record a few minutes of the load test with JFR and print the pinned events.", "code": "jcmd $(pgrep -f quote-service) JFR.start name=pins settings=profile duration=120s filename=pins.jfr\njfr print --events jdk.VirtualThreadPinned pins.jfr | head -40", "lang": "bash"},
   {"say": "Read the stack in the event. The pin lasts as long as the FX call, and the frame just above the blocking call is a `synchronized` method of your cache.", "code": "jdk.VirtualThreadPinned {\n  duration = 103 ms\n  stackTrace = [\n    java.lang.VirtualThread.parkOnCarrierThread(boolean, long)\n    ...\n    sun.nio.ch.NioSocketImpl.read(byte[], int, int)\n    ...\n    com.example.quotes.FxRateCache.rate(String)   <- synchronized\n  ]\n}", "lang": "text"},
   {"say": "Replace the monitor with a `ReentrantLock`, keeping the same \"load once\" behavior. The lock still serializes loads, but a waiting virtual thread now parks and frees its carrier.", "code": "private final ReentrantLock lock = new ReentrantLock();\n\npublic BigDecimal rate(String pair) {\n    lock.lock();                                 // 1. take the lock (parks, doesn't pin)\n    try {\n        BigDecimal r = rates.get(pair);\n        if (r == null) {\n            r = ratesService.fetch(pair);        // 2. slow call: the thread can unmount here\n            rates.put(pair, r);\n        }\n        return r;\n    } finally {\n        lock.unlock();                           // 3. always release\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "private val lock = ReentrantLock()\n\nfun rate(pair: String): BigDecimal = lock.withLock {   // 1. take the lock (parks, doesn't pin)\n    rates[pair] ?: ratesService.fetch(pair)          // 2. slow call: the thread can unmount here\n        .also { rates[pair] = it }\n}                                                    // 3. withLock always releases"},
   {"say": "Verify with the same recording under the same load: zero `jdk.VirtualThreadPinned` events from `FxRateCache`, and p99 back near 150 ms. Then put the JDK 25 upgrade on the plan, so the next `synchronized` in a library doesn't need the same fix."}
  ]
 },
 "lab": {
  "title": "Unpin a cache and retire a ThreadLocal",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/FxRateCache.java", f"{lab}/main/{P}/ReceiptStamp.java"],
  "run": "./gradlew :vthreads:test --tests 'workbench.vthreads.l04.*'",
  "steps": [
   "Run the tests once. Three fail: the monitor check, the JFR pinning check (on JDK 21 to 23; on JDK 24+ it passes even now, which is the point of JEP 491) and the formatter count.",
   "In `FxRateCache`, remove both `synchronized` modifiers and add a `private final ReentrantLock lock`. Wrap the bodies of `rate` and `size` in `lock.lock(); try { ... } finally { lock.unlock(); }`.",
   "Read the JFR test in `TrapsTest`. It records `jdk.VirtualThreadPinned` while four virtual threads load four pairs, then asserts the recording is empty. You can use the same few lines in your own services' tests.",
   "In `ReceiptStamp`, replace the `ThreadLocal<SimpleDateFormat>` with one `static final DateTimeFormatter`, built once with `.withZone(ZoneOffset.UTC)`. Count it in `BUILT` when you build it, and format with `FORMAT.format(Instant.ofEpochMilli(epochMillis))`.",
   "Run the tests until all six pass."
  ],
  "hints": [
   "The monitor test calls `Thread.holdsLock(cache)` from inside the rates service. That returns true only for a `synchronized` monitor on the cache object, never for a `ReentrantLock`.",
   "Don't drop the lock entirely: the load-once test sends 100 virtual threads at the same pair and expects exactly one call to the rates service.",
   "`DateTimeFormatter.ofPattern(\"yyyy-MM-dd'T'HH:mm:ss.SSS'Z'\")` needs a zone to format an `Instant`; without `withZone` you get an `UnsupportedTemporalTypeException`."
  ],
  "done_when": "All six tests in `TrapsTest` pass."
 },
 "drill": {
  "title": "Unpin a method from memory",
  "minutes": 4,
  "prompt": "Close the lab. Rewrite this method for a JDK 21 service so it never holds a monitor during the call, without changing what it does: `synchronized Token refresh() { if (token.expired()) token = authServer.fetchToken(); return token; }`. Then say in one sentence whether you would still change it on JDK 25.",
  "answer": {"lang": "java", "src": "private final ReentrantLock lock = new ReentrantLock();\n\nToken refresh() {\n    lock.lock();                              // outside the try\n    try {\n        if (token.expired()) token = authServer.fetchToken();   // may block: parks, doesn't pin\n        return token;\n    } finally {\n        lock.unlock();\n    }\n}\n// On JDK 25: no need. synchronized no longer pins (JEP 491), so the original is fine.",
             "alt": {"lang": "kotlin", "src": "private val lock = ReentrantLock()\n\nfun refresh(): Token = lock.withLock {          // lock, try, finally unlock\n    if (token.expired()) token = authServer.fetchToken()   // may block: parks, doesn't pin\n    token\n}\n// On JDK 25: no need. @Synchronized no longer pins (JEP 491), so the original is fine."}}
 },
 "recap": [
  "A pinned virtual thread can't unmount at a blocking call, so its carrier blocks with it.",
  "On JDK 21 to 23, blocking while holding a monitor (`synchronized`, `@Synchronized`, `Object.wait`) pins. JDK 24 (JEP 491) fixed that, and JDK 25 is the first LTS with the fix.",
  "On JDK 25, blocking inside a class initializer or under a native frame still pins. File I/O captures the carrier, and the scheduler compensates.",
  "Find pins with the JFR event `jdk.VirtualThreadPinned` (on by default, 20 ms threshold). `-Djdk.tracePinnedThreads` was removed in JDK 24.",
  "A `ThreadLocal` cache builds one object per virtual thread, which means one per task. Share an immutable object such as `DateTimeFormatter` instead.",
  "CPU-bound work gains nothing and, with no time slicing, can starve other virtual threads. Run it on a bounded platform pool."
 ],
 "quiz": [
  {"q": "A service on JDK 25 has `synchronized` blocks around JDBC calls in an old DAO. You are moving request handling to virtual threads. What should you do about those blocks?",
   "options": ["Replace every one with `ReentrantLock` before the switch, or the service will pin", "Nothing for pinning: on JDK 24+ they don't pin. Keep a JFR recording to catch the pins that remain", "Run with `-Djdk.tracePinnedThreads=full` and fix what it prints", "Wrap each JDBC call in `Thread.ofPlatform().start(...)`"], "answer": 1,
   "why": "JEP 491 (JDK 24) lets virtual threads hold monitors without pinning, so on JDK 25 these blocks are fine. Rewriting them is the JDK 21 advice. `-Djdk.tracePinnedThreads` no longer exists on JDK 24+, so it would print nothing and prove nothing."},
  {"q": "Which tool shows you, on JDK 25, that a virtual thread pinned its carrier for 180 ms and why?",
   "options": ["`jstack <pid>`", "`Thread.getAllStackTraces()` from a debug endpoint", "The JFR event `jdk.VirtualThreadPinned`, printed with `jfr print`", "`-Djdk.tracePinnedThreads=short`"], "answer": 2,
   "why": "`jdk.VirtualThreadPinned` is recorded for pins over 20 ms by default and carries the stack, and on JDK 25 also the pinned reason and carrier. `jstack` and `getAllStackTraces()` show platform threads, not parked virtual threads, and the trace property was removed in JDK 24."},
  {"q": "A payment service hashes request bodies with a `ThreadLocal<MessageDigest>` cache. It moves from a 200-thread pool to one virtual thread per request and serves 1 million requests. About how many `MessageDigest` objects does it create?",
   "options": ["200, the same as before", "One per carrier thread, so about the number of cores", "About 1 million, one per request", "One, because ThreadLocal values are shared between virtual threads"], "answer": 2,
   "why": "Each virtual thread has its own thread-local map, and each request runs on a new virtual thread, so `withInitial` runs once per request. Carriers don't matter: the JDK keeps a virtual thread's thread locals separate from its carrier's. Share a thread-safe object, or create one per call on purpose."},
  {"q": "An 8-core batch job resizes 10,000 images, each taking about 50 ms of pure CPU. It runs on `newFixedThreadPool(8)`. What happens if you switch it to `newVirtualThreadPerTaskExecutor()`?",
   "options": ["It finishes in about the same time, about 62 s, because only 8 can compute at once either way", "It finishes in about 50 ms, because all 10,000 run at once", "It finishes about 8 times faster", "It deadlocks, because virtual threads can't run CPU work"], "answer": 0,
   "why": "There are 8 carriers, so at most 8 virtual threads compute at once: 10,000 × 50 ms / 8 = 62.5 s, the same as the pool. Virtual threads only help when tasks spend their time waiting. With no time slicing, they can also delay other virtual threads in the same JVM."},
  {"q": "From the lesson \"Don't share: immutability, confinement, ThreadLocal\": `SimpleDateFormat` is not thread-safe. Which fix works equally well on a platform pool and on one virtual thread per task, with no per-thread state at all?",
   "options": ["Wrap every `format` call in `synchronized`", "One shared, immutable `DateTimeFormatter`", "A `ThreadLocal<SimpleDateFormat>`", "A `volatile SimpleDateFormat` field"], "answer": 1,
   "why": "An immutable object is safe to share with any number of threads, so it needs no per-thread copies and no locking. The `ThreadLocal` works on a pool but becomes one formatter per task on virtual threads. `synchronized` is correct but makes every caller wait in line. `volatile` makes the reference visible but leaves the formatter's internal state racy.", "from": "conc-11"}
 ],
 "flashcards": [
  {"front": "What does it mean that a virtual thread is pinned?", "back": "It reaches a blocking call but can't unmount, so it stays on its carrier and the carrier blocks with it."},
  {"front": "Does blocking inside `synchronized` pin a virtual thread on JDK 25?", "back": "No. Since JDK 24 (JEP 491) monitors don't pin. On JDK 21 to 23 they do."},
  {"front": "What still pins a virtual thread on JDK 25?", "back": "Blocking while a class initializer or a native frame (JNI, or an FFM downcall that calls back into Java) is on its stack."},
  {"front": "How do you detect pinning on JDK 24 and later?", "back": "The JFR event `jdk.VirtualThreadPinned` (on by default, 20 ms threshold). `-Djdk.tracePinnedThreads` was removed in JDK 24."},
  {"front": "Why does a `ThreadLocal` cache stop working with one virtual thread per task?", "back": "Each task runs on a new virtual thread with an empty thread-local map, so the cached object is built once per task and thrown away."},
  {"front": "Do virtual threads speed up CPU-bound work?", "back": "No. At most one virtual thread per carrier (per core) computes at once, and there is no time slicing."},
  {"front": "Kotlin replacement for `@Synchronized` around I/O on JDK 21?", "back": "`private val lock = ReentrantLock()` and `lock.withLock { ... }` from `kotlin.concurrent`."}
 ],
 "terms": [
  {"term": "Pinning", "plain": "A virtual thread stuck on its carrier during a blocking call, so the carrier blocks too."},
  {"term": "Monitor", "plain": "The lock behind `synchronized` and `@Synchronized`, built into every Java object."},
  {"term": "JEP 491", "plain": "The JDK 24 change that lets virtual threads hold monitors without pinning."},
  {"term": "JFR", "plain": "Java Flight Recorder: the JVM's built-in, low-overhead event recorder."},
  {"term": "jdk.VirtualThreadPinned", "plain": "The JFR event recorded when a virtual thread blocks while pinned for longer than the threshold."},
  {"term": "Carrier capture", "plain": "A blocking call, such as a file read, that keeps the carrier; the scheduler adds a temporary carrier."},
  {"term": "ThreadLocal cache", "plain": "Keeping one copy of an object per thread to reuse it. Useless when every task gets a new thread."}
 ],
 "explain_back": {
  "prompt": "Your team lead read a 2023 article and wants to ban `synchronized` before the move to virtual threads. The service runs on JDK 25. Explain what pinning is, whether the ban helps, and what you would check instead.",
  "answer": "Pinning is when a virtual thread can't unmount at a blocking call, so it keeps its carrier and the carrier blocks with it. On JDK 21 to 23, holding a `synchronized` monitor while blocking caused it, and a few pinned threads could block every carrier. JDK 24 fixed that with JEP 491, so on JDK 25 a ban on `synchronized` changes nothing for pinning and just churns code. What still pins on JDK 25 is blocking inside a class initializer or under native code, so I'd keep a JFR recording with `jdk.VirtualThreadPinned` running in staging and production and fix what it reports. I'd also check the traps that have nothing to do with pinning: `ThreadLocal` caches that now build an object per request, and CPU-heavy steps that should stay on a bounded platform pool."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Why monitors pinned in the first place.** Before JDK 24, HotSpot recorded the owner of a monitor as the OS thread that held it. If a virtual thread could unmount while holding a monitor, another virtual thread mounted on the same carrier would appear to own it too. Rather than redesign monitors for JDK 21, the Loom team shipped with pinning and a warning. JEP 491 changed the JVM to record the virtual thread as the owner, so the thread can move freely.\n\n**Object.wait() on JDK 21.** A virtual thread in `Object.wait()` was pinned too, but the scheduler compensated by adding a temporary carrier, up to `jdk.virtualThreadScheduler.maxPoolSize`. That kept wait-heavy code alive at the cost of extra OS threads. Blocking on monitor entry got no such help, which is why the deadlock in this lesson's figure was possible.\n\n**Testing for pins.** The lab's JFR test is a pattern you can copy into a service's integration tests: start a `jdk.jfr.Recording` with `jdk.VirtualThreadPinned` enabled, run a realistic slice of traffic on virtual threads, stop and dump the recording, and assert there are no events. Warm up first, so one-time class loading doesn't show up as a pin. On JDK 24 and later, such a test catches class initializer and native pins. On JDK 21, it also catches every `synchronized` around I/O.\n\n**Inheritable thread locals.** A new thread copies its parent's `InheritableThreadLocal` values by default, and that includes virtual threads. Creating a million virtual threads from a thread with large inheritable values copies them a million times. `Thread.ofVirtual().inheritInheritableThreadLocals(false)` turns the copy off for threads that don't need it."
 },
 "sources": [
  {"title": "JEP 491: Synchronize Virtual Threads without Pinning", "url": "https://openjdk.org/jeps/491"},
  {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444"},
  {"title": "ReentrantLock (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html"},
  {"title": "jdk.jfr.Recording (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/jdk.jfr/jdk/jfr/Recording.html"}
 ]
}
out = ROOT / "content/lessons/vt-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
