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
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

# ---------------------------------------------------------------- code samples in the prose
J_LIVE = """// Naive: every call is thread-safe, the refresh as a whole is not
private final Map<String, Long> prices = new ConcurrentHashMap<>();

void refresh(Map<String, Long> fresh) {
    prices.putAll(fresh);              // one price at a time, while the tills read
}

Long price(String item) {
    return prices.get(item);
}"""
K_LIVE = """// Naive: every call is thread-safe, the refresh as a whole is not
private val prices = ConcurrentHashMap<String, Long>()

fun refresh(fresh: Map<String, Long>) {
    prices.putAll(fresh)               // one price at a time, while the tills read
}

fun price(item: String): Long? = prices[item]"""

J_REC = """public record Price(String item, long cents) {       // fields are final

    public Price withCents(long newCents) {          // "changes" return a new object
        return new Price(item, newCents);
    }
}"""
K_REC = """data class Price(val item: String, val cents: Long)   // vals: final fields

val cheaper = bread.copy(cents = 230)                // "changes" return a new object"""

J_SWAP = """// Fixed: an immutable snapshot, replaced whole
private volatile Map<String, Long> prices = Map.of();

void refresh(Map<String, Long> fresh) {
    prices = Map.copyOf(fresh);        // build it completely, then publish it in one write
}

Long price(String item) {
    return prices.get(item);           // no lock: every map this field ever holds is immutable
}"""
K_SWAP = """// Fixed: an immutable snapshot, replaced whole
@Volatile private var prices: Map<String, Long> = emptyMap()

fun refresh(fresh: Map<String, Long>) {
    prices = java.util.Map.copyOf(fresh)   // build it completely, then publish it in one write
}

fun price(item: String): Long? = prices[item]   // no lock: every map this field ever holds is immutable"""

J_SHALLOW = """// Naive: the fields are final, the list and the array are not
record Quote(String item, List<String> tiers, byte[] signature) {}

List<String> tiers = new ArrayList<>(List.of("1 to 9 loaves at 2.50"));
Quote quote = new Quote("bread", tiers, signature);
tiers.add("10 or more at 0.01");          // the caller keeps changing its own list"""
K_SHALLOW = """// Naive: the vals are final, the list and the array are not
data class Quote(val item: String, val tiers: List<String>, val signature: ByteArray)

val tiers = mutableListOf("1 to 9 loaves at 2.50")
val quote = Quote("bread", tiers, signature)
tiers.add("10 or more at 0.01")           // the caller keeps changing its own list"""

J_DEEP = """// Fixed: copy in, and copy the array out
record Quote(String item, List<String> tiers, byte[] signature) {
    Quote {
        tiers = List.copyOf(tiers);         // reassign the parameter: the field gets the copy
        signature = signature.clone();
    }

    @Override
    public byte[] signature() {
        return signature.clone();           // readers get a copy, never our array
    }
}"""
K_DEEP = """// Fixed: copy in, and copy the array out
class Quote(val item: String, tiers: List<String>, signature: ByteArray) {
    val tiers: List<String> = java.util.List.copyOf(tiers)   // unmodifiable, even through a cast
    private val sig = signature.copyOf()
    val signature: ByteArray get() = sig.copyOf()             // readers get a copy, never our array
}"""

J_STACK = """String receiptLine(Sale s) {
    StringBuilder sb = new StringBuilder();      // local: no other thread can ever see it
    sb.append(s.item()).append(';').append(s.cents());
    return sb.toString();                        // only the immutable String leaves
}"""
K_STACK = """fun receiptLine(s: Sale): String = buildString {   // the builder is local: no other thread can see it
    append(s.item).append(';').append(s.cents)
}                                                  // only the immutable String leaves"""

J_HAND = """List<String> ticket = new ArrayList<>();         // owned by the waiter's thread
ticket.add("soup");
ticket.add("bread");
rail.put(ticket);                                // ownership moves to whoever takes it
// from here on, the waiter never touches ticket again"""
K_HAND = """val ticket = ArrayList<String>()                 // owned by the waiter's thread
ticket.add("soup")
ticket.add("bread")
rail.put(ticket)                                 // ownership moves to whoever takes it
// from here on, the waiter never touches ticket again"""

J_TL_BAD = """// Naive: sets the user, never clears it
static final ThreadLocal<String> USER = new ThreadLocal<>();

String handle(String user) {
    if (user != null) USER.set(user);
    return "request(" + user + ") ran as " + USER.get();
}"""
K_TL_BAD = """// Naive: sets the user, never clears it
val USER = ThreadLocal<String>()

fun handle(user: String?): String {
    if (user != null) USER.set(user)
    return "request($user) ran as ${USER.get()}"
}"""

