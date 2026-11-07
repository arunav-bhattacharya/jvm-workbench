import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/concurrency/src"
P = "java/workbench/concurrency/l11"
K = "kotlin/workbench/concurrency/l11"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"./gradlew :concurrency:demo -Pmain=workbench.concurrency.l11.{name}"
def code(name):
    """A Java demo with its Kotlin twin (Foo.kt with a top-level main, class FooKt)."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": demo(name), "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": demo(f"{name}Kt"), "file": f"{lab}/demo/{K}/{name}.kt"}}
def pair(java, kotlin):
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

J_REC = """public record Merchant(String id, int feeBps, Currency settlementCurrency) {   // fields are final

    public Merchant withFeeBps(int newFee) {             // "changes" return a new object
        return new Merchant(id, newFee, settlementCurrency);
    }
}"""
K_REC = """data class Merchant(val id: String, val feeBps: Int, val settlementCurrency: Currency)   // vals: final fields

val cheaper = merchant.copy(feeBps = 180)                // "changes" return a new object"""

J_SWAP = """private volatile Map<String, BigDecimal> rates = Map.of();      // an immutable map, replaced whole

void refresh(Map<String, BigDecimal> fresh) {
    rates = Map.copyOf(fresh);                 // build it completely, then publish it in one write
}

BigDecimal rate(String pair) {
    return rates.get(pair);                    // no lock: every map this field ever points to is immutable
}"""
K_SWAP = """@Volatile private var rates: Map<String, BigDecimal> = emptyMap()   // an immutable map, replaced whole

fun refresh(fresh: Map<String, BigDecimal>) {
    rates = java.util.Map.copyOf(fresh)        // build it completely, then publish it in one write
}

fun rate(pair: String): BigDecimal? = rates[pair]   // no lock: every map this field ever points to is immutable"""

J_SETTLE = """public record Settlement(String merchantId, List<Payment> payments) {
    public Settlement {
        payments = List.copyOf(payments);      // reassign the parameter: the field gets the copy
    }
}"""
K_SETTLE = """class Settlement(val merchantId: String, payments: List<Payment>) {
    val payments: List<Payment> = java.util.List.copyOf(payments)   // a plain parameter, copied into a property
}"""

J_STACK = """String statementLine(Payment p) {
    StringBuilder sb = new StringBuilder();      // local: no other thread can ever see it
    sb.append(p.id()).append(';').append(p.cents());
    return sb.toString();                        // only the immutable String leaves
}"""
K_STACK = """fun statementLine(p: Payment): String = buildString {   // the builder is local: no other thread can see it
    append(p.id).append(';').append(p.cents)
}                                                        // only the immutable String leaves"""

J_HAND = """List<Entry> batch = new ArrayList<>();          // owned by this thread
fill(batch);
queue.put(batch);                               // ownership moves to whoever takes it
// from here on, this thread never touches batch again"""
K_HAND = """val batch = ArrayList<Entry>()                  // owned by this thread
fill(batch)
queue.put(batch)                                // ownership moves to whoever takes it
// from here on, this thread never touches batch again"""

J_TL = """private static final ThreadLocal<String> TENANT = new ThreadLocal<>();

void handle(Request r) {
    TENANT.set(r.tenant());
    try {
        process(r);                  // deep code calls TENANT.get()
    } finally {
        TENANT.remove();             // the pool thread goes back clean
    }
}"""
K_TL = """private val TENANT = ThreadLocal<String>()

fun handle(r: Request) {
    TENANT.set(r.tenant)
    try {
        process(r)                   // deep code calls TENANT.get()
    } finally {
        TENANT.remove()              // the pool thread goes back clean
    }
}"""
J_SV = """static final ScopedValue<String> TENANT = ScopedValue.newInstance();   // JDK 25+

void handle(Request r) {
    ScopedValue.where(TENANT, r.tenant()).run(() -> process(r));   // bound for this call only
}"""
K_SV = """val TENANT: ScopedValue<String> = ScopedValue.newInstance()            // JDK 25+

fun handle(r: Request) {
    ScopedValue.where(TENANT, r.tenant).run { process(r) }          // bound for this call only
}"""

