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

SHOOTOUT = """HashMap.merge                    total   200,410 of 800,000   keys 1,019 of 1,000   threw ConcurrentModificationException
ConcurrentHashMap get then put   total   797,768 of 800,000   keys 1,000 of 1,000
ConcurrentHashMap.merge          total   800,000 of 800,000   keys 1,000 of 1,000"""

J_CHM = """ConcurrentHashMap<String, Long> balances = new ConcurrentHashMap<>();

void deposit(String account, long cents) {
    balances.merge(account, cents, Long::sum);          // insert or add, atomically for this key
}

boolean open(String account) {
    return balances.putIfAbsent(account, 0L) == null;   // true only for the caller that opened it
}"""
K_CHM = """val balances = ConcurrentHashMap<String, Long>()

fun deposit(account: String, cents: Long) {
    balances.merge(account, cents, Long::plus)          // insert or add, atomically for this key
}

fun open(account: String): Boolean =
    balances.putIfAbsent(account, 0L) == null           // true only for the caller that opened it"""

J_ONE = """ConcurrentHashMap<String, BigDecimal> rates = new ConcurrentHashMap<>();

BigDecimal rate(String pair) {
    return rates.computeIfAbsent(pair, rateService::lookup);   // 120 ms, with the bin locked
}"""
K_ONE = """val rates = ConcurrentHashMap<String, BigDecimal>()

fun rate(pair: String): BigDecimal =
    rates.computeIfAbsent(pair, rateService::lookup)           // 120 ms, with the bin locked"""

J_FIB = """long fib(int n) {
    if (n < 2) return n;
    return memo.computeIfAbsent(n, k -> fib(k - 1) + fib(k - 2));   // calls computeIfAbsent again, inside
}"""
K_FIB = """fun fib(n: Int): Long {
    if (n < 2) return n.toLong()
    return memo.computeIfAbsent(n) { k -> fib(k - 1) + fib(k - 2) }   // calls computeIfAbsent again, inside
}"""

J_MEMO = """private final ConcurrentHashMap<String, CompletableFuture<BigDecimal>> rates = new ConcurrentHashMap<>();

BigDecimal rate(String pair) {
    // 1. claim the pair: the function only creates a future, so the bin is locked for microseconds
    CompletableFuture<BigDecimal> f = rates.computeIfAbsent(pair,
            p -> CompletableFuture.supplyAsync(() -> rateService.lookup(p), slowCalls));
    try {
        return f.join();                                  // 2. wait outside the map, with every other caller
    } catch (CompletionException e) {
        rates.remove(pair, f);                            // 3. failed: forget THIS future so a retry loads again
        throw e;
    }
}"""
K_MEMO = """private val rates = ConcurrentHashMap<String, CompletableFuture<BigDecimal>>()

fun rate(pair: String): BigDecimal {
    // 1. claim the pair: the function only creates a future, so the bin is locked for microseconds
    val f = rates.computeIfAbsent(pair) { p ->
        CompletableFuture.supplyAsync({ rateService.lookup(p) }, slowCalls)
    }
    try {
        return f.join()                                   // 2. wait outside the map, with every other caller
    } catch (e: CompletionException) {
        rates.remove(pair, f)                             // 3. failed: forget THIS future so a retry loads again
        throw e
    }
}"""

J_DRILL = """class DepositCounter {
    private final ConcurrentHashMap<String, LongAdder> byAccount = new ConcurrentHashMap<>();

    void record(String account) {
        byAccount.computeIfAbsent(account, a -> new LongAdder()).increment();
    }

    long count(String account) {
        LongAdder a = byAccount.get(account);
        return a == null ? 0 : a.sum();
    }
}"""
K_DRILL = """class DepositCounter {
    private val byAccount = ConcurrentHashMap<String, LongAdder>()

    fun record(account: String) {
        byAccount.computeIfAbsent(account) { LongAdder() }.increment()
    }

    fun count(account: String): Long = byAccount[account]?.sum() ?: 0L
}"""

TABLE = """| | Throws | Returns a special value | Waits | Waits, up to a time limit |
|---|---|---|---|---|
| Insert | `add(e)` | `offer(e)`: `false` if full | `put(e)` | `offer(e, time, unit)` |
| Remove | `remove()` | `poll()`: `null` if empty | `take()` | `poll(time, unit)` |
| Examine | `element()` | `peek()`: `null` if empty | | |"""

QUEUE_OUT = """add:            throws java.lang.IllegalStateException: Queue full
offer:          false
offer(300 ms):  false after 300 ms
put:            the waiter is WAITING until a slot opens
take:           ticket-1 (frees a slot)
queue now:      [ticket-2, ticket-3]
offer(null):    throws NullPointerException
new LinkedBlockingQueue<>() capacity: 2147483647
SynchronousQueue.offer with no taker waiting: false"""

