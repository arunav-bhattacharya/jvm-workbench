import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """By the end of this track you can explain why one thread may never see a value that another thread wrote, and name the rule that makes a read safe. You can choose between `volatile`, an atomic and a lock for any shared field. You can hand an object to other threads so they never see it half-built, like a letter in a sealed envelope. You can build something on first use exactly once, like a stockroom opened for the first customer. And you can read the lighter memory modes, the labels on single reads and writes, without guessing. This is the rulebook under every concurrent class you use, and the reason "it passed on my machine" means so little.

You need the first track, Threads and the bugs they cause: threads, race conditions, `synchronized` and atomics. Nothing else. Install JDK 25. The memory model, the rules for what one thread sees of another thread's writes, hasn't changed since Java 5 (JSR-133), so everything here holds from JDK 21 to JDK 27. When a lesson mentions a newer feature, it says which JDK.

Every lesson has a lab in `labs/jmm`, in the package `workbench.jmm.lNN`. The labs are in Java, and every code sample and Try-it program also comes in Kotlin. Memory-model bugs rarely show up on demand, so the tests check code that behaves the same on every run once it's right: a loop that must stop, a value that must be built exactly once while eight threads ask for it, a hand-over that must deliver every item whole. Generous time limits make a broken version fail instead of hanging the build. From `labs/`, run `./gradlew :jmm:test --tests 'workbench.jmm.lNN.*'` until it passes; `./gradlew :jmm:solutionTest` runs the same tests against the reference answers. The last lesson shows how to go further with jcstress, a tool that runs tiny tests millions of times, outside Gradle."""