J_TL = """static final ThreadLocal<String> USER = new ThreadLocal<>();

void handle(Request r) {
    USER.set(r.user());
    try {
        process(r);                  // deep code calls USER.get()
    } finally {
        USER.remove();               // housekeeping: the pool thread goes back clean
    }
}"""
K_TL = """val USER = ThreadLocal<String>()

fun handle(r: Request) {
    USER.set(r.user)
    try {
        process(r)                   // deep code calls USER.get()
    } finally {
        USER.remove()                // housekeeping: the pool thread goes back clean
    }
}"""
J_SV = """static final ScopedValue<String> USER = ScopedValue.newInstance();   // JDK 25+

void handle(Request r) {
    ScopedValue.where(USER, r.user()).run(() -> process(r));   // bound for this call only
}"""
K_SV = """val USER: ScopedValue<String> = ScopedValue.newInstance()            // JDK 25+

fun handle(r: Request) {
    ScopedValue.where(USER, r.user).run { process(r) }          // bound for this call only
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

static final Money DELIVERY_FEE = new Money(300, EUR);     // "a constant"

Money total = order.amount().add(DELIVERY_FEE);            // also changes order.amount()"""
K_W1 = """class Money(private var centsValue: Long, val currency: Currency) {
    fun add(other: Money): Money {         // changes this object, then returns it
        centsValue += other.centsValue
        return this
    }

    val cents: Long get() = centsValue
}

val DELIVERY_FEE = Money(300, EUR)                         // "a constant"

val total = order.amount.add(DELIVERY_FEE)                 // also changes order.amount"""
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

J_DRILL = """public record Order(String customer, List<LineItem> items, String note) {
    public Order {
        items = List.copyOf(items);                   // copy in; unmodifiable for everyone
    }

    public Order withNote(String newNote) {
        return new Order(customer, items, newNote);   // a new object, same items
    }
}"""
K_DRILL = """class Order(val customer: String, items: List<LineItem>, val note: String) {
    val items: List<LineItem> = java.util.List.copyOf(items)   // copy in; unmodifiable for everyone

    fun withNote(newNote: String) = Order(customer, items, newNote)   // a new object, same items
}"""

J_CMP = """public record Receipt(String till, List<Line> lines) {
    public Receipt {
        lines = List.copyOf(lines);      // reassign the parameter: the field gets the copy
    }
}"""
K_CMP = """class Receipt(val till: String, lines: List<Line>) {
    val lines: List<Line> = java.util.List.copyOf(lines)   // a plain parameter, copied into a property
}
// a data class can't do this: its constructor parameters ARE the properties"""

FIG = (
    '<svg viewBox="0 0 680 230" role="img" aria-label="Ownership hand-off: the waiter thread writes a ticket and puts it on the rail, a BlockingQueue; the cook thread takes it and owns it from then on">'
    '<rect class="box-a" x="30" y="60" width="170" height="70" rx="8"/>'
    '<text class="t" x="115" y="90" text-anchor="middle">waiter thread</text>'
    '<text class="t-s t-m" x="115" y="112" text-anchor="middle">writes the ticket</text>'
    '<rect class="box" x="255" y="70" width="170" height="50" rx="8"/>'
    '<text class="t t-code" x="340" y="100" text-anchor="middle">BlockingQueue</text>'
    '<rect class="box-b" x="480" y="60" width="170" height="70" rx="8"/>'
    '<text class="t" x="565" y="90" text-anchor="middle">cook thread</text>'
    '<text class="t-s t-m" x="565" y="112" text-anchor="middle">owns it from here</text>'
    '<line class="ln-a" x1="200" y1="95" x2="252" y2="95" marker-end="url(#arr)"/>'
    '<text class="t-s t-code" x="226" y="52" text-anchor="middle">put(ticket)</text>'
    '<line class="ln-a" x1="425" y1="95" x2="477" y2="95" marker-end="url(#arr)"/>'
    '<text class="t-s t-code" x="451" y="52" text-anchor="middle">take()</text>'
    '<line class="ln" x1="30" y1="160" x2="290" y2="160"/>'
    '<text class="t-s" x="160" y="180" text-anchor="middle">owner: waiter thread</text>'
    '<line class="ln" x1="390" y1="160" x2="650" y2="160"/>'
    '<text class="t-s" x="520" y="180" text-anchor="middle">owner: cook thread</text>'
    '<text class="t-s t-a" x="340" y="164" text-anchor="middle">happens-before</text>'
    '<text class="t-s t-bad" x="340" y="212" text-anchor="middle">after put, the waiter never touches the ticket again</text>'
    '</svg>'
)