def bin_box(i, cls="box", label=None):
    x = 40 + 76 * i
    return (f'<rect class="{cls}" x="{x}" y="100" width="64" height="44" rx="8"/>'
            f'<text class="t-s" x="{x + 32}" y="127" text-anchor="middle">{label or "bin " + str(i)}</text>')

FIG = (
    '<svg viewBox="0 0 680 250" role="img" aria-label="ConcurrentHashMap bins: teller A locks bin 3, teller B updates bin 6 at the same time, teller C waits for bin 3, teller D reads bin 1 without locking">'
    + "".join(bin_box(i, {3: "box-a", 6: "box-ok"}.get(i, "box")) for i in range(8))
    + '<rect class="box" x="215" y="20" width="170" height="36" rx="8"/>'
    '<text class="t t-code" x="300" y="43" text-anchor="middle">A: merge(acct-17)</text>'
    '<line class="ln-a" x1="300" y1="56" x2="300" y2="96" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="308" y="82">holds bin 3</text>'
    '<rect class="box" x="443" y="20" width="170" height="36" rx="8"/>'
    '<text class="t t-code" x="528" y="43" text-anchor="middle">B: merge(acct-42)</text>'
    '<line class="ln" x1="528" y1="56" x2="528" y2="96" marker-end="url(#arr)"/>'
    '<text class="t-s t-ok" x="536" y="82">other bin: no wait</text>'
    '<rect class="box" x="215" y="196" width="170" height="36" rx="8"/>'
    '<text class="t t-code" x="300" y="219" text-anchor="middle">C: merge(acct-90)</text>'
    '<line class="ln-bad" x1="300" y1="196" x2="300" y2="148" marker-end="url(#arr)"/>'
    '<text class="t-s t-bad" x="308" y="176">same bin: waits</text>'
    '<rect class="box" x="48" y="196" width="150" height="36" rx="8"/>'
    '<text class="t t-code" x="123" y="219" text-anchor="middle">D: get(acct-5)</text>'
    '<line class="ln-d" x1="123" y1="196" x2="123" y2="148" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="131" y="176">reads never lock</text>'
    '</svg>'
)

OPENING = """Picture the bank's book of accounts: one page per account number, with a balance on each page. In a program, that book is a map, a collection that finds a value by its key: here, the balance by its account number. On payday, eight tellers write in the book at once, each on its own thread, one line of work among several in the program.

In Race conditions: why count++ lies, a `ConcurrentHashMap` and one call, `merge`, kept every cent of those deposits. We took the map's word for it. A plain `HashMap` does worse than lose a few cents. In one run here, it lost three quarters of the deposits and counted 1,019 accounts in a bank that has 1,000. It also threw `ConcurrentModificationException`, a name that seems to blame two threads, though the same exception turns up in programs with only one.

The JDK's concurrent collections are built from the last two lessons' parts: locks and compare-and-set. In this lesson, we'll open the map to see why one call is safe, keep the work inside it short, decode that exception, and meet the kitchen's rail as a ready-made class. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Let's put three versions of the book through one test. `MapShootout` has eight tellers record 800,000 deposits across 1,000 accounts, counting one per deposit. It runs three times: on a plain `HashMap` with `merge`, on a `ConcurrentHashMap` with a `get` followed by a `put`, and on a `ConcurrentHashMap` with `merge`. One run printed:

```text
""" + SHOOTOUT + """
```

The `HashMap` kept a quarter of the deposits and found 19 accounts that nobody opened. In other runs it kept between 100,008 and 200,410, and threw every time. It was never built for more than one thread, and it never claimed to be. The concurrent map with `get` then `put` lost 2,232 deposits: every call was safe, and the gap between two calls was not, just as in Race conditions. Only `merge` was exact.

So why is one call safe? A hash map keeps an array of slots, called **bins**. A key's hash code, a number computed from the key, picks its bin, and every key whose hash lands there shares that bin. Picture the bank's old card files: a cabinet of drawers, each holding the cards for some of the account numbers. A clerk who updates a card opens one drawer. Another clerk can work in another drawer at the same time, but two clerks can't work in the same drawer at once.

`ConcurrentHashMap` works like that cabinet. A write locks only the bin its key lands in: while one thread holds a bin's lock, no other thread can write to that bin. So writes to different keys mostly run side by side. A write into an empty bin takes no lock at all: it uses compare-and-set, a write that happens only if nobody changed the slot first, as in the last lesson. And reads never lock. That's where the cabinet picture breaks: in the map, anyone may read any card at any moment, even one that a clerk is busy updating.

Every single-key call is atomic, done as one step that no other thread can split, because a write does its whole job inside one bin lock or one compare-and-set. Two calls in a row are two separate steps, and another thread's write can land between them. So the map offers methods that do a whole read-modify-write (read the value, change it, write it back) on one key in one call:

- `putIfAbsent(k, v)` inserts only if the key is missing.
- `computeIfAbsent(k, f)` computes and inserts only if the key is missing, and runs `f` at most once.
- `compute(k, f)` and `computeIfPresent(k, f)` replace the value with `f` of the old one.
- `merge(k, v, f)` inserts `v`, or replaces the old value with `f(old, v)`.
- `replace(k, expected, next)` is a compare-and-set on one key.

The Javadoc (the official API documentation) of each compute method says "The entire method invocation is performed atomically." That sentence is the reason to use them. Here are two of them at the bank:

""" + pair(J_CHM, K_CHM) + """

The figure shows why this scales. Two tellers who update accounts in different bins never meet. Two tellers who update the same account take turns, which is exactly what we want.

**One call is atomic for its key. Do the whole read-modify-write in that one call.**

Two more details. `ConcurrentHashMap` rejects `null` keys and values with `NullPointerException`. That's on purpose. When `get(k)` returns `null`, it always means "absent", so you never need a second call to tell "missing" from "mapped to null". A second call would be check-then-act: a check, then an action that assumes the check still holds. And `Collections.synchronizedMap(new HashMap<>())` is no substitute. It has one lock for the whole map, and the same gap between calls.

The function you hand to `merge` runs inside that bin lock, though. What happens when it's slow?"""

