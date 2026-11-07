import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l10"
K = "kotlin/workbench/patterns/l10"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l10.{cls}"


def code(lang, name, cls, alt_lang, alt_name, alt_cls):
    d1 = J if lang == "java" else K
    d2 = J if alt_lang == "java" else K
    return {"lang": lang, "title": name, "src": read(f"{lab}/demo/{d1}/{name}"), "run": demo(cls), "file": f"{lab}/demo/{d1}/{name}",
            "alt": {"lang": alt_lang, "title": alt_name, "src": read(f"{lab}/demo/{d2}/{alt_name}"), "run": demo(alt_cls), "file": f"{lab}/demo/{d2}/{alt_name}"}}


FIG = """<svg viewBox="0 0 680 252" role="img" aria-label="Left: inventory, payments, shipping and email all call each other, six links. Right: each of the four talks only to a mediator in the middle, four links">
<text class="t-s t-m" x="160" y="28" text-anchor="middle">without: every service knows the others</text>
<rect class="box" x="20" y="50" width="100" height="36" rx="8"/>
<text class="t" x="70" y="73" text-anchor="middle">inventory</text>
<rect class="box" x="200" y="50" width="100" height="36" rx="8"/>
<text class="t" x="250" y="73" text-anchor="middle">payments</text>
<rect class="box" x="20" y="170" width="100" height="36" rx="8"/>
<text class="t" x="70" y="193" text-anchor="middle">shipping</text>
<rect class="box" x="200" y="170" width="100" height="36" rx="8"/>
<text class="t" x="250" y="193" text-anchor="middle">email</text>
<line class="ln-bad" x1="120" y1="68" x2="200" y2="68"/>
<line class="ln-bad" x1="120" y1="188" x2="200" y2="188"/>
<line class="ln-bad" x1="70" y1="86" x2="70" y2="170"/>
<line class="ln-bad" x1="250" y1="86" x2="250" y2="170"/>
<line class="ln-bad" x1="120" y1="86" x2="200" y2="170"/>
<line class="ln-bad" x1="200" y1="86" x2="120" y2="170"/>
<text class="t-s t-bad" x="160" y="236" text-anchor="middle">6 links; each new rule edits two services</text>
<text class="t-s t-m" x="520" y="28" text-anchor="middle">with: each knows only the mediator</text>
<rect class="box" x="380" y="50" width="100" height="36" rx="8"/>
<text class="t" x="430" y="73" text-anchor="middle">inventory</text>
<rect class="box" x="560" y="50" width="100" height="36" rx="8"/>
<text class="t" x="610" y="73" text-anchor="middle">payments</text>
<rect class="box" x="380" y="170" width="100" height="36" rx="8"/>
<text class="t" x="430" y="193" text-anchor="middle">shipping</text>
<rect class="box" x="560" y="170" width="100" height="36" rx="8"/>
<text class="t" x="610" y="193" text-anchor="middle">email</text>
<rect class="box-a" x="460" y="108" width="120" height="40" rx="8"/>
<text class="t" x="520" y="133" text-anchor="middle">mediator</text>
<line class="ln-a" x1="440" y1="86" x2="490" y2="108"/>
<line class="ln-a" x1="600" y1="86" x2="550" y2="108"/>
<line class="ln-a" x1="440" y1="170" x2="490" y2="148"/>
<line class="ln-a" x1="600" y1="170" x2="550" y2="148"/>
<text class="t-s t-ok" x="520" y="236" text-anchor="middle">4 links; the rules live in one place</text>
</svg>""".replace("\n", "")