J_W1 = """public class Money {
    private long cents;
    private final Currency currency;

    public Money(long cents, Currency currency) { this.cents = cents; this.currency = currency; }

    public Money add(Money other) {        // changes this object, then returns it
        this.cents += other.cents;
        return this;
    }

    public long cents() { return cents; }
}

static final Money CARD_FEE = new Money(30, EUR);      // "a constant"

Money total = order.amount().add(CARD_FEE);            // also changes order.amount()"""
K_W1 = """class Money(private var centsValue: Long, val currency: Currency) {
    fun add(other: Money): Money {         // changes this object, then returns it
        centsValue += other.centsValue
        return this
    }

    val cents: Long get() = centsValue
}

val CARD_FEE = Money(30, EUR)                          // "a constant"

val total = order.amount.add(CARD_FEE)                 // also changes order.amount"""
J_W2 = """public record Money(long cents, Currency currency) {
    public Money {
        Objects.requireNonNull(currency, "currency");
    }

    public Money plus(Money other) {                     // 1. never change this; return a new value
        if (!currency.equals(other.currency)) throw new IllegalArgumentException("currency mismatch");
        return new Money(Math.addExact(cents, other.cents), currency);   // 2. overflow fails loudly
    }
}"""
K_W2 = """data class Money(val cents: Long, val currency: Currency) {
    operator fun plus(other: Money): Money {           // 1. never change this; return a new value
        require(currency == other.currency) { "currency mismatch" }
        return copy(cents = Math.addExact(cents, other.cents))   // 2. overflow fails loudly
    }
}"""
J_W3 = """BigDecimal total = BigDecimal.ZERO;
for (BigDecimal fee : fees) total.add(fee);            // does nothing: the result is thrown away
for (BigDecimal fee : fees) total = total.add(fee);    // right"""
K_W3 = """var total = BigDecimal.ZERO
for (fee in fees) total.add(fee)                 // does nothing: the result is thrown away
for (fee in fees) total += fee                   // right: plus() returns a new BigDecimal"""

J_DRILL = """public record Refund(String paymentId, List<LineItem> items, String reason) {
    public Refund {
        items = List.copyOf(items);              // copy in; unmodifiable for everyone
    }

    public Refund withReason(String newReason) {
        return new Refund(paymentId, items, newReason);   // a new object, same items
    }
}"""
K_DRILL = """class Refund(val paymentId: String, items: List<LineItem>, val reason: String) {
    val items: List<LineItem> = java.util.List.copyOf(items)    // copy in; unmodifiable for everyone

    fun withReason(newReason: String) = Refund(paymentId, items, newReason)   // a new object, same items
}"""

FIG = (
    '<svg viewBox="0 0 680 230" role="img" aria-label="Ownership hand-off: the producer thread builds a batch, puts it into a BlockingQueue, and the consumer thread takes it and owns it from then on">'
    '<rect class="box-a" x="30" y="60" width="170" height="70" rx="8"/>'
    '<text class="t" x="115" y="90" text-anchor="middle">request thread</text>'
    '<text class="t-s t-m" x="115" y="112" text-anchor="middle">builds the batch</text>'
    '<rect class="box" x="255" y="70" width="170" height="50" rx="8"/>'
    '<text class="t t-code" x="340" y="100" text-anchor="middle">BlockingQueue</text>'
    '<rect class="box-b" x="480" y="60" width="170" height="70" rx="8"/>'
    '<text class="t" x="565" y="90" text-anchor="middle">writer thread</text>'
    '<text class="t-s t-m" x="565" y="112" text-anchor="middle">owns it from here</text>'
    '<line class="ln-a" x1="200" y1="95" x2="252" y2="95" marker-end="url(#arr)"/>'
    '<text class="t-s t-code" x="226" y="52" text-anchor="middle">put(batch)</text>'
    '<line class="ln-a" x1="425" y1="95" x2="477" y2="95" marker-end="url(#arr)"/>'
    '<text class="t-s t-code" x="451" y="52" text-anchor="middle">take()</text>'
    '<line class="ln" x1="30" y1="160" x2="300" y2="160"/>'
    '<text class="t-s" x="165" y="180" text-anchor="middle">owner: request thread</text>'
    '<line class="ln" x1="380" y1="160" x2="650" y2="160"/>'
    '<text class="t-s" x="515" y="180" text-anchor="middle">owner: writer thread</text>'
    '<text class="t-s t-a" x="340" y="164" text-anchor="middle">happens-before</text>'
    '<text class="t-s t-bad" x="340" y="212" text-anchor="middle">after put, the request thread never touches the batch again</text>'
    '</svg>'
)

