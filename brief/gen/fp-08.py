import json, pathlib

ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/functional/src"
K = "kotlin/workbench/functional/l08"
J = "java/workbench/functional/l08"
read = lambda p: (ROOT / p).read_text()
run = lambda cls: f"./gradlew :functional:demo -Pmain=workbench.functional.l08.{cls}"


def tryit(kt, java):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(f"{LAB}/demo/{K}/{kt}"), "run": run(k + "Kt"), "file": f"{LAB}/demo/{K}/{kt}",
            "alt": {"lang": "java", "title": java, "src": read(f"{LAB}/demo/{J}/{java}"), "run": run(j), "file": f"{LAB}/demo/{J}/{java}"}}


FIG = (
    '<svg viewBox="0 0 680 280" role="img" aria-label="A functional core inside an imperative shell. The shell reads the clock and the payment store, '
    'passes plain values to planSettlement in the core, gets a SettlementPlan back, and then sends payouts and saves the ledger.">'
    '<rect class="box-dim" x="150" y="36" width="380" height="210" rx="8"/>'
    '<text class="t-s" x="340" y="58" text-anchor="middle">imperative shell: read, decide, act</text>'
    '<rect class="box-a" x="232" y="88" width="216" height="110" rx="8"/>'
    '<text class="t" x="340" y="114" text-anchor="middle">functional core</text>'
    '<text class="t-s t-code" x="340" y="140" text-anchor="middle">planSettlement(payments,</text>'
    '<text class="t-s t-code" x="340" y="158" text-anchor="middle">merchants, today)</text>'
    '<text class="t-s" x="340" y="184" text-anchor="middle">returns a SettlementPlan</text>'
    '<rect class="box" x="20" y="72" width="100" height="40" rx="8"/>'
    '<text class="t-s" x="70" y="97" text-anchor="middle">Clock</text>'
    '<rect class="box" x="20" y="160" width="100" height="40" rx="8"/>'
    '<text class="t-s" x="70" y="185" text-anchor="middle">PaymentStore</text>'
    '<rect class="box" x="560" y="72" width="100" height="40" rx="8"/>'
    '<text class="t-s" x="610" y="97" text-anchor="middle">PayoutApi</text>'
    '<rect class="box" x="560" y="160" width="100" height="40" rx="8"/>'
    '<text class="t-s" x="610" y="185" text-anchor="middle">save ledger</text>'
    '<line class="ln" x1="120" y1="92" x2="168" y2="120" marker-end="url(#arr)"/>'
    '<line class="ln" x1="120" y1="180" x2="168" y2="160" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="190" y="214" text-anchor="middle">read</text>'
    '<line class="ln-a" x1="176" y1="140" x2="228" y2="140" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="450" y1="140" x2="504" y2="140" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="490" y="214" text-anchor="middle">act</text>'
    '<line class="ln" x1="512" y1="120" x2="556" y2="94" marker-end="url(#arr)"/>'
    '<line class="ln" x1="512" y1="160" x2="556" y2="180" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="340" y="268" text-anchor="middle">The core gets many tests with plain values; the shell gets one test with fakes.</text>'
    '</svg>'
)