S1 = """Visitor lets you add operations to a fixed set of classes without editing those classes. Here is the classic form, for a tiny expression tree:

```java
interface ExprVisitor<R> { R visitNum(Num n); R visitAdd(Add a); R visitMul(Mul m); }

sealed interface Expr permits Num, Add, Mul { <R> R accept(ExprVisitor<R> v); }
record Num(int value) implements Expr { public <R> R accept(ExprVisitor<R> v) { return v.visitNum(this); } }
record Add(Expr l, Expr r) implements Expr { public <R> R accept(ExprVisitor<R> v) { return v.visitAdd(this); } }
record Mul(Expr l, Expr r) implements Expr { public <R> R accept(ExprVisitor<R> v) { return v.visitMul(this); } }

final class Eval implements ExprVisitor<Integer> {
    public Integer visitNum(Num n) { return n.value(); }
    public Integer visitAdd(Add a) { return a.l().accept(this) + a.r().accept(this); }
    public Integer visitMul(Mul m) { return m.l().accept(this) * m.r().accept(this); }
}

int result = expr.accept(new Eval());      // double dispatch: accept picks the case, visit picks the operation
```

```kotlin
interface ExprVisitor<R> { fun visitNum(n: Num): R; fun visitAdd(a: Add): R; fun visitMul(m: Mul): R }

sealed interface Expr { fun <R> accept(v: ExprVisitor<R>): R }
data class Num(val value: Int) : Expr { override fun <R> accept(v: ExprVisitor<R>) = v.visitNum(this) }
data class Add(val l: Expr, val r: Expr) : Expr { override fun <R> accept(v: ExprVisitor<R>) = v.visitAdd(this) }
data class Mul(val l: Expr, val r: Expr) : Expr { override fun <R> accept(v: ExprVisitor<R>) = v.visitMul(this) }

object Eval : ExprVisitor<Int> {
    override fun visitNum(n: Num) = n.value
    override fun visitAdd(a: Add) = a.l.accept(this) + a.r.accept(this)
    override fun visitMul(m: Mul) = m.l.accept(this) * m.r.accept(this)
}

val result = expr.accept(Eval)             // double dispatch: accept picks the case, visit picks the operation
```

A new operation, such as printing, is one new visitor class. A new case, `Neg`, costs a method on the visitor interface, an `accept` on `Neg`, and an edit in every visitor anyone ever wrote.

That trade-off is the **expression problem**. With ordinary virtual methods (an `eval()` on each record), a new case is cheap and a new operation touches every class. With Visitor it's the other way round. Plain Java and Kotlin can't make both cheap, so you pick the axis you expect to grow.

In payment code, the axis that grows is usually operations. The instruction types (card, SEPA transfer, wallet payout) change rarely, while new validations, exports, reports and fee rules arrive all the time. That favors Visitor's side of the trade.

Sealed types and pattern matching give you Visitor's side of the trade without its machinery: no `accept`, no visitor interface, one function per operation with a `switch` or `when` inside. The comparison below shows it in both languages. Brian Goetz puts it bluntly in the pattern-matching design notes: \"if your language has sufficiently powerful pattern matching, the Visitor pattern is almost completely unnecessary\". The same notes say this doesn't make virtual methods wrong.

So, for a closed hierarchy you own, delete the visitor. Keep Visitor when the hierarchy is open across modules, or when a library hands you one: `javax.lang.model.element.ElementVisitor` in annotation processors, javac's Tree API, ASM's `ClassVisitor`."""

S2 = """Listing every refund from a PSP means walking a cursor-paginated API: fetch a page, hand out its items, follow the `next` cursor, stop when it's null. Loading every page into a list first wastes memory and makes the first item wait for the last page. An **iterator** hands them out one at a time. In Java you write its state machine by hand:

```java
static Iterator<String> refunds(Function<Integer, RefundPage> fetch) {
    return new Iterator<>() {
        private Iterator<String> current = Collections.emptyIterator();
        private Integer cursor = 0;                              // null = no more pages

        public boolean hasNext() {
            while (!current.hasNext() && cursor != null) {       // while, not if: skip empty pages
                RefundPage page = fetch.apply(cursor);
                current = page.items().iterator();
                cursor = page.next();
            }
            return current.hasNext();
        }

        public String next() {
            if (!hasNext()) throw new NoSuchElementException();
            return current.next();
        }
    };
}
```

```kotlin
fun refunds(fetch: (Int) -> RefundPage): Sequence<String> = sequence {
    var cursor: Int? = 0
    while (cursor != null) {
        val page = fetch(cursor)                                 // runs only when the consumer needs more
        yieldAll(page.items)
        cursor = page.next
    }
}
```

The Java version keeps two fields of state, and `hasNext` holds a classic bug: write `if` instead of `while` and an empty page in the middle ends the iteration early. Kotlin's `sequence {}` builder lets you write the loop you'd write for a list. `yield` and `yieldAll` suspend the block until the consumer asks for the next item, and the compiler builds the state machine. Nothing runs until someone iterates, and `refunds(fetch).take(2).toList()` fetches one page.

Remember two properties. A sequence built this way is cold: each new iteration runs the block again from the top, so iterating twice fetches every page twice. And if the consumer stops early, the rest of the block never runs. The `iterator {}` docs warn that \"finally blocks may be left unexecuted\". Don't open a connection inside the block and close it in `finally`; open it at the call site with `use {}`.

When you want your own type to work in a `for` loop, make it `Iterable` and build its iterator with `iterator {}`, the sibling of `sequence {}`: `class RefundLog(...) : Iterable<String> { override fun iterator() = iterator { yieldAll(...) } }`.

Java has no generators. `Stream.iterate(seed, hasNext, next)` covers simple cases, but for paging, the hand-written iterator is still the clearest Java."""

