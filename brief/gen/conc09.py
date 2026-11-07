import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/concurrency/src"
P = "java/workbench/concurrency/l09"
K = "kotlin/workbench/concurrency/l09"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"./gradlew :concurrency:demo -Pmain=workbench.concurrency.l09.{name}"
def code(name):
    """A Java demo with its Kotlin twin (Foo.kt with a top-level main, class FooKt)."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": demo(name), "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": demo(f"{name}Kt"), "file": f"{lab}/demo/{K}/{name}.kt"}}
def pair(java, kotlin):
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

J_CHM = """ConcurrentHashMap<String, Long> settledCents = new ConcurrentHashMap<>();

void onSettled(String merchant, long cents) {
    settledCents.merge(merchant, cents, Long::sum);     // insert or add, atomically for this key
}

String issuerFor(String bin) {
    return issuers.computeIfAbsent(bin, directory::lookup);   // lookup runs at most once per BIN
}"""
K_CHM = """val settledCents = ConcurrentHashMap<String, Long>()

fun onSettled(merchant: String, cents: Long) {
    settledCents.merge(merchant, cents, Long::plus)     // insert or add, atomically for this key
}

fun issuerFor(bin: String): String =
    issuers.computeIfAbsent(bin, directory::lookup)       // lookup runs at most once per BIN"""

J_MEMO = """private final ConcurrentHashMap<String, CompletableFuture<String>> issuers = new ConcurrentHashMap<>();

String issuerFor(String bin) {
    // 1. claim the BIN: the function only creates a future, so the bin is locked for microseconds
    CompletableFuture<String> f = issuers.computeIfAbsent(bin,
            b -> CompletableFuture.supplyAsync(() -> directory.lookup(b), ioPool));
    try {
        return f.join();                                  // 2. wait outside the map, with every other caller
    } catch (CompletionException e) {
        issuers.remove(bin, f);                           // 3. failed: forget THIS future so a retry loads again
        throw e;
    }
}"""
K_MEMO = """private val issuers = ConcurrentHashMap<String, CompletableFuture<String>>()

fun issuerFor(bin: String): String {
    // 1. claim the BIN: the function only creates a future, so the bin is locked for microseconds
    val f = issuers.computeIfAbsent(bin) { b ->
        CompletableFuture.supplyAsync({ directory.lookup(b) }, ioPool)
    }
    try {
        return f.join()                                   // 2. wait outside the map, with every other caller
    } catch (e: CompletionException) {
        issuers.remove(bin, f)                            // 3. failed: forget THIS future so a retry loads again
        throw e
    }
}"""
J_ONE = """String issuerFor(String bin) {
    return issuers.computeIfAbsent(bin, directory::lookup);   // 80 ms with the bin locked
}"""
K_ONE = """fun issuerFor(bin: String): String =
    issuers.computeIfAbsent(bin, directory::lookup)           // 80 ms with the bin locked"""

J_DRILL = """class DeclineCounter {
    private final ConcurrentHashMap<String, LongAdder> byReason = new ConcurrentHashMap<>();

    void record(String reason) {
        byReason.computeIfAbsent(reason, r -> new LongAdder()).increment();
    }

    long count(String reason) {
        LongAdder a = byReason.get(reason);
        return a == null ? 0 : a.sum();
    }
}"""
K_DRILL = """class DeclineCounter {
    private val byReason = ConcurrentHashMap<String, LongAdder>()

    fun record(reason: String) {
        byReason.computeIfAbsent(reason) { LongAdder() }.increment()
    }

    fun count(reason: String): Long = byReason[reason]?.sum() ?: 0L
}"""

TABLE = """| | Throws | Returns a special value | Blocks | Times out |
|---|---|---|---|---|
| Insert | `add(e)` | `offer(e)`: `false` if full | `put(e)` | `offer(e, time, unit)` |
| Remove | `remove()` | `poll()`: `null` if empty | `take()` | `poll(time, unit)` |
| Examine | `element()` | `peek()`: `null` if empty | | |"""

def bin_box(i, cls="box", label=None):
    x = 40 + 76 * i
    return (f'<rect class="{cls}" x="{x}" y="100" width="64" height="44" rx="8"/>'
            f'<text class="t-s" x="{x + 32}" y="127" text-anchor="middle">{label or "bin " + str(i)}</text>')