CHEAT = """## The one rule

A write is guaranteed visible to a read in another thread only if the write **happens-before** the read. Without that edge you have a data race: values that are stale and may never update, writes that seem to arrive out of order, and `long` and `double` values that arrive in two halves.

Picture it with the three scenes from lessons 1 to 3. Shared memory is the office whiteboard, and each core works from its own notepad and outbox tray, so a note on the whiteboard is not seen until someone looks up. Happens-before is the cashier's key: whoever takes the same key next is promised to see what was left in the cabinet. `volatile` is the museum's OPEN/CLOSED sign: everyone checks it at the door, but changing it and counting visitors are two separate trips.

## The edges you use

| The writer does | The reader does | Edge? |
|---|---|---|
| anything, then leaves `synchronized (m)` | enters `synchronized (m)` on the same `m` | yes |
| anything, then writes volatile `v` | reads the same `v` and sees that write | yes |
| `t.start()` | anything inside `t` | yes |
| anything inside `t` | `t.join()` returns | yes |
| puts into a concurrent collection | a `get` or `take` that returns it | yes |
| `executor.submit(task)` | the task runs | yes |
| the task of a `Future` | `future.get()` returns | yes |
| `latch.countDown()`, `semaphore.release()`, `lock.unlock()` | `latch.await()`, `acquire()`, `lock()` returns | yes |
| `Thread.sleep`, a different lock, a different volatile field | anything | **no** |

Edges chain: if A happens-before B and B happens-before C, then A happens-before C. That's how a plain field written before a volatile write reaches the thread that reads that volatile.

## Pick the tool for a shared field

| Situation | Use | Picture it |
|---|---|---|
| One writer, readers want the latest value | `volatile` / `@Volatile` | a stop flag, a status, a version number |
| Many writers update one number (`count++`, `balance += x`) | `AtomicLong`, `LongAdder`, `ConcurrentHashMap.merge` | eight tills adding to one total |
| Several fields must change together | a lock, or one immutable object behind a volatile reference | a delivery fee and its free-delivery threshold |
| A whole object replaced while the program runs | an immutable snapshot published with one volatile write | the day's rate card, printed whole and swapped in |
| One value per key, built once | `computeIfAbsent` (not Kotlin's `getOrPut`) | one connection per bank |
| "First writer wins" | `compareAndSet` | the first reason a switch was tripped |

`volatile` gives visibility, keeps the plain writes before it in order, puts all volatile accesses in one order, and makes 64-bit reads and writes whole. It does not make `v++` atomic, does not protect the object it points to, and does nothing for a thread that doesn't read it.

## Safe publication and immutability: seal the envelope

Publishing an object is a write, and a reader can see the reference before the fields behind it. Publish through a seal: a static initializer; a volatile field or `AtomicReference`; a final field of a properly built object; a lock or a `java.util.concurrent` hand-over. Writer and reader must use the same seal. Final fields are pages glued in at the factory: seen whole through any race, but they don't deliver the envelope. An immutable object (final class, final fields, changing inputs copied, nothing changeable handed out, no escaping `this`) is safe through any race.

Don't open the house before the builders finish: never let `this` escape a constructor. Register listeners and start threads afterwards, in a static factory method, a `start()` method or a framework's `@PostConstruct` method.

```java
public record DeliverySettings(long feeCents, long freeAboveCents) {}   // immutable

private volatile DeliverySettings settings = new DeliverySettings(499, 5_000);
void refresh(Settings s) { settings = new DeliverySettings(s.feeCents(), s.freeAboveCents()); }   // one volatile write
DeliverySettings current() { return settings; }                                                   // one complete version
```

```kotlin
data class DeliverySettings(val feeCents: Long, val freeAboveCents: Long)   // immutable

@Volatile private var settings = DeliverySettings(499, 5_000)
fun refresh(s: Settings) { settings = DeliverySettings(s.feeCents, s.freeAboveCents) }   // one volatile write
fun current(): DeliverySettings = settings                                               // one complete version
```

## Lazy initialization: open the stockroom once

| Need | Use |
|---|---|
| Nearly every call needs it anyway | build it eagerly, at startup |
| One per program, building it can't fail | holder class idiom, enum, Kotlin `object` |
| One per object, or must retry after a failure | double-checked locking on a volatile field, Kotlin `by lazy` |
| One per key | `computeIfAbsent` |

```java
private static final class Holder { static final CardBinTable INSTANCE = new CardBinTable(); }
static CardBinTable instance() { return Holder.INSTANCE; }    // the JVM's class-init lock does the work

private volatile ReceiptPrinter printer;                      // volatile is not optional
ReceiptPrinter printer() {
    ReceiptPrinter p = printer;                               // one volatile read on the fast path
    if (p != null) return p;
    synchronized (this) {
        if (printer == null) printer = shop.connectPrinter();
        return printer;
    }
}
```

```kotlin
class CardBinTable private constructor() {
    private object Holder { val INSTANCE = CardBinTable() }
    companion object { fun instance(): CardBinTable = Holder.INSTANCE }
}

val printer: ReceiptPrinter by lazy { shop.connectPrinter() }   // SYNCHRONIZED: a volatile double check
```

Kotlin modes: `SYNCHRONIZED` (the default: runs once, others wait, retries if it throws), `PUBLICATION` (may run on several threads, one result wins: only for cheap work with no side effects), `NONE` (one thread only). A holder whose initializer throws never retries: later calls get `NoClassDefFoundError`.

## VarHandle access modes: labels on single reads and writes

| Mode | Methods | Adds | Picture it |
|---|---|---|---|
| plain | `get`, `set` | nothing across threads | no label |
| opaque | `getOpaque`, `setOpaque` | each access really happens, in one piece; eventually visible | deliver for sure, in order |
| acquire/release | `getAcquire`, `setRelease` | writes before the release are seen after the matching acquire | the label goes on the box's lid last |
| volatile | `getVolatile`, `setVolatile` | one total order of all volatile accesses | registered mail in one central book |

`compareAndSet` and `getAndAdd` behave like volatile. Release/acquire does not forbid the store-buffering result (each thread writes its own flag, both read the other's as 0); only volatile does. `AtomicReference` and friends offer the same modes without a lookup. In application code use `volatile`, the `Atomic` classes and `java.util.concurrent`. Test any code that leans on the lighter modes with jcstress, on ARM if you can, because x86 hides many ordering bugs."""