OPENING = """Picture the price board above a shop's counter. Ten customers can read it at once, and nobody takes turns, because nobody writes on it while they read. When prices change, the owner doesn't erase numbers while people read. She prints a new board and hangs it up in one move.

The shop's program usually does the opposite. It keeps the prices in a map that one thread updates in place while the threads at the tills (the cash registers) read it. (A thread is one path of work that runs side by side with others in the same program.) For a moment, a till can see the new price of bread next to the old price of milk. After ten lessons of tools, the habit is to add one more: a lock around the map.

Synchronizers made threads wait for each other. This lesson removes the reason to wait. We'll take a race apart into its two ingredients, sharing and change, and remove them one at a time: objects that never change, state only one thread can reach, and values each thread keeps for itself. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Look back at every race in this track and you'll find the same two ingredients. In Race conditions, eight threads added deposits to one balance: the balance was shared, and it changed. In Deadlock, livelock and starvation, two transfers locked the same two accounts: shared, and changing. A race needs both, so taking away either one leaves nothing to lock.

**A race needs state that is shared and changing. Take away either one, and there is nothing to lock.**

This lesson takes them away one at a time, starting with change. Here's the shop's price list. A refresher thread moves every price to a new version now and then, and the tills read prices all day. Most programs start with one map, updated in place:

""" + pair(J_LIVE, K_LIVE) + """

`ConcurrentHashMap`, the thread-safe map from Concurrent collections, makes every single `put` and `get` safe. But a refresh is four puts, and a till can read between them. The Try it counts how often that happens. Each refresh moves all four prices (bread, milk, eggs and apples) to the same version number, and the main thread reads all four, over and over, for one second. A read that sees two versions at once caught a refresh half done. It printed:

```text
reads: 4,702,038   mixed versions, shared mutable map: 981,129   immutable snapshot: 0
```

About one read in five saw a price list that never existed. Every call was thread-safe, and the answer was still wrong.

Now take away change. An object is **immutable** when nobody can change it after it's built, and then every thread can read it at any time, with no lock. In Java that takes four things. All its fields are `final` and set in the constructor. It has no setters. Every changing thing it holds is copied in and never handed out. And the constructor doesn't let `this` escape, that is, it doesn't hand a reference to the half-built object to other code. A record, Java's short form for a class of final fields, gets you most of the way, and so does a Kotlin data class with `val`s:

""" + pair(J_REC, K_REC) + """

To "change" an immutable object, you build a new one. That's the price board again: print a new one and swap it. In code, the swap is one write to a `volatile` field, a field that every thread always reads fresh, so a write to it is seen by every later reader:

""" + pair(J_SWAP, K_SWAP) + """

The refresher builds the new map off to the side, where no till can see it. `Map.copyOf` makes it unmodifiable, and one `volatile` write publishes it. A till that reads the field once gets one complete version: the old board or the new one, never half of each. That's the `immutable snapshot: 0` in the output, every run. If a till needs several prices from the same version, it copies the field into a local variable first and reads them all from that.

`final` fields carry one more promise, from the Java memory model, the rules for what one thread sees of another thread's writes. A thread that gets a reference to an object after its constructor has finished sees the right values in its `final` fields, even if nothing else synchronized the hand-over. Non-final fields get no such promise, and the memory model track explains why.

The snapshot took away change. Records have a catch, though: they freeze less than they seem to."""

ASIDE0 = {
 "title": "Isn't a new object for every change slow?",
 "body": "You may wonder whether building a whole new map for every refresh costs too much. For a price list that changes a few times an hour and is read thousands of times a second, it costs nothing you could measure. Making a small object in the JVM, the program that runs your Java code, is cheap, often little more than moving a pointer, and short-lived objects are cheap to clean up. The JIT compiler, the part of the JVM that turns busy code into machine code, can sometimes remove the new object altogether. Where it does hurt is data that changes millions of times a second, such as a hit counter, and for that an atomic from Atomics and compare-and-set fits better."
}

# ---------------------------------------------------------------- section 1
S1 = """`final` freezes the reference, not the object it points to. A record that stores a caller's `ArrayList` or array changes whenever the caller changes that list, and so does anyone you hand the array to.

Here's the trap in the shop. A big customer asks for a price quote for bread, with tiers: one price up to 9 loaves, and a lower one for more. The quote also carries a signature, a few bytes that prove who made it. It's a record, so it looks safe:

""" + pair(J_SHALLOW, K_SHALLOW) + """

The Try it builds this quote, then changes the caller's list and array after construction, and also writes into the array it gets back from `signature()`. It printed:

```text
shallow: [1 to 9 loaves at 2.50, 10 or more at 0.01]  signature [0, 0, 7]
deep:    [1 to 9 loaves at 2.50]  signature [7, 7, 7]
unmodifiableList view: [1 to 9 loaves at 2.50, 10 or more at 0.01]
```

The "immutable" quote now sells bread at a cent a loaf, and its signature changed twice: once through the caller's array, and once through a reader's. Nothing in the record was reassigned. The objects behind its final fields changed. That's **shallow immutability**: final references to things that can still change.

The fix is a **defensive copy**: copy each changing part on the way in, and for arrays on the way out too. A record's compact constructor, the one with no parameter list, runs before the fields are set, so it can replace each parameter with a copy:

""" + pair(J_DEEP, K_DEEP) + """

That's the `deep` line in the output. A few details decide whether the copy works.

`List.copyOf` makes an unmodifiable copy: later changes to the source don't show, and `add` on the copy throws. `Collections.unmodifiableList(list)` is not a copy. It's a read-only view of the caller's list, so the caller's later changes show straight through it, as the third line of the output shows.

Arrays can't be made read-only. Clone them in the constructor and again in the accessor, or keep the data in an immutable type instead.

The elements must be immutable too. A copied list of changeable objects is a new list of the same shared objects. `String`, `BigDecimal`, `Instant`, `LocalDate` and the boxed numbers such as `Integer` are immutable already; arrays, `Date` and `Calendar` are not.

Kotlin adds one trap of its own. Its `List` type is a read-only *interface*, not an immutable list. A data class with `val tiers: List<String>` stores whatever `MutableList` the caller passed, and a cast or Java code can still change it. The Kotlin twin of the Try it adds a line to prove it. A data class also can't copy its constructor parameters, because those parameters are its properties. When you need the copy, use a plain class with a separate property, as above.

**A final field freezes the reference, not the object. Copy what can change.**

So far we've taken away change. The other ingredient is sharing: state that changes freely is still safe if only one thread can ever reach it."""