FIG = (
    '<svg viewBox="0 0 680 250" role="img" aria-label="ConcurrentHashMap bins: thread A locks bin 3, thread B updates bin 6 at the same time, thread C waits for bin 3, thread D reads bin 1 without locking">'
    + "".join(bin_box(i, {3: "box-a", 6: "box-ok"}.get(i, "box")) for i in range(8))
    + '<rect class="box" x="225" y="20" width="150" height="36" rx="8"/>'
    '<text class="t t-code" x="300" y="43" text-anchor="middle">A: merge(m-17)</text>'
    '<line class="ln-a" x1="300" y1="56" x2="300" y2="96" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="308" y="82">holds bin 3</text>'
    '<rect class="box" x="453" y="20" width="150" height="36" rx="8"/>'
    '<text class="t t-code" x="528" y="43" text-anchor="middle">B: merge(m-42)</text>'
    '<line class="ln" x1="528" y1="56" x2="528" y2="96" marker-end="url(#arr)"/>'
    '<text class="t-s t-ok" x="536" y="82">other bin: no wait</text>'
    '<rect class="box" x="230" y="196" width="140" height="36" rx="8"/>'
    '<text class="t t-code" x="300" y="219" text-anchor="middle">C: merge(m-90)</text>'
    '<line class="ln-bad" x1="300" y1="196" x2="300" y2="148" marker-end="url(#arr)"/>'
    '<text class="t-s t-bad" x="308" y="176">same bin: waits</text>'
    '<rect class="box" x="78" y="196" width="140" height="36" rx="8"/>'
    '<text class="t t-code" x="148" y="219" text-anchor="middle">D: get(m-5)</text>'
    '<line class="ln-d" x1="148" y1="196" x2="148" y2="148" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="156" y="176">reads never lock</text>'
    '</svg>'
)