S3 = """An analyst editing a draft refund batch adds lines, sets a note, then wants to undo. *Observer and Command* undid a command by running its inverse. That works for \"add 30\". It doesn't for \"apply the discount rules\", which has no clean inverse. **Memento** saves a snapshot of the state before the change and puts it back on undo:

```java
final class Cart {
    private final List<String> items = new ArrayList<>();
    private String coupon = "";

    interface Memento {}                                             // what callers hold: opaque
    private record State(List<String> items, String coupon) implements Memento {}

    Memento save() { return new State(List.copyOf(items), coupon); } // copy: later edits must not leak in

    void restore(Memento m) {
        State s = (State) m;
        items.clear();
        items.addAll(s.items());                                     // copy back in: the memento stays intact
        coupon = s.coupon();
    }
}
```

```kotlin
class Cart {
    private val items = mutableListOf<String>()
    private var coupon = ""

    interface Memento                                                // what callers hold: opaque
    private data class State(val items: List<String>, val coupon: String) : Memento

    fun save(): Memento = State(items.toList(), coupon)             // copy: later edits must not leak in

    fun restore(m: Memento) {
        val s = m as State
        items.clear()
        items += s.items                                             // copy back in: the memento stays intact
        coupon = s.coupon
    }
}
```

Three rules make it work. The snapshot must not share mutable parts with the live object: copy the list with `List.copyOf` or `toList()`, or later edits leak into the saved state. Restore must copy back in rather than point at the memento's list, so the same memento can be restored twice. And only the originator reads it. Callers get an opaque `Memento` to store and hand back, while the record with the data is private, so nothing else depends on the cart's insides.

When the whole state is already an immutable record or data class, the pattern almost disappears: the state is its own memento, and an undo history is a `List<State>`. That is a strong argument for immutable aggregates.

There are two costs. History grows with every checkpoint, so bound it; the lab keeps the newest N. And snapshots of large aggregates are expensive, which is why event-sourced systems store one every few hundred events and replay the rest."""

S4 = """A checkout touches inventory, payments, shipping and email, and each reacts to the others: missing stock means a refund, a captured payment means ship and send a receipt. If every service calls the ones it reacts to, four services need six links, and every new rule edits two of them. A **mediator** owns the coordination, and each colleague talks only to it:

```java
interface Colleague { void receive(String event); }

final class CheckoutMediator {
    private final Map<String, List<Colleague>> routes = new HashMap<>();
    void on(String event, Colleague c) { routes.computeIfAbsent(event, k -> new ArrayList<>()).add(c); }
    void emit(String event) { routes.getOrDefault(event, List.of()).forEach(c -> c.receive(event)); }
}

mediator.on("payment.captured", shipping);
mediator.on("payment.captured", email);
mediator.on("stock.missing", payments);        // payments refunds; inventory never calls payments directly
```

```kotlin
fun interface Colleague { fun receive(event: String) }

class CheckoutMediator {
    private val routes = mutableMapOf<String, MutableList<Colleague>>()
    fun on(event: String, c: Colleague) { routes.getOrPut(event) { mutableListOf() } += c }
    fun emit(event: String) { routes[event].orEmpty().forEach { it.receive(event) } }
}

mediator.on("payment.captured", shipping)
mediator.on("payment.captured", email)
mediator.on("stock.missing", payments)         // payments refunds; inventory never calls payments directly
```

Mediator and Observer look alike. An observer is one subject telling many listeners about itself. A mediator sits between many parties and holds the rules about who reacts to what. In coroutine code, a `MutableSharedFlow<CheckoutEvent>` that all colleagues share is a natural mediator bus. Across services, the mediator becomes a message broker or a saga orchestrator: a Temporal workflow that calls the inventory, payment and shipping activities in order is a mediator with durable state.

The risk is the god object. A mediator should route and sequence. When it starts computing fees or validating addresses, move that logic back to the colleague that owns it.

Check yourself. A new rule arrives: when stock is missing, shipping must cancel the parcel it has booked. With the mediator above, what do you change? (One registration, `mediator.on("stock.missing", shipping)`, plus shipping's own handling of that event. Inventory doesn't change, and it still knows nothing about shipping.)"""