# ---------------------------------------------------------------- section 1
S1 = """The function you pass to `compute`, `merge` or `computeIfAbsent` runs while the map holds the lock on that key's bin. Three things follow from that.

First, other writes to the same bin wait for your whole function. The Javadoc says so: "Some attempted update operations on this map by other threads may be blocked while computation is in progress, so the computation should be short and simple." Remember the exchange-rate table from Explicit locks? On a `ConcurrentHashMap`, its load-once logic shrinks to one line:

""" + pair(J_ONE, K_ONE) + """

The read-write lock version had to let go, take the write lock and check again. Here the map does all of that, for one key. The catch is the loader, the function that fetches a missing rate. Say it calls a slow web service, a program on another computer that answers over the network, and the answer takes 120 ms. Then every write that lands in that bin waits 120 ms too. Reads aren't blocked. For a table that loads each pair once, that's often fine. When it isn't, the worked example shows how to keep the slow work outside the map.

Second, the function must not change the map. The Javadoc is blunt again: "The mapping function must not modify this map during computation." Memoized recursion is how people break this rule without noticing. That's a function that saves each answer in a map, so it never works out the same answer twice:

""" + pair(J_FIB, K_FIB) + """

On JDK 21, `ConcurrentHashMap` throws `IllegalStateException: Recursive update` here, and `HashMap` throws `ConcurrentModificationException`. The JDK catches only some of these cases, so don't count on an exception. Compute the value outside the map, or fill the table from the bottom up, smallest first.

Third, if the function throws, nothing is stored, and the exception reaches the caller, so the next call tries again. If it returns `null`, nothing is stored either. The lab relies on that.

**The function inside compute holds a lock. Keep it short, and leave the map alone.**

So far, single calls have changed the map. Loops over a collection that others are changing come next, and that's where the exception with the misleading name lives."""

# ---------------------------------------------------------------- section 2
S2 = """`ConcurrentModificationException` sounds like "two threads touched my collection". It means something narrower: this collection's own iterator noticed that the collection changed in a way the iterator didn't make. (An iterator is the object a for-each loop uses to step through a collection.) `ArrayList` and `HashMap` iterators are **fail-fast**. They keep a count of changes, and check it at every step.

Picture a careful bookkeeper reading down a list of payments. At every line he checks the page count, and if it changed, he stops and complains, even when he made the change himself. That's why one thread is enough to trip the check, as the warm-up showed. And he's careful, not watchful. When two threads really race, the check is only best effort. It may not fire at all, and you get lost entries or a damaged structure instead. Never treat the exception as a race detector.

The concurrent collections have **weakly consistent** iterators instead. They never throw `ConcurrentModificationException`, and they show the collection as it was at some point at or after the moment the loop began. A change made during the loop may or may not show up.

The same goes for `size()`, `isEmpty()` and `containsValue()` on `ConcurrentHashMap`. While other threads update the map, they describe a moving target. The Javadoc calls them useful for monitoring and estimation, not for program control. So `if (balances.size() < 10_000) balances.put(k, v)` is check-then-act on an estimate.

`CopyOnWriteArrayList` takes the opposite trade. Every write copies the whole array. Every loop walks the array as it was when the loop started, so a loop never locks and never throws. Remember the listeners from synchronized and intrinsic locks, the pieces of code that ask to hear about every new balance? A list of them changes rarely and is read on every deposit, which suits a copy-on-write list perfectly. It's terrible for a list that grows with traffic, though: adding the 100,000th element copies 100,000 references. Its set cousin is `CopyOnWriteArraySet`, and `ConcurrentSkipListMap` is the concurrent map that keeps its keys sorted.

**The exception is a bookkeeping check, not a race detector. Never count on it to find races.**

Maps and lists hold data that threads share. The last collection in this lesson moves work from one thread to another, and you've already built it by hand."""