L = {
 "id": "conc-09",
 "title": "Concurrent collections",
 "minutes": 37,
 "goal": "By the end you can pick the right concurrent collection for a job, use `ConcurrentHashMap`'s atomic per-key methods correctly, and explain what weakly consistent iteration and `ConcurrentModificationException` really mean.",
 "warmup": {
  "q": "A single thread loops over an `ArrayList` with for-each and calls `list.remove(item)` for one of the items. No other thread exists. What happens?",
  "options": ["It works: `ConcurrentModificationException` needs two threads", "It throws `ConcurrentModificationException`", "It silently skips the rest of the list", "It deadlocks"],
  "answer": 1,
  "why": "The exception has nothing to do with threads. The list's iterator keeps a count of structural changes, and the next call to `next()` sees that the list changed behind its back. One thread is enough. And the opposite surprise is worse: when two threads really do race on an `ArrayList`, the check is best effort, so you may get lost or corrupted data with no exception at all."
 },
 "sections": [
  {
   "h": "ConcurrentHashMap is atomic per key, not per map",
   "body": "`ConcurrentHashMap` is the map to use when threads share one. Reads never lock. A write locks only the **bin** that its key hashes to, so writes to different keys mostly run in parallel. A write into an empty bin doesn't lock at all: it uses compare-and-set, as in the previous lesson.\n\nEvery single method is atomic. As lesson 3 of this track showed, a sequence of calls is not. So the map offers methods that do a whole read-modify-write on one key in one call:\n\n- `putIfAbsent(k, v)` inserts only if the key is missing.\n- `computeIfAbsent(k, f)` computes and inserts only if missing, and runs `f` at most once.\n- `compute(k, f)` and `computeIfPresent(k, f)` replace the value with `f` of the old one.\n- `merge(k, v, f)` inserts `v`, or replaces the old value with `f(old, v)`.\n- `replace(k, expected, next)` is a compare-and-set on one key.\n\nThe Javadoc of each compute method says \"The entire method invocation is performed atomically.\" That sentence is the reason to use them:\n\n" + pair(J_CHM, K_CHM) + "\n\nThe figure shows why this scales. Two threads that update keys in different bins never meet. Two threads that update the same key take turns, which is exactly what you want.\n\nTwo more rules. `ConcurrentHashMap` rejects `null` keys and values with `NullPointerException`. That is on purpose: when `get(k)` returns `null`, it always means \"absent\", so you never need a second call to tell \"missing\" from \"mapped to null\" (and a second call would be check-then-act). And `Collections.synchronizedMap(new HashMap<>())` is no substitute. It has one lock for the whole map, and the same gap between calls.",
   "figure": {"svg": FIG, "caption": "Writes lock one bin, not the map. A and B update different bins at the same time. C waits only because its key lands in A's bin. Reads never lock."},
   "try": {
    "title": "Three maps, one count",
    "minutes": 3,
    "steps": [
     "Read `MapShootout`. Eight threads record 800,000 payments across 1,000 merchants: on a `HashMap` with `merge`, on a `ConcurrentHashMap` with get-then-put, and on a `ConcurrentHashMap` with `merge`.",
     "Predict the total for each.",
     "Run it twice."
    ],
    "code": code("MapShootout"),
    "expect": "The `HashMap` loses most of the counts, and usually one of its threads dies with `ConcurrentModificationException` (`HashMap.merge` notices the map changed while it worked). In runs here it kept 100,000 to 200,000 of 800,000. `ConcurrentHashMap` with get-then-put loses a few thousand: every call is safe, the pair isn't. Only `ConcurrentHashMap.merge` gives exactly 800,000."
   },
   "refs": [
    {"title": "ConcurrentHashMap.java at jdk-25-ga (compute and merge contracts)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/ConcurrentHashMap.java", "kind": "read"}
   ]
  },
  {
   "h": "Keep the function short, and never touch the map from inside it",
   "body": "The function you pass to `compute`, `merge` or `computeIfAbsent` runs while the map holds the lock for that key's bin. Three things follow from that.\n\nFirst, other writes to the same bin wait for your whole function. The Javadoc says so: \"Some attempted update operations on this map by other threads may be blocked while computation is in progress, so the computation should be short and simple.\" An 80 ms call to the issuer directory inside `computeIfAbsent` makes every write that lands in that bin wait 80 ms. Reads are not blocked. For a cache that loads each key once, that is often fine. When it isn't, the worked example shows how to keep the slow work outside the map.\n\nSecond, the function must not change the map. The Javadoc is blunt again: \"The mapping function must not modify this map during computation.\" Memoized recursion is how people break this rule without noticing:\n\n```java\nlong fib(int n) {\n    if (n < 2) return n;\n    return memo.computeIfAbsent(n, k -> fib(k - 1) + fib(k - 2));   // calls computeIfAbsent again, inside\n}\n```\n\n```kotlin\nfun fib(n: Int): Long {\n    if (n < 2) return n.toLong()\n    return memo.computeIfAbsent(n) { k -> fib(k - 1) + fib(k - 2) }   // calls computeIfAbsent again, inside\n}\n```\n\nOn JDK 21, `ConcurrentHashMap` throws `IllegalStateException: Recursive update` here, and `HashMap` throws `ConcurrentModificationException`. The JDK only catches some of these cases, so don't count on an exception. Compute the value outside the map, or build the table bottom-up.\n\nThird, if the function throws, nothing is stored and the exception reaches the caller, so the next call tries again. If it returns `null`, nothing is stored either. The lab relies on that.",
   "try": {
    "title": "Break the rule on purpose",
    "minutes": 2,
    "steps": [
     "Run `RecursiveUpdate`. It computes `fib(30)` with memoized recursion on a `ConcurrentHashMap`, then on a `HashMap`, then bottom-up.",
     "Read the exception messages. Which map tells you what you did wrong?"
    ],
    "code": code("RecursiveUpdate"),
    "expect": "`ConcurrentHashMap: threw java.lang.IllegalStateException: Recursive update`, `HashMap: threw java.util.ConcurrentModificationException`, and `bottom-up: fib(30) = 832040`. Only the version that fills the table outside any compute call works."
   }
  },
  {
   "h": "Weak iterators, estimated sizes, and what ConcurrentModificationException means",
   "body": "`ConcurrentModificationException` sounds like \"two threads touched my collection\". It means something narrower: this collection's own iterator noticed that the collection changed in a way the iterator didn't make. `ArrayList` and `HashMap` iterators are **fail-fast**. They keep a count of changes and check it on every `next()`. One thread is enough to trip it, as the warm-up showed. And the check is best effort: when two threads race, it may not fire at all, and you get lost entries or a damaged structure instead. Never treat the exception as a race detector.\n\nThe concurrent collections have weakly consistent iterators. They never throw `ConcurrentModificationException`, and they reflect the collection at some point at or after the moment the iterator was created. A change made during the loop may or may not show up.\n\nThe same goes for `size()`, `isEmpty()` and `containsValue()` on `ConcurrentHashMap`. While other threads update the map, they describe a moving target. The Javadoc calls them useful for monitoring and estimation, not for program control. `if (map.size() < 10_000) map.put(k, v)` is check-then-act on an estimate.\n\n`CopyOnWriteArrayList` takes the opposite trade. Every write copies the whole array. Every iterator walks the array as it was when the loop started, so iteration never locks and never throws. That is perfect for a list of webhook listeners that changes at deploy time and is iterated on every payment. It is terrible for a list that grows with traffic: adding the 100,000th element copies 100,000 references. `CopyOnWriteArraySet` works the same way, and `ConcurrentSkipListMap` is the concurrent sorted map.",
   "try": {
    "title": "Trip a fail-fast iterator with one thread",
    "minutes": 3,
    "steps": [
     "Read `FailFast`. It modifies an `ArrayList`, a `ConcurrentHashMap` and a `CopyOnWriteArrayList` while iterating over each one, all on the main thread.",
     "Predict what each line prints. In the copy-on-write loop, the body adds an item for every item it sees: does the loop ever end?",
     "Run it."
    ],
    "code": code("FailFast"),
    "expect": "The `ArrayList` throws `ConcurrentModificationException` with one thread. The `ConcurrentHashMap` loop throws nothing and ends with 4 keys. The copy-on-write loop sees 3 items and ends, while the list now has 6, because the loop walks the snapshot it started with. `removeIf` is the single-thread fix for the first case."
   },
   "refs": [
    {"title": "CopyOnWriteArrayList.java at jdk-25-ga (copy cost, snapshot iterators)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/CopyOnWriteArrayList.java", "kind": "read"}
   ]
  },
  {
   "h": "BlockingQueue is the collection for handing work between threads",
   "body": "Lesson 5 of this track built a bounded buffer by hand. `ArrayBlockingQueue` is the production version, and every `BlockingQueue` offers the same four ways to add and remove:\n\n" + TABLE + "\n\nPick the column by what the caller should do when the queue is full or empty. A request thread usually wants `offer` and an answer now. A dedicated consumer thread wants `take` and sleeps until there is work. Queues reject `null` because `poll` uses `null` to mean \"empty\".\n\nThe implementations differ in ways that matter in production:\n\n- `ArrayBlockingQueue` is bounded, backed by one array and one lock.\n- `LinkedBlockingQueue` takes an optional capacity, and the default is `Integer.MAX_VALUE`. That is unbounded in practice. It uses separate locks for the head and the tail, so producers and consumers contend less.\n- `SynchronousQueue` has no capacity at all. Each `put` waits for a `take`, and `offer` with no waiting taker returns `false`.\n- `PriorityBlockingQueue` orders by priority and is unbounded. `DelayQueue` releases each element only when its delay has passed.\n\nA bounded queue gives you **back-pressure**. When the consumer falls behind, `put` makes the producer wait, or `offer` tells it to back off, so the system slows down instead of filling memory. `drainTo(list, max)` moves everything already queued in one call without waiting, which is how you batch. The lab's `Batcher` uses exactly that pair: `poll` with a timeout for the first entry, then `drainTo` for the rest.",
   "try": {
    "title": "Fill a queue every way you can",
    "minutes": 3,
    "steps": [
     "Read `QueueMethods`. It fills an `ArrayBlockingQueue` of 2, then tries `add`, `offer`, timed `offer` and `put` on the full queue.",
     "Predict each line, including the capacity of a `LinkedBlockingQueue` built with no arguments.",
     "Run it."
    ],
    "code": code("QueueMethods"),
    "expect": "`add` throws `IllegalStateException: Queue full`, `offer` returns `false` at once, the timed `offer` returns `false` after about 300 ms, and the producer in `put` is `WAITING` until `take` frees a slot. The no-argument `LinkedBlockingQueue` reports a capacity of 2,147,483,647. `SynchronousQueue.offer` returns `false` because nobody is waiting to take."
   },
   "refs": [
    {"title": "BlockingQueue (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/BlockingQueue.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A `ConcurrentHashMap` is a bank with many tellers, one per group of account numbers. Customers with accounts in different groups are served at the same time; two customers for the same group queue at that one teller. Anyone may look at the balance board without queueing at all. A `CopyOnWriteArrayList` is a printed notice board: to change it, you print a whole new sheet and pin it up, and people reading the old sheet keep reading the old sheet. A bounded `BlockingQueue` is a coat check with 50 hooks: when they're full, the next guest waits or is told to come back later. The analogy breaks at the teller: a human teller would notice if you asked them to serve you while they were already serving you. `computeIfAbsent` calling itself only sometimes gets caught.",
 "in_your_world": "Most of these show up in a payment service within a week. A BIN or tenant-config cache is a `ConcurrentHashMap` with `computeIfAbsent`. Per-merchant totals for a settlement report are `merge(merchant, cents, Long::sum)`, or `computeIfAbsent(merchant, m -> new LongAdder()).increment()` when the keys are hot. Webhook or fraud-rule listeners that change only at deploy time live in a `CopyOnWriteArrayList`. And the outbox relay that moves ledger entries from request threads to a single Kafka-producing thread is a `BlockingQueue`. Give it a capacity, and decide what a full queue means: block the producer, answer 503, or `pause()` the Kafka consumer that feeds it.",
 "mistake": "The most common real mistake is the unbounded queue. `new LinkedBlockingQueue<>()` looks harmless, and `put` never blocks, so it works in every test. Then the database slows down during an incident, the consumer falls behind, the queue grows to millions of entries, the garbage collector thrashes, and the pod is killed for running out of memory, taking every queued entry with it. `Executors.newFixedThreadPool` uses the same unbounded queue internally, which the executors track comes back to. The fix is to always pass a capacity and to decide, on purpose, what happens when the queue is full: `put` to slow the producer down, or `offer` to reject the work with a retryable error.",
 "compare": {
  "title": "Load-once caching in Java and Kotlin",
  "java": {"title": "Java", "src": """ConcurrentHashMap<String, String> issuers = new ConcurrentHashMap<>();

String issuerFor(String bin) {
    return issuers.computeIfAbsent(bin, directory::lookup);   // lookup runs at most once per BIN
}"""},
  "kotlin": {"title": "Kotlin", "src": """val issuers = ConcurrentHashMap<String, String>()

fun issuerFor(bin: String): String =
    issuers.getOrPut(bin) { directory.lookup(bin) }           // atomic put, but lookup may run several times

fun issuerForOnce(bin: String): String =
    issuers.computeIfAbsent(bin) { directory.lookup(it) }     // lookup runs at most once per BIN"""},
  "note": "Kotlin's idiomatic `getOrPut` is the trap. The standard library has a special version for `ConcurrentMap` that uses `putIfAbsent`, so it never overwrites a value that is already there. But its documentation says the default function \"may be invoked even if the key is already in the map\". With 8 threads racing for one new key, the lookup ran 8 times in a check here, against once for `computeIfAbsent`. And if the variable's declared type is plain `MutableMap`, Kotlin picks the general `getOrPut`, which is a check followed by a put with no atomicity at all. Use `computeIfAbsent` when the loader is slow or must run once. Kotlin's type system does help in one place: `ConcurrentHashMap<String, String>` can't be handed a `null` value, so the `NullPointerException` that Java callers can hit becomes a compile error."
 },
 "worked": {
  "title": "Load once, without holding the bin for 80 ms",
  "steps": [
   {"say": "The issuer directory takes 80 ms. This cache loads each BIN once, which is good. But while it loads, every other write that lands in the same bin waits, and the Javadoc asks for short functions. The goal: keep the map operation tiny and do the slow work outside it, while still loading each BIN once.",
    "code": J_ONE, "lang": "java", "alt_code": K_ONE, "alt_lang": "kotlin"},
   {"say": "Cache the *promise* of a value instead of the value. The function inside `computeIfAbsent` now only creates a `CompletableFuture` that starts the lookup on another pool. That takes microseconds, so the bin is free again almost at once. Every caller for the BIN gets the same future and waits on it outside the map.",
    "code": J_MEMO, "lang": "java", "alt_code": K_MEMO, "alt_lang": "kotlin"},
   {"say": "Before reading on, explain to yourself: why `remove(bin, f)` with two arguments, and not `remove(bin)`? Answer: between the failure and the remove, another thread may already have put a fresh future in place of the failed one. The two-argument `remove` deletes the entry only if it still maps to the future that failed. It is a compare-and-set on one key, and it keeps you from throwing away someone else's good load.", "code": "", "lang": ""},
   {"say": "This is the Memoizer from *Java Concurrency in Practice*, section 5.6, written with `CompletableFuture`. One gap is left: entries never expire, so a BIN that moves to a new issuer stays wrong until restart. A production service would use a caching library with expiry and asynchronous loading. Writing it once by hand tells you what that library does for you, and what to look for when it misbehaves.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Three concurrent-collection fixes",
  "minutes": 14,
  "files": [f"{lab}/main/{P}/BinCache.java", f"{lab}/main/{P}/WebhookRegistry.java", f"{lab}/main/{P}/Batcher.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l09.*'",
  "steps": [
   "Run the tests. Six of eight fail: `BinCache` calls its loader 8 times for one BIN, `WebhookRegistry` throws `ConcurrentModificationException` (once even with a single thread), and `Batcher` throws `UnsupportedOperationException`.",
   "Fix `BinCache.issuerFor` with one `ConcurrentHashMap` call.",
   "Fix `WebhookRegistry` by changing the type of collection it uses. You don't need a lock.",
   "Write `Batcher` on an `ArrayBlockingQueue`. `submit` uses `offer`. `nextBatch` waits with `poll(timeout)` for the first entry, then calls `drainTo(batch, max - 1)`.",
   "Run the tests until all eight pass, then twice more."
  ],
  "hints": [
   "`computeIfAbsent` takes the loader as it is: `issuers.computeIfAbsent(bin, loader)`. If the loader throws, nothing is stored, which is what the third test checks.",
   "Why not `Collections.synchronizedList` for the registry? Its `add` and `remove` are safe, but you must hold its lock for the whole loop while iterating, and a listener that unregisters itself during `publish` still throws, on the same thread.",
   "`poll(timeout)` returns `null` when time runs out. `drainTo` never waits; it moves only what is already there."
  ],
  "done_when": "All eight tests in `ConcurrentCollectionsTest` pass, three runs in a row."
 },
 "drill": {
  "title": "A per-key counter from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `DeclineCounter` with `record(String reason)` and `long count(String reason)`, safe for many threads, using a `ConcurrentHashMap` and one `LongAdder` per reason. Check: can two threads ever create two adders for the same reason?",
  "answer": {"lang": "java", "src": J_DRILL, "alt": {"lang": "kotlin", "title": "Kotlin", "src": K_DRILL}}
 },
 "recap": [
  "`ConcurrentHashMap` locks per bin and never for reads. Single calls are atomic; sequences of calls are not.",
  "Use `computeIfAbsent`, `compute`, `merge`, `putIfAbsent` and two-argument `remove`/`replace` for per-key read-modify-write.",
  "The compute function runs under the bin's lock: keep it short, and never modify the map from inside it.",
  "`ConcurrentModificationException` is a fail-fast iterator check, often tripped by one thread. Concurrent collections never throw it; their iterators and `size()` are weakly consistent.",
  "`CopyOnWriteArrayList` suits small, rarely changed, often iterated lists, such as listeners.",
  "Use a bounded `BlockingQueue` for hand-offs between threads. The no-argument `LinkedBlockingQueue` is unbounded."
 ],
 "quiz": [
  {"q": "From atomics and compare-and-set: 16 threads count events for about 200 hot merchant keys. Which is the best fit?",
   "options": ["`HashMap<String, Long>` with `merge`", "`ConcurrentHashMap<String, LongAdder>` with `computeIfAbsent(k, x -> new LongAdder()).increment()`", "`ConcurrentHashMap<String, Long>` with `put(k, get(k) + 1)`", "`Collections.synchronizedMap(new HashMap<>())` with `merge`"],
   "answer": 1, "why": "`computeIfAbsent` creates each adder once, and after that every increment goes to a `LongAdder`, which spreads hot keys over cells. `merge` on a `ConcurrentHashMap<String, Long>` would also be correct, just with more contention on hot keys. A plain `HashMap` breaks, get-then-put loses updates, and a synchronized map serializes every thread on one lock.",
   "from": "conc-08"},
  {"q": "Why does `ConcurrentHashMap` throw `NullPointerException` for `put(k, null)`?",
   "options": ["So that `get(k) == null` always means the key is absent, with no second call needed", "Because nulls would corrupt its bins", "It doesn't: only null keys are rejected", "To save memory"],
   "answer": 0, "why": "If null values were allowed, `get` returning null would be ambiguous, and telling \"absent\" from \"mapped to null\" would need `containsKey` too. Two calls is check-then-act, which another thread can break. Banning null removes the ambiguity."},
  {"q": "A cache uses `map.computeIfAbsent(id, k -> loadAccount(k))`, and `loadAccount` calls `map.computeIfAbsent(parentId, ...)` on the same map. What should you expect?",
   "options": ["It works, because the two keys differ", "A deadlock every time", "It breaks the documented contract; `ConcurrentHashMap` may throw `IllegalStateException: Recursive update` or misbehave", "A `ConcurrentModificationException` from the iterator"],
   "answer": 2, "why": "The Javadoc says the mapping function must not modify the map. Whether the JDK detects it depends on where the keys land, so sometimes it throws `Recursive update` and sometimes it seems to work. Don't rely on either. Load the parent first, outside the compute call."},
  {"q": "A list of five fraud-rule listeners changes only at deploy time and is iterated on every one of 3,000 payments a second, from many threads. Which collection fits?",
   "options": ["`ArrayList` guarded by `synchronized` around every loop", "`Collections.synchronizedList(new ArrayList<>())`", "`ConcurrentLinkedQueue`", "`CopyOnWriteArrayList`"],
   "answer": 3, "why": "Reads vastly outnumber writes and the list is tiny, so copying the array on each rare write is cheap, and every iteration runs lock-free over a stable snapshot. The synchronized options make every payment take a lock for the whole loop. A queue would work for iteration, but it doesn't model a list you add to and remove from by identity as cleanly."},
  {"q": "A Kafka consumer thread puts records into `new LinkedBlockingQueue<>()` and a single writer thread inserts them into Oracle. During a slow-database incident, what happens?",
   "options": ["`put` blocks the consumer once the queue holds 10,000 records", "The queue grows without limit, because the default capacity is `Integer.MAX_VALUE`, until memory runs out", "`put` throws `IllegalStateException` when the queue is full", "The writer thread speeds up to match"],
   "answer": 1, "why": "With no capacity, the queue never fills, so nothing pushes back on the consumer. Memory grows until the pod dies. Give the queue a capacity so `put` blocks the consumer (or `offer` fails), and pause the Kafka consumer when it does."}
 ],
 "flashcards": [
  {"front": "What does `ConcurrentHashMap.computeIfAbsent(k, f)` guarantee?", "back": "The whole call is atomic for that key: if `k` is absent, `f` runs at most once and its result is stored. Other updates to the same bin wait while `f` runs."},
  {"front": "Can a `ConcurrentHashMap` hold null keys or null values?", "back": "No. Both throw `NullPointerException`, so `get(k) == null` always means \"absent\"."},
  {"front": "What happens if the function passed to `computeIfAbsent` modifies the same map?", "back": "It breaks the contract. `ConcurrentHashMap` may throw `IllegalStateException: Recursive update`; `HashMap` may throw `ConcurrentModificationException`; sometimes nothing is caught."},
  {"front": "Is `ConcurrentHashMap.size()` exact while other threads update it?", "back": "No. It is an estimate of a moving target: fine for monitoring, wrong for decisions."},
  {"front": "What does a `ConcurrentHashMap` iterator do if the map changes during the loop?", "back": "It never throws. It is weakly consistent: changes made during the loop may or may not appear."},
  {"front": "On a full `ArrayBlockingQueue`, what do `offer(e)` and `put(e)` do?", "back": "`offer(e)` returns `false` at once. `put(e)` waits until there is space (and throws `InterruptedException` if interrupted)."},
  {"front": "What is the capacity of `new LinkedBlockingQueue<>()`?", "back": "`Integer.MAX_VALUE`: unbounded in practice. Pass a capacity to get back-pressure."}
 ],
 "terms": [
  {"term": "ConcurrentHashMap", "plain": "A thread-safe hash map that locks per bin for writes and never locks for reads."},
  {"term": "Bin", "plain": "One slot of a hash table; keys whose hashes land in the same slot share it."},
  {"term": "Fail-fast iterator", "plain": "An iterator that throws `ConcurrentModificationException` when it notices its collection changed; best effort only."},
  {"term": "Weakly consistent iterator", "plain": "An iterator that never throws and may or may not show changes made while it runs."},
  {"term": "CopyOnWriteArrayList", "plain": "A list that copies its whole array on every write so readers can iterate a stable snapshot without locks."},
  {"term": "BlockingQueue", "plain": "A queue whose `put` and `take` wait when it is full or empty, used to hand work between threads."},
  {"term": "Back-pressure", "plain": "Slowing or rejecting producers when consumers fall behind, instead of buffering without limit."}
 ],
 "explain_back": {
  "prompt": "A teammate says: \"We switched to ConcurrentHashMap, so our cache and counters are thread-safe now.\" Explain what that does and doesn't buy them, with one example of each.",
  "answer": "It buys them a map whose individual calls are safe from many threads: no corrupted structure, no lost entries from concurrent puts, reads that never block, and iteration that never throws. It does not make sequences of calls atomic. `if (map.get(k) == null) map.put(k, load(k))` can still load twice, and `map.put(k, map.get(k) + 1)` can still lose counts. Those need the per-key atomic methods: `computeIfAbsent` and `merge`. They should also keep those functions short, never touch the map inside them, and not use `size()` for decisions while other threads write."
 },
 "deeper": {
  "minutes": 10,
  "body": "Since JDK 8, `ConcurrentHashMap` is an array of bins. An empty bin is filled with a compare-and-set, with no lock. An update to a non-empty bin takes the monitor of the bin's first node with `synchronized`. That is why a long compute function blocks other writers in the same bin but nobody else. `computeIfAbsent` on an empty bin first installs a placeholder, a reservation node, and holds its lock while your function runs. A nested call that runs into a reservation node in the same thread is how the map detects many recursive updates and throws `Recursive update`.\n\nA bin that collects 8 or more entries turns into a small red-black tree, as long as the table has at least 64 bins, so a bad `hashCode` degrades lookups to logarithmic time instead of linear. When the table grows, threads that try to write during the resize help move bins to the new table instead of waiting for it.\n\nThe size is kept the way `LongAdder` keeps a count: a base value plus counter cells that threads update under contention. That is why `size()` can't be an exact snapshot while writers are busy, and why `mappingCount()`, which returns a `long`, is the method the Javadoc prefers.\n\nThe map also has bulk operations that most people never find: `forEach`, `search` and `reduce`, each with a `parallelismThreshold`. `settledCents.reduceValuesToLong(Long.MAX_VALUE, Long::longValue, 0L, Long::sum)` sums all values on the calling thread; a small threshold such as `1` lets it split the work over the common fork-join pool. Like the iterators, these see a weakly consistent view, so a total taken while payments settle is close but not exact."
 },
 "sources": [
  {"title": "ConcurrentHashMap.java at jdk-25-ga", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/ConcurrentHashMap.java"},
  {"title": "CopyOnWriteArrayList.java at jdk-25-ga", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/CopyOnWriteArrayList.java"},
  {"title": "BlockingQueue (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/BlockingQueue.html"},
  {"title": "Kotlin standard library: getOrPut (including the ConcurrentMap version)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.collections/get-or-put.html"},
  {"title": "Java Concurrency in Practice, Goetz et al., chapter 5", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/conc-09.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
