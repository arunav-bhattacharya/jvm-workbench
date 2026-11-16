import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/concurrency/src"
P = "java/workbench/concurrency/l07"
K = "kotlin/workbench/concurrency/l07"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"./gradlew :concurrency:demo -Pmain=workbench.concurrency.l07.{name}"
def jv(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": demo(name), "file": f"{lab}/demo/{P}/{name}.java"}
def kt(name):
    """The Kotlin twin of a Java demo: Foo.kt with a top-level main, class FooKt."""
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
            "run": demo(f"{name}Kt"), "file": f"{lab}/demo/{K}/{name}.kt"}
def code(name):
    c = jv(name)
    c["alt"] = kt(name)
    return c
def pair(java, kotlin):
    """A Java fence followed by its Kotlin twin, as the brief asks."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

J_IDIOM = """private final ReentrantLock lock = new ReentrantLock();
private final List<Entry> entries = new ArrayList<>();   // the ledger's entries, guarded by lock

void post(Entry e) {
    lock.lock();               // before the try, never inside it
    try {
        entries.add(e);
    } finally {
        lock.unlock();         // first line of finally: runs even if add throws
    }
}"""
K_IDIOM = """private val lock = ReentrantLock()
private val entries = mutableListOf<Entry>()       // the ledger's entries, guarded by lock

fun post(e: Entry) {
    lock.withLock {            // kotlin.concurrent: lock(), try, finally unlock()
        entries += e
    }
}"""

J_PUT = """private final ReentrantLock lock = new ReentrantLock();
private final Condition notFull = lock.newCondition();    // waiters wait here for a free slot
private final Condition notEmpty = lock.newCondition();   // cooks wait here for a ticket

public void put(T ticket) throws InterruptedException {
    lock.lock();
    try {
        while (items.size() == capacity) notFull.await();   // lets go of the lock while waiting
        items.addLast(ticket);
        notEmpty.signal();                                   // wake one cook
    } finally {
        lock.unlock();
    }
}"""
K_PUT = """private val lock = ReentrantLock()
private val notFull = lock.newCondition()      // waiters wait here for a free slot
private val notEmpty = lock.newCondition()     // cooks wait here for a ticket

fun put(ticket: T) = lock.withLock {
    while (items.size == capacity) notFull.await()   // lets go of the lock while waiting
    items.addLast(ticket)
    notEmpty.signal()                                 // wake one cook
}"""

J_RW = """private final ReentrantReadWriteLock rw = new ReentrantReadWriteLock();
private final Map<String, BigDecimal> rates = new HashMap<>();   // guarded by rw

BigDecimal rate(String pair) {
    rw.readLock().lock();                 // many threads can hold this at once
    try {
        return rates.get(pair);
    } finally {
        rw.readLock().unlock();
    }
}

void refresh(Map<String, BigDecimal> fresh) {
    rw.writeLock().lock();                // waits until no reader and no writer holds the lock
    try {
        rates.clear();
        rates.putAll(fresh);
    } finally {
        rw.writeLock().unlock();
    }
}"""
K_RW = """private val rw = ReentrantReadWriteLock()
private val rates = HashMap<String, BigDecimal>()    // guarded by rw

fun rate(pair: String): BigDecimal? = rw.read {     // many threads can hold this at once
    rates[pair]
}

fun refresh(fresh: Map<String, BigDecimal>) = rw.write {   // waits until no reader and no writer holds the lock
    rates.clear()
    rates.putAll(fresh)
}"""

J_UPGRADE = """// Naive: hangs the first time a pair is missing
rw.readLock().lock();
try {
    BigDecimal r = rates.get(pair);
    if (r != null) return r;
    rw.writeLock().lock();         // waits for every reader to leave, this thread included: forever
    try {
        r = loader.apply(pair);
        rates.put(pair, r);
        return r;
    } finally {
        rw.writeLock().unlock();
    }
} finally {
    rw.readLock().unlock();
}"""
K_UPGRADE = """// Naive: hangs the first time a pair is missing
rw.readLock().lock()
try {
    val r = rates[pair]
    if (r != null) return r
    rw.writeLock().lock()         // waits for every reader to leave, this thread included: forever
    try {
        return loader(pair).also { rates[pair] = it }
    } finally {
        rw.writeLock().unlock()
    }
} finally {
    rw.readLock().unlock()
}"""

DUMP = """"main" #1 ... waiting on condition
   java.lang.Thread.State: WAITING (parking)
	at jdk.internal.misc.Unsafe.park(java.base@21.0.12.1/Native Method)
	- parking to wait for  <0x0000000737818bc0> (a java.util.concurrent.locks.ReentrantReadWriteLock$NonfairSync)
	...
	at java.util.concurrent.locks.ReentrantReadWriteLock$WriteLock.lock(java.base@21.0.12.1/ReentrantReadWriteLock.java:959)
	at workbench.concurrency.l07.UpgradeDeadlock.main(UpgradeDeadlock.java:22)

   Locked ownable synchronizers:
	- None"""

J_OPT = """long stamp = lock.tryOptimisticRead();   // 1. no lock, just a version number
long b = buy, s = sell;                  // 2. copy both prices into locals
if (!lock.validate(stamp)) {             // 3. a writer got in: the copies may be torn
    stamp = lock.readLock();             // 4. fall back to a real read lock
    try { b = buy; s = sell; } finally { lock.unlockRead(stamp); }
}
return new EuroPrices(b, s);             // 5. use the locals only after validate"""
K_OPT = """var stamp = lock.tryOptimisticRead()     // 1. no lock, just a version number
var b = buy; var s = sell                // 2. copy both prices into locals
if (!lock.validate(stamp)) {             // 3. a writer got in: the copies may be torn
    stamp = lock.readLock()              // 4. fall back to a real read lock
    try { b = buy; s = sell } finally { lock.unlockRead(stamp) }
}
return EuroPrices(b, s)                  // 5. use the locals only after validate"""