# ---------------------------------------------------------------- section 3
S3 = """In wait, notify and guarded blocks, we built the kitchen's rail by hand. Waiters put order tickets on, cooks take them off, and each side waits when it must. In Explicit locks, we rebuilt it with two `Condition`s. `ArrayBlockingQueue` is the version that comes with the JDK. A **blocking queue** is a queue whose put and take wait when it's full or empty, and every `BlockingQueue` offers four ways to add and remove:

""" + TABLE + """

Pick the column by what the caller should do when the rail is full or empty. A waiter with a customer at the table might use `offer` and get an answer now. A cook with nothing else to do uses `take`, and sleeps until a ticket arrives. Queues reject `null`, because `poll` uses `null` to mean "empty".

`QueueMethods` tries each column on a rail with room for two tickets. One run printed:

```text
""" + QUEUE_OUT + """
```

Each of the first five lines matches its column in the table. The last two are the surprises, and the list of implementations explains them:

- `ArrayBlockingQueue` has a fixed capacity, backed by one array and one lock.
- `LinkedBlockingQueue` takes an optional capacity, and the default is `Integer.MAX_VALUE`, over two billion. That's unbounded in practice. It uses separate locks for the head and the tail, so waiters and cooks get in each other's way less.
- `SynchronousQueue` has no capacity at all. Each `put` waits for a `take`, and an `offer` with no cook waiting returns `false`.
- `PriorityBlockingQueue` orders by priority and is unbounded. `DelayQueue` releases each element only when its delay has passed.

That default capacity is the trap. `new LinkedBlockingQueue<>()` looks harmless, and its `put` never waits, so it passes every test. Then one evening the cooks slow down, the waiters keep adding, and the rail grows to millions of tickets. The heap, the memory where Java keeps its objects, fills up, and the program dies, taking every waiting ticket with it.

A queue with a capacity gives you **backpressure** instead, the term from the kitchen lesson. When the cooks fall behind, `put` makes the waiters wait, or `offer` tells them to come back later. The program slows down instead of filling memory.

**Give every queue between threads a capacity. Decide on purpose what a full queue means.**

`drainTo(list, max)` moves everything already queued in one call, without waiting, which is how you take work in batches. The lab's `Batcher` uses exactly that pair: `poll` with a timeout for the first entry, then `drainTo` for the rest. The executors track meets the same unbounded queue again, hidden inside `Executors.newFixedThreadPool`, a ready-made thread pool (a fixed group of threads that runs the tasks you hand it).

That's where collections stop. Each one makes a call safe, or moves work between threads. None of them can make a thread wait until five others are ready, or let only three threads in at a time."""

ASIDE3 = {
    "title": "Why have a SynchronousQueue, if it holds nothing?",
    "body": "Because sometimes you want a hand-off, not storage. With a `SynchronousQueue`, a waiter hands the ticket straight to a cook and waits until one takes it, so nothing ever piles up on the rail. `Executors.newCachedThreadPool` uses one for exactly that reason: each new task either goes straight to an idle thread, or the pool starts a new thread for it. The executors track looks inside that pool."
}