RECAP = [
 "The JIT may read a plain field once for a whole loop, and a processor's store buffer lets a later read overtake an earlier write. Neither is a bug: the memory model allows both.",
 "A read is guaranteed to see a write only through a happens-before edge: the same lock, the same volatile field, start, join, or a `java.util.concurrent` hand-over. Sleep is not an edge.",
 "volatile gives visibility and ordering for one variable, not an atomic read-modify-write. Use atomics or `LongAdder` for counters, and a lock or an immutable snapshot for several fields.",
 "Publishing an object is a write that can race. Seal the envelope: a volatile field, a static initializer, a final field or a `java.util.concurrent` hand-over. Prefer immutable objects, which survive any race.",
 "Final fields are seen as the constructor left them, but only if `this` didn't escape the constructor. Build first, wire up afterwards.",
 "Double-checked locking needs a volatile field. For statics the holder idiom is simpler, and Kotlin's `by lazy` is the same double check. A failed holder never retries.",
 "Access modes form a ladder: plain, opaque, acquire/release, volatile. Release/acquire hands data from one writer through one variable; only volatile gives one total order.",
 "Tests can't prove that nothing reorders. Write code that is correct by the rules, and use jcstress, ideally on ARM, for anything that leans on the lighter modes."
]

QUIZ = [
 {"q": "A worker runs `while (!stopped) { doOneJob(); }`, where `doOneJob` is small enough for the JIT to copy into the loop, and `stopped` is a plain boolean that another thread sets. Now and then the worker never stops. Why, and what's the fix?",
  "options": [
   "A CPU cache keeps the old value forever; call `System.gc()` to flush it",
   "The JIT may read `stopped` once and loop forever; make the field volatile",
   "Add `Thread.sleep(10)` to the loop, because sleeping forces a fresh read",
   "Use an AtomicBoolean, because boolean writes can arrive in two halves"
  ],
  "answer": 1,
  "why": "Caches keep each other up to date; the compiler is the problem. With no edge, the JIT may lift the read out of the loop. A volatile read can't be lifted. Sleep creates no edge, and a boolean can't arrive in two halves.", "from": "jmm-01"},
 {"q": "In which case is the reader guaranteed to see `x = 42`?",
  "options": [
   "The writer sets `x`, then writes volatile `a`; the reader reads volatile `b`, then `x`",
   "The writer sets `x` inside `synchronized (lockA)`; the reader reads `x` inside `synchronized (lockB)`",
   "The writer sets `x`, then sleeps 100 ms; the reader sleeps 200 ms, then reads `x`",
   "The writer sets `x`, then calls `latch.countDown()`; the reader returns from `latch.await()` and reads `x`"
  ],
  "answer": 3,
  "why": "`countDown` happens-before a successful `await` on the same latch, and the write to `x` comes before `countDown` in the writer's own order. The other options use different variables, different locks, or sleep, which creates no edge at all.", "from": "jmm-02"},
 {"q": "Fifty threads each add 1 to `volatile int inShop` when a customer comes in and subtract 1 when one leaves. The count on the shop's screen drifts further from the truth every hour. What's the fix?",
  "options": [
   "Use an AtomicInteger (`incrementAndGet`, `decrementAndGet`)",
   "Make it `volatile long` so it can't overflow",
   "Add `Thread.yield()` after each update",
   "Read it inside a synchronized block on the screen's side"
  ],
  "answer": 0,
  "why": "`inShop++` is a read, an add and a write. volatile makes each one visible, but it doesn't stop two threads from reading the same value, so updates get lost. An atomic does the whole update as one step.", "from": "jmm-03"},
 {"q": "The version number of the shop's price list is written only by one loader thread and read by every till thread. What is enough?",
  "options": [
   "A lock around every read and write",
   "An AtomicLong updated with compareAndSet",
   "A volatile long",
   "A plain long, because writes are rare"
  ],
  "answer": 2,
  "why": "With a single writer there's no read-modify-write race, so the only problem is visibility, and that's what volatile solves. It also makes the 64-bit write whole. A lock and compareAndSet work but buy nothing here; a plain long has no edge at all.", "from": "jmm-03"},
 {"q": "`record RateCard(String currency, Map<String, Long> fees)` stores the caller's HashMap as it is. Is a RateCard safe to share between threads?",
  "options": [
   "Yes: record fields are final",
   "Not quite: the reference is final, but the caller can still change the HashMap; copy it with `Map.copyOf` in a compact constructor",
   "No: records can't be shared between threads",
   "Yes, as long as it's published through a volatile field"
  ],
  "answer": 1,
  "why": "Final fields freeze what the constructor stored, which is a reference to someone else's changeable map. Later changes through the caller's reference are ordinary unprotected writes. A defensive copy makes the record truly immutable.", "from": "jmm-04"},
 {"q": "A listener's constructor calls `bus.register(this)` and only then sets its `phone` field. The bus replays its last event to every new listener. What can happen?",
  "options": [
   "Nothing: a constructor always runs to the end before anyone can use the object",
   "The compiler rejects `this` as an argument inside a constructor",
   "The bus calls the listener before `phone` is set, and the listener throws a NullPointerException",
   "Nothing, as long as `phone` is final"
  ],
  "answer": 2,
  "why": "`this` escaped before the constructor finished, so a callback on the same thread, or another thread, can use a half-built object. Final doesn't help: its promise starts when the constructor returns. Register after construction.", "from": "jmm-04"},
 {"q": "Which of these lazy initializers can hand a caller a half-built object?",
  "options": [
   "Double-checked locking on a plain (non-volatile) field",
   "The holder class idiom",
   "Kotlin `by lazy` with the default mode",
   "`ConcurrentHashMap.computeIfAbsent`"
  ],
  "answer": 0,
  "why": "The first check takes no lock, so its read has no edge to the write, and the reference can become visible before the constructor's writes. The holder relies on the JVM's class-initialization lock, `by lazy` uses a volatile field, and computeIfAbsent publishes through the map.", "from": "jmm-05"},
 {"q": "A static holder builds the connection to a receipt printer, and the constructor connects over the network. The printer is switched off when the first sale arrives. What do later calls get once it's switched back on?",
  "options": [
   "A fresh attempt: the holder retries on the next call",
   "The half-built connection from the first attempt",
   "null",
   "`NoClassDefFoundError` on every call until the program restarts"
  ],
  "answer": 3,
  "why": "If a static initializer throws, the JVM marks the class as failed and never initializes it again. The first caller gets ExceptionInInitializerError and everyone after it NoClassDefFoundError. Use a volatile double check or Kotlin `lazy`, which retry, for anything that can fail.", "from": "jmm-05"},
 {"q": "Two threads each set their own flag with `setRelease`, then read the other's flag with `getAcquire`. Can both read false?",
  "options": [
   "No: release/acquire keeps each write before the read that follows it",
   "Yes, even on x86; volatile accesses would forbid it",
   "Only on ARM",
   "Only if the flags are long fields"
  ],
  "answer": 1,
  "why": "Release keeps earlier accesses before the write, but a later read of a different variable may still pass it, and an x86 store buffer does exactly that. Only volatile's single total order forbids both reading false.", "from": "jmm-06"},
 {"q": "Many threads may try to record \"the first failure reason\", and only the first one should stick. Which tool fits?",
  "options": [
   "A plain String field",
   "`setRelease` through a VarHandle",
   "`compareAndSet(null, reason)` on an AtomicReference or a VarHandle",
   "A volatile String set with `if (reason == null) reason = r;`"
  ],
  "answer": 2,
  "why": "First writer wins is a read-modify-write, so it needs one atomic step. compareAndSet succeeds for exactly one caller and behaves like volatile. The volatile check-then-set leaves a gap between the check and the set, and setRelease is just a write.", "from": "jmm-06"}
]

T = {"id": "jmm", "intro": INTRO, "cheatsheet": CHEAT, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/jmm.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