L = {
 "id": "fp-08",
 "title": "Immutable data and a functional core",
 "minutes": 38,
 "goal": "By the end you can tell read-only from immutable, avoid the `copy()` and `BigDecimal` equality traps, choose between `tailrec`, `DeepRecursiveFunction` and `fold`, and split a settlement job into a pure core that decides and a thin shell that does the I/O.",
 "warmup": {
  "q": "`data class Batch(val id: String, val paymentIds: List<String>)`. You build `Batch(\"b-7\", ids)` from a `MutableList` holding `p1`, and later the caller runs `ids += \"p2\"`. What does `batch.paymentIds` show?",
  "options": [
   "`[p1]`, because `val` and `List` make it immutable",
   "`[p1, p2]`, because the batch holds the same list",
   "It throws `UnsupportedOperationException`",
   "It doesn't compile: a `MutableList` can't be passed as a `List`"
  ],
  "answer": 1,
  "why": "`val` only stops the property from pointing at another list, and `List` only stops writes made through that reference. The batch and the caller hold the same `ArrayList`, so the caller's change shows up in the batch. A `MutableList` is a `List`, so passing it compiles. Copy at the boundary (`ids.toList()`) to take a snapshot."
 },
 "sections": [
  {
   "h": "Read-only is not immutable: what val and List really promise",
   "body": """A payout batch is built from a Kafka consumer's buffer, written to a payout file, and then the consumer clears the buffer for the next poll:

```kotlin
data class Batch(val id: String, val paymentIds: List<String>)

val batch = Batch("b-7", buffer)      // buffer is the consumer's MutableList
payoutFile.write(batch)
buffer.clear()                        // batch.paymentIds is now empty too
```

```java
record Batch(String id, List<String> paymentIds) {}

Batch batch = new Batch("b-7", buffer);   // buffer is the consumer's ArrayList
payoutFile.write(batch);
buffer.clear();                           // batch.paymentIds() is now empty too
```

Everything in `Batch` looks frozen: a data class, `val` properties, a read-only `List`. But `val` only means the property can't point at a different list. `List` only means you can't call `add` *through that reference*. Neither freezes the object behind them, and here both sides hold the same `ArrayList`. The Kotlin docs say it plainly: a read-only interface "prevents accidental modification through that interface. By contrast, an immutable collection doesn't allow you to change its elements after creation."

The read-only part is checked only at compile time. On the JVM, `listOf("p1", "p2")` is a `java.util.Arrays$ArrayList`; cast it to `MutableList` and `set(0, "p9")` works, while `add` throws `UnsupportedOperationException`.

Data classes add two traps of their own. `copy()` is shallow: "it doesn't copy components recursively". `a.copy(id = "p2")` shares `a`'s tag list, so a tag added through the copy shows up in the original. And `equals` compares every property with its own `equals`, which for `BigDecimal` includes the **scale**. `Fee("m-1", BigDecimal("10.00")) == Fee("m-1", BigDecimal("10.0"))` is `false`, although `compareTo` says the amounts are equal. Parse `10.0` from one partner's JSON and compute `10.00` yourself, and your duplicate check misses a real duplicate:

```kotlin
val amount = BigDecimal(json.amount).setScale(2, RoundingMode.UNNECESSARY)   // one scale for all money
```

```java
BigDecimal amount = new BigDecimal(json.amount()).setScale(2, RoundingMode.UNNECESSARY);   // same fix
```

`UNNECESSARY` throws if rounding would be needed, so a third decimal fails loudly instead of being rounded away. Storing money as a `Long` of cents avoids the question entirely.

So an immutable value needs three layers. Its properties are `val`. Their types are immutable all the way down: `String`, `BigDecimal`, `LocalDate`, other immutable data classes, immutable collections. And nothing mutable leaks in or out, which at a boundary means a copy: `toList()` for a snapshot, or `toImmutableList()` from the next section when you want the type to promise it.""",
   "try": {
    "title": "Five ways a frozen-looking value changes",
    "minutes": 4,
    "steps": [
     "Read `ReadOnly.kt` and predict each of the five numbered lines before you run it.",
     "Run it, then run `ReadOnlyJava.java`, where `List.copyOf` takes a real snapshot.",
     "In `ReadOnly.kt`, change `Batch(\"b-7\", backing)` to `Batch(\"b-7\", backing.toList())`. Predict lines 1 and 2 now."
    ],
    "code": tryit("ReadOnly.kt", "ReadOnlyJava.java"),
    "expect": "Line 1 shows `[p1, p2]`: the batch sees the caller's add. Line 2 shows `[p1, p2, p3]`: a cast gets past the read-only type. `listOf` is a `java.util.Arrays$ArrayList`, so `set` works and `add` throws. `copy()` shares the tag list (`same list: true`), and `Fee(10.00) == Fee(10.0)` is `false` while `compareTo` says equal. Java's `Collections.unmodifiableList` is also only a view, but `List.copyOf` is a snapshot. With `toList()`, line 1 shows `[p1]`: the batch has its own snapshot. Line 2 now throws `UnsupportedOperationException`, but only by luck: for one element, `toList()` returns `java.util.Collections$SingletonList`. From two elements up it returns a plain `ArrayList`, and the cast-and-add would work. The read-only type is the only promise you get."
   },
   "refs": [{"title": "Collections overview: read-only and mutable (Kotlin docs)", "url": "https://kotlinlang.org/docs/collections-overview.html", "kind": "docs"}]
  },
  {
   "h": "Persistent collections: change means a new version",
   "body": """Immutable values pay you back in three ways. You can share them between threads with no lock, because nobody can write ("Don't share: immutability, confinement, ThreadLocal" in the first track). You can keep the old version for an audit trail. And a test can hold the "before" and "after" side by side. The price is that every change makes a new value. Copying a whole ledger to append one entry is what Java does in the Try it, and it costs time and memory in proportion to the list's size, on every change.

**Persistent collections** avoid most of that copy. A new version shares most of its internal structure with the old one, so adding an entry builds a few new nodes and reuses the rest. The library is `kotlinx-collections-immutable`, version 0.5.2 in the lab. Its README still says "the library is experimental and the API is subject to change", so treat it as a pre-1.0 dependency. `ImmutableList` promises that nobody can change the list; `PersistentList` adds the operations that return a new version:

```kotlin
val v1 = persistentListOf("opening")
val v2 = v1.adding("payout:m-acme")                  // a new list; v1 is untouched
val v3 = v2.addingAll(listOf("fee-income", "payout:m-globex"))
val v4 = v3.mutate { it.removeAt(0); it += "closing" }   // several changes in one go
```

```java
// Java equivalent: no persistent collections in the JDK, so copy the whole list per version
List<String> v1 = List.of("opening");
List<String> v2 = Stream.concat(v1.stream(), Stream.of("payout:m-acme")).toList();
List<String> tmp = new ArrayList<>(v2);
tmp.addAll(List.of("fee-income", "payout:m-globex"));
List<String> v3 = List.copyOf(tmp);
```

Notice the names. Until 0.5.0 these methods were called `add`, `remove`, `put` and `set`, like the mutating methods on `MutableList`. That invited a quiet bug: `ledger.entries.add(entry)` as a statement builds a new list and throws it away, and the ledger never changes. Version 0.5.0 renamed the copy-returning methods to `adding`, `removing`, `putting`, `replacingAt` and `removingAt`, following a naming proposal (KEEP-0459, still a draft) where a verb like `add` changes the object and a participle like `adding` returns a copy, as `sorted()` does next to `sort()`. The old names still compile, with a warning: `'fun add(element: Long): PersistentList<Long>' is deprecated. Use adding() instead.`

In the lab, the ledger is a data class around a `PersistentList<Entry>`, and posting returns a new ledger with `copy(entries = entries.addingAll(...))`. The ledger you posted to is still there, unchanged, for the test to compare against.""",
   "try": {
    "title": "Four versions of one ledger",
    "minutes": 3,
    "steps": [
     "Run `Persistent.kt`. Predict what `v1` and `v3` print at the end.",
     "Uncomment `v1.add(\"lost\")` and run again. Read the build warning and the last line.",
     "Run `PersistentJava.java` and count how many times it copies the whole list."
    ],
    "code": tryit("Persistent.kt", "PersistentJava.java"),
    "expect": "`v1` stays `[opening]` and `v3` stays four entries long, even after `v4` is built from it with `mutate`. `v1` is a `SmallPersistentVector`. With `v1.add(\"lost\")`, the build warns `'fun add(element: String): PersistentList<String>' is deprecated. Use adding() instead.` and the last line still shows `[opening]`: `add` returned a new list that nobody kept. The Java version copies the full list for every version it makes."
   },
   "refs": [{"title": "kotlinx.collections.immutable (GitHub)", "url": "https://github.com/Kotlin/kotlinx.collections.immutable", "kind": "read"}]
  },
  {
   "h": "Recursion: tailrec is a loop, everything else uses the stack",
   "body": """Functional code often recurses where Java code loops. On the JVM that has a hard limit: every call takes a stack frame, and the JVM never removes a call, even the last call in a method. Sum the numbers 1 to 1,000,000 by recursion and you get a `StackOverflowError`, in both languages. In Java it overflows even when the recursive call is the last thing the method does.

Kotlin's `tailrec` moves the fix into the compiler. "When a function is marked with the `tailrec` modifier and meets the required formal conditions, the compiler optimizes out the recursion, leaving behind a fast and efficient loop based version instead." The trick is an **accumulator**: make the pending work an argument, so the recursive call is the last thing that happens.

```kotlin
tailrec fun sumTo(n: Long, acc: Long = 0): Long = if (n == 0L) acc else sumTo(n - 1, acc + n)
// sumTo(1_000_000) == 500000500000, no stack growth
```

```java
// Java has no tailrec: write the loop the Kotlin compiler would write
static long sumTo(long n) {
    long acc = 0;
    while (n > 0) { acc += n; n--; }
    return acc;
}
```

`javap -c` shows what the compiler did: `sumTo` stores the new values into its own parameter slots and ends with `goto 0`, a jump back to its first instruction. There is no `invokestatic sumTo` left. The conditions are strict. The function must call itself as its very last operation, not inside `try`, `catch` or `finally`, and it can't be `open`. Get it wrong and Kotlin only warns: `A function is marked as tail-recursive but no tail calls are found.` and `Recursive call is not a tail call.` The code compiles to ordinary recursion and still overflows. Read the warnings.

Some recursion has no tail form. Counting the nodes of a deep tree, such as a merchant hierarchy, makes several recursive calls per node. `DeepRecursiveFunction` from the standard library runs such a function with its "stack" on the heap, using coroutine machinery. In the Try it it counts a tree 100,001 levels deep, where the same code as a plain function overflows.

Most of the time you need neither. Summing a ledger or applying events to a state is a `fold` or a `sumOf` (the collections lesson), which says what it means in one line and compiles to the same kind of loop. Recursion that walks a list with `first()` and `drop(1)` is worse than either: `drop(1)` copies the rest of the list at every step. Keep `tailrec` for algorithms that are recursive by nature, like walking a chain of refunds back to the original payment.""",
   "try": {
    "title": "Watch tailrec become a goto",
    "minutes": 4,
    "steps": [
     "Run `Recursion.kt`. Predict which lines print a number and which print `StackOverflowError`.",
     "From `labs/`, run `javap -c -p -cp functional/build/classes/kotlin/demo workbench.functional.l08.RecursionKt` and find `sumTo` and `sumNaive`. Which one calls itself?",
     "Add `tailrec` in front of `fun sumNaive` and run again. Read the warnings in the build output.",
     "Run `RecursionJava.java`. Does `sumTail`, with its call in tail position, survive?"
    ],
    "code": tryit("Recursion.kt", "RecursionJava.java"),
    "expect": "`sumTo` and `fold` both print `500000500000`; `sumNaive` overflows; `originOf` walks 100,000 refunds back to `t1`; `countNodes` returns `100001`. In `javap`, `sumTo` ends with `goto 0` and never calls itself, while `sumNaive` has `invokestatic sumNaive`. Marking `sumNaive` as `tailrec` gives `A function is marked as tail-recursive but no tail calls are found.` and `Recursive call is not a tail call.`, and it still overflows. In Java, `sumTail` overflows too: the JVM doesn't remove tail calls, so only a loop helps."
   },
   "refs": [{"title": "Functions: tail recursive functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/functions.html", "kind": "docs"}]
  },
  {
   "h": "A functional core decides, a thin shell does the I/O",
   "body": """Here is the track's last step: put the pieces into one shape. The lab's `LegacySettlementJob` is a real-looking settlement job. In one loop it reads the clock, loads payments, skips refunds, holds payments that are too recent, sums per merchant, computes fees, calls the payout API, posts to the ledger and saves it, with `println` in between. It works. But to test one fee rule you need a fake store, a fake API, a fixed clock, and assertions on what the fakes recorded.

The fix is the shape from the first lesson of this track, usually called **functional core, imperative shell**. The core is a pure function. It takes plain values, today's date included, and returns a value that describes what should happen:

```kotlin
fun planSettlement(payments: List<Payment>, merchants: Map<String, Merchant>, today: LocalDate): SettlementPlan
```

```java
static SettlementPlan planSettlement(List<Payment> payments, Map<String, Merchant> merchants, LocalDate today)
```

Everything from this track fits in there. `filterNot`, `partition`, `groupBy` and `sumOf` from the collections lesson do the work. Data classes of `val`s with `BigDecimal` at scale 2 carry it. Expected outcomes, like a payment whose merchant we don't know, come back as values in the plan instead of exceptions or log lines (the errors lesson).

The shell is the only code that touches the world, and it has almost no branches:

```kotlin
fun run(): SettlementPlan {
    val today = LocalDate.now(clock)                                              // 1. read
    val plan = planSettlement(store.capturedPayments(), store.merchants(), today)  // 2. decide
    plan.payouts.forEach(payouts::send)                                           // 3. act
    store.saveLedger(store.loadLedger().posting(plan.payouts, "settlement-$today"))
    return plan
}
```

```java
SettlementPlan run() {
    LocalDate today = LocalDate.now(clock);                                              // 1. read
    SettlementPlan plan = planSettlement(store.capturedPayments(), store.merchants(), today);  // 2. decide
    plan.payouts().forEach(payouts::send);                                               // 3. act
    store.saveLedger(posting(store.loadLedger(), plan.payouts(), "settlement-" + today));
    return plan;
}
```

The tests change shape with the code. The core gets many small tests that build a list, call a function and compare the result with `equals`: no fakes, no clock, milliseconds each. Because the date is a parameter, "a payment captured yesterday is held" and "the same payment is paid out next week" are two lines. The shell gets one test with fakes that checks the wiring.

The shell isn't pure and doesn't try to be. The program still does all its I/O. What moved is the decisions: each one now lives where you can test it with a value.""",
   "figure": {"svg": FIG, "caption": "The shell reads the world, hands plain values to the pure core, and carries out the plan the core returns."},
   "try": {
    "title": "Run a core and its shell",
    "minutes": 3,
    "steps": [
     "Read `CoreShell.kt`. `decideVoids` is the core and `VoidJob` is the shell. Predict the two decisions and the one gateway call.",
     "Run it, then run `CoreShellJava.java`.",
     "Change `now` to one day later. Without running anything, which decision changes? Then run it to check."
    ],
    "code": tryit("CoreShell.kt", "CoreShellJava.java"),
    "expect": "The core prints `VoidIt(authId=a1)` (8 days old) and `Keep(authId=a2, expiresIn=PT138H)` (30 hours old, 138 hours left). The shell makes one call, `POST /authorizations/a1/void`. One day later, `a2` is still kept with `PT114H` left, and `a1` is voided as before. You could check that from the core alone, with no clock and no gateway, which is the point."
   }
  }
 ],
 "analogy": "A functional core is an accountant who works only from the documents on her desk. You hand her the statements, the fee schedule and today's date, and she hands back a written plan: pay these merchants these amounts, hold these payments. She never phones the bank or looks at the wall clock. The imperative shell is the office manager who fetches the documents and then makes the phone calls the plan lists. To check the accountant, you give her a sample pile of papers and read her plan, with no phone lines needed. The analogy breaks in one place: a real accountant would notice if the pile of papers changed while she was reading. Code doesn't, which is why the documents you hand the core must be immutable.",
 "in_your_world": "Most payments services already have the shell. It is the Quarkus resource, the Kafka consumer, the scheduled job, the Temporal activity. What's usually missing is the pure core underneath. A Temporal workflow makes the split explicit, because workflow code must be deterministic and all I/O goes into activities, so the decision logic in a workflow is already a core in disguise. Look for methods that call `Instant.now()`, `LocalDate.now()` or `UUID.randomUUID()` in the middle of business rules, and pass those values in instead. Look for data classes that hold a `MutableList` from a caller, and copy at the boundary. And check every `BigDecimal` you put in a data class: normalize the scale when you parse, or two equal payments from two acquirers won't be equal.",
 "mistake": "The most common mistake is believing a data class of `val`s is immutable, and so safe to share, cache or use as a map key, while one of its properties is a list the caller still holds. People make it because everything they can see says \"frozen\": `data class`, `val`, `List`. But a read-only `List` is a view, and the class holds the caller's object. The batch changes when the caller's buffer changes, a cached value changes after it was cached, and a key changes its `hashCode` while it sits in a `HashMap`. The fix is to copy at the boundary: `Batch(id, ids.toList())`, or better, make the property an `ImmutableList` or `PersistentList` and convert with `toImmutableList()`, so the type says what you mean.",
 "compare": {
  "title": "Immutable values and a pure core: Java records vs Kotlin data classes",
  "java": {"title": "Settlement.java", "src": "record Payout(String merchantId, BigDecimal gross, BigDecimal fee, BigDecimal net) {}\nrecord Ledger(List<Entry> entries) {\n    Ledger { entries = List.copyOf(entries); }                // snapshot: nobody can change it later\n    Ledger posting(List<Entry> more) {                        // a new version, by copying everything\n        List<Entry> all = new ArrayList<>(entries);\n        all.addAll(more);\n        return new Ledger(all);\n    }\n}\n\nstatic BigDecimal fee(BigDecimal gross, BigDecimal rate) {   // pure: same inputs, same output\n    return gross.multiply(rate).setScale(2, RoundingMode.HALF_EVEN);\n}"},
  "kotlin": {"title": "Settlement.kt", "src": "data class Payout(val merchantId: String, val gross: BigDecimal, val fee: BigDecimal, val net: BigDecimal)\ndata class Ledger(val entries: PersistentList<Entry>)    // the type promises it can't change\n\nfun Ledger.posting(more: List<Entry>): Ledger =\n    copy(entries = entries.addingAll(more))              // a new version that shares structure\n\nfun fee(gross: BigDecimal, rate: BigDecimal): BigDecimal =   // pure: same inputs, same output\n    (gross * rate).setScale(2, RoundingMode.HALF_EVEN)"},
  "note": "Both languages give you a value type with structural equality, and in both `equals` uses `BigDecimal.equals`, so the scale counts. Kotlin's data class adds `copy()`, which Java records lack (you write \"withers\" by hand), and both are shallow. The real difference is in collections. Java's `List.copyOf` makes a runtime-unmodifiable snapshot but every new version copies the whole list. Kotlin's `List` is only a compile-time read-only view, so you need `toList()` for a snapshot or kotlinx.collections.immutable for a real guarantee; its `PersistentList` makes new versions cheaply by sharing structure. The pure functions themselves look the same in both languages. Purity is a habit, not a keyword: neither compiler checks it."
 },
 "worked": {
  "title": "Pull the decisions out of a chargeback job",
  "steps": [
   {"say": "A nightly job handles open chargebacks: escalate a case whose deadline is two days away or less, accept the loss once the deadline has passed, otherwise wait. Before reading on, label every line as read, decide or act.", "code": "fun runChargebacks() {\n    for (case in repo.openCases()) {                          // read\n        val daysLeft = ChronoUnit.DAYS.between(LocalDate.now(), case.deadline)   // read (the clock!)\n        if (daysLeft < 0) {                                   // decide\n            scheme.acceptLoss(case.id)                        // act\n            repo.close(case.id)                               // act\n        } else if (daysLeft <= 2 && !case.evidenceSent) {     // decide\n            ops.escalate(case.id, \"deadline in $daysLeft days\")   // act\n        }\n    }\n}", "lang": "kotlin", "alt_lang": "java", "alt_code": "void runChargebacks() {\n    for (Case c : repo.openCases()) {                                          // read\n        long daysLeft = ChronoUnit.DAYS.between(LocalDate.now(), c.deadline());  // read (the clock!)\n        if (daysLeft < 0) {                                                    // decide\n            scheme.acceptLoss(c.id());                                         // act\n            repo.close(c.id());                                                // act\n        } else if (daysLeft <= 2 && !c.evidenceSent()) {                       // decide\n            ops.escalate(c.id(), \"deadline in \" + daysLeft + \" days\");         // act\n        }\n    }\n}"},
   {"say": "1. Name the decisions as values. A sealed type makes the plan explicit and lets the shell's `when` be exhaustive.", "code": "sealed interface CaseAction {\n    data class AcceptLoss(val caseId: String) : CaseAction\n    data class Escalate(val caseId: String, val daysLeft: Long) : CaseAction\n    data class Wait(val caseId: String) : CaseAction\n}", "lang": "kotlin", "alt_lang": "java", "alt_code": "sealed interface CaseAction {}\nrecord AcceptLoss(String caseId) implements CaseAction {}\nrecord Escalate(String caseId, long daysLeft) implements CaseAction {}\nrecord Wait(String caseId) implements CaseAction {}"},
   {"say": "2. Write the core as a pure function. The clock becomes a parameter, `today`, and the result is a list of decisions. Every rule is now testable with one line: `decide(listOf(case), LocalDate.of(2026, 3, 10))`.", "code": "fun decide(cases: List<Case>, today: LocalDate): List<CaseAction> = cases.map { case ->\n    val daysLeft = ChronoUnit.DAYS.between(today, case.deadline)\n    when {\n        daysLeft < 0 -> CaseAction.AcceptLoss(case.id)\n        daysLeft <= 2 && !case.evidenceSent -> CaseAction.Escalate(case.id, daysLeft)\n        else -> CaseAction.Wait(case.id)\n    }\n}", "lang": "kotlin", "alt_lang": "java", "alt_code": "static List<CaseAction> decide(List<Case> cases, LocalDate today) {\n    return cases.stream().<CaseAction>map(c -> {\n        long daysLeft = ChronoUnit.DAYS.between(today, c.deadline());\n        if (daysLeft < 0) return new AcceptLoss(c.id());\n        if (daysLeft <= 2 && !c.evidenceSent()) return new Escalate(c.id(), daysLeft);\n        return new Wait(c.id());\n    }).toList();\n}"},
   {"say": "3. The shell reads, calls the core and carries out each action with an exhaustive `when`. It has no rules left, so one test with fakes covers it. The many rule tests go against `decide` with plain values.", "code": "fun runChargebacks() {\n    val actions = decide(repo.openCases(), LocalDate.now(clock))   // read, then decide\n    for (action in actions) when (action) {                         // act\n        is CaseAction.AcceptLoss -> { scheme.acceptLoss(action.caseId); repo.close(action.caseId) }\n        is CaseAction.Escalate -> ops.escalate(action.caseId, \"deadline in ${action.daysLeft} days\")\n        is CaseAction.Wait -> Unit\n    }\n}", "lang": "kotlin", "alt_lang": "java", "alt_code": "void runChargebacks() {\n    List<CaseAction> actions = decide(repo.openCases(), LocalDate.now(clock));   // read, then decide\n    for (CaseAction action : actions) {                                          // act\n        switch (action) {\n            case AcceptLoss a -> { scheme.acceptLoss(a.caseId()); repo.close(a.caseId()); }\n            case Escalate e -> ops.escalate(e.caseId(), \"deadline in \" + e.daysLeft() + \" days\");\n            case Wait w -> { }\n        }\n    }\n}"}
  ]
 },
 "lab": {
  "title": "Split the settlement job into a pure core and a thin shell",
  "minutes": 15,
  "files": [f"{LAB}/main/{K}/SettlementCore.kt", f"{LAB}/main/{K}/SettlementJob.kt", f"{LAB}/main/{K}/LegacySettlementJob.kt", f"{LAB}/main/{K}/Model.kt"],
  "run": "./gradlew :functional:test --tests 'workbench.functional.l08.*'",
  "steps": [
   "Run the tests. All eight fail. Seven of them call `planSettlement` or `posting` with plain values: no fakes and no clock.",
   "Read `LegacySettlementJob.run` and label each line read, decide or act. `Model.kt` holds the types and needs no changes.",
   "Write `planSettlement` in `SettlementCore.kt` from the rules in its KDoc. `today` is a parameter; don't touch a clock.",
   "Write `Ledger.posting` with `copy` and `addingAll`.",
   "Write `SettlementJob.run` as a thin shell: read, call the core, send each payout, post and save the ledger once, return the plan.",
   "Run the tests until all eight pass. Then ask: which test would fail if `planSettlement` called `LocalDate.now()` instead of using `today`?"
  ],
  "hints": [
   "`partition` splits a list in two in one pass. Use it twice: first known and unknown merchants, then due and held payments.",
   "`sumOf { it.amount }` has a `BigDecimal` overload. Round the fee with `setScale(2, RoundingMode.HALF_EVEN)`, or the test's `BigDecimal(\"3.64\")` won't equal your `3.63950`.",
   "`groupBy` keeps first-seen order. `toSortedMap()` orders the groups by merchant id.",
   "In the shell, `plan.payouts.forEach(payouts::send)` and `store.loadLedger().posting(plan.payouts, \"settlement-$today\")` cover steps 3 and 4."
  ],
  "done_when": "All eight tests in `FunctionalCoreTest` pass."
 },
 "drill": {
  "title": "tailrec from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `originOf(id, byId)`, which follows `parentId` links from a refund back to the original payment, as a `tailrec` function. Then write the Java loop. Last, predict: what happens if you add a `log.debug(...)` line after the recursive call?",
  "answer": {
   "lang": "kotlin",
   "src": "tailrec fun originOf(id: String, byId: Map<String, Txn>): String {\n    val parent = byId.getValue(id).parentId ?: return id   // no parent: this is the original\n    return originOf(parent, byId)                          // the last thing the function does\n}\n// A log line after the call makes it no longer a tail call: Kotlin warns\n// \"Recursive call is not a tail call.\" and compiles ordinary recursion, which can overflow.",
   "alt": {"lang": "java", "src": "static String originOf(String id, Map<String, Txn> byId) {\n    String current = id;\n    while (true) {\n        String parent = byId.get(current).parentId();\n        if (parent == null) return current;   // no parent: this is the original\n        current = parent;                     // what tailrec's goto does\n    }\n}"}
  }
 },
 "recap": [
  "`val` stops reassignment and `List` stops writes through that reference. Neither freezes the object: a read-only view changes when its backing list does.",
  "`copy()` is shallow, and data class `equals` uses `BigDecimal.equals`, which compares the scale. Normalize money when you parse it.",
  "kotlinx.collections.immutable 0.5.2, still marked experimental, gives persistent collections: `adding`, `putting` and `removingAt` return new versions that share structure, and `mutate { }` batches changes.",
  "`tailrec` turns a self-call in tail position into a `goto`. Anywhere else it is only a warning, and the stack still overflows. `DeepRecursiveFunction` handles deep non-tail recursion, and `fold` is usually simplest.",
  "A functional core decides from plain values, with the clock passed in; a thin shell reads, calls the core and does the I/O.",
  "Core tests need no fakes and no clock; the shell needs one wiring test."
 ],
 "quiz": [
  {"q": "A Kafka consumer builds `Batch(\"b-9\", buffer)` from its `MutableList` buffer, hands the batch to a payout writer on another thread, then calls `buffer.clear()` for the next poll. What can the writer see in `batch.paymentIds`?", "options": ["Always the ids at the moment the batch was built", "An empty list, or ids from the next poll, depending on timing", "`UnsupportedOperationException`, because `List` is read-only", "A compile error, because `paymentIds` is a `val`"], "answer": 1, "why": "The batch holds the consumer's list, not a copy, so clearing and refilling the buffer changes what the batch shows. On another thread it's also a data race. `Batch(\"b-9\", buffer.toList())` takes a snapshot at the boundary; `toImmutableList()` puts the guarantee in the type."},
  {"q": "`data class Payment(val id: String, val amount: BigDecimal)`. What is `setOf(Payment(\"p1\", BigDecimal(\"10.0\")), Payment(\"p1\", BigDecimal(\"10.00\"))).size`?", "options": ["1", "It depends on the JVM", "2", "It throws ArithmeticException"], "answer": 2, "why": "Data class `equals` compares each property with `equals`, and `BigDecimal.equals` treats `10.0` and `10.00` as different because their scales differ. `compareTo` would say they're equal. Normalize with `setScale(2, ...)` when you parse, or store minor units as a `Long`."},
  {"q": "`val ledger = persistentListOf<Entry>()`, then `ledger.adding(e1)` and `ledger.adding(e2)` as two statements. What is `ledger.size`?", "options": ["0", "2", "1", "It doesn't compile, because `ledger` is a `val`"], "answer": 0, "why": "`adding` returns a new list and leaves the receiver alone, and both results were thrown away. You need `val v2 = ledger.adding(e1).adding(e2)`. This is the exact bug the 0.5 rename from `add` to `adding` makes easier to spot."},
  {"q": "`tailrec fun depth(n: Node?): Int = if (n == null) 0 else 1 + depth(n.parent)`, called on a chain of 1,000,000 nodes. What happens?", "options": ["It compiles to a loop and returns 1,000,000", "It doesn't compile, because `tailrec` needs an accumulator", "It returns 0", "It compiles with warnings, stays ordinary recursion, and throws StackOverflowError"], "answer": 3, "why": "`1 + depth(...)` still has work to do after the call, so the call isn't in tail position. Kotlin only warns (`A function is marked as tail-recursive but no tail calls are found.`, `Recursive call is not a tail call.`) and compiles normal recursion. Make the pending work an argument: `tailrec fun depth(n: Node?, acc: Int = 0): Int = if (n == null) acc else depth(n.parent, acc + 1)`."},
  {"q": "From the errors lesson: inside `planSettlement`, a payment names a merchant that isn't in the map. What should the pure core do?", "options": ["`merchants.getValue(id)`, and let `NoSuchElementException` stop the run", "`merchants[id]!!`", "Return it as a value in the plan, such as an `unknownMerchants` list or a sealed error", "Log a warning and skip it"], "answer": 2, "why": "An unknown merchant is an expected outcome that someone must handle, so it belongs in the result. Throwing would stop the whole settlement for one bad row, `!!` gives a `NullPointerException` with no message, and logging is I/O, which doesn't belong in a pure core and leaves the caller unable to act on it.", "from": "fp-07"}
 ],
 "flashcards": [
  {"front": "Does `val ids: List<String>` make the list immutable?", "back": "No. `val` stops reassigning the reference and `List` stops writes through it. The list can still change through another reference or a cast."},
  {"front": "Is a data class `copy()` deep or shallow?", "back": "Shallow. Properties are copied as references, so a nested `MutableList` is shared between the original and the copy."},
  {"front": "`Fee(BigDecimal(\"10.00\")) == Fee(BigDecimal(\"10.0\"))`?", "back": "`false`. Data class equals uses `BigDecimal.equals`, which compares the scale. `compareTo` returns 0."},
  {"front": "What did kotlinx.collections.immutable 0.5 rename, and why?", "back": "The copy-returning methods: `add` to `adding`, `put` to `putting`, `set` to `replacingAt` and so on, so a call whose result is dropped looks wrong. The old names are deprecated."},
  {"front": "What does `tailrec` compile to?", "back": "A loop: the self-call in tail position becomes stores into the parameter slots and a `goto` back to the start. No new stack frame."},
  {"front": "What if a `tailrec` function isn't really tail-recursive?", "back": "Only a warning, such as `Recursive call is not a tail call.` It compiles to ordinary recursion and can still overflow."},
  {"front": "Functional core vs imperative shell?", "back": "Core: pure decisions from plain values, with the clock passed in, and many fast tests. Shell: reads inputs, calls the core, performs the I/O, with few branches and one wiring test."}
 ],
 "terms": [
  {"term": "Read-only", "plain": "You can't change it through this reference. Someone else may still change it."},
  {"term": "Immutable", "plain": "Nobody can change it after it is built, through any reference."},
  {"term": "Shallow copy", "plain": "A copy whose properties point at the same objects as the original's."},
  {"term": "Persistent collection", "plain": "An immutable collection whose \"change\" operations return a new version that shares most of its structure with the old one."},
  {"term": "Tail call", "plain": "A call that is the very last thing a function does, with no work left after it returns."},
  {"term": "Accumulator", "plain": "An extra parameter that carries the result so far, which turns pending work into an argument."},
  {"term": "Functional core", "plain": "The pure part of a program: it decides from plain values and returns a value."},
  {"term": "Imperative shell", "plain": "The thin outer part that reads inputs, calls the core and carries out the result."}
 ],
 "explain_back": {
  "prompt": "A new teammate asks why the settlement job was split into `planSettlement` and `SettlementJob`, when the old job \"worked fine\". Explain what changed and how it changes the tests.",
  "answer": "The old job worked, but its decisions were mixed with its I/O. It read the clock, loaded data, applied the fee and hold rules, called the payout API and saved the ledger in one loop, so testing a single rule needed a fake store, a fake API and a fixed clock, plus checks on what the fakes recorded. Now `planSettlement` is a pure function: payments, merchants and today's date go in, and a plan comes out, with the same answer every time. All the rules live there, and each test builds a few values and compares the plan with `equals`, in milliseconds. A different day is just a different argument. `SettlementJob` keeps only the I/O: read, call the core, send the payouts, post and save the ledger. It has almost no branches, so one test with fakes is enough to check the wiring. The data is immutable too, so the plan and the ledger versions can't change behind our backs while we test or retry."
 },
 "deeper": {
  "minutes": 8,
  "body": """Immutability is also a concurrency tool, and the memory model track explains why. A `val` property compiles to a `final` field, and the Java memory model gives final fields a special guarantee: once the constructor has finished, any thread that sees the object sees those fields fully set, without a lock, as long as the constructor didn't let `this` escape ("Safe publication, final fields and escaping this"). So an object whose state is all `val`s of immutable types can be handed to another thread with no synchronization at all. A persistent collection extends that: one thread builds a new version with `adding` while other threads keep reading the old one, and neither can disturb the other. The catch is the same as in the first section. A `val` holding a `MutableList` gets the guarantee only for the reference, not for the list's contents.

The naming change in kotlinx.collections.immutable came with a compiler feature. The 0.5.0 line builds the library itself with Kotlin's Experimental return-value checker in its strictest mode, `-Xreturn-value-checker=full`. The checker arrived in Kotlin 2.3.0, is off by default, and warns when a call's result is ignored. Both changes go after the same bug: a new version computed and then dropped.

On recursion, `arrow-core` 2.3.0 also contains a `MemoizedDeepRecursiveFunction`, a memoizing variant of the standard library's `DeepRecursiveFunction`. Reach for either only after a plain `fold` or a loop has been ruled out."""
 },
 "sources": [
  {"title": "Collections overview (Kotlin docs)", "url": "https://kotlinlang.org/docs/collections-overview.html"},
  {"title": "Data classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/data-classes.html"},
  {"title": "Functions: tail recursive functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/functions.html"},
  {"title": "kotlinx.collections.immutable CHANGELOG", "url": "https://github.com/Kotlin/kotlinx.collections.immutable/blob/master/CHANGELOG.md"},
  {"title": "KEEP-0459: naming conventions for copy-returning operations", "url": "https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0459-naming-conventions-for-copy-returning-operations.md"}
 ]
}

out = ROOT / "content/lessons/fp-08.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