L = {
 "id": "conc-09",
 "title": "Concurrent collections",
 "minutes": 37,
 "goal": "By the end you can pick the right concurrent collection for a job, use `ConcurrentHashMap`'s atomic per-key methods correctly, and explain what weakly consistent iteration and `ConcurrentModificationException` really mean.",
 "opening": OPENING,
 "warmup": {
  "q": "A single thread loops over an `ArrayList` with for-each and calls `list.remove(item)` for one of the items. No other thread exists. What happens?",
  "options": ["It works: `ConcurrentModificationException` needs two threads", "It throws `ConcurrentModificationException`", "It quietly skips the rest of the list", "It deadlocks"],
  "answer": 1,
  "why": "The exception has nothing to do with threads. The list's iterator keeps a count of changes, and its next step sees that the list changed behind its back. One thread is enough. The opposite surprise is worse: when two threads really do race on an `ArrayList`, the check is only best effort, so you may get lost or damaged data with no exception at all. The third section explains both."
 },
 "sections": [
  {
   "h": "Inside the map: why ConcurrentHashMap is safe one key at a time",
   "body": S0,
   "figure": {"svg": FIG, "caption": "Writes lock one bin, not the map. Tellers A and B update different bins at the same time. C waits only because its account lands in A's bin. Reads never lock."},
   "try": {
    "title": "Three maps, one count",
    "minutes": 3,
    "steps": [
     "Read `MapShootout`. Eight tellers record 800,000 deposits across 1,000 accounts: on a `HashMap` with `merge`, on a `ConcurrentHashMap` with get-then-put, and on a `ConcurrentHashMap` with `merge`.",
     "Predict the total and the number of keys for each.",
     "Run it twice."
    ],
    "code": code("MapShootout"),
    "expect": "The `HashMap` loses most of the counts, and one of its threads dies with `ConcurrentModificationException` (`HashMap.merge` notices that the map changed while it worked). In runs here it kept 100,008 to 200,410 of 800,000, and sometimes reported more than 1,000 keys. `ConcurrentHashMap` with get-then-put loses a few thousand: every call is safe, the pair isn't. Only `ConcurrentHashMap.merge` gives exactly 800,000."
   },
   "refs": [
    {"title": "ConcurrentHashMap.java at jdk-25-ga (compute and merge contracts)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/ConcurrentHashMap.java", "kind": "read"}
   ]
  },
  {
   "h": "Keeping the work inside compute short, and never touching the map from it",
   "body": S1,
   "try": {
    "title": "Break the rule on purpose",
    "minutes": 2,
    "steps": [
     "Run `RecursiveUpdate`. It works out `fib(30)` with memoized recursion on a `ConcurrentHashMap`, then on a `HashMap`, then from the bottom up.",
     "Read the exception messages. Which map tells you what you did wrong?"
    ],
    "code": code("RecursiveUpdate"),
    "expect": "`ConcurrentHashMap: threw java.lang.IllegalStateException: Recursive update`, `HashMap: threw java.util.ConcurrentModificationException`, and `bottom-up: fib(30) = 832040`. Only the version that fills the table outside any compute call works."
   }
  },
  {
   "h": "What ConcurrentModificationException really means: fail-fast and weakly consistent iterators",
   "body": S2,
   "try": {
    "title": "Trip a fail-fast iterator with one thread",
    "minutes": 3,
    "steps": [
     "Read `FailFast`. It changes an `ArrayList`, a `ConcurrentHashMap` and a `CopyOnWriteArrayList` while looping over each one, all on the main thread.",
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
   "h": "The kitchen's rail, ready-made: BlockingQueue and backpressure",
   "body": S3,
   "aside": ASIDE3,
   "try": {
    "title": "Fill the rail every way you can",
    "minutes": 3,
    "steps": [
     "Read `QueueMethods`. It fills an `ArrayBlockingQueue` with room for 2 tickets, then tries `add`, `offer`, timed `offer` and `put` on the full rail.",
     "Predict each line, including the capacity of a `LinkedBlockingQueue` built with no arguments.",
     "Run it."
    ],
    "code": code("QueueMethods"),
    "expect": "`add` throws `IllegalStateException: Queue full`, `offer` returns `false` at once, the timed `offer` returns `false` after about 300 ms, and the waiter in `put` is `WAITING` until `take` frees a slot. The no-argument `LinkedBlockingQueue` reports a capacity of 2,147,483,647. `SynchronousQueue.offer` returns `false` because no cook is waiting to take."
   },
   "refs": [
    {"title": "BlockingQueue (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/BlockingQueue.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "Load-once caching in Java and Kotlin",
  "java": {"title": "Java", "src": """ConcurrentHashMap<String, BigDecimal> rates = new ConcurrentHashMap<>();

BigDecimal rate(String pair) {
    return rates.computeIfAbsent(pair, rateService::lookup);   // lookup runs at most once per pair
}"""},
  "kotlin": {"title": "Kotlin", "src": """val rates = ConcurrentHashMap<String, BigDecimal>()

fun rate(pair: String): BigDecimal =
    rates.getOrPut(pair) { rateService.lookup(pair) }          // atomic put, but lookup may run several times

fun rateOnce(pair: String): BigDecimal =
    rates.computeIfAbsent(pair) { rateService.lookup(it) }     // lookup runs at most once per pair"""},
  "note": "Kotlin's usual `getOrPut` is the trap. The standard library has a special version for `ConcurrentMap` that uses `putIfAbsent`, so it never overwrites a value that is already there. But its documentation says the default function \"may be invoked even if the key is already in the map\". With 8 threads racing for one new key, the lookup ran 8 times in a check here, against once for `computeIfAbsent`. And if the variable's declared type is plain `MutableMap`, Kotlin picks the general `getOrPut`, which is a check followed by a put with no atomicity at all. Use `computeIfAbsent` when the loader is slow or must run once. Kotlin's types do help in one place: a `ConcurrentHashMap<String, BigDecimal>` can't be handed a `null` value, so the `NullPointerException` that Java callers can hit becomes a compile error."
 },
 "worked": {
  "title": "Load once, without holding the bin for 120 ms",
  "steps": [
   {"say": "The rate service takes 120 ms to answer. This table loads each currency pair once, which is good. But while it loads, every other write that lands in the same bin waits, and the Javadoc asks for short functions. The goal: keep the map call tiny and do the slow work outside it, while still loading each pair once.",
    "code": J_ONE, "lang": "java", "alt_code": K_ONE, "alt_lang": "kotlin"},
   {"say": "Store the *promise* of a value instead of the value. A `CompletableFuture` is that promise: a box that will hold a result later, and anyone can wait for the result with `join()`. The function inside `computeIfAbsent` now only creates the box and starts the lookup on `slowCalls`, a thread pool kept for slow calls. That takes microseconds, so the bin is free again almost at once. Every caller for the pair gets the same box and waits on it outside the map.",
    "code": J_MEMO, "lang": "java", "alt_code": K_MEMO, "alt_lang": "kotlin"},
   {"say": "Before reading on, explain to yourself: why `remove(pair, f)` with two arguments, and not `remove(pair)`? Answer: between the failure and the remove, another thread may already have put a fresh future in place of the failed one. The two-argument `remove` deletes the entry only if it still maps to the future that failed. It's a compare-and-set on one key, and it keeps you from throwing away someone else's good load.", "code": "", "lang": ""},
   {"say": "This is the Memoizer from *Java Concurrency in Practice*, section 5.6, written with `CompletableFuture`. One gap is left: entries never expire, so yesterday's rate stays in the table until the program restarts. If you write services, a caching library with expiry and loading in the background does all this for you. Writing it once by hand shows you what such a library does, and what to look for when it misbehaves.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Three concurrent-collection fixes",
  "minutes": 14,
  "files": [f"{lab}/main/{P}/BinCache.java", f"{lab}/main/{P}/WebhookRegistry.java", f"{lab}/main/{P}/Batcher.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l09.*'",
  "steps": [
   "Run the tests. Six of eight fail: `BinCache` calls its loader 8 times for one key, `WebhookRegistry` throws `ConcurrentModificationException` (once even with a single thread), and `Batcher` throws `UnsupportedOperationException`.",
   "`BinCache` remembers which bank issued each kind of card. The first six digits of a card number, called the BIN, say which bank issued it, and the loader asks a slow service. Fix `issuerFor` with one `ConcurrentHashMap` call, so the loader runs once per BIN.",
   "`WebhookRegistry` keeps the list of listeners that hear about every payment. (It's named after webhooks, the web addresses that shops give a bank so it can tell them about each payment.) Fix it by changing the type of collection it uses. You don't need a lock.",
   "`Batcher` collects entries from many threads and hands them to one writer thread in groups, so the writer can save 100 at a time instead of one. Write it on an `ArrayBlockingQueue`. `submit` uses `offer`. `nextBatch` waits with `poll(timeout)` for the first entry, then calls `drainTo(batch, max - 1)`.",
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
  "prompt": "Close this page. Write `DepositCounter` with `record(String account)` and `long count(String account)`, safe for many threads, using a `ConcurrentHashMap` and one `LongAdder` per account. Then check: can two threads ever create two adders for the same account?",
  "answer": {"lang": "java", "src": J_DRILL, "alt": {"lang": "kotlin", "title": "Kotlin", "src": K_DRILL}}
 },
 "recap": [
  "`ConcurrentHashMap` locks one bin per write and never locks for reads. Single calls are atomic for their key; a sequence of calls is not.",
  "Use `computeIfAbsent`, `compute`, `merge`, `putIfAbsent` and the two-argument `remove` and `replace` for a read-modify-write on one key.",
  "The function inside a compute call runs under the bin's lock: keep it short, and never change the map from inside it.",
  "`ConcurrentModificationException` is a fail-fast iterator's check, often tripped by one thread. Concurrent collections never throw it; their iterators and `size()` are weakly consistent.",
  "`CopyOnWriteArrayList` suits small lists that change rarely and are looped over often, such as listeners. Use a `BlockingQueue` with a capacity to hand work between threads.",
  "The limit: one call is atomic for one key, and the no-argument `LinkedBlockingQueue` has no real limit. A change across two keys, such as a transfer, still needs a lock or one swapped object."
 ],
 "closing": "We started with eight tellers writing in the bank's book of accounts, and a `HashMap` that lost three quarters of their deposits. Inside `ConcurrentHashMap`, each write locks one bin, so one call is atomic for its key and two calls are not. We kept the work inside `compute` short, found that the exception with the alarming name is a bookkeeper's check, and gave the kitchen's rail a capacity.\n\nNow search your own code for `new LinkedBlockingQueue<>()` with nothing between the brackets. Each one is a rail with no end.\n\nNext, we'll make threads wait for each other instead of for a lock: a latch, a barrier, a semaphore and a phaser. How does a program say \"start when everyone is ready\"?",
 "quiz": [
  {"q": "From Atomics and compare-and-set: sixteen threads count deposits per account, and about 200 accounts get most of the traffic. Which is the best fit?",
   "options": ["`HashMap<String, Long>` with `merge`", "`ConcurrentHashMap<String, LongAdder>` with `computeIfAbsent(k, x -> new LongAdder()).increment()`", "`ConcurrentHashMap<String, Long>` with `put(k, get(k) + 1)`", "`Collections.synchronizedMap(new HashMap<>())` with `merge`"],
   "answer": 1, "why": "`computeIfAbsent` creates each adder once, and after that every increment goes to a `LongAdder`, which spreads a busy account over several cells. `merge` on a `ConcurrentHashMap<String, Long>` would also be correct, just with more contention on the busy accounts. A plain `HashMap` breaks, get-then-put loses updates, and a synchronized map makes every thread wait on one lock.",
   "from": "conc-08"},
  {"q": "Why does `ConcurrentHashMap` throw `NullPointerException` for `put(k, null)`?",
   "options": ["So that `get(k) == null` always means the key is absent, with no second call needed", "Because nulls would damage its bins", "It doesn't: only null keys are rejected", "To save memory"],
   "answer": 0, "why": "If null values were allowed, `get` returning null would be ambiguous, and telling \"absent\" from \"mapped to null\" would need `containsKey` as well. Two calls is check-then-act, which another thread can break. Banning null removes the question."},
  {"q": "A cache uses `map.computeIfAbsent(id, k -> loadAccount(k))`, and `loadAccount` calls `map.computeIfAbsent(parentId, ...)` on the same map. What should you expect?",
   "options": ["It works, because the two keys differ", "A deadlock every time", "It breaks the documented contract; `ConcurrentHashMap` may throw `IllegalStateException: Recursive update`, or misbehave", "A `ConcurrentModificationException` from an iterator"],
   "answer": 2, "why": "The Javadoc says the mapping function must not modify the map. Whether the JDK notices depends on where the keys land, so sometimes it throws `Recursive update` and sometimes it seems to work. Don't rely on either. Load the parent first, outside the compute call."},
  {"q": "A list of five listeners, pieces of code that hear about every new balance, changes only when the program is updated. It's looped over on each of 3,000 deposits a second, from many threads. Which collection fits?",
   "options": ["`ArrayList` guarded by `synchronized` around every loop", "`Collections.synchronizedList(new ArrayList<>())`", "`ConcurrentLinkedQueue`", "`CopyOnWriteArrayList`"],
   "answer": 3, "why": "Reads far outnumber writes and the list is tiny, so copying the array on each rare write is cheap, and every loop runs without a lock over a snapshot that can't change. The synchronized options make every deposit take a lock for the whole loop. A queue would work for looping, but it doesn't model a list you add to and remove from as cleanly."},
  {"q": "Request threads put ledger entries into `new LinkedBlockingQueue<>()`, and a single writer thread saves them to a database. One evening the database slows down. What happens?",
   "options": ["`put` makes the request threads wait once the queue holds 10,000 entries", "The queue grows without limit, because the default capacity is `Integer.MAX_VALUE`, until memory runs out", "`put` throws `IllegalStateException` when the queue is full", "The writer thread speeds up to match"],
   "answer": 1, "why": "With no capacity, the queue never fills, so nothing pushes back on the request threads. Memory grows until the program dies, taking the queued entries with it. Give the queue a capacity, so `put` makes the producers wait, or `offer` fails and they can answer \"try again later\"."}
 ],
 "flashcards": [
  {"front": "What does `ConcurrentHashMap.computeIfAbsent(k, f)` guarantee?", "back": "The whole call is atomic for that key: if `k` is absent, `f` runs at most once and its result is stored. Other updates to the same bin wait while `f` runs."},
  {"front": "Can a `ConcurrentHashMap` hold null keys or null values?", "back": "No. Both throw `NullPointerException`, so `get(k) == null` always means \"absent\"."},
  {"front": "What happens if the function passed to `computeIfAbsent` changes the same map?", "back": "It breaks the contract. `ConcurrentHashMap` may throw `IllegalStateException: Recursive update`; `HashMap` may throw `ConcurrentModificationException`; sometimes nothing is caught."},
  {"front": "Is `ConcurrentHashMap.size()` exact while other threads update it?", "back": "No. It is an estimate of a moving target: fine for monitoring, wrong for decisions."},
  {"front": "What does a `ConcurrentHashMap` iterator do if the map changes during the loop?", "back": "It never throws. It is weakly consistent: changes made during the loop may or may not appear."},
  {"front": "On a full `ArrayBlockingQueue`, what do `offer(e)` and `put(e)` do?", "back": "`offer(e)` returns `false` at once. `put(e)` waits until there is space (and throws `InterruptedException` if interrupted)."},
  {"front": "What is the capacity of `new LinkedBlockingQueue<>()`?", "back": "`Integer.MAX_VALUE`: unbounded in practice. Pass a capacity to get backpressure."}
 ],
 "terms": [
  {"term": "ConcurrentHashMap", "plain": "A thread-safe hash map that locks one bin per write and never locks for reads."},
  {"term": "Bin", "plain": "One slot of a hash table; keys whose hashes land in the same slot share it."},
  {"term": "Fail-fast iterator", "plain": "An iterator that throws `ConcurrentModificationException` when it notices its collection changed; best effort only."},
  {"term": "Weakly consistent iterator", "plain": "An iterator that never throws and may or may not show changes made while it runs."},
  {"term": "CopyOnWriteArrayList", "plain": "A list that copies its whole array on every write, so readers can loop over a snapshot without locks."},
  {"term": "BlockingQueue", "plain": "A queue whose `put` and `take` wait when it is full or empty, used to hand work between threads."},
  {"term": "Backpressure", "plain": "Slowing down or turning away producers when consumers fall behind, instead of storing work without limit."}
 ],
 "explain_back": {
  "prompt": "A teammate says: \"We switched to ConcurrentHashMap, so our cache and counters are thread-safe now.\" Explain what that does and doesn't buy them, with one example of each.",
  "answer": "It buys them a map whose individual calls are safe from many threads: no damaged structure, no lost entries from puts that happen at the same time, reads that never wait, and loops that never throw. It does not make a sequence of calls atomic. `if (map.get(k) == null) map.put(k, load(k))` can still load twice, and `map.put(k, map.get(k) + 1)` can still lose counts. Those need the per-key atomic methods, `computeIfAbsent` and `merge`. They should also keep those functions short, never change the map inside them, and not use `size()` for decisions while other threads write."
 },
 "deeper": {
  "minutes": 10,
  "body": "Since JDK 8, `ConcurrentHashMap` is an array of bins. An empty bin is filled with a compare-and-set, with no lock. An update to a bin that already holds entries takes the monitor of the bin's first node with `synchronized`. That's why a long compute function blocks other writers in the same bin but nobody else. `computeIfAbsent` on an empty bin first puts in a placeholder, a reservation node, and holds its lock while your function runs. A nested call on the same thread that runs into that reservation node is how the map detects many recursive updates and throws `Recursive update`.\n\nA bin that collects 8 or more entries turns into a small red-black tree (a kind of sorted tree that stays balanced), as long as the table has at least 64 bins. So a bad `hashCode` slows lookups to logarithmic time instead of linear. When the table grows, threads that try to write during the resize help move bins to the new table instead of waiting for it.\n\nThe size is kept the way `LongAdder` keeps a count: a base value plus counter cells that threads update when they collide. That's why `size()` can't be an exact snapshot while writers are busy, and why `mappingCount()`, which returns a `long`, is the method the Javadoc prefers.\n\nThe map also has bulk operations that most people never find: `forEach`, `search` and `reduce`, each with a `parallelismThreshold`. `balances.reduceValuesToLong(Long.MAX_VALUE, Long::longValue, 0L, Long::sum)` adds up all the balances on the calling thread; a small threshold such as `1` lets it split the work over the common fork-join pool, the JVM's shared group of worker threads. Like the iterators, these see a weakly consistent view, so a total taken while deposits arrive is close but not exact."
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