L = {
 "id": "pat-10",
 "title": "Visitor, Iterator, Mediator and Memento",
 "minutes": 38,
 "goal": "By the end you can explain the expression problem and replace a Visitor with a sealed switch, write a lazy paging iterator with Kotlin's `sequence {}` (and know what Java needs instead), take snapshots that don't leak with Memento, and say when a Mediator helps.",
 "warmup": {
  "q": "A codebase evaluates expressions with a classic Visitor: `ExprVisitor` with `visitNum`, `visitAdd`, `visitMul`, and four visitor classes. You add a fifth node type, `Neg`. What do you have to touch?",
  "options": ["Only the new `Neg` class", "The visitor interface, an `accept` on `Neg`, and all four visitor classes", "Only the visitor interface", "Nothing: the visitor finds `Neg` through reflection"],
  "answer": 1,
  "why": "Visitor makes new operations cheap (a new visitor class) and new cases expensive: every visitor must learn the new case, and the interface needs a `visitNeg`. That is one half of the expression problem. A sealed type with `switch` has the same trade-off, but the compiler lists every place to change."
 },
 "sections": [
  {
   "h": "Visitor, the expression problem, and sealed types",
   "body": S1,
   "try": {
    "title": "Add a case in both styles",
    "minutes": 5,
    "steps": [
     "Run `VisitorVsSwitch` (Java or Kotlin) and check both results agree.",
     "Add a `Neg` case. Java: add `Neg` to `permits` and `record Neg(Expr e) implements Expr { public <R> R accept(ExprVisitor<R> v) { return v.visitNeg(this); } }`. Kotlin: `data class Neg(val e: Expr) : Expr { override fun <R> accept(v: ExprVisitor<R>) = v.visitNeg(this) }`. Build with the demo command.",
     "Fix each error the compiler gives you, build again, and keep a count of the places you edited."
    ],
    "code": code("java", "VisitorVsSwitch.java", "VisitorVsSwitch", "kotlin", "VisitorVsSwitch.kt", "VisitorVsSwitchKt"),
    "expect": "Both print `(2 + 3 * 4) = 14` from the visitor and from the switch, then `0 * (2 + 3 * 4) = 0`. Kotlin lists all three errors at once: `unresolved reference 'visitNeg'` and `'when' expression must be exhaustive. Add the 'is Neg' branch` twice. javac reports them in rounds: `cannot find symbol` first; add `visitNeg` to `ExprVisitor` and you get `Eval is not abstract and does not override abstract method visitNeg(Neg)`; implement that and the two switches fail with `does not cover all possible input values`. Visitor style cost the interface, `accept` and every visitor; switch style cost one branch per function."
   },
   "refs": [
    {"title": "Pattern matching for Java (Bierman and Goetz)", "url": "https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/pattern-matching-for-java.md", "kind": "read"}
   ]
  },
  {
   "h": "Iterator: let Kotlin write the state machine",
   "body": S2,
   "try": {
    "title": "Count the page fetches",
    "minutes": 4,
    "steps": [
     "Run `PagingDemo.kt` (or its Java twin, `PagingDemoJava`). Before you run, predict how many `GET` lines each of the two calls prints.",
     "Kotlin: change `take(2)` to `take(3)` and predict the number of GETs. Java: in `hasNext`, change `while` to `if` and predict the `all:` line.",
     "Run, then undo the change."
    ],
    "code": code("kotlin", "PagingDemo.kt", "PagingDemoKt", "java", "PagingDemoJava.java", "PagingDemoJava"),
    "expect": "`first two:` fetches only page 0; `all:` fetches pages 0, 1 and 2 and prints `[rf_1, rf_2, rf_3]`. With `take(3)`, three GETs run, because the third item sits behind the empty page. With `if` in Java, the iterator fetches the empty page, finds nothing and gives up: `all: [rf_1, rf_2]` after two GETs, and `rf_3` is silently lost."
   },
   "refs": [
    {"title": "Sequences (Kotlin docs)", "url": "https://kotlinlang.org/docs/sequences.html", "kind": "docs"},
    {"title": "iterator {} builder (Kotlin API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.sequences/iterator.html", "kind": "docs"}
   ]
  },
  {
   "h": "Memento: a snapshot you can hand back",
   "body": S3,
   "try": {
    "title": "Let the snapshot share the list",
    "minutes": 4,
    "steps": [
     "Run `MementoDemo` in either language and read both lines.",
     "In `save()`, store the live list instead of a copy: `new State(items, coupon)` in Java, `State(items, coupon)` in Kotlin. Predict the `restored:` line, then run.",
     "Put the copy back."
    ],
    "code": code("java", "MementoDemo.java", "MementoDemo", "kotlin", "MementoDemo.kt", "MementoDemoKt"),
    "expect": "`edited:   [sku-1, sku-2] coupon=AUTUMN10`, then `restored: [sku-1] coupon=`. Without the copy, the memento and the cart share one list. `sku-2` lands in the \"saved\" state too, and `restore` then clears that shared list before copying from it, so you get `restored: [] coupon=`: worse than no undo at all."
   }
  },
  {
   "h": "Mediator in brief",
   "body": S4,
   "figure": {"svg": FIG, "caption": "Without a mediator every service knows the others. With one, each knows only the hub, and the coordination rules live in one place."}
  }
 ],
 "analogy": "A visitor is a tax inspector who visits every kind of business with a different checklist for each; a new kind of business means every inspector learns a new checklist. An iterator is a librarian fetching books one at a time from the stacks, so you can start reading before the last shelf is reached. A memento is a photo of a whiteboard before you erase it. A mediator is an air-traffic tower: planes talk to the tower, never to each other. The analogy breaks on the photo. A photo can't change after you take it, but a software memento that shares a list with the live object changes every time you edit, which is the bug the lesson's demo shows.",
 "in_your_world": "The PSP clients in your services almost certainly page: refunds, disputes, payouts, settlement lines. Expose each as a Kotlin `Sequence` (or a Java `Iterator`) that fetches lazily, and the reconciliation job can stop at the first mismatch without downloading the rest. Mind that iterating twice hits the API twice. Memento is how a back-office tool offers undo on a draft refund batch, and how an event-sourced ledger keeps snapshots so that replay stays fast. Mediator is your checkout orchestration: inside one Quarkus service it can be a small router or a shared flow, and across services it is the Temporal workflow that sequences inventory, payment and shipping activities. Visitor shows up mostly when you write annotation processors or bytecode tools; in your own domain code, sealed types and `switch` or `when` replace it.",
 "mistake": "The most common Memento mistake is a shallow snapshot: `save()` stores a reference to the object's live mutable list (or an array, or a mutable nested object) instead of a copy. It happens because records and data classes look immutable, so `new State(items, coupon)` feels like a snapshot. It isn't: the record holds the same list the object keeps editing, so the \"saved\" state changes with every edit, and undo restores the present instead of the past. Copy every mutable part when you save (`List.copyOf`, `toList()`), copy again when you restore, and test it the way the lab does: save, edit, restore, edit again, restore again.",
 "compare": {
  "title": "Replacing a visitor: nested patterns in Java, guards in Kotlin",
  "java": {"title": "Expr.java", "src": """sealed interface Expr permits Num, Add, Mul {}
record Num(int value) implements Expr {}
record Add(Expr left, Expr right) implements Expr {}
record Mul(Expr left, Expr right) implements Expr {}

static int eval(Expr e) {
    return switch (e) {
        case Num(var v) -> v;
        case Add(var l, var r) -> eval(l) + eval(r);
        case Mul(Num(var z), var r) when z == 0 -> 0;       // nested record pattern: skip the right side
        case Mul(var l, var r) -> eval(l) * eval(r);
    };
}

static String show(Expr e) {                               // a new operation: one new function, no class touched
    return switch (e) {
        case Num(var v) -> Integer.toString(v);
        case Add(var l, var r) -> "(" + show(l) + " + " + show(r) + ")";
        case Mul(var l, var r) -> show(l) + " * " + show(r);
    };
}"""},
  "kotlin": {"title": "Expr.kt", "src": """sealed interface Expr
data class Num(val value: Int) : Expr
data class Add(val left: Expr, val right: Expr) : Expr
data class Mul(val left: Expr, val right: Expr) : Expr

fun eval(e: Expr): Int = when (e) {
    is Num -> e.value
    is Add -> eval(e.left) + eval(e.right)
    is Mul if e.left == Num(0) -> 0                         // no nested patterns in Kotlin: a guard says it
    is Mul -> eval(e.left) * eval(e.right)
}

fun show(e: Expr): String = when (e) {                      // a new operation: one new function, no class touched
    is Num -> e.value.toString()
    is Add -> "(${show(e.left)} + ${show(e.right)})"
    is Mul -> "${show(e.left)} * ${show(e.right)}"
}"""},
  "note": "Both delete the visitor interface and every `accept` method, and both make a new operation a single function. The difference is how far the patterns reach. Java 21 record patterns nest, so `Mul(Num(var z), var r) when z == 0` matches \"a multiplication whose left side is the literal 0\" in one case, and binds the fields as it goes. Kotlin's `when` matches on type and smart-casts, but has no destructuring patterns, so the same rule is a guard (`is Mul if e.left == Num(0)`), which works because data classes compare by value. Guards in `when` are stable since Kotlin 2.2.0. In both, adding a case such as `Neg` breaks every function that switches over `Expr`, which is the compiler listing your work."
 },
 "worked": {
  "title": "Retire a visitor in four steps",
  "steps": [
   {"say": "A fee-formula engine evaluates and prints expressions with a classic visitor. Product wants negation. Before reading on, list every file a `Neg` node touches in this design.",
    "code": """interface ExprVisitor<R> { R visitNum(Num n); R visitAdd(Add a); R visitMul(Mul m); }

sealed interface Expr permits Num, Add, Mul { <R> R accept(ExprVisitor<R> v); }
// Num, Add, Mul: each record implements accept(v) by calling its own visitXxx(this)

final class Eval implements ExprVisitor<Integer> { /* three visit methods */ }
final class Show implements ExprVisitor<String> { /* three visit methods */ }
// ...and any visitor another team wrote against ExprVisitor""", "lang": "java",
    "alt_code": """interface ExprVisitor<R> { fun visitNum(n: Num): R; fun visitAdd(a: Add): R; fun visitMul(m: Mul): R }

sealed interface Expr { fun <R> accept(v: ExprVisitor<R>): R }
// Num, Add, Mul: each data class implements accept(v) by calling its own visitXxx(this)

object Eval : ExprVisitor<Int> { /* three visit methods */ }
object Show : ExprVisitor<String> { /* three visit methods */ }
// ...and any visitor another team wrote against ExprVisitor""", "alt_lang": "kotlin"},
   {"say": "`Neg` needs a `visitNeg` on the interface, an `accept` on itself, and a new method in `Eval`, `Show` and every other visitor. The hierarchy is closed and ours, so retire the machinery first: drop `accept` and the interface, and write each operation as a switch. Behavior doesn't change; run the old tests.",
    "code": """sealed interface Expr permits Num, Add, Mul {}                 // 1. no accept, no visitor interface
record Num(int value) implements Expr {}
record Add(Expr left, Expr right) implements Expr {}
record Mul(Expr left, Expr right) implements Expr {}

static int eval(Expr e) {                                      // 2. each visitor becomes one function
    return switch (e) {
        case Num(var v) -> v;
        case Add(var l, var r) -> eval(l) + eval(r);
        case Mul(var l, var r) -> eval(l) * eval(r);
    };
}""", "lang": "java",
    "alt_code": """sealed interface Expr                                          // 1. no accept, no visitor interface
data class Num(val value: Int) : Expr
data class Add(val left: Expr, val right: Expr) : Expr
data class Mul(val left: Expr, val right: Expr) : Expr

fun eval(e: Expr): Int = when (e) {                            // 2. each visitor becomes one function
    is Num -> e.value
    is Add -> eval(e.left) + eval(e.right)
    is Mul -> eval(e.left) * eval(e.right)
}""", "alt_lang": "kotlin"},
   {"say": "Now add the case, and compile before writing any logic. The errors are the to-do list: one per function that switches over `Expr`.",
    "code": """sealed interface Expr permits Num, Add, Mul, Neg {}
record Neg(Expr e) implements Expr {}                          // 3. the new case

// javac: error: the switch expression does not cover all possible input values   (eval)
// javac: error: the switch expression does not cover all possible input values   (show)""", "lang": "java",
    "alt_code": """data class Neg(val e: Expr) : Expr                             // 3. the new case

// kotlinc: 'when' expression must be exhaustive. Add the 'is Neg' branch or an 'else' branch.   (eval)
// kotlinc: 'when' expression must be exhaustive. Add the 'is Neg' branch or an 'else' branch.   (show)""", "alt_lang": "kotlin"},
   {"say": "Fill in one branch per function. A brand-new operation, counting nodes for a complexity limit, is one more function, and no type changes at all.",
    "code": """case Neg(var x) -> -eval(x);                                   // 4. in eval
case Neg(var x) -> "-" + show(x);                              //    in show

static int count(Expr e) {                                     // 5. a new operation: one function
    return switch (e) {
        case Num n -> 1;
        case Add(var l, var r) -> 1 + count(l) + count(r);
        case Mul(var l, var r) -> 1 + count(l) + count(r);
        case Neg(var x) -> 1 + count(x);
    };
}""", "lang": "java",
    "alt_code": """is Neg -> -eval(e.e)                                           // 4. in eval
is Neg -> "-${show(e.e)}"                                      //    in show

fun count(e: Expr): Int = when (e) {                           // 5. a new operation: one function
    is Num -> 1
    is Add -> 1 + count(e.left) + count(e.right)
    is Mul -> 1 + count(e.left) + count(e.right)
    is Neg -> 1 + count(e.e)
}""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A lazy paging sequence and an invoice draft with undo",
  "minutes": 13,
  "files": [f"{lab}/main/{K}/Paging.kt", f"{lab}/main/{K}/InvoiceDraft.kt"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l10.*'",
  "steps": [
   "Run the tests once: all nine fail.",
   "In `Paging.kt`, write `pagedSequence` with the `sequence {}` builder: start at cursor 0, fetch a page, hand out its items, follow `next` until it is null.",
   "In `InvoiceDraft`, add a private data class that implements `Memento` and holds the lines and the note. `save()` stores copies; `restore` checks the type with `require`, then copies the lines back into the draft's own list.",
   "Write `DraftHistory`: keep mementos in an `ArrayDeque`, drop the oldest when there are more than `limit`, and restore the newest on `undo`.",
   "Run the tests until all nine pass. Then read the test that restores the same memento twice, and say which line of your `restore` makes it pass."
  ],
  "hints": [
   "Inside `sequence {}`, an ordinary `while` loop and `yieldAll(page.items)` are all you need. An empty page yields nothing, and the loop carries on to the next cursor.",
   "After `require(m is State) { \"...\" }`, Kotlin smart-casts `m` to `State` for the rest of the function. A private nested class may implement a public nested interface.",
   "In `restore`, `lines.clear()` then `lines.addAll(m.lines)` keeps the memento's list untouched. Assigning the memento's list to the draft instead would let the next edit change the memento."
  ],
  "done_when": "All nine tests in `IteratorMementoTest` pass."
 },
 "drill": {
  "title": "A paging iterator in Java, from memory",
  "minutes": 5,
  "prompt": "Close this page. Write the Java version: `static Iterator<String> refunds(Function<Integer, RefundPage> fetch)`, where `RefundPage(List<String> items, Integer next)` and `next` is null on the last page. It must skip empty pages and fetch nothing until `hasNext` is called. Then write the Kotlin `sequence {}` version and compare how much state each one keeps.",
  "answer": {"lang": "java", "src": """static Iterator<String> refunds(Function<Integer, RefundPage> fetch) {
    return new Iterator<>() {
        private Iterator<String> current = Collections.emptyIterator();
        private Integer cursor = 0;                              // null = no more pages

        @Override public boolean hasNext() {
            while (!current.hasNext() && cursor != null) {       // while, not if: skip empty pages
                RefundPage page = fetch.apply(cursor);
                current = page.items().iterator();
                cursor = page.next();
            }
            return current.hasNext();
        }

        @Override public String next() {
            if (!hasNext()) throw new NoSuchElementException();
            return current.next();
        }
    };
}""",
   "alt": {"lang": "kotlin", "title": "Kotlin", "src": """fun refunds(fetch: (Int) -> RefundPage): Sequence<String> = sequence {
    var cursor: Int? = 0                                         // the only state you write
    while (cursor != null) {
        val page = fetch(cursor)
        yieldAll(page.items)                                     // an empty page yields nothing
        cursor = page.next
    }
}"""}}
 },
 "recap": [
  "The expression problem: virtual methods make new cases cheap, Visitor makes new operations cheap. Sealed types plus `switch` or `when` give Visitor's side with no `accept` and no visitor interface.",
  "Delete visitors for closed hierarchies you own. Keep Visitor for open hierarchies or library APIs, such as annotation processing and bytecode tools.",
  "Kotlin's `sequence {}` turns a plain loop into a lazy iterator. Java needs a hand-written `Iterator`, with `while`, not `if`, in `hasNext`.",
  "A built sequence is cold (iterating again reruns the block) and may stop early, so `finally` inside it may never run.",
  "Memento: save a private, immutable snapshot that copies every mutable part, restore by copying back in, and bound the history.",
  "Mediator: colleagues talk only to a hub that holds the coordination rules. Keep it to routing and sequencing."
 ],
 "quiz": [
  {"q": "Your team owns a sealed `PaymentInstruction` hierarchy with five records, and keeps adding operations: validate, render, price, export. Which design makes each new operation cheapest?",
   "options": ["A classic Visitor with an `accept` method on each record", "An abstract method per operation on the sealed interface", "One function per operation with an exhaustive `switch` or `when`", "`instanceof` chains with a final `else` that throws"],
   "answer": 2,
   "why": "Operations are the axis that grows, so you want operations to be single functions: a sealed switch gives that, with the compiler checking each one covers all five records. A Visitor gets the same trade-off with more machinery. Abstract methods make each new operation touch all five records, and an `instanceof` chain loses the compiler's check."},
  {"q": "A Java paging iterator has `if (!current.hasNext() && cursor != null)` in `hasNext`. Pages are `[rf_1, rf_2]`, then an empty page, then `[rf_3]`. What does a full iteration return?",
   "options": ["`[rf_1, rf_2]`", "`[rf_1, rf_2, rf_3]`", "It throws `NoSuchElementException`", "It loops forever"],
   "answer": 0,
   "why": "After `rf_2`, `hasNext` fetches the empty page once, finds nothing, and returns false, because `if` doesn't try again. The iteration ends early and `rf_3` is never seen, with no error. `while` keeps fetching until it finds an item or runs out of pages."},
  {"q": "`val refunds = pagedSequence(fetch)` uses the `sequence {}` builder. The code calls `refunds.count()` and then `refunds.first()`. How many times is page 0 fetched?",
   "options": ["Once: a sequence caches its pages", "Twice: each terminal operation runs the block again from the top", "Never: sequences are lazy", "Once, but only if the pages are small"],
   "answer": 1,
   "why": "A sequence from `sequence {}` is cold: every new iteration starts the block over. `count()` walks all pages and `first()` starts again from page 0. If you need the items twice, collect them once with `toList()`, or accept the second round of API calls."},
  {"q": "`Draft.save()` returns `new State(lines, note)`, where `lines` is the draft's own `ArrayList`. The analyst saves, adds a line, and restores. What do they get?",
   "options": ["The draft as it was at save time", "An `UnsupportedOperationException`", "A `ConcurrentModificationException`", "The draft with the new line still in it, because the snapshot shares the live list"],
   "answer": 3,
   "why": "The record holds a reference to the same list the draft keeps editing, so the new line is in the \"saved\" state too. Depending on how `restore` copies, you get the present back or even an empty list. Copy every mutable part on save (`List.copyOf`) and on restore."},
  {"q": "From *Observer and Command*: an analyst's draft supports undo for \"add line\" and for \"apply discount rules\", which has no simple inverse. Which approach handles both?",
   "options": ["A command stack where every command implements `undo()`", "A memento saved before each edit, restored on undo", "A StateFlow of the draft that collectors can rewind", "A Chain of Responsibility of undo handlers"],
   "answer": 1,
   "why": "Command-based undo needs an inverse for every command, and \"apply discount rules\" doesn't have a clean one. A snapshot taken before any edit can always be restored, whatever the edit did. The two combine well: commands for the log, mementos for the undo. A StateFlow keeps only the latest value, so there is nothing to rewind to.",
   "from": "pat-08"}
 ],
 "flashcards": [
  {"front": "What is the expression problem, in one line each?", "back": "Virtual methods: new cases are cheap, new operations touch every class. Visitor (or sealed + switch): new operations are cheap, new cases touch every operation."},
  {"front": "When does Visitor still fit in modern Java or Kotlin?", "back": "For open hierarchies across modules, or when a library hands you one: `ElementVisitor` in annotation processors, javac's Tree API, ASM's `ClassVisitor`."},
  {"front": "Java pattern for \"a multiplication whose left side is 0\"? And Kotlin?", "back": "Java 21: `case Mul(Num(var z), var r) when z == 0`. Kotlin: `is Mul if e.left == Num(0)` (no nested patterns)."},
  {"front": "Why `while`, not `if`, in a paging iterator's `hasNext`?", "back": "An empty page must not end the iteration; `while` keeps fetching until it finds an item or runs out of pages."},
  {"front": "Iterating a `sequence {}` twice: what happens to the work inside it?", "back": "It runs again from the top: sequences built that way are cold. Collect with `toList()` if you need the items twice."},
  {"front": "Why can `finally` inside `sequence {}` or `iterator {}` fail to run?", "back": "If the consumer stops early, the rest of the block never runs. Open resources at the call site with `use {}`."},
  {"front": "What makes a memento safe?", "back": "It copies every mutable part on save, restore copies back in, only the originator can read it, and the history is bounded."}
 ],
 "terms": [
  {"term": "Visitor", "plain": "One class per operation, with a method per case, called through `accept` on each element."},
  {"term": "Double dispatch", "plain": "Choosing code by two runtime types: `accept` picks the case, `visit` picks the operation."},
  {"term": "Expression problem", "plain": "No plain design makes both new cases and new operations cheap; you pick the axis that grows."},
  {"term": "Iterator", "plain": "An object that hands out a collection's elements one at a time without exposing how they are stored."},
  {"term": "Cold sequence", "plain": "A sequence whose work reruns for every iteration, from the start."},
  {"term": "Memento", "plain": "An opaque snapshot of an object's state that only the object can read and restore."},
  {"term": "Mediator", "plain": "A hub that holds the rules for how several parts react to each other, so they don't call each other."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to add a Visitor to the sealed `PaymentInstruction` hierarchy \"so we can add operations without touching the classes\". Explain what you would do instead, and when you would agree with them.",
  "answer": "We own the hierarchy and it's sealed, so we already get what a visitor gives: we can add an operation without touching the records by writing one function with a `switch` (or `when`) over the five types. The compiler checks that each function covers every type, and record patterns let us match nested shapes that a visitor can't express easily. A visitor would add an interface with five methods and an `accept` on every record, and nothing else. The cost is the same either way when a new instruction type arrives: every operation must handle it, but with sealed types the compiler lists each one. I'd agree to a visitor if the hierarchy were open to other modules we can't recompile, or if we were plugging into a library that already speaks visitors, such as an annotation processor."
 },
 "deeper": {
  "minutes": 10,
  "body": """Kotlin's `sequence {}` is built on the same machinery as coroutines, but restricted. Its block runs on a `SequenceScope`, which allows only `yield` and `yieldAll` to suspend, so you can't call `delay` or another suspend function inside it. For asynchronous paging, where each page fetch is itself a suspending HTTP call, use `flow {}` and `emit` instead: a `Flow` is the suspending cousin of a sequence, cold in the same way, as you saw in *Flow basics: cold streams and operators* in the coroutines track.

Java's `Iterator` has an optional `remove()`, and its Javadoc says iterators \"allow the caller to remove elements from the underlying collection during the iteration with well-defined semantics\". That's why `iterator.remove()` is safe inside a loop where `list.remove(x)` throws `ConcurrentModificationException`. For paging iterators, leave `remove()` unsupported, which is the default.

Visitor and Composite often travel together: a visitor walks a composite tree. With sealed types, the walk is just recursion in each function, as in *Composite, Bridge and Flyweight*. If trees get deep enough to overflow the stack, an explicit stack in an iterator (or a `sequence {}` that pushes children) turns the recursion into iteration.

Memento meets event sourcing in snapshots. An aggregate's state is the fold of its events. Replaying ten thousand events on every load is slow, so the store keeps a snapshot every few hundred events, and loading means restoring the newest snapshot and replaying what came after it. The snapshot format then becomes a contract between versions of your code, so give it a version field from the start."""
 },
 "sources": [
  {"title": "Pattern matching for Java (Bierman and Goetz)", "url": "https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/pattern-matching-for-java.md"},
  {"title": "Sequences (Kotlin docs)", "url": "https://kotlinlang.org/docs/sequences.html"},
  {"title": "iterator {} builder (Kotlin API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.sequences/iterator.html"},
  {"title": "Iterator.java at jdk-25-ga", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Iterator.java"},
  {"title": "Data classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/data-classes.html"}
 ]
}

out = ROOT / "content/lessons/pat-10.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