# ---------------------------------------------------------------- section 2
S2 = """Changing state is fine as long as only one thread can reach it. That's **confinement**, keeping state where only one thread can get at it, and you already use it every day.

Stack confinement is the simplest kind. Local variables live on one thread's stack, its private list of method calls in progress, and no other thread can see them. A `StringBuilder` or `ArrayList` created inside a method and never stored anywhere else needs no protection at all:

""" + pair(J_STACK, K_STACK) + """

Thread confinement is the same idea, made bigger. One thread owns some state, and every other thread asks that thread to act on it instead of touching the state itself. The mail-room helper from A thread's life worked this way: other parts of the program dropped messages into its tray, and only the helper ever sent them. Many screen toolkits work the same way, with one thread that is the only one allowed to draw on the screen.

When work has to move between threads, move the ownership with it. Back to the kitchen from wait, notify and guarded blocks: a waiter writes a ticket, clips it to the rail and never touches it again. The cook takes it and owns it from then on. In code, the rail is a `BlockingQueue`, the queue from Concurrent collections whose `take()` waits until something arrives:

""" + pair(J_HAND, K_HAND) + """

The queue does two jobs. It hands the ticket over, and it makes the hand-over visible. Everything the waiter wrote before `put` happens-before the cook's `take` returns, so the cook sees the whole ticket. (Happens-before is the memory model's promise that one thread sees what another wrote first.) The figure shows the moment the owner changes.

The whole duty sits on the waiter's side: once you've handed something over, it isn't yours. Picture a waiter who saves paper by erasing a ticket the cook is still reading and writing the next table's order on it. The Try it does exactly that with `-Pargs=reuse`: the waiter clears one list and fills it again instead of making a new one. Each ticket holds 100 numbered dishes, so the cook can check that nothing is missing or out of order:

```text
new ticket each time: 5,000 tickets handed over, 0 damaged
one ticket, reused: 5,000 tickets handed over, 447 damaged
```

The reused ticket is a changing object shared by two threads with no synchronization at all, and the cook found 447 half-written tickets. Run it again and the number changes: runs here ranged from 10 to over 3,000. A lucky run could even show 0, which is exactly how this bug gets through testing.

**A queue hands over the object, not a copy. After put, never touch it again.**

Confinement keeps state on one thread. The last tool in this lesson does something stranger: it gives every thread its own copy of the same variable."""

# ---------------------------------------------------------------- section 3
S3 = """`ThreadLocal<T>` gives every thread its own value for the same variable. Web services use it for request context. A web service answers requests from other programs over the network, and it handles each request on a thread. The handler stores the current user once, and code deep in the call chain reads it without passing it through every method. Many logging libraries keep per-request fields the same way, so every log line shows whose request it belongs to.

The catch is where the value lives. Each `Thread` object has its own small map from `ThreadLocal` to value, and `get()` looks in the current thread's map. The value stays there as long as the thread is alive. Now add a thread pool, a fixed group of threads that is reused for request after request. A pool thread lives for days, and so does whatever a request left on it.

A pool thread is like a hotel room. The next guest finds whatever the last guest left behind, unless housekeeping clears the room between stays. Here's a handler with no housekeeping. It sets the user only when the request carries one:

""" + pair(J_TL_BAD, K_TL_BAD) + """

The Try it runs six requests on a pool of one thread, so every request lands in the same room:

```text
  request(alice) ran as alice
  request(null) ran as alice
  request(bob) ran as bob
  request(null) ran as bob
  request(null) ran as bob
  request(carol) ran as carol
```

The first anonymous request ran as alice, and the next two ran as bob, whoever that thread served last. In a real service, that's one customer seeing another customer's data. With 200 pool threads instead of one, it happens rarely and at random, which is how it gets past testing and reaches real users.

**A pool thread keeps its thread-local values for good. Set them, then remove() them in finally.**

`remove()` is the housekeeping:

""" + pair(J_TL, K_TL) + """

Call `remove()`, not `set(null)`. `remove()` deletes the thread's entry, while `set(null)` keeps an entry that holds `null`. With the `finally` in place, the same six requests run as `null` whenever no user came in. The lab's `TenantScope` carries the customer company a request works for, and it goes one step further. It puts back the previous value, so a call nested inside another hands the thread back exactly as it found it.

`ThreadLocal`'s other common use is a private copy of an object that isn't thread-safe, such as the old `SimpleDateFormat`. Prefer an immutable replacement there: `DateTimeFormatter` is immutable, so one shared instance does the job of a copy per thread. Per-thread copies also scale badly with virtual threads, the very light threads from JDK 21 that programs start one per task: every task gets a new thread, and so a new, empty copy. The virtual threads track goes into that.

For request context, JDK 25 made **scoped values** final (JEP 506). A scoped value is bound for one call and everything it calls, and it's gone when that call returns, so there's no housekeeping to forget:

""" + pair(J_SV, K_SV) + """

That code needs JDK 25 or later. On JDK 21 to 24 the API is a preview, a feature you have to switch on with a flag and that may still change. The labs compile for JDK 21, so they use `ThreadLocal`.

Each tool in this lesson took away one ingredient of a race. Immutability took away change, confinement and hand-over took away sharing, and `ThreadLocal` gave each thread a copy of its own. Their limit is state that is shared and changes by its nature, such as a bank balance. That state still needs the locks and atomics of earlier lessons, and the next lesson puts them to work on three classic problems."""