J_ACCT = """class AccountLocks {
    private final ConcurrentHashMap<String, ReentrantLock> locks = new ConcurrentHashMap<>();

    <T> T withAccount(String accountId, Duration maxWait, Supplier<T> action) throws InterruptedException {
        // 1. one lock per account, created at most once
        ReentrantLock lock = locks.computeIfAbsent(accountId, id -> new ReentrantLock());
        // 2. wait a bounded time; an interrupt also ends the wait
        if (!lock.tryLock(maxWait.toNanos(), TimeUnit.NANOSECONDS)) {
            throw new AccountBusyException(accountId);    // 3. busy: give up, the caller tries again later
        }
        try {
            return action.get();                          // 4. critical section
        } finally {
            lock.unlock();                                // 5. always release
        }
    }
}"""
K_ACCT = """class AccountLocks {
    private val locks = ConcurrentHashMap<String, ReentrantLock>()

    fun <T> withAccount(accountId: String, maxWait: Duration, action: () -> T): T {
        // 1. one lock per account, created at most once
        val lock = locks.computeIfAbsent(accountId) { ReentrantLock() }
        // 2. wait a bounded time; an interrupt also ends the wait
        if (!lock.tryLock(maxWait.toNanos(), TimeUnit.NANOSECONDS)) {
            throw AccountBusyException(accountId)         // 3. busy: give up, the caller tries again later
        }
        try {
            return action()                               // 4. critical section
        } finally {
            lock.unlock()                                 // 5. always release
        }
    }
}"""
J_STRIPE = """private final ReentrantLock[] stripes = new ReentrantLock[256];
{
    for (int i = 0; i < stripes.length; i++) stripes[i] = new ReentrantLock();
}

ReentrantLock lockFor(String accountId) {
    return stripes[Math.floorMod(accountId.hashCode(), stripes.length)];   // two accounts may share a stripe: fine
}"""
K_STRIPE = """private val stripes = Array(256) { ReentrantLock() }

fun lockFor(accountId: String): ReentrantLock =
    stripes[Math.floorMod(accountId.hashCode(), stripes.size)]          // two accounts may share a stripe: fine"""

J_DRILL = """class Buffer<T> {
    private final ReentrantLock lock = new ReentrantLock();
    private final Condition notFull = lock.newCondition();
    private final Condition notEmpty = lock.newCondition();
    private final Deque<T> items = new ArrayDeque<>();
    private final int capacity;

    Buffer(int capacity) { this.capacity = capacity; }

    void put(T item) throws InterruptedException {
        lock.lock();
        try {
            while (items.size() == capacity) notFull.await();
            items.addLast(item);
            notEmpty.signal();
        } finally {
            lock.unlock();
        }
    }

    T take() throws InterruptedException {
        lock.lock();
        try {
            while (items.isEmpty()) notEmpty.await();
            T head = items.removeFirst();
            notFull.signal();
            return head;
        } finally {
            lock.unlock();
        }
    }
}"""
K_DRILL = """class Buffer<T>(private val capacity: Int) {
    private val lock = ReentrantLock()
    private val notFull = lock.newCondition()
    private val notEmpty = lock.newCondition()
    private val items = ArrayDeque<T>()

    fun put(item: T) = lock.withLock {
        while (items.size == capacity) notFull.await()
        items.addLast(item)
        notEmpty.signal()
    }

    fun take(): T = lock.withLock {
        while (items.isEmpty()) notEmpty.await()
        items.removeFirst().also { notFull.signal() }
    }
}"""

FIG = (
    '<svg viewBox="0 0 680 250" role="img" aria-label="One ReentrantLock with a line of threads that want it and two condition queues: waiters wait on notFull, cooks wait on notEmpty">'
    '<rect class="box" x="40" y="20" width="240" height="60" rx="8"/>'
    '<text class="t" x="160" y="45" text-anchor="middle">entry queue</text>'
    '<text class="t-s t-m" x="160" y="66" text-anchor="middle">W5, C2: want the lock</text>'
    '<rect class="box-a" x="400" y="20" width="240" height="60" rx="8"/>'
    '<text class="t" x="520" y="45" text-anchor="middle">lock owner: W1</text>'
    '<text class="t-s t-m" x="520" y="66" text-anchor="middle">running put()</text>'
    '<line class="ln" x1="280" y1="50" x2="396" y2="50" marker-end="url(#arr)"/>'
    '<text class="t-s t-code" x="338" y="42" text-anchor="middle">lock()</text>'
    '<rect class="box-ok" x="40" y="170" width="260" height="60" rx="8"/>'
    '<text class="t t-code" x="170" y="195" text-anchor="middle">notEmpty</text>'
    '<text class="t-s" x="170" y="216" text-anchor="middle">cooks C1, C3 wait here</text>'
    '<rect class="box-b" x="380" y="170" width="260" height="60" rx="8"/>'
    '<text class="t t-code" x="510" y="195" text-anchor="middle">notFull</text>'
    '<text class="t-s" x="510" y="216" text-anchor="middle">waiters W2, W4 wait here</text>'
    '<line class="ln-a" x1="560" y1="80" x2="560" y2="166" marker-end="url(#arr)"/>'
    '<text class="t-s t-a t-code" x="572" y="120">await()</text>'
    '<text class="t-s t-m" x="572" y="138">lets go, parks</text>'
    '<line class="ln-a" x1="120" y1="170" x2="120" y2="84" marker-end="url(#arr)"/>'
    '<text class="t-s t-a t-code" x="132" y="120">signal()</text>'
    '<text class="t-s t-m" x="132" y="138">one waiter moves up</text>'
    '</svg>'
)