L = {
 "id": "conc-11",
 "title": "Don't share: immutability, confinement, ThreadLocal",
 "minutes": 36,
 "goal": "By the end you can remove shared mutable state instead of locking it: build deeply immutable objects, publish snapshots, keep state confined to one thread, hand objects over through a queue, and use `ThreadLocal` without leaking between requests.",
 "warmup": {
  "q": "`record Quote(String pair, List<BigDecimal> tiers) {}`. A caller builds it from an `ArrayList`, then adds an element to that same `ArrayList`. What does `quote.tiers()` show?",
  "options": ["The original elements: records are immutable", "The new element too: the record holds the caller's list", "It throws `UnsupportedOperationException` when the caller adds", "It depends on whether the record was built with `new`"],
  "answer": 1,
  "why": "A record's fields are final, so `tiers` will always point to the same list. But it's the caller's list, and nothing stops the caller from changing it. Records are shallowly immutable. To make the quote really immutable, copy the list in a compact constructor with `List.copyOf`."
 },
 "sections": [
  {
   "h": "Immutable objects need no locks",
   "body": "The surest way to avoid a race is to have nothing to race on. If no thread can change an object after it is built, every thread can read it at any time, with no lock, no `volatile` and no atomics. Lesson 3 of this track listed \"don't share\" as the first fix to reach for. This lesson is about that fix.\n\nAn object is immutable when all its fields are `final` and set in the constructor, it has no setters, every mutable thing it holds is copied in and never handed out, and `this` doesn't escape during construction. Records and Kotlin data classes with `val`s get you most of the way:\n\n" + pair(J_REC, K_REC) + "\n\n`final` fields also carry a guarantee from the memory model (JLS 17.5). A thread that gets a reference to the object after its constructor has finished sees the correct values of its `final` fields, even if the reference reached it through a data race. Non-final fields have no such promise. The memory model track covers why.\n\nThe pattern that follows is the cheapest way to share data that changes now and then: keep an immutable snapshot behind a `volatile` reference and replace it whole.\n\n" + pair(J_SWAP, K_SWAP) + "\n\nThis is the FX cache from lesson 7 of this track without any lock. The refresher builds the new map off to the side, where no reader can see it, and publishes it with one `volatile` write. A reader that reads the field once sees one complete version. If a reader needs several values from the same version, it copies the reference into a local first and reads them all from that.",
   "try": {
    "title": "Half-done refreshes, counted",
    "minutes": 3,
    "steps": [
     "Read `SnapshotSwap`. A refresher moves four FX rates to a new version over and over. It updates a `ConcurrentHashMap` in place, and also publishes an immutable snapshot through a `volatile` field.",
     "For one second, the main thread reads all four rates from each and counts reads that saw two versions at once. Predict both counts.",
     "Run it."
    ],
    "code": code("SnapshotSwap"),
    "expect": "The shared mutable map shows mixed versions in hundreds of thousands of reads (271,876 of 1,422,759 in one run here), although every single `put` and `get` was thread-safe. The immutable snapshot shows 0, every run."
   }
  },
  {
   "h": "Records and data classes are only shallowly immutable",
   "body": "`final` freezes the reference, not the object behind it. A record that stores a caller's `ArrayList` or `byte[]` can change whenever the caller changes it, and so can anyone you hand the array to. The lab's `FxQuote` has exactly this problem. The fix is a **defensive copy**: copy mutable things on the way in, and, for arrays, on the way out too.\n\n" + pair(J_SETTLE, K_SETTLE) + "\n\nA few details decide whether the copy works.\n\n`List.copyOf` makes an unmodifiable copy: later changes to the source don't show, and `add` on the copy throws. `Collections.unmodifiableList(list)` is not a copy. It is a read-only view of the caller's list, so the caller's later changes show straight through it.\n\nArrays can't be made read-only. Clone in the constructor, and clone again in the accessor, or keep the data in an immutable type instead.\n\nElements must be immutable too. A copied list of mutable `Payment` objects is a new list of the same shared objects.\n\nKotlin adds one trap of its own. `List` is a read-only *interface*, not an immutable list: a `data class` with `val tiers: List<Tier>` stores whatever `MutableList` the caller passed, and Java code, or a cast, can still change it. A data class also can't copy its constructor parameters, because those parameters are its properties. Use a plain class, as above, when you need the copy.\n\nIn Java, `BigDecimal`, `String`, `Instant`, `LocalDate`, `UUID` and the boxed numbers are immutable already. `Date`, `Calendar` and arrays are not.",
   "try": {
    "title": "Mutate a record from outside",
    "minutes": 3,
    "steps": [
     "Read `ShallowRecord`. `ShallowQuote` keeps the caller's list and array; `DeepQuote` copies them in and out. A third reference is an `unmodifiableList` view.",
     "After construction, the caller changes its list and array, and a reader writes into the array it got from `signature()`. Predict all three lines.",
     "Run it, then run the Kotlin twin, which adds one more line."
    ],
    "code": code("ShallowRecord"),
    "expect": "The shallow quote shows the extra tier and a signature of `[0, 0, 7]`: both the caller and a reader changed it. The deep quote still shows one tier and `[7, 7, 7]`. The `unmodifiableList` view shows the extra tier, because it's a view. In Kotlin, a cast to `MutableList` adds to the shallow quote's \"read-only\" list."
   }
  },
  {
   "h": "Confinement keeps mutable state on one thread",
   "body": "Mutable state is fine as long as only one thread can reach it. That is **confinement**, and you already use it every day.\n\nStack confinement is the simplest: local variables live on one thread's stack. A `StringBuilder` or `ArrayList` created inside a method and never stored anywhere else needs no protection at all.\n\n" + pair(J_STACK, K_STACK) + "\n\nThread confinement is the same idea at a larger scale: one thread owns some state, and every other thread asks that thread to act on it. A Kafka consumer is the classic case. Each partition is read by one consumer thread at a time, so per-partition state such as the last processed offset or a running total can live in a plain `HashMap` that only that thread touches. Event loops work the same way.\n\nWhen work moves between threads, move ownership with it. A request thread builds a batch, puts it into a `BlockingQueue`, and never touches it again. The writer thread takes it and owns it from then on.\n\n" + pair(J_HAND, K_HAND) + "\n\nThe queue does two jobs. It hands the object over, and it makes the hand-off visible: everything the producer did before `put` happens-before the consumer's `take` returns. The figure shows the moment ownership changes. The rule is all on the producer: once you've handed it over, it isn't yours. A producer that reuses the list for the next batch is sharing a mutable object with no synchronization at all, and the writer sees half-cleared batches.",
   "figure": {"svg": FIG, "caption": "Ownership moves through the queue. Writes before put happen-before the take, and the old owner never touches the batch again."},
   "try": {
    "title": "Hand over, or keep using?",
    "minutes": 3,
    "steps": [
     "Read `HandOff`. A producer fills 5,000 batches of 100 entries and puts each into a queue. A writer thread checks that every batch it takes is complete and in order.",
     "Run it. Then run it with `-Pargs=reuse`, where the producer clears and refills one list instead of creating a new one.",
     "Run the `reuse` version a few times. Is the damage count the same each time?"
    ],
    "code": code("HandOff"),
    "expect": "With a new list each time: 0 damaged batches. With `reuse`: some batches arrive damaged (from about a dozen to a few hundred in runs here), and the count changes every run. A lucky run could even show 0, which is exactly why this bug survives testing."
   }
  },
  {
   "h": "ThreadLocal gives each thread its own copy, and pools keep it forever",
   "body": "`ThreadLocal<T>` gives every thread its own value for the same variable. It has two common uses: a per-thread copy of an object that isn't thread-safe, and request context, such as the tenant or user, that deep code reads without passing it around. Logging MDC is usually a `ThreadLocal` underneath.\n\nThe catch is that pool threads live forever, and so does whatever you left on them. A value set for one request is still there when the same thread serves the next one. If the next request sets nothing, it runs as the previous customer. That's a data leak between merchants, in a payment system. The rule has no exceptions: **set it, then remove it in `finally`**.\n\n" + pair(J_TL, K_TL) + "\n\nCall `remove()`, not `set(null)`. `remove()` deletes the thread's entry; `set(null)` keeps an entry that holds `null`.\n\nFor non-thread-safe helpers, prefer an immutable replacement over a per-thread copy. `DateTimeFormatter` is immutable, so one shared instance replaces a `ThreadLocal<SimpleDateFormat>`. Per-thread copies also scale badly with virtual threads, where every task is a new thread with an empty copy. The virtual threads track goes into that.\n\nFor request context, JDK 25 made **scoped values** final (JEP 506). A scoped value is bound for the duration of one call and is gone when the call returns, so there is nothing to forget:\n\n" + pair(J_SV, K_SV) + "\n\nThat code needs JDK 25 or later; on JDK 21 to 24 the API is a preview, so the labs, which compile for JDK 21, use `ThreadLocal`.",
   "try": {
    "title": "Watch one customer's context leak into another's request",
    "minutes": 3,
    "steps": [
     "Read `ThreadLocalBleed`. Six requests run one after another on a pool of one thread. The handler sets the user only when the request carries one.",
     "Predict what each request without a user runs as, in the leaky version and in the clean one.",
     "Run it."
    ],
    "code": code("ThreadLocalBleed"),
    "expect": "Leaky: the first anonymous request runs as `alice`, and the next two run as `bob`, whoever that thread served last. Clean: every anonymous request runs as `null`, because `remove()` in `finally` put the thread back as it was. A pool of one makes it happen every time. With 200 threads it happens rarely and randomly, which is how it reaches production."
   },
   "refs": [
    {"title": "JEP 506: Scoped Values", "url": "https://openjdk.org/jeps/506", "kind": "read"}
   ]
  }
 ],
 "analogy": "An immutable object is a printed price list: anyone can read it at the same time, and to change a price you print a new list and swap it on the wall. Confinement is a ledger kept in one clerk's desk; others pass notes to that clerk instead of writing in it. A hand-off through a queue is passing a folder across the counter: once it's handed over, you don't reach back to add a page. A `ThreadLocal` on a pool thread is a locker that the next shift inherits, with whatever the last person left in it, unless someone empties it at the end of every shift. The analogy breaks at the price list: a printed list can't be edited by a stranger, but a Java object with one unprotected `List` field can.",
 "in_your_world": "Kafka already confines state for you: one partition is read by one consumer thread at a time, so per-partition state needs no locks, as long as you don't hand it to another thread. Events and commands on the bus should be immutable records, so a consumer can pass them to a worker pool without copying. Temporal runs a workflow's code one thread at a time, so workflow state is confined by design; activities run on an ordinary thread pool and get none of that protection. And look at every `ThreadLocal` in your Quarkus services, including the ones inside libraries: logging MDC, a tenant or merchant context, a security principal. Each one needs a `finally` that clears it, or a framework hook that does it for you. A merchant id that leaks from one request into the next is a reportable incident, not just a bug.",
 "mistake": "The most common mistake is setting a `ThreadLocal` and never clearing it, usually because the code was written and tested where each request seemed to get a fresh thread. On a pool, the value stays on the thread. The next request that doesn't set it reads the previous request's tenant, user or MDC fields, and the logs show one customer's id on another customer's payment. Unit tests rarely catch it, because each test usually runs on a fresh thread or in a fresh JVM. The fix is mechanical: every `set` is paired with a `remove()` in a `finally`, or replaced by a scoped value on JDK 25 and later. The lab's `TenantScope` goes one step further and restores the previous value, so nested calls work too.",
 "compare": {
  "title": "A deeply immutable value in Java and Kotlin",
  "java": {"title": "Java record", "src": J_SETTLE},
  "kotlin": {"title": "Kotlin class", "src": K_SETTLE + "\n// a data class can't do this: its constructor parameters ARE the properties"},
  "note": "Both compile to a class with `final` fields, so both get the memory model's final-field guarantee. The difference is where the copy can go. A Java record's compact constructor may reassign its parameters before the fields are set, so `payments = List.copyOf(payments)` stores the copy. A Kotlin data class can't do that, because its primary-constructor parameters are the properties, so you use a plain class with a separate property, as here, or a private constructor and a factory. Kotlin's `List` type doesn't help as much as it looks: it's a read-only interface, and `listOf` or `toList` results can still be changed through a cast or from Java. `java.util.List.copyOf` gives you a list that is unmodifiable for everyone. Data class `copy()` is shallow too: the copy shares the same list."
 },
 "worked": {
  "title": "A shared constant that someone changed",
  "steps": [
   {"say": "A payment service adds a card fee to every order. `Money` looks like a value, and `CARD_FEE` looks like a constant. Read it and find what changes, and for whom.",
    "code": J_W1, "lang": "java", "alt_code": K_W1, "alt_lang": "kotlin"},
   {"say": "`add` changes the object it's called on. The line `order.amount().add(CARD_FEE)` changes the order's own amount. Somewhere else, `CARD_FEE.add(surcharge)` changes the fee for every request on every thread. And because `cents` is neither `final` nor `volatile`, other threads may see the old fee, the new one, or a mix, at different times. `static final` on the reference didn't make the object constant.", "code": "", "lang": ""},
   {"say": "Make `Money` a value: final fields, and operations that return a new instance. Now `CARD_FEE` can be read by 200 threads with no lock, and nobody can change it.",
    "code": J_W2, "lang": "java", "alt_code": K_W2, "alt_lang": "kotlin"},
   {"say": "Before reading on, explain to yourself why the record version needs no synchronization even though `CARD_FEE` is read by every request thread. Then look at the classic trap with immutable types, which catches people moving from mutable ones: calling the operation and ignoring the result.",
    "code": J_W3, "lang": "java", "alt_code": K_W3, "alt_lang": "kotlin"},
   {"say": "Answer: the fields are `final`, set once in the constructor, and the object never changes, so every thread that can see the reference sees 30 EUR. There is nothing to race on. The price is an allocation per operation, which the JIT often removes when the object doesn't escape. For money, that trade is easy.", "code": "", "lang": ""}
 ]},
 "lab": {
  "title": "A deeply immutable quote and a tenant scope that cleans up",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/FxQuote.java", f"{lab}/main/{P}/TenantScope.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l11.*'",
  "steps": [
   "Run the tests. All six fail. The three `FxQuote` tests change the quote from outside, through the list you passed in, the list it returns, and its signature array. The three `TenantScope` tests run on a pool of one thread and find a tenant left over from an earlier call.",
   "Give `FxQuote` a compact constructor that replaces `tiers` with `List.copyOf(tiers)` and `signature` with a clone.",
   "Override `signature()` so it returns a clone, not the field.",
   "Fix `TenantScope.runAs`: remember the previous value, set the new one (or `remove()` for `null`), run the work in a `try`, and in `finally` put the previous value back (or `remove()` if there was none).",
   "Run the tests until all six pass."
  ],
  "hints": [
   "In a compact constructor you assign to the parameter (`tiers = List.copyOf(tiers);`), not to `this.tiers`. The record assigns the fields after your code runs.",
   "`List.copyOf` also rejects `null` elements, which is usually what you want in a quote.",
   "Restoring the previous value instead of always calling `remove()` makes nested calls work: an inner `runAs` must hand the thread back to the outer one, not wipe it."
  ],
  "done_when": "All six tests in `DontShareTest` pass."
 },
 "drill": {
  "title": "An immutable refund from memory",
  "minutes": 4,
  "prompt": "Close this page. Write an immutable `Refund` with a payment id, a list of line items and a reason, safe to share between threads, plus `withReason(String)` that returns a changed copy. Check: can the caller's list, or the list you return, change your refund?",
  "answer": {"lang": "java", "src": J_DRILL, "alt": {"lang": "kotlin", "title": "Kotlin", "src": K_DRILL}}
 },
 "recap": [
  "An object nobody can change needs no locks. Make fields final, add no setters, copy mutable parts, and don't let `this` escape.",
  "For data that changes now and then, publish an immutable snapshot through a `volatile` field and replace it whole.",
  "Records and data classes are shallow. Copy lists with `List.copyOf` and clone arrays in and out. `unmodifiableList` is a view, not a copy.",
  "Confinement: locals, one owner thread (one Kafka partition per consumer), or ownership handed through a queue and never touched again.",
  "Every `ThreadLocal.set` on a pool thread needs a `remove()` in `finally`. On JDK 25+, scoped values do the cleanup for you."
 ],
 "quiz": [
  {"q": "Which of these can be shared between threads with no synchronization at all?",
   "options": ["A record whose `List<String>` component is the caller's `ArrayList`", "A class with `volatile` fields and setters", "A final class whose `private final` fields are a `String`, an `Instant` and a `BigDecimal`, with no setters", "A record with an `int[]` component and the default accessor"],
   "answer": 2, "why": "All three field types are immutable and the fields are final, so the object can never change and the final-field rule makes it visible correctly. The record with the caller's list and the record with an array can be changed from outside. `volatile` fields with setters make each write visible, but the object still changes under readers."},
  {"q": "A constructor stores `this.items = Collections.unmodifiableList(items);`. The caller later adds an item to its own `items` list. What does the object's list show?",
   "options": ["The original items only", "It throws `UnsupportedOperationException` in the caller", "The caller's add is ignored", "The new item too, because `unmodifiableList` is a view of the caller's list"],
   "answer": 3, "why": "`unmodifiableList` only stops *you* from changing the list through that reference. It still reads the caller's list, so the caller's changes show through. `List.copyOf` makes a copy that nobody can change."},
  {"q": "From explicit locks: an FX rate table is replaced as a whole every 5 seconds and read 5,000 times a second. What is the simplest correct design?",
   "options": ["A `ReentrantReadWriteLock` around a `HashMap`", "A `volatile` field holding an immutable map, replaced with a freshly built `Map.copyOf(...)` on each refresh", "A `ConcurrentHashMap` refreshed with `clear()` and `putAll()`", "A `synchronized` getter and setter on a `HashMap`"],
   "answer": 1, "why": "Readers never block, and each one sees one complete version, because the new map is built fully before one `volatile` write publishes it. The read-write lock also works, with more code and some cost on every read. `clear` plus `putAll` on a concurrent map lets readers see an empty or half-filled table.",
   "from": "conc-07"},
  {"q": "A Quarkus request handler does `USER.set(request.user())` on a `ThreadLocal` when the request is authenticated, and never removes it. What does a later anonymous request on the same worker thread see?",
   "options": ["The previous request's user", "`null`, because each request gets a fresh thread", "An `IllegalStateException`", "A random user from another thread"],
   "answer": 0, "why": "Worker threads come from a pool and are reused. The value stays on the thread until someone removes it, so the anonymous request runs as whoever that thread served last. Pair every `set` with `remove()` in `finally`."},
  {"q": "A producer puts an `ArrayList` of entries into a `BlockingQueue`, then calls `clear()` on the same list and refills it for the next batch. What does that do to the consumer?",
   "options": ["Nothing: `take()` returns a copy of the list", "Nothing: `put` made the list thread-safe", "The consumer can see a partly cleared or refilled batch, because the producer kept changing an object it had handed over", "`put` throws, because the list is already in the queue"],
   "answer": 2, "why": "The queue hands over a reference, not a copy. `put` happens-before `take` only for what the producer did before the `put`. After that, the producer and consumer share one mutable list with no synchronization. Hand over a new list each time."}
 ],
 "flashcards": [
  {"front": "What does a class need to be immutable?", "back": "All fields `final` and set in the constructor, no setters, mutable components copied in and never handed out, and `this` doesn't escape during construction."},
  {"front": "What does the memory model guarantee for `final` fields?", "back": "A thread that gets a reference to the object after its constructor finished sees the correct values of its final fields, even without synchronization."},
  {"front": "Is a record with a `List` component immutable?", "back": "Only shallowly. Copy it in the compact constructor: `items = List.copyOf(items);`."},
  {"front": "`Collections.unmodifiableList(list)` vs `List.copyOf(list)`?", "back": "`unmodifiableList` is a read-only view: the owner's later changes show through. `List.copyOf` is an unmodifiable copy that nobody can change."},
  {"front": "How do you share data that changes rarely, without locks?", "back": "Build a new immutable snapshot, then publish it with one write to a `volatile` field (or an `AtomicReference`). Readers read the reference once."},
  {"front": "A pool thread runs a task that calls `ThreadLocal.set` and never `remove()`. What happens next?", "back": "The value stays on the thread. The next task on that thread sees it if it doesn't set its own."},
  {"front": "What makes passing a mutable object through a `BlockingQueue` safe?", "back": "`put` happens-before `take`, so the consumer sees everything done before the put, as long as the producer never touches the object again."}
 ],
 "terms": [
  {"term": "Immutable object", "plain": "An object whose state can't change after construction; safe to share without locks."},
  {"term": "Defensive copy", "plain": "Copying a mutable argument or return value so no one else can change your object through it."},
  {"term": "Shallow immutability", "plain": "Final references to objects that can still change, as in a record holding an `ArrayList`."},
  {"term": "Snapshot publication", "plain": "Replacing a whole immutable object through one `volatile` write, so readers see one complete version."},
  {"term": "Thread confinement", "plain": "Keeping mutable state reachable by only one thread."},
  {"term": "Ownership hand-off", "plain": "Passing an object to another thread, through a queue, and never touching it again."},
  {"term": "ThreadLocal", "plain": "A variable with a separate value per thread; values live as long as the thread unless removed."},
  {"term": "Scoped value", "plain": "A JDK 25 value bound for one call and its callees, gone when the call returns (JEP 506)."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to add a lock around a merchant-settings object that a refresher updates every minute and every request reads. Explain the alternative you'd suggest, and why it is safe.",
  "answer": "I'd make the settings an immutable record, with final fields and copied lists, and keep the current one in a `volatile` field. The refresher builds a complete new settings object off to the side and then assigns it to the field in one write. Requests read the field once and use that object. It's safe because nothing a reader can reach is ever modified: the old object stays valid for whoever is still using it, and the `volatile` write makes the new object, including all its fields, visible to every reader that reads the field afterwards. Readers never wait, and there's no lock to forget. The one thing to watch is a reader that reads the field twice and gets two different versions, so read it into a local first."
 },
 "deeper": {
  "minutes": 10,
  "body": "Each `Thread` object has its own small hash map for its thread locals, called `ThreadLocalMap`. The keys are weak references to the `ThreadLocal` objects, and the values are strong references. When a `ThreadLocal` itself becomes garbage, its key goes away, but the value stays in the map until a later `get`, `set` or `remove` on that thread happens to clean it up. On a pool thread that lives for days, that can be a long time. In application servers this is a famous leak: a value whose class came from a redeployed web application keeps that application's whole class loader alive. `remove()` avoids all of it.\n\n`InheritableThreadLocal` copies values from a parent thread to a child thread when the child is created. It does nothing useful with pools, because pool threads are created once, long before the request that submits work to them.\n\nScoped values (JEP 506, final in JDK 25) fix the design problems rather than the symptoms. A binding is immutable: there is no `set`, so code deep in the call stack can't change the tenant under you. It has a clear lifetime: it ends when `run` or `call` returns, even on an exception. And it is cheap to share with child tasks: with structured concurrency, still a preview API in JDK 25, threads forked inside the scope see the same bindings without copying a map per thread.\n\nOne immutability trap to know: an object is only safe to share through a data race if `this` didn't escape while the constructor was running. A constructor that registers `this` as a listener, or starts a thread that uses `this`, hands out the object before its final fields are guaranteed to be visible. Build first, register after. The memory model track's lesson on safe publication covers the full rules."
 },
 "sources": [
  {"title": "Java Language Specification, chapter 17, section 17.5: final field semantics", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html"},
  {"title": "ThreadLocal.java at jdk-25-ga", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/lang/ThreadLocal.java"},
  {"title": "JEP 506: Scoped Values", "url": "https://openjdk.org/jeps/506"},
  {"title": "Java Concurrency in Practice, Goetz et al., chapter 3 (sharing objects)", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/conc-11.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