L = {
 "id": "conc-11",
 "title": "Don't share: immutability, confinement, ThreadLocal",
 "minutes": 38,
 "goal": "By the end you can remove shared changing state instead of locking it: build objects that never change, publish a new snapshot in one write, keep state on one thread, hand objects over through a queue, and use `ThreadLocal` without leaking one request's data into the next.",
 "opening": OPENING,
 "warmup": {
  "q": "A record is Java's short form for a class whose fields are `final`. Take `record Quote(String item, List<String> tiers) {}`. A caller builds a quote from an `ArrayList` of price tiers, then adds one more tier to that same `ArrayList`. What does `quote.tiers()` show?",
  "options": ["The original tiers only, because records are immutable", "The new tier too, because the record holds the caller's list", "It throws `UnsupportedOperationException` when the caller adds", "It depends on whether the record was built with `new`"],
  "answer": 1,
  "why": "A record's fields are final, so `tiers` always points to the same list. But it's the caller's list, and nothing stops the caller from changing it. Records are only shallowly immutable. To make the quote really immutable, copy the list in a compact constructor with `List.copyOf`. The second section runs this with a bread quote."
 },
 "sections": [
  {
   "h": "A race needs two ingredients: take away change with immutable snapshots",
   "body": S0,
   "aside": ASIDE0,
   "try": {
    "title": "Half-done refreshes, counted",
    "minutes": 3,
    "steps": [
     "Read `SnapshotSwap`. A refresher thread moves four prices to a new version over and over. It updates a `ConcurrentHashMap` in place, and it also publishes an immutable snapshot through a `volatile` field.",
     "For one second, the main thread reads all four prices from each and counts the reads that saw two versions at once. Predict both counts.",
     "Run it, then run the Kotlin twin."
    ],
    "code": code("SnapshotSwap"),
    "expect": "The shared mutable map shows mixed versions in hundreds of thousands of reads (981,129 of 4,702,038 in one run here, about one in five), although every single `put` and `get` was thread-safe. The immutable snapshot shows 0, every run. Your counts will differ."
   }
  },
  {
   "h": "Records and data classes freeze less than they seem: defensive copies",
   "body": S1,
   "try": {
    "title": "Change a record from outside",
    "minutes": 3,
    "steps": [
     "Read `ShallowRecord`. `ShallowQuote` keeps the caller's list and array; `DeepQuote` copies them in and out. A third reference is an `unmodifiableList` view of the caller's list.",
     "After construction, the caller changes its list and array, and a reader writes into the array it got from `signature()`. Predict all three lines.",
     "Run it, then run the Kotlin twin, which adds one more line."
    ],
    "code": code("ShallowRecord"),
    "expect": "The shallow quote shows the extra tier and a signature of `[0, 0, 7]`: both the caller and a reader changed it. The deep quote still shows one tier and `[7, 7, 7]`. The `unmodifiableList` view shows the extra tier, because it's a view. In Kotlin, a cast to `MutableList` adds a line to the shallow quote's \"read-only\" list."
   }
  },
  {
   "h": "Taking away sharing: confinement, and handing objects over",
   "body": S2,
   "figure": {"svg": FIG, "caption": "Ownership moves through the queue. What the waiter wrote before put happens-before the take, and the waiter never touches the ticket again."},
   "try": {
    "title": "Hand over, or keep using?",
    "minutes": 3,
    "steps": [
     "Read `HandOff`. A waiter thread writes 5,000 tickets of 100 numbered dishes and puts each one on the rail, a queue with room for 4. A cook thread checks that every ticket it takes is complete and in order.",
     "Run it. Then run it with `-Pargs=reuse`, where the waiter clears and refills one list instead of making a new one.",
     "Run the `reuse` version a few times. Is the damage count the same each time?"
    ],
    "code": code("HandOff"),
    "expect": "With a new ticket each time: 0 damaged. With `reuse`: some tickets arrive damaged (from 10 to over 3,000 of the 5,000 in runs here), and the count changes every run. A lucky run could even show 0, which is exactly why this bug survives testing."
   }
  },
  {
   "h": "One copy per thread: ThreadLocal, and why pool threads never forget",
   "body": S3,
   "try": {
    "title": "Watch one customer's context leak into another's request",
    "minutes": 3,
    "steps": [
     "Read `ThreadLocalBleed`. Six requests run one after another on a pool of one thread. The handler sets the user only when the request carries one.",
     "Predict what each request without a user runs as, in the leaky version and in the clean one.",
     "Run it."
    ],
    "code": code("ThreadLocalBleed"),
    "expect": "Leaky: the first anonymous request runs as `alice`, and the next two run as `bob`, whoever that thread served last. Clean: every anonymous request runs as `null`, because `remove()` in `finally` put the thread back as it was. A pool of one makes it happen every time. With 200 threads it happens rarely and at random, which is how it reaches real users."
   },
   "refs": [
    {"title": "JEP 506: Scoped Values", "url": "https://openjdk.org/jeps/506", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "A deeply immutable value in Java and Kotlin",
  "java": {"title": "Java record", "src": J_CMP},
  "kotlin": {"title": "Kotlin class", "src": K_CMP},
  "note": "Both compile to a class with `final` fields, so both get the memory model's promise for final fields. The difference is where the copy can go. A Java record's compact constructor may reassign its parameters before the fields are set, so `lines = List.copyOf(lines)` stores the copy; that's Java doing the right thing with very little code. A Kotlin data class can't do the same, because its primary-constructor parameters are its properties. So you use a plain class with a separate property, as here, or a private constructor and a factory function. Kotlin's `List` type helps less than it looks: it's a read-only interface, and the results of `listOf` or `toList` can still be changed through a cast or from Java. `java.util.List.copyOf` gives you a list that is unmodifiable for everyone. A data class's `copy()` is shallow too: the copy shares the same list."
 },
 "worked": {
  "title": "A shared constant that someone changed",
  "steps": [
   {"say": "The shop adds a delivery fee to every online order. `Money` looks like a value, and `DELIVERY_FEE` looks like a constant. Read it and find what changes, and for whom.",
    "code": J_W1, "lang": "java", "alt_code": K_W1, "alt_lang": "kotlin"},
   {"say": "`add` changes the object it's called on, so `order.amount().add(DELIVERY_FEE)` changes the order's own amount. Somewhere else, `DELIVERY_FEE.add(surcharge)` changes the fee for every order on every thread. And because `cents` is neither `final` nor `volatile`, other threads may see the old fee, the new one, or a mix, at different times. `static final` on the reference didn't make the object constant.", "code": "", "lang": ""},
   {"say": "Make `Money` a value: final fields, and operations that return a new object. Now 200 threads can read `DELIVERY_FEE` with no lock, and nobody can change it.",
    "code": J_W2, "lang": "java", "alt_code": K_W2, "alt_lang": "kotlin"},
   {"say": "Before reading on, explain to yourself why the record needs no synchronization even though every request thread reads `DELIVERY_FEE`. Then look at the classic trap with immutable types, which catches everyone moving from changeable ones: calling the operation and throwing the result away.",
    "code": J_W3, "lang": "java", "alt_code": K_W3, "alt_lang": "kotlin"},
   {"say": "Answer: the fields are `final`, set once in the constructor, and the object never changes, so every thread that can see the reference sees 3.00 EUR. There's nothing to race on. The price is one new object per operation, which the JIT compiler often removes when the object never leaves the method. For money, that's an easy trade.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A deeply immutable quote and a tenant scope that cleans up",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/FxQuote.java", f"{lab}/main/{P}/TenantScope.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l11.*'",
  "steps": [
   "Meet the two classes. `FxQuote` is a price quote for changing money from one currency into another (FX is short for foreign exchange): a currency pair such as `EURUSD`, a list of price tiers and a signature, just like the bread quote in the second section. `TenantScope` carries the current tenant, the customer company a request works for, through one request on a pool thread, so deep code can ask `TenantScope.current()`.",
   "Run the tests. All six fail. The three `FxQuote` tests change the quote from outside, through the list you passed in, the list it returns, and its signature array. The three `TenantScope` tests run on a pool of one thread and find a tenant left over from an earlier call.",
   "Give `FxQuote` a compact constructor that replaces `tiers` with `List.copyOf(tiers)` and `signature` with a clone.",
   "Override `signature()` so it returns a clone, not the field.",
   "Fix `TenantScope.runAs`: remember the previous value, set the new one (or `remove()` for `null`), run the work in a `try`, and in `finally` put the previous value back (or `remove()` if there was none).",
   "Run the tests until all six pass."
  ],
  "hints": [
   "In a compact constructor you assign to the parameter (`tiers = List.copyOf(tiers);`), not to `this.tiers`. The record sets the fields after your code runs.",
   "`List.copyOf` also rejects `null` elements, which is usually what you want in a quote.",
   "Putting back the previous value instead of always calling `remove()` makes nested calls work: an inner `runAs` must hand the thread back to the outer one, not wipe it."
  ],
  "done_when": "All six tests in `DontShareTest` pass."
 },
 "drill": {
  "title": "An immutable order from memory",
  "minutes": 4,
  "prompt": "Close this page. Write an immutable `Order` with a customer name, a list of line items and a note, safe to share between threads, plus `withNote(String)` that returns a changed copy. Then check: can the caller's list, or the list you return, change your order?",
  "answer": {"lang": "java", "src": J_DRILL, "alt": {"lang": "kotlin", "title": "Kotlin", "src": K_DRILL}}
 },
 "recap": [
  "A race needs state that is shared and changing. Take away either one, and there's nothing to lock.",
  "An object nobody can change needs no locks: final fields, no setters, changing parts copied, and no `this` handed out before the constructor ends. For data that changes now and then, publish a new immutable snapshot with one write to a `volatile` field.",
  "Records and data classes are shallow. Copy lists with `List.copyOf` and clone arrays on the way in and out; `unmodifiableList` is a view, not a copy.",
  "Confinement keeps changing state on one thread: locals, one owner thread, or ownership handed through a queue and never touched again.",
  "Every `ThreadLocal.set` on a pool thread needs a `remove()` in `finally`. On JDK 25 and later, scoped values do the cleanup for you.",
  "The limit: state that is shared and changes by its nature, such as a balance, still needs a lock or an atomic."
 ],
 "closing": "We started with a price board that ten customers could read at once, because nobody wrote on it while they read. We gave the shop's program the same board, an immutable snapshot swapped in one write. Then we copied lists into records, handed tickets over for good, and cleaned up after every request.\n\nNow search your own code for `ThreadLocal`. Every `set(` needs a `remove()` in a nearby `finally`, or a framework that clears it. Then look for records that keep a caller's list or array without copying it.\n\nSome state can't be taken away. Next, we'll use the whole track's tools on three classic problems, starting with how a kitchen closes for the night without losing an order.",
 "quiz": [
  {"q": "Which of these can be shared between threads with no synchronization at all?",
   "options": ["A record whose `List<String>` component is the caller's `ArrayList`", "A class with `volatile` fields and setters", "A final class whose `private final` fields are a `String`, an `Instant` and a `BigDecimal`, with no setters", "A record with an `int[]` component and the default accessor"],
   "answer": 2, "why": "All three field types are immutable and the fields are final, so the object can never change, and the promise for final fields makes it visible correctly. The record with the caller's list and the record with an array can both be changed from outside. `volatile` fields with setters make each write visible, but the object still changes under its readers."},
  {"q": "A constructor stores `this.items = Collections.unmodifiableList(items);`. Later the caller adds an item to its own `items` list. What does the object's list show?",
   "options": ["The original items only", "It throws `UnsupportedOperationException` in the caller", "The caller's add is ignored", "The new item too, because `unmodifiableList` is a view of the caller's list"],
   "answer": 3, "why": "`unmodifiableList` only stops *you* from changing the list through that reference. It still reads the caller's list, so the caller's changes show through. `List.copyOf` makes a copy that nobody can change."},
  {"q": "From Explicit locks: the shop's price list is replaced as a whole every 5 minutes and read 5,000 times a second. What is the simplest correct design?",
   "options": ["A `ReentrantReadWriteLock` around a `HashMap`", "A `volatile` field holding an immutable map, replaced with a freshly built `Map.copyOf(...)` on each refresh", "A `ConcurrentHashMap` refreshed with `clear()` and `putAll()`", "A `synchronized` getter and setter on a `HashMap`"],
   "answer": 1, "why": "Readers never wait, and each one sees one complete version, because the new map is built fully before one `volatile` write publishes it. The read-write lock also works, with more code and some cost on every read. `clear` plus `putAll` on a concurrent map lets readers see an empty or half-filled list.",
   "from": "conc-07"},
  {"q": "A web service's request handler does `USER.set(request.user())` on a `ThreadLocal` when the request carries a user, and never removes it. Its threads come from a pool. What does a later anonymous request on the same thread see?",
   "options": ["The previous request's user", "`null`, because each request gets a fresh thread", "An `IllegalStateException`", "A random user from another thread"],
   "answer": 0, "why": "Pool threads are reused. The value stays on the thread until someone removes it, so the anonymous request runs as whoever that thread served last. Pair every `set` with `remove()` in `finally`."},
  {"q": "A waiter thread puts an `ArrayList` ticket into a `BlockingQueue`, then calls `clear()` on the same list and fills it again for the next table. What does that do to the cook thread that takes it?",
   "options": ["Nothing: `take()` returns a copy of the list", "Nothing: `put` made the list thread-safe", "The cook can see a partly cleared or refilled ticket, because the waiter kept changing an object it had handed over", "`put` throws, because the list is already in the queue"],
   "answer": 2, "why": "The queue hands over a reference, not a copy. `put` happens-before `take` only for what the waiter did before the `put`. After that, the two threads share one changing list with no synchronization. Hand over a new list each time."}
 ],
 "flashcards": [
  {"front": "What does a class need to be immutable?", "back": "All fields `final` and set in the constructor, no setters, changing parts copied in and never handed out, and `this` doesn't escape during construction."},
  {"front": "What does the memory model promise for `final` fields?", "back": "A thread that gets a reference to the object after its constructor finished sees the correct values of its final fields, even without synchronization."},
  {"front": "Is a record with a `List` component immutable?", "back": "Only shallowly. Copy the list in the compact constructor: `items = List.copyOf(items);`."},
  {"front": "`Collections.unmodifiableList(list)` vs `List.copyOf(list)`?", "back": "`unmodifiableList` is a read-only view: the owner's later changes show through. `List.copyOf` is an unmodifiable copy that nobody can change."},
  {"front": "How do you share data that changes rarely, without locks?", "back": "Build a new immutable snapshot, then publish it with one write to a `volatile` field (or an `AtomicReference`). Readers read the reference once."},
  {"front": "A pool thread runs a task that calls `ThreadLocal.set` and never `remove()`. What happens next?", "back": "The value stays on the thread. The next task on that thread sees it if it doesn't set its own."},
  {"front": "What makes passing a changeable object through a `BlockingQueue` safe?", "back": "`put` happens-before `take`, so the taker sees everything done before the put, as long as the giver never touches the object again."}
 ],
 "terms": [
  {"term": "Immutable object", "plain": "An object whose state can't change after it's built; safe to share without locks."},
  {"term": "Defensive copy", "plain": "Copying a changeable argument or return value so nobody else can change your object through it."},
  {"term": "Shallow immutability", "plain": "Final references to objects that can still change, as in a record holding an `ArrayList`."},
  {"term": "Snapshot publication", "plain": "Replacing a whole immutable object with one `volatile` write, so readers see one complete version."},
  {"term": "Thread confinement", "plain": "Keeping changing state reachable by only one thread."},
  {"term": "Ownership hand-off", "plain": "Passing an object to another thread, through a queue, and never touching it again."},
  {"term": "ThreadLocal", "plain": "A variable with a separate value per thread; values live as long as the thread unless removed."},
  {"term": "Scoped value", "plain": "A value bound for one call and everything it calls, gone when the call returns (final in JDK 25, JEP 506)."}
 ],
 "explain_back": {
  "prompt": "A friend wants to add a lock around the shop's settings (opening hours, prices, offers), which a refresher replaces every minute and every request reads. Explain the alternative you'd suggest, and why it's safe.",
  "answer": "I'd make the settings an immutable record, with final fields and copied lists, and keep the current one in a `volatile` field. The refresher builds a complete new settings object off to the side and then assigns it to the field in one write. Each request reads the field once and uses that object. It's safe because nothing a reader can reach ever changes. The old object stays valid for whoever is still using it, and the `volatile` write makes the new object, with all its fields, visible to every reader that reads the field afterwards. Readers never wait, and there's no lock to forget. The one thing to watch is a reader that reads the field twice and gets two different versions, so read it into a local first."
 },
 "deeper": {
  "minutes": 10,
  "body": "Each `Thread` object keeps its thread-locals in its own small hash map, called `ThreadLocalMap`. The keys are weak references to the `ThreadLocal` objects (references that don't keep an object alive), and the values are ordinary, strong references. When a `ThreadLocal` itself becomes garbage, its key goes away, but the value stays in the map until a later `get`, `set` or `remove` on that thread happens to clean it up. On a pool thread that lives for days, that can be a long time. Servers that load and unload applications while they run know this as a famous leak. A value whose class came from an unloaded application keeps that application's whole class loader, the object that loaded its classes, alive. `remove()` avoids all of it.\n\n`InheritableThreadLocal` copies values from a parent thread to a child thread when the child is created. It does nothing useful with pools, because pool threads are created once, long before the request that hands them work.\n\nScoped values (JEP 506, final in JDK 25) fix the design problems rather than the symptoms. A binding is immutable: there is no `set`, so code deep in the call chain can't change the value under you. It has a clear lifetime: it ends when `run` or `call` returns, even on an exception. And it is cheap to share with child tasks. With structured concurrency, still a preview API in JDK 25, threads started inside the scope see the same bindings without copying a map per thread.\n\nOne immutability trap to know: an object is only safe to share without synchronization if `this` didn't escape while the constructor was running. A constructor that registers `this` as a listener, or starts a thread that uses `this`, hands out the object before its final fields are guaranteed to be visible. Build first, register after. The memory model track's lesson on safe publication covers the full rules."
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