OPENING = """Picture the bank at the end of the day. A batch job, a program that works through a long list in one go, adds the day's interest to every account. It runs on its own thread, one line of work among several in the program. For a second and a half, it holds the lock on the ledger, the bank's book of balances. A lock lets one thread at a time in.

Just then, a customer at a cash machine asks for her balance. With `synchronized`, her request joins the line for the lock and stays there. It can't give up after 200 ms and ask her to try again, and even a shutdown can't call it back. So she watches a spinning wheel the whole time.

Deadlock, livelock and starvation ended with a lock that can give up. `ReentrantLock` is that lock, and switching takes one line. It's almost too easy: unlike `synchronized`, it never lets go by itself.

In this lesson, we'll wait for a busy lock three ways, give each kind of waiting thread its own waiting room, and let readers share a lock, or skip it. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """In synchronized and intrinsic locks, we pictured a lock as the key to the bank's vault: one door, one key, and a line of threads outside. `synchronized` gives that line no choices. A thread that joins it waits until the key comes back, however long that takes. It can't give up after a timeout. An interrupt, another thread's request that it stop, doesn't reach it until it holds the key.

`ReentrantLock`, from `java.util.concurrent.locks`, is the same vault with controls on the door. Like `synchronized`, it lets one thread in at a time, and the next owner sees every write the last owner made. It's reentrant too: the owner can take it again, and the lock counts the holds. Unlike `synchronized`, it gives a waiting thread choices:

- `tryLock()` takes the lock only if it's free right now, and returns `false` otherwise.
- `tryLock(200, MILLISECONDS)` waits at most 200 ms. The last lesson used it to break deadlocks, where threads wait for each other forever.
- `lockInterruptibly()` waits, but leaves the line with `InterruptedException` when the thread is interrupted.
- `new ReentrantLock(true)` makes a fair lock, which hands the lock to the thread that has waited longest.

`TryLockDemo` plays out the evening from the opening. The `interest` thread holds the ledger lock for 1.5 seconds. Older code in the bank still guards the ledger with `synchronized`, so the job also holds that monitor, the built-in lock every Java object has. Three threads want in. The `cash-machine` waits with `tryLock(200 ms)`, the `statement` printer with `lockInterruptibly()`, and an old `teller` screen with `synchronized`. After 400 ms, the main thread prints two of their states and interrupts those two, as a shutdown would. Before you read the output, guess which of the three keeps waiting after it's interrupted:

```text
cash-machine: gave up after 200 ms, asked the customer to try again
states: statement=WAITING, teller=BLOCKED
statement: interrupted while waiting, gave up cleanly
teller: got the monitor at last, interrupted=true
```

The cash machine waited exactly as long as we allowed, then gave its customer an answer. The statement printer left the line the moment it was interrupted. The teller heard nothing. It got the monitor after the full 1.5 seconds, and only then found out that someone had asked it to stop, more than a second earlier.

The two states differ, too. A thread waiting for a `ReentrantLock` is parked, which means put to sleep until another thread wakes it, so it shows `WAITING`. A thread waiting for a monitor shows `BLOCKED`. Expect `WAITING (parking)` when you read a thread dump (the printout of every thread's state) of code that uses explicit locks.

All that control has a price, the one the opening warned about. A `synchronized` block lets go when it exits, even when it throws. A `ReentrantLock` lets go only when you call `unlock()`. So every use follows one pattern. Here it guards the ledger's entries, the amounts paid in and out:

""" + pair(J_IDIOM, K_IDIOM) + """

Read the Java version aloud: take the lock; try the work; finally, whatever happens, give the lock back. In Kotlin, `withLock { }` writes the `lock()`, the `try` and the `finally` for you.

Leave out the `finally`, and one rare exception, from a bad input say, skips the `unlock()`. The thread moves on with the lock still taken, and every thread after it parks in `lock()` for good. A thread dump then shows dozens of threads `WAITING`, while `jcmd <pid> Thread.print -l` names an owner that is busy somewhere else entirely.

**A ReentrantLock lets go only when you tell it to. Put every `unlock()` in a finally.**

My rule: use `synchronized` for a short, simple critical section (the code that runs under the lock), and switch to `ReentrantLock` when you need one of its controls. For ordinary code, the two cost about the same on current JDKs. One old reason to switch is mostly gone, too. A virtual thread is a very light thread that the JVM runs on top of an ordinary one. Before JDK 24, a virtual thread that blocked inside `synchronized` held on to that ordinary thread. JDK 24 fixed that in most cases (the change is called JEP 491), and the virtual threads track covers it.

The cash machine can give up now. But a lock is also a place to wait for something to change, as the cooks did in wait, notify and guarded blocks. There, too, `ReentrantLock` has something better."""

ASIDE0 = {
    "title": "Why does lock() go before the try, and not inside it?",
    "body": "Because the `finally` should run only when you really hold the lock. If `lock()` sat inside the `try` and something failed before the lock was taken, the `finally` would call `unlock()` on a lock you don't hold. `unlock()` then throws `IllegalMonitorStateException`, and that new exception hides the one that really went wrong. `lockInterruptibly()` is the call most likely to fail that way, when an interrupt arrives while it waits. The same goes for `tryLock`: call it before the `try`, and enter the `try` only when it returned `true`."
}

# ---------------------------------------------------------------- section 1
S1 = """Remember the kitchen from wait, notify and guarded blocks. Waiters clip order tickets to a rail, and cooks take them off. When the rail is full, waiters wait for a free slot. When it's empty, cooks wait for a ticket. A monitor has only one wait set, the group of threads waiting on it, so both kinds sat on the same bench. A `notify()` meant for a cook could wake a waiter instead, and that stalled the kitchen. So we woke everyone with `notifyAll()` and let each `while` loop decide.

A `ReentrantLock` can have as many benches as you like. Each one is a **Condition**: a queue of threads waiting for one particular change, made with `lock.newCondition()`. `await()` plays the part of `wait()`. It lets go of the lock, parks, and takes the lock back before it returns. `signal()` and `signalAll()` play `notify()` and `notifyAll()`.

Let's rebuild the rail with two of them: `notFull`, where waiters wait for a free slot, and `notEmpty`, where cooks wait for a ticket. Here's the waiter's side, `put`:

""" + pair(J_PUT, K_PUT) + """

First we take the lock. While the rail is full, we wait on `notFull`, which lets go of the lock until a cook signals. Then we clip the ticket on and signal `notEmpty`. Only cooks ever wait there, and one new ticket lets exactly one cook go on. Those are the two conditions under which the kitchen lesson said a single `notify()` is safe, and now they hold on each bench. So `signal()` is enough, and the other waiters sleep on.

Is it worth the trouble? `WakeupCount` measures it. Four waiters and four cooks move 20,000 tickets through a rail with room for one, twice. The first run uses one `Condition` with `signalAll()`, the kitchen lesson's design. The second uses two with `signal()`. Each run counts its wasted wake-ups, the times a thread woke, checked its loop, and had to wait again. One run printed:

```text
one condition, signalAll():        wasted wake-ups:    88,340   (2175 ms)
notFull + notEmpty, signal():      wasted wake-ups:       375   (676 ms)
```

Both runs moved all 20,000 tickets. With one bench, every `signalAll()` woke all seven other threads, and most went straight back to sleep: 88,340 times. With two benches, that fell to 375, and the run took a third of the time. The Kotlin twin printed 93,684 against 3,155. The count isn't zero, because of barging: a running thread can grab the lock and the ticket before the signalled thread wakes up. That's why the `while` loop stays.

The rules from the kitchen still hold:

- Call `await()` and `signal()` only while you hold the lock, or you get `IllegalMonitorStateException`.
- Wait in a `while` loop. The `Condition` Javadoc (the official API documentation) allows spurious wake-ups, wake-ups with no signal at all. And another thread can take the ticket between the signal and your return.
- Don't call `wait()` or `notify()` on a `Condition`. It's an object like any other, so `notFull.wait()` compiles. It uses the condition's own monitor, which you don't hold, and throws.

A `Condition` can also wait against a deadline. `awaitNanos(n)` waits at most `n` nanoseconds (billionths of a second) and returns the time left, so a loop can keep waiting for whatever remains. The lab's `offer(item, timeout)` uses it.

**One kind of waiting thread per Condition lets signal() wake the right one. Keep the while loop anyway.**

Waiters and cooks both change the rail, so they have to take turns. Many threads only read shared data, though, and readers never get in each other's way. Making them take turns anyway is a waste."""

# ---------------------------------------------------------------- section 2
S2 = """The bank keeps a table of exchange rates. For each currency pair, such as `EURUSD`, it says how many dollars one euro costs. Every cash machine and every teller reads it, about 5,000 times a second, and a refresh job replaces the rates every five seconds. Behind a plain lock, each reader waits for every other reader, though reading changes nothing.

Picture a reading room in a library. Anyone may come in and read, as many people at once as like. Rearranging the shelves is different: the librarian waits until the room is empty, then works alone with the door shut. A `ReentrantReadWriteLock` is that room. It has two locks inside. Many threads can hold the read lock together. The write lock is exclusive: it waits until no reader and no writer is inside, and while it's held, nobody else gets in:

""" + pair(J_RW, K_RW) + """

Readers share the room, and the refresh works alone. The trap is a missing rate. The table is a cache, a store of answers kept close at hand, and a pair that isn't in it yet is called a cache miss. The natural code checks under the read lock and, if the rate is missing, takes the write lock to load it:

""" + pair(J_UPGRADE, K_UPGRADE) + """

Asking for the write lock while you still hold the read lock is called an **upgrade**, and `ReentrantReadWriteLock` doesn't support it. The write lock waits for every reader to leave. This thread is a reader, and it won't leave until it gets the write lock. So it waits, very patiently, for itself. In the reading room, it's a reader who decides to rearrange the shelves and waits inside for the room to empty. Two threads that try it at once wait for each other.

The thread dump won't point it out, either. Run `UpgradeDeadlock` with `-Pargs=hang` and ask for a dump with `jcmd <pid> Thread.print -l`. On JDK 21, `main` looks like this, trimmed:

```text
""" + DUMP + """
```

There's no `Found one Java-level deadlock`, and the list of locks that `main` owns is empty. A read lock has no single owner, so the JVM's deadlock detector has no cycle to find. It's a deadlock with one thread in it, and nobody reports it.

The fix has three steps: let go of the read lock, take the write lock, and check again. The check matters, because another thread may have loaded the rate while you held nothing. The lab's `FxRateCache` needs exactly that. Going the other way, a **downgrade**, is allowed: while holding the write lock, take the read lock, then let go of the write lock.

**A read lock never turns into a write lock. Let go first, then check again under the write lock.**

A read-write lock pays off when reads are frequent and take a while, and writes are rare. For a map lookup that takes 50 nanoseconds, its extra bookkeeping can cost more than it saves. And when the refresh replaces the whole table at once, a map that never changes, held in a `volatile` field (one whose reads always see the latest write), needs no lock at all. Lesson 11 of this track shows that pattern.

The read lock still writes to memory, though: every reader adds one to its count on the way in. On a very busy path, that one write is the next cost to go."""

# ---------------------------------------------------------------- section 3
S3 = """Every reader of a read lock adds one to the lock's count, and takes one away on the way out. On a machine with many cores, that count lives in one cache line. A cache line is the small block of memory that a core copies into its own fast memory, its cache. A core must own the line before it can write to it. So every reader pulls the line over to its own core, and the line bounces from core to core.

`StampedLock` (JDK 8) adds a mode that writes nothing at all, the **optimistic read**. Read it as "go ahead and read, then check whether anyone wrote while you did". The rate table shows two prices for the euro: the bank buys euros at one price and sells them 2 cents higher. A reader must never see a new buying price with an old selling price:

""" + pair(J_OPT, K_OPT) + """

`tryOptimisticRead()` returns a stamp, a version number of the lock (or 0 if a writer holds it). We copy both prices into locals with no lock held. Then `validate(stamp)` asks: did any writer get in since that stamp? If not, the two copies belong together. If one did, we throw them away and read again under a real read lock.

Between the stamp and the check, the copies can be **torn**: half old and half new, such as a new buying price with an old selling price. The Javadoc promises sound values only if a later `validate` returns `true`. So the code in between must not act on them: no loops driven by them, no array index, no calls that could throw.

**An optimistic read can be torn. Copy, validate, and only then use.**

`OptimisticRead` checks that promise. A writer keeps moving both prices, and a reader reads them optimistically for one second. One run printed:

```text
reads: 843,481   failed validate(): 22,969   torn pairs caught: 12,960   torn pairs that passed validate(): 0
```

About one read in 37 failed to validate, and more than half of those had really caught a torn pair. Not one torn pair got past `validate()`.

The speed comes without the safety rails of the other locks:

- `StampedLock` is **not reentrant**. A thread that holds the write lock and asks for it again waits for itself, which makes it the second lock in this lesson that can.
- It has no `Condition`s.
- A stamp isn't tied to a thread, and you must pass the right stamp to `unlockRead` or `unlockWrite`.

Use it for a few fields that are read on a very busy path and written rarely, like these two prices. Even then, wait until a profiler, a tool that measures where a program spends its time, shows that the read-write lock is the cost. For most code, `ReentrantReadWriteLock`, or no lock at all, is the better choice.

That's where this lesson's tools stop. Each one still makes some thread wait for a lock, or fall back to one when its optimism fails. For a single number, such as one balance, there's a way to change it safely with no lock at all."""

L = {
 "id": "conc-07",
 "title": "Explicit locks: ReentrantLock, Condition, ReadWriteLock",
 "minutes": 38,
 "goal": "By the end you can use `ReentrantLock` safely (`unlock()` in a `finally`, `tryLock`, `lockInterruptibly`), give each kind of waiting thread its own `Condition`, and use a read-write lock without the upgrade that hangs.",
 "opening": OPENING,
 "warmup": {
  "q": "A thread holds the read lock of a `ReentrantReadWriteLock`. Then it calls `writeLock().lock()` on the same lock. No other thread touches the lock. What happens?",
  "options": ["It gets the write lock at once, because it is the only reader", "It waits forever: the write lock waits for every reader to leave, and this thread is one of them", "It throws `IllegalMonitorStateException`", "It gets the write lock and quietly drops its read lock"],
  "answer": 1,
  "why": "`ReentrantReadWriteLock` can't turn a read lock into a write lock. The write lock needs zero readers, and the thread's own read lock counts, so the thread parks and never wakes. Nothing throws, and, as the third section shows, a thread dump doesn't even report it as a deadlock. Kotlin's `write { }` helper behaves differently, and the comparison near the end shows how."
 },
 "sections": [
  {
   "h": "A lock that can give up: ReentrantLock, tryLock and lockInterruptibly",
   "body": S0,
   "aside": ASIDE0,
   "try": {
    "title": "Three ways to wait for a busy lock",
    "minutes": 4,
    "steps": [
     "Read `TryLockDemo`. The `interest` thread holds the ledger lock and the old monitor for 1.5 seconds. `cash-machine` waits with `tryLock(200 ms)`, `statement` with `lockInterruptibly()`, and `teller` with `synchronized`.",
     "Predict the order of the four output lines, and the states printed for `statement` and `teller`.",
     "Run it. Then let the cash machine wait 2 seconds instead of 200 ms, and run it again."
    ],
    "code": code("TryLockDemo"),
    "expect": "The cash machine gives up after about 200 ms. The states are `statement=WAITING` (parked on the lock) and `teller=BLOCKED` (waiting for a monitor). The interrupt ends the statement printer's wait at once. The teller keeps waiting until the interest job finishes, and only then sees `interrupted=true`. With a 2-second wait, the cash machine gets the lock as soon as the job is done."
   },
   "refs": [
    {"title": "ReentrantLock (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html", "kind": "docs"}
   ]
  },
  {
   "h": "One waiting room per reason to wait: Condition",
   "body": S1,
   "figure": {"svg": FIG, "caption": "One lock, one line of threads that want it, and a separate waiting room for each condition. await() lets go of the lock and parks in its room; signal() sends one thread from the room back to the line."},
   "try": {
    "title": "Count the wasted wake-ups",
    "minutes": 4,
    "steps": [
     "Read `WakeupCount`. Four waiters and four cooks move 20,000 tickets through a rail with room for one: once with one `Condition` and `signalAll()`, once with two `Condition`s and `signal()`.",
     "A wake-up is wasted when a thread wakes, checks its `while` loop, and has to wait again. Predict which version wastes more, and roughly how many more.",
     "Run it twice and compare the counts and the times."
    ],
    "code": code("WakeupCount"),
    "expect": "With one condition, tens of thousands of wake-ups are wasted (88,340 and 93,684 in runs here), because every `signalAll()` wakes all seven other threads and most of them go back to sleep. With two conditions, the count drops to hundreds or a few thousand, and the run takes about a third or a quarter of the time. It isn't zero, because a running thread can barge in and take the ticket before the signalled thread wakes. That's why the `while` loop stays."
   },
   "refs": [
    {"title": "Condition.java at jdk-25-ga (spurious wake-ups, await and signal)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/Condition.java", "kind": "read"}
   ]
  },
  {
   "h": "Many readers, one writer: ReadWriteLock, and the upgrade that hangs",
   "body": S2,
   "try": {
    "title": "Upgrade, then downgrade",
    "minutes": 3,
    "steps": [
     "Run `UpgradeDeadlock`. It tries the upgrade with `tryLock(1, SECONDS)` so it can't hang, then does a downgrade.",
     "Run the Kotlin twin. Its last line puts `write { }` inside `read { }`. Predict: does it hang?",
     "Optional: run the Java one with `-Pargs=hang`. In a second terminal, run `jcmd <pid> Thread.print -l` with the printed PID and find `main`. Stop it with Ctrl+C."
    ],
    "code": code("UpgradeDeadlock"),
    "expect": "`write lock while holding a read lock, after 1 s: false`, then `downgraded: write locked = false, read holds = 1`. The Kotlin `write { }` inside `read { }` doesn't hang: it prints `write locked = true, read holds = 0`, because Kotlin's `write` lets go of this thread's read locks first. With `-Pargs=hang`, the dump shows `main` parked in `WriteLock.lock` and no deadlock report."
   },
   "refs": [
    {"title": "ReentrantReadWriteLock (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantReadWriteLock.html", "kind": "docs"}
   ]
  },
  {
   "h": "Reading with no lock at all: StampedLock and the optimistic read",
   "body": S3,
   "try": {
    "title": "Catch torn reads with validate()",
    "minutes": 3,
    "steps": [
     "Read `OptimisticRead`. A writer keeps moving the bank's two euro prices, and once a write is done the selling price is always the buying price plus 2. The reader counts the optimistic reads that saw a pair where that isn't true.",
     "Predict: will any torn pair get past `validate()`?",
     "Run it. Then delete the `validate` check (treat every optimistic read as good) and count the torn pairs that would have reached the caller."
    ],
    "code": code("OptimisticRead"),
    "expect": "Tens of thousands of reads fail validation in the second (22,969 of 843,481 in one run here), and more than half of those saw a torn pair, a new buying price with an old selling price. The last number, torn pairs that passed `validate()`, is always 0. Without the check, every one of those torn pairs would have gone to the caller."
   }
  }
 ],
 "compare": {
  "title": "A read-mostly cache in Java and Kotlin",
  "java": {"title": "Java", "src": """BigDecimal rate(String pair) {
    rw.readLock().lock();
    try {
        BigDecimal r = rates.get(pair);
        if (r != null) return r;            // 1. fast path under the read lock
    } finally {
        rw.readLock().unlock();             // 2. let go BEFORE asking for the write lock
    }
    rw.writeLock().lock();
    try {
        return rates.computeIfAbsent(pair, loader);   // 3. check again under the write lock
    } finally {
        rw.writeLock().unlock();
    }
}"""},
  "kotlin": {"title": "Kotlin", "src": """fun rate(pair: String): BigDecimal = rw.read {
    rates[pair] ?: rw.write {
        // write {} let go of our read lock first, so another thread may have loaded it: check again
        rates.getOrPut(pair) { loader(pair) }
    }
}"""},
  "note": "The Java version must let go of the read lock before it takes the write lock, or it hangs. The Kotlin version looks like an upgrade, and it doesn't hang, because the standard library's `ReentrantReadWriteLock.write` releases every read lock this thread holds, takes the write lock, and takes the read locks back afterwards. Its documentation warns that this is not an atomic upgrade: another thread can write in the gap, so anything you checked before `write` must be checked again inside it. That's why both versions check again (`computeIfAbsent`, `getOrPut`). Kotlin's helpers remove the ceremony of `lock`, `try` and `finally`. They don't remove the reasoning."
 },
 "worked": {
  "title": "A lock per account that gives up",
  "steps": [
   {"say": "Each account's changes must run one at a time, because each one checks and then updates that account's balance. Changes to different accounts must not wait for each other. And if one thread gets stuck while holding an account, other requests for that account should give up after a short wait and ask the caller to try again, instead of piling up behind it. Read the solution and its subgoal labels.",
    "code": J_ACCT, "lang": "java", "alt_code": K_ACCT, "alt_lang": "kotlin"},
   {"say": "Before reading on, explain to yourself: why does `tryLock` sit outside the `try`, when `unlock()` is inside the `finally`? Answer: if `tryLock` returns `false` or throws `InterruptedException`, this thread doesn't hold the lock. A `finally` that called `unlock()` would throw `IllegalMonitorStateException` and hide the real result. Only the code that runs while you hold the lock goes inside the `try`.",
    "code": "", "lang": ""},
   {"say": "Why not `synchronized (accountId)`? Two `String`s with the same letters are often different objects, so two requests for the same account could each lock their own string and run together. Interned strings, the single shared copy Java keeps of each string literal, go the other way: unrelated code that locks the same literal shares your lock, as synchronized and intrinsic locks showed. And `synchronized` has no timeout. A map of real lock objects avoids all three problems.",
    "code": "", "lang": ""},
   {"say": "One problem remains: the map gains a lock for every account it ever sees, and never shrinks. With millions of accounts, that's memory you don't get back. Removing entries safely is harder than it looks, because another thread may be about to lock the entry you remove. The usual answer is **lock striping**: a fixed array of locks, with each account mapped to one of them by its hash.",
    "code": J_STRIPE, "lang": "java", "alt_code": K_STRIPE, "alt_lang": "kotlin"},
   {"say": "Two accounts that share a stripe now wait for each other. That costs a little speed and nothing in correctness. If you ever hold two account locks at once, for a transfer, take the stripes in index order, as in Deadlock, livelock and starvation, and skip the second lock when both accounts land on the same stripe.",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A rail with two conditions and a rate table that doesn't hang",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/LockBuffer.java", f"{lab}/main/{P}/FxRateCache.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l07.*'",
  "steps": [
   "Run the tests. All eight fail. The five `LockBuffer` tests hit `UnsupportedOperationException`. Two `FxRateCache` tests time out (the upgrade hang), and the snapshot test finds rates from two different refreshes mixed together.",
   "Part 1: `LockBuffer` is the kitchen's rail from the second section, for any kind of item. Write it with one `ReentrantLock` and two `Condition`s, `notFull` and `notEmpty`. Check the capacity in the constructor. `put` and `take` follow the shape in the second section, with `signal()`.",
   "Write `offer(item, timeout)`: the same as `put`, but wait with `notFull.awaitNanos(remaining)` and return `false` when the time runs out.",
   "Part 2: `FxRateCache` is the bank's exchange-rate table from the third section. Fix `rate`: let go of the read lock, take the write lock, and check again before calling the loader, so the loader runs once per currency pair.",
   "Fix `snapshot` so it reads every pair under one read lock. Run the tests until all eight pass, then twice more."
  ],
  "hints": [
   "`awaitNanos` returns the nanoseconds still left (zero or less when time is up). Keep the returned value and pass it to the next `awaitNanos` in the loop.",
   "Use `lock.lockInterruptibly()` at the top of `put`, `take` and `offer`, so an interrupted thread doesn't wait for the lock either. `await()` already throws `InterruptedException` when interrupted.",
   "The cache's `HashMap` is fine as it is: every access to it happens under the read or the write lock. Only the order in which you take the locks is wrong."
  ],
  "done_when": "All eight tests in `ExplicitLocksTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Two conditions from memory",
  "minutes": 5,
  "prompt": "Close this page. Write a bounded buffer, the kitchen's rail, with a `ReentrantLock` and two `Condition`s: `put` waits while it's full, `take` waits while it's empty. Then check your work: is every `unlock()` in a `finally`, every `await()` in a `while`, and does each method signal the other side's condition?",
  "answer": {"lang": "java", "src": J_DRILL, "alt": {"lang": "kotlin", "title": "Kotlin", "src": K_DRILL}}
 },
 "recap": [
  "`ReentrantLock` lets one thread in at a time and makes its writes visible, like `synchronized`, but you release it yourself: `lock()` right before `try`, `unlock()` first in `finally`, or Kotlin's `withLock`.",
  "Reach for it when a waiting thread needs a choice: `tryLock` with a timeout, `lockInterruptibly`, a fair lock, or more than one condition.",
  "Each `Condition` is its own waiting room. With one per kind of waiting thread, `signal()` is enough. Still wait in a `while` loop.",
  "A read-write lock lets readers share. Asking for the write lock while you hold the read lock waits forever, and the deadlock detector won't report it. Let go, take the write lock, check again.",
  "`StampedLock`'s optimistic read takes no lock: copy into locals, `validate`, and only then use the values. It isn't reentrant.",
  "The limit: every tool here still makes threads wait for a lock, or fall back to one. For a single number, the next lesson changes it with no lock at all."
 ],
 "closing": "We started with a customer at a cash machine, watching a spinning wheel while the interest job held the ledger. `ReentrantLock` let her request give up after 200 ms. `Condition` gave the kitchen's waiters and cooks a waiting room each. The read-write lock let readers share the rate table, as long as no reader tries to become a writer.\n\nNow search your own code for `.lock()`. Each one should sit right before a `try` whose `finally` starts with `unlock()`. A `lock()` with no `finally` is waiting for its first exception.\n\nNext, we'll take the optimistic idea further and change a balance with no lock at all. How can two threads update one number safely if neither ever waits?",
 "quiz": [
  {"q": "A cash machine's request needs the ledger lock, but it must ask the customer to try again if it can't get the lock within 50 ms. Which tool fits?",
   "options": ["`synchronized (ledger)`", "`ledger.lockInterruptibly()`", "`ledger.tryLock(50, TimeUnit.MILLISECONDS)`", "A `volatile boolean busy` flag checked before `lock()`"],
   "answer": 2, "why": "`tryLock` with a timeout waits at most 50 ms and returns `false` if the lock is still taken. `lockInterruptibly` waits with no limit unless someone interrupts the thread, and `synchronized` can't time out at all. The flag is the tempting one, and it's check-then-act: another thread can take the lock between the check and the `lock()` call."},
  {"q": "Kotlin code: `rw.read { if (cache[k] == null) rw.write { cache[k] = load(k) } }`. Two threads ask for the same missing key. What can happen?",
   "options": ["Both hang, because a read lock can't be upgraded", "`load(k)` can run twice, because `write { }` lets go of the read lock before it takes the write lock", "Nothing bad: `write { }` upgrades atomically", "It throws `IllegalMonitorStateException`"],
   "answer": 1, "why": "Kotlin's `write` releases this thread's read locks, takes the write lock, and takes the read locks back afterwards. Both threads can see `null`, both let go, and each then loads in turn. It doesn't hang, as it would in Java, but it isn't atomic either. Check again inside `write`, for example with `getOrPut`."},
  {"q": "From wait, notify and guarded blocks: a teammate merges `notFull` and `notEmpty` into one `Condition changed`, but keeps `changed.signal()` in both `put` and `take`. With several waiters and cooks, what can happen?",
   "options": ["Nothing changes: `signal()` always wakes the right kind of thread", "Tickets are lost", "It throws, because two methods can't share one `Condition`", "The kitchen can stall: a `signal()` meant for a cook can wake a waiter, which waits again, and nobody signals the cooks"],
   "answer": 3, "why": "With one queue for both kinds of waiting thread, `signal()` may pick the wrong kind. That thread checks its loop, waits again, and the signal is gone. It's the same lost wake-up that made the one-monitor rail need `notifyAll()`. With one condition, use `signalAll()`; with two, `signal()` is fine. No ticket is lost, which is why this bug hides in tests.",
   "from": "conc-05"},
  {"q": "With `StampedLock`, you call `tryOptimisticRead()` and copy `buy` and `sell` into locals. What must happen before you use them?",
   "options": ["Call `validate(stamp)`; if it returns false, read them again under `readLock()`", "Nothing: the stamp guarantees the two copies match", "Call `unlockRead(stamp)`", "Call `tryConvertToWriteLock(stamp)`"],
   "answer": 0, "why": "An optimistic read takes no lock, so a writer can change the prices while you copy them. `validate` tells you whether a writer got in since the stamp, and only after it returns `true` do the copies belong together. There's nothing to release, because nothing was locked."},
  {"q": "A dump shows 40 threads `WAITING (parking)` in `ReentrantLock.lock()`. `Thread.print -l` says the lock is owned by `interest`, the end-of-day job, whose stack shows it asleep in `Thread.sleep`, waiting for tomorrow's run, outside any code that uses the lock. What is the most likely bug?",
   "options": ["A deadlock between the 40 threads", "The lock is unfair, so the 40 threads are starving", "A code path in the interest job took the lock and left without `unlock()`, for example on an exception with no `finally`", "`Thread.sleep` gives the lock back, so the dump is out of date"],
   "answer": 2, "why": "The owner isn't waiting for anything that needs the lock, and it isn't in the critical section. It has moved on while still holding the lock, which happens when an exception or an early return skips the release. An unfair lock would still change hands now and then, a deadlock needs the owner to wait for a lock too, and `Thread.sleep` never gives back a lock."}
 ],
 "flashcards": [
  {"front": "Where do `lock()` and `unlock()` go relative to `try` and `finally`?", "back": "`lock()` on the line right before `try`. `unlock()` as the first statement of `finally`. In Kotlin, `lock.withLock { }` does both."},
  {"front": "What does `lock.tryLock(50, MILLISECONDS)` do when another thread holds the lock?", "back": "It waits up to 50 ms. It returns `true` (and you hold the lock) if it got it in time, `false` otherwise. It throws `InterruptedException` if interrupted while waiting."},
  {"front": "A thread waits in `lockInterruptibly()` and another thread interrupts it. What happens? And for a thread waiting to enter `synchronized`?", "back": "`lockInterruptibly()` gives up at once with `InterruptedException`. The `synchronized` waiter keeps waiting until it gets the monitor, and only sees its interrupt flag afterwards."},
  {"front": "Why can a bounded buffer with `notFull` and `notEmpty` conditions use `signal()` instead of `signalAll()`?", "back": "Each condition has only one kind of waiting thread, and one change (one item in, or one slot free) lets exactly one of them go on."},
  {"front": "A thread holding the read lock of a `ReentrantReadWriteLock` calls `writeLock().lock()`. What happens?", "back": "It waits forever. The write lock waits for every reader to leave, including this thread. Let go of the read lock first, then check again under the write lock."},
  {"front": "After `long s = lock.tryOptimisticRead()` and copying fields into locals, what must you do?", "back": "Call `lock.validate(s)`. If it returns false, a writer got in: read the fields again under `lock.readLock()`."},
  {"front": "In Kotlin, what does `rw.write { }` do when called inside `rw.read { }`?", "back": "It releases this thread's read locks, takes the write lock, and takes the read locks back afterwards. It doesn't hang, but it isn't atomic: check again inside the block."}
 ],
 "terms": [
  {"term": "ReentrantLock", "plain": "An explicit lock with the same rules as `synchronized`, plus `tryLock`, timeouts, interruptible waits, fairness and conditions."},
  {"term": "Hold count", "plain": "How many times the owning thread has taken a reentrant lock. It must release it as many times."},
  {"term": "Condition", "plain": "A waiting room tied to a lock. `await()` lets go of the lock and waits; `signal()` wakes one waiting thread."},
  {"term": "Fair lock", "plain": "A lock that hands over to the longest-waiting thread instead of letting a newly arrived thread barge in."},
  {"term": "Read-write lock", "plain": "A pair of locks: many threads may hold the read lock together; the write lock is held by one thread alone."},
  {"term": "Lock upgrade", "plain": "Asking for the write lock while still holding the read lock. `ReentrantReadWriteLock` waits forever if you try."},
  {"term": "Optimistic read", "plain": "A `StampedLock` read that takes no lock and checks afterwards, with `validate`, that no writer got in."},
  {"term": "Torn read", "plain": "Copies of several fields that mix old and new values, because a writer ran while they were being read."}
 ],
 "explain_back": {
  "prompt": "A teammate asks: \"Should we replace all our `synchronized` blocks with `ReentrantLock`? I heard it's faster.\" Explain what you would tell them.",
  "answer": "Not by default. Both let one thread in at a time and make its writes visible to the next owner, and on current JDKs they cost about the same for ordinary code. `synchronized` can't leak: it lets go on every exit. With `ReentrantLock` you must release it in a `finally`, and one missed path holds the lock forever. I'd switch only where we need something `synchronized` can't do: give up after a timeout with `tryLock`, let an interrupt cancel the wait with `lockInterruptibly`, use a fair lock, or have separate conditions for different kinds of waiting threads. For data that is read far more than it's written, I'd look at a read-write lock, or better, a snapshot that never changes behind a `volatile` reference."
 },
 "deeper": {
  "minutes": 10,
  "body": "`ReentrantLock`, `ReentrantReadWriteLock`, `Semaphore` and `CountDownLatch` are all built on one class, `AbstractQueuedSynchronizer` (AQS). It keeps one `int` of state and a queue of waiting threads. For `ReentrantLock` the state is the hold count; for a semaphore it is the number of permits left; for a latch it is the count. A thread that can't go on joins the queue and parks with `LockSupport.park`. That's why it shows as `WAITING` in a dump, with a line like `parking to wait for <0x...> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)`. A release unparks the next thread in the queue.\n\nIn non-fair mode, the default, a thread that arrives just as the lock is released can take it before the queued thread wakes. That's barging, and it's why the two-condition rail in the second Try it still wasted some wake-ups. It's also why non-fair locks get through far more work: waking a parked thread takes microseconds, and a running thread can take and release the lock many times in that gap. Fair mode closes the gap and pays the wake-up cost on every hand-off. Even on a fair lock, the untimed `tryLock()` barges: its Javadoc says it does not honor the fairness setting.\n\n`ReentrantReadWriteLock` splits its 32-bit state into two 16-bit halves, one for read holds and one for write holds. That's why its Javadoc caps it at 65,535 recursive write locks and 65,535 read locks.\n\n`StampedLock` also has `tryConvertToWriteLock(stamp)`, which upgrades a read or optimistic stamp to a write stamp if no other thread is in the way, and returns 0 if it can't. It's the only upgrade among the JDK's locks, and it can fail, so you still need the fallback path.\n\nIf you ever build your own synchronizer, subclass AQS and implement `tryAcquire` and `tryRelease`; its Javadoc has a small `Mutex` example. First check `java.util.concurrent` for one that already exists. Lesson 10 of this track covers the common ones."
 },
 "sources": [
  {"title": "ReentrantLock.java at jdk-25-ga (the try/finally idiom, fairness notes)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/ReentrantLock.java"},
  {"title": "StampedLock.java at jdk-25-ga (optimistic reads, not reentrant)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/StampedLock.java"},
  {"title": "ReentrantReadWriteLock (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantReadWriteLock.html"},
  {"title": "Kotlin standard library: ReentrantReadWriteLock.write", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.concurrent/write.html"},
  {"title": "Java Concurrency in Practice, Goetz et al., chapters 13 and 14", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/conc-07.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
