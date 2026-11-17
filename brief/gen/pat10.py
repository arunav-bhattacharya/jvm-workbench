import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l10"
K = "kotlin/workbench/patterns/l10"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l10.{cls}"


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def code(lang, name, cls, alt_lang, alt_name, alt_cls):
    d1 = J if lang == "java" else K
    d2 = J if alt_lang == "java" else K
    return {"lang": lang, "title": name, "src": read(f"{lab}/demo/{d1}/{name}"), "run": demo(cls), "file": f"{lab}/demo/{d1}/{name}",
            "alt": {"lang": alt_lang, "title": alt_name, "src": read(f"{lab}/demo/{d2}/{alt_name}"), "run": demo(alt_cls), "file": f"{lab}/demo/{d2}/{alt_name}"}}


FIG = """<svg viewBox="0 0 680 252" role="img" aria-label="Left: the stock room, the bike, the van and the counter all phone each other, six lines. Right: each of the four talks only to a dispatcher in the middle, four lines">
<text class="t-s t-m" x="160" y="28" text-anchor="middle">without: everyone phones everyone</text>
<rect class="box" x="20" y="50" width="100" height="36" rx="8"/>
<text class="t" x="70" y="73" text-anchor="middle">stock room</text>
<rect class="box" x="200" y="50" width="100" height="36" rx="8"/>
<text class="t" x="250" y="73" text-anchor="middle">bike</text>
<rect class="box" x="20" y="170" width="100" height="36" rx="8"/>
<text class="t" x="70" y="193" text-anchor="middle">van</text>
<rect class="box" x="200" y="170" width="100" height="36" rx="8"/>
<text class="t" x="250" y="193" text-anchor="middle">counter</text>
<line class="ln-bad" x1="120" y1="68" x2="200" y2="68"/>
<line class="ln-bad" x1="120" y1="188" x2="200" y2="188"/>
<line class="ln-bad" x1="70" y1="86" x2="70" y2="170"/>
<line class="ln-bad" x1="250" y1="86" x2="250" y2="170"/>
<line class="ln-bad" x1="120" y1="86" x2="200" y2="170"/>
<line class="ln-bad" x1="200" y1="86" x2="120" y2="170"/>
<text class="t-s t-bad" x="160" y="236" text-anchor="middle">6 lines; each new rule edits two parties</text>
<text class="t-s t-m" x="520" y="28" text-anchor="middle">with: everyone phones the dispatcher</text>
<rect class="box" x="380" y="50" width="100" height="36" rx="8"/>
<text class="t" x="430" y="73" text-anchor="middle">stock room</text>
<rect class="box" x="560" y="50" width="100" height="36" rx="8"/>
<text class="t" x="610" y="73" text-anchor="middle">bike</text>
<rect class="box" x="380" y="170" width="100" height="36" rx="8"/>
<text class="t" x="430" y="193" text-anchor="middle">van</text>
<rect class="box" x="560" y="170" width="100" height="36" rx="8"/>
<text class="t" x="610" y="193" text-anchor="middle">counter</text>
<rect class="box-a" x="460" y="108" width="120" height="40" rx="8"/>
<text class="t" x="520" y="133" text-anchor="middle">dispatcher</text>
<line class="ln-a" x1="440" y1="86" x2="490" y2="108"/>
<line class="ln-a" x1="600" y1="86" x2="550" y2="108"/>
<line class="ln-a" x1="440" y1="170" x2="490" y2="148"/>
<line class="ln-a" x1="600" y1="170" x2="550" y2="148"/>
<text class="t-s t-ok" x="520" y="236" text-anchor="middle">4 lines; the rules live in one place</text>
</svg>""".replace("\n", "")

OPENING = """Once a month, an inspector from the town hall visits the corner shop and goes through the Saturday breakfast box. Her check depends on what she finds: the date on the milk, the price label on the jam. Inside it she finds a smaller box, opens it and starts again. Every spring brings a new checklist, but the kinds of goods hardly change.

Three more jobs belong to the same family. The old warehouse program sends its stock list a page at a time, to be read item by item. The town's dispatcher tells bikes and vans where to go, so the riders never phone each other. And before rearranging a shelf, the shopkeeper takes a photo, so a bad change can be undone. The easy traps are a new method in every class for each new job, and a photo that changes with the shelf.

The last lesson asked where new jobs should go when the kinds stay fixed. In this lesson, we'll answer with Visitor and with sealed types, then walk the stock list lazily (Iterator), take a safe photo (Memento) and hire the dispatcher (Mediator). Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_VISITOR = """interface GoodsVisitor<R> { R visitItem(Item i); R visitFresh(Fresh f); R visitBox(Box b); }

sealed interface Goods permits Item, Fresh, Box { <R> R accept(GoodsVisitor<R> v); }
record Item(String name, long cents) implements Goods {
    public <R> R accept(GoodsVisitor<R> v) { return v.visitItem(this); }
}
record Fresh(String name, long cents, int daysLeft) implements Goods {
    public <R> R accept(GoodsVisitor<R> v) { return v.visitFresh(this); }
}
record Box(List<Goods> contents) implements Goods {
    public <R> R accept(GoodsVisitor<R> v) { return v.visitBox(this); }
}

final class Price implements GoodsVisitor<Long> {        // one job, one method per kind of goods
    public Long visitItem(Item i) { return i.cents(); }
    public Long visitFresh(Fresh f) { return f.daysLeft() == 0 ? f.cents() / 2 : f.cents(); }
    public Long visitBox(Box b) {
        long sum = 0;
        for (Goods g : b.contents()) sum += g.accept(this);
        return sum;
    }
}

long total = breakfast.accept(new Price());   // two hops: accept picks the kind, visit picks the job"""
K_VISITOR = """interface GoodsVisitor<R> { fun visitItem(i: Item): R; fun visitFresh(f: Fresh): R; fun visitBox(b: Box): R }

sealed interface Goods { fun <R> accept(v: GoodsVisitor<R>): R }
data class Item(val name: String, val cents: Long) : Goods {
    override fun <R> accept(v: GoodsVisitor<R>) = v.visitItem(this)
}
data class Fresh(val name: String, val cents: Long, val daysLeft: Int) : Goods {
    override fun <R> accept(v: GoodsVisitor<R>) = v.visitFresh(this)
}
data class Box(val contents: List<Goods>) : Goods {
    override fun <R> accept(v: GoodsVisitor<R>) = v.visitBox(this)
}

object Price : GoodsVisitor<Long> {                      // one job, one method per kind of goods
    override fun visitItem(i: Item) = i.cents
    override fun visitFresh(f: Fresh) = if (f.daysLeft == 0) f.cents / 2 else f.cents
    override fun visitBox(b: Box) = b.contents.sumOf { it.accept(this) }
}

val total = breakfast.accept(Price)          // two hops: accept picks the kind, visit picks the job"""

J_SWITCH = """static long price(Goods g) {
    return switch (g) {
        case Item(var name, var cents) -> cents;
        case Fresh(var name, var cents, var days) when days == 0 -> cents / 2;   // last day: half price
        case Fresh(var name, var cents, var days) -> cents;
        case Box(var contents) -> contents.stream().mapToLong(VisitorVsSwitch::price).sum();
    };
}

static List<String> inspect(Goods g) {        // a new job: one new function, no class touched
    return switch (g) {
        case Item i -> i.cents() > 0 ? List.of() : List.of(i.name() + ": no price label");
        case Fresh f -> f.daysLeft() > 0 ? List.of() : List.of(f.name() + ": last day");
        case Box b -> b.contents().stream().flatMap(x -> inspect(x).stream()).toList();
    };
}"""
K_SWITCH = """fun price(g: Goods): Long = when (g) {
    is Item -> g.cents
    is Fresh if g.daysLeft == 0 -> g.cents / 2               // last day: half price
    is Fresh -> g.cents
    is Box -> g.contents.sumOf { price(it) }
}

fun inspect(g: Goods): List<String> = when (g) {             // a new job: one new function, no class touched
    is Item -> if (g.cents > 0) emptyList() else listOf("${g.name}: no price label")
    is Fresh -> if (g.daysLeft > 0) emptyList() else listOf("${g.name}: last day")
    is Box -> g.contents.flatMap { inspect(it) }
}"""

S0 = """The breakfast box from *Composite, Bridge and Flyweight* now holds three kinds of goods: a packet with a price (an `Item`), fresh food that also knows how many days it has left (a `Fresh` item), and a smaller `Box`. The shop keeps adding jobs that treat each kind differently: the price (fresh food is half price on its last day), the inspector's check, the label printer, the weight for the courier.

**Visitor** is the 1994 book's answer: put each job in a class of its own, called a visitor, with one method per kind of goods. Each kind gets one small `accept` method that calls the right one:

""" + pair(J_VISITOR, K_VISITOR) + """

Read `breakfast.accept(new Price())` as two hops. First `accept` runs on the box, so the box's own version is chosen, and it calls `visitBox`. Then `visitBox` asks each thing inside to `accept` the same visitor. Choosing the code by two types at once, the kind of goods and the job, is called **double dispatch**.

The inspector is the picture: she visits each kind of goods and does a different check for each. A new checklist is one new visitor class, and nothing in the box changes. A new kind of goods, say `Frozen`, costs a method on the visitor interface, an `accept` on `Frozen`, and an edit in every visitor anyone ever wrote. That's a lot of paperwork for a bag of frozen peas.

That trade-off is called the **expression problem**. With ordinary methods, a `price()` on each record, a new kind is cheap and a new job touches every class. With Visitor it's the other way round. Plain Java and Kotlin can't make both cheap, so you pick the side you expect to grow. In the shop, the kinds of goods change rarely and new jobs arrive every month, which favors Visitor's side.

Sealed types and pattern matching give you that side without the machinery: no `accept`, no visitor interface, one function per job with a `switch` or `when` inside, over the same records:

""" + pair(J_SWITCH, K_SWITCH) + """

`VisitorVsSwitch`, in the Try it, prices the box both ways and sends the inspector through it:

```text
breakfast box: 1060 cents (visitor) = 1060 cents (switch)
inspector found: [milk: last day]
```

The two prices agree. The switch version is one function per job, and the guard `when days == 0` states the last-day rule right in the case. The design notes for Java's pattern matching put it plainly: "if your language has sufficiently powerful pattern matching, the Visitor pattern is almost completely unnecessary". The same notes say ordinary methods are still fine where they fit.

The inspector picture breaks at a new kind of goods. A real inspector who meets something new can improvise. A visitor can't: it has no method for a kind it was never told about. With sealed types that's the point, because the compiler lists every job that needs a new branch.

**For a closed set of kinds you own, a sealed switch does Visitor's job. Keep Visitor for sets you can't close.**

Visitor still fits when the set of kinds is open to code you don't compile, or when a library hands you one, such as the visitors in Java's annotation processing API or in ASM, a library for reading and writing compiled classes. Next, we'll walk along a list that arrives in pages."""

# ---------------------------------------------------------------- section 1
J_ITER = """static Iterator<String> stock(Function<Integer, StockPage> fetch) {
    return new Iterator<>() {
        private Iterator<String> current = Collections.emptyIterator();
        private Integer cursor = 0;                              // null = no more pages

        public boolean hasNext() {
            while (!current.hasNext() && cursor != null) {       // while, not if: skip empty pages
                StockPage page = fetch.apply(cursor);
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
}"""
K_ITER = """fun stock(fetch: (Int) -> StockPage): Sequence<String> = sequence {
    var cursor: Int? = 0
    while (cursor != null) {
        val page = fetch(cursor)                                 // runs only when the consumer needs more
        yieldAll(page.items)
        cursor = page.next
    }
}"""

S1 = """The old warehouse program from *Adapter and Facade* lists its stock a page at a time. Ask for page 0, and it sends a few items plus a **cursor**, a bookmark that says where the next page starts. Follow the cursors until one comes back empty (`null`), and you've seen everything. Loading every page into a list first wastes memory, and it makes the first item wait for the last page.

An **iterator** is an object that hands out items one at a time without saying how they're stored. It's walking along a shelf: look at one item, then step to the next. In Java you write its bookkeeping by hand:

""" + pair(J_ITER, K_ITER) + """

The Java version keeps two fields of state, and `hasNext` holds a classic bug: write `if` instead of `while`, and an empty page in the middle ends the walk early. Kotlin's `sequence {}` builder lets you write the loop you'd write for a list. `yield` and `yieldAll` pause the block until the consumer asks for the next item, and the compiler writes the bookkeeping. Nothing runs until someone starts walking. `PagingDemo`, in the Try it, takes the first two items and then all of them:

```text
  warehouse: sending page 0
first two: [rye bread, jam]
  warehouse: sending page 0
  warehouse: sending page 1
  warehouse: sending page 2
all: [rye bread, jam, tea]
```

`take(2)` needed one page, and the warehouse program, which does exactly what it's asked and nothing more, sent one. The full walk needed all three pages, the empty one included.

Two properties surprise people. A sequence built this way is **cold**: each new walk runs the block again from the top, so walking twice fetches every page twice. And if the consumer stops early, the rest of the block never runs. The `iterator {}` docs warn that "finally blocks may be left unexecuted". So don't open a connection inside the block and close it in `finally`; open it where you call the sequence, with `use {}`.

The shelf picture breaks right there. A real shelf is there whether you look or not, and walking it twice shows the same items. A cold sequence builds the shelf again for every walk.

**A sequence does its work again for every walk. Collect it with `toList()` when you need the items twice.**

When you want your own type to work in a `for` loop, make it `Iterable` and build its iterator with `iterator {}`, the sibling of `sequence {}`: `class Shelf(...) : Iterable<String> { override fun iterator() = iterator { yieldAll(...) } }`. Java has no such builder. `Stream.iterate(seed, hasNext, next)` covers simple cases, but for pages like these the hand-written iterator is still the clearest Java.

The iterator reads the shelf. Next, we'll take a photo of it before a change."""

# ---------------------------------------------------------------- section 2
J_MEMENTO = """final class Shelf {
    private final List<String> items = new ArrayList<>();
    private String sign = "";

    interface Memento {}                                             // what callers hold: opaque
    private record Photo(List<String> items, String sign) implements Memento {}

    Memento save() { return new Photo(List.copyOf(items), sign); }   // copy: later changes must not leak in

    void restore(Memento m) {
        Photo p = (Photo) m;
        items.clear();
        items.addAll(p.items());                                     // copy back in: the photo stays as it was
        sign = p.sign();
    }
}"""
K_MEMENTO = """class Shelf {
    private val items = mutableListOf<String>()
    private var sign = ""

    interface Memento                                                // what callers hold: opaque
    private data class Photo(val items: List<String>, val sign: String) : Memento

    fun save(): Memento = Photo(items.toList(), sign)               // copy: later changes must not leak in

    fun restore(m: Memento) {
        val p = m as Photo
        items.clear()
        items += p.items                                             // copy back in: the photo stays as it was
        sign = p.sign
    }
}"""

S2 = """Before the shopkeeper rearranges the front shelf, she takes a photo of it. If the new layout is a mess, she puts everything back exactly as in the photo. *Observer and Command* undid a change by running its opposite, and that works for "restock 12 loaves". It doesn't work for "rearrange the whole shelf for the autumn sale", which has no clean opposite.

**Memento** is the photo. An object saves a snapshot of its state before a change, and puts it back on undo. The object that takes and restores the snapshot is called the **originator**; the snapshot itself is the **memento**:

""" + pair(J_MEMENTO, K_MEMENTO) + """

`MementoDemo`, in the Try it, puts rye bread on the shelf, takes the photo, adds jam and an autumn sign, then restores:

```text
changed:  [rye bread, jam] sign=Autumn sale
restored: [rye bread] sign=
```

Three rules make it work. The snapshot must not share anything changeable with the live object: copy the list with `List.copyOf` or `toList()`, or later changes leak into the photo. Restore must copy back in rather than point at the photo's list, so the same photo can be restored twice. And only the originator reads it. Callers get an opaque `Memento`, something to keep and hand back, while the record with the data is private, so nothing else depends on how the shelf stores things.

The photo picture breaks exactly where the first rule guards. A real photo can't change after you take it. A memento that shares a list with the live shelf changes with every edit: a window, not a photo. The Try it shows what that costs.

**A snapshot that shares a changeable list is no snapshot. Copy every changeable part, on save and on restore.**

Records and data classes make the rest easy. When the whole state is already an immutable record, the pattern almost disappears: the state is its own memento, and an undo history is a list of old states. That's a strong argument for immutable data.

There are two costs. History grows with every checkpoint, so bound it; the lab keeps the newest few. And a snapshot of a big object takes memory, which is why programs with long histories save one now and then and replay the changes made after it.

Next, a pattern for parts of a program that keep reacting to each other."""

# ---------------------------------------------------------------- section 3
J_MEDIATOR = """interface Colleague { void receive(String message); }

final class Dispatcher {
    private final Map<String, List<Colleague>> routes = new HashMap<>();
    void on(String message, Colleague c) { routes.computeIfAbsent(message, k -> new ArrayList<>()).add(c); }
    void send(String message) { routes.getOrDefault(message, List.of()).forEach(c -> c.receive(message)); }
}

dispatcher.on("parcel.packed", bike);
dispatcher.on("parcel.packed", counter);        // the counter texts the customer
dispatcher.on("parcel.tooHeavy", van);          // the bike never calls the van directly"""
K_MEDIATOR = """fun interface Colleague { fun receive(message: String) }

class Dispatcher {
    private val routes = mutableMapOf<String, MutableList<Colleague>>()
    fun on(message: String, c: Colleague) { routes.getOrPut(message) { mutableListOf() } += c }
    fun send(message: String) { routes[message].orEmpty().forEach { it.receive(message) } }
}

dispatcher.on("parcel.packed", bike)
dispatcher.on("parcel.packed", counter)         // the counter texts the customer
dispatcher.on("parcel.tooHeavy", van)           // the bike never calls the van directly"""

S3 = """The town's couriers used to phone each other. A bike rider who found a parcel too heavy rang the van driver, the stock room rang the bike when an item ran out, and the counter rang everyone when an order was cancelled. Four parties need six phone lines, and every new rule means teaching two of them a new call. So the town hired a dispatcher. Everyone phones the dispatcher, and the dispatcher knows who needs to hear what.

A **mediator** is that dispatcher: an object that holds the rules for how several parts of a program react to each other, so the parts, called **colleagues**, never call each other directly:

""" + pair(J_MEDIATOR, K_MEDIATOR) + """

When the bike finds a parcel too heavy, it calls `dispatcher.send("parcel.tooHeavy")` and goes back to riding. It doesn't know the van exists. The figure counts the lines: six without the dispatcher, four with it.

Mediator and Observer look alike. An observer, from *Observer and Command*, is one subject telling its listeners about itself. A mediator sits between many parties and holds the rules about who reacts to what. In coroutine code, one `MutableSharedFlow` of messages that every colleague shares is a natural mediator.

The dispatcher picture holds up well, and it breaks where dispatchers get ambitious. A real dispatcher who starts weighing parcels and planning routes is one person doing two jobs. A mediator that starts working out delivery fees or checking addresses becomes a **god object**, a class that knows everything and that everything depends on.

**A mediator routes messages. When it starts doing the work, move the work back to the colleague that owns it.**

Check yourself. A new rule arrives: when stock runs out, the bike must cancel its pickup. With the dispatcher above, what do you change? (One registration, `dispatcher.on("stock.missing", bike)`, plus the bike's own handling of that message. The stock room doesn't change, and it still knows nothing about bikes.)"""

L = {
 "id": "pat-10",
 "title": "Visitor, Iterator, Mediator and Memento",
 "minutes": 38,
 "goal": "By the end you can explain the expression problem and replace a Visitor with a sealed switch, write a lazy paging iterator with Kotlin's `sequence {}` (and know what Java needs instead), take snapshots that don't leak with Memento, and say when a Mediator helps.",
 "opening": OPENING,
 "warmup": {
  "q": "The shop prices its goods with a classic Visitor: `GoodsVisitor` has `visitItem`, `visitFresh` and `visitBox`, and there are four visitor classes (price, inspect, label and weigh). You add a new kind of goods, `Frozen`. What do you have to touch?",
  "options": ["Only the new `Frozen` class", "The visitor interface, an `accept` on `Frozen`, and all four visitor classes", "Only the visitor interface", "Nothing: the visitor finds `Frozen` through reflection"],
  "answer": 1,
  "why": "Visitor makes new jobs cheap (a new visitor class) and new kinds expensive: every visitor must learn the new kind, and the interface needs a `visitFrozen`. That is one half of the expression problem. A sealed type with `switch` has the same trade-off, but the compiler lists every place to change, and there's no `accept` to write."
 },
 "sections": [
  {
   "h": "Visitor: an inspector with a different check for each kind of goods",
   "body": S0,
   "try": {
    "title": "Add a kind of goods in both styles",
    "minutes": 5,
    "steps": [
     "Run `VisitorVsSwitch` (Java or Kotlin) and check that both prices agree.",
     "Add a `Frozen` kind. Java: add `Frozen` to `permits` and add `record Frozen(String name, long cents) implements Goods { public <R> R accept(GoodsVisitor<R> v) { return v.visitFrozen(this); } }`. Kotlin: add `data class Frozen(val name: String, val cents: Long) : Goods { override fun <R> accept(v: GoodsVisitor<R>) = v.visitFrozen(this) }`. Build with the demo command.",
     "Fix each error the compiler gives you, build again, and count the places you edited."
    ],
    "code": code("java", "VisitorVsSwitch.java", "VisitorVsSwitch", "kotlin", "VisitorVsSwitch.kt", "VisitorVsSwitchKt"),
    "expect": "Both print `breakfast box: 1060 cents (visitor) = 1060 cents`, then `inspector found: [milk: last day]`: the milk has no days left, so it's half price, and the inspector flags it. Kotlin lists all three errors at once: `Unresolved reference 'visitFrozen'`, then `'when' expression must be exhaustive. Add the 'is Frozen' branch or an 'else' branch.` twice. javac reports them in rounds: `cannot find symbol` first; add `visitFrozen` to `GoodsVisitor` and you get `Price is not abstract and does not override abstract method visitFrozen(Frozen) in GoodsVisitor`; write that method and the two switches fail with `the switch expression does not cover all possible input values`. The visitor style cost the interface, `accept` and every visitor; the switch style cost one branch per function."
   },
   "refs": [
    {"title": "Pattern matching for Java (Bierman and Goetz)", "url": "https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/pattern-matching-for-java.md", "kind": "read"}
   ]
  },
  {
   "h": "Iterator: walk the warehouse's stock list one item at a time",
   "body": S1,
   "try": {
    "title": "Count the pages the warehouse sends",
    "minutes": 4,
    "steps": [
     "Open `PagingDemo.kt` (or its Java twin, `PagingDemoJava`). Before you run it, predict how many `warehouse:` lines each of the two calls prints.",
     "Kotlin: change `take(2)` to `take(3)` and predict the number of pages sent. Java: in `hasNext`, change `while` to `if` and predict the `all:` line.",
     "Run, then undo the change."
    ],
    "code": code("kotlin", "PagingDemo.kt", "PagingDemoKt", "java", "PagingDemoJava.java", "PagingDemoJava"),
    "expect": "`first two:` needs only page 0; `all:` fetches pages 0, 1 and 2 and prints `[rye bread, jam, tea]`. With `take(3)`, three pages go out, because the third item sits behind the empty page (the line still says `first two:`, since only the number changed). With `if` in Java, the iterator fetches the empty page, finds nothing and gives up: `all: [rye bread, jam]` after two pages, and the tea is silently lost."
   },
   "refs": [
    {"title": "Sequences (Kotlin docs)", "url": "https://kotlinlang.org/docs/sequences.html", "kind": "docs"},
    {"title": "iterator {} builder (Kotlin API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.sequences/iterator.html", "kind": "docs"}
   ]
  },
  {
   "h": "Memento: a photo of the shelf you can put back",
   "body": S2,
   "try": {
    "title": "Let the photo share the list",
    "minutes": 4,
    "steps": [
     "Run `MementoDemo` in either language and read both lines.",
     "In `save()`, store the live list instead of a copy: `new Photo(items, sign)` in Java, `Photo(items, sign)` in Kotlin. Predict the `restored:` line, then run.",
     "Put the copy back."
    ],
    "code": code("java", "MementoDemo.java", "MementoDemo", "kotlin", "MementoDemo.kt", "MementoDemoKt"),
    "expect": "`changed:  [rye bread, jam] sign=Autumn sale`, then `restored: [rye bread] sign=`. Without the copy, the photo and the shelf share one list. The jam lands in the \"saved\" state too, and `restore` then clears that shared list before copying from it, so you get `restored: [] sign=`: an empty shelf, which is worse than no undo at all."
   }
  },
  {
   "h": "Mediator: one dispatcher, so bikes and vans never phone each other",
   "body": S3,
   "figure": {"svg": FIG, "caption": "Without a dispatcher, every party phones the others. With one, each knows only the dispatcher, and the rules about who hears what live in one place."}
  }
 ],
 "compare": {
  "title": "Replacing a visitor: nested record patterns in Java, guards in Kotlin",
  "java": {"title": "GoodsJobs.java", "src": """sealed interface Goods permits Item, Fresh, Box, Gift {}
record Item(String name, long cents) implements Goods {}
record Fresh(String name, long cents, int daysLeft) implements Goods {}
record Box(List<Goods> contents) implements Goods {}
record Gift(Goods inside, String paper) implements Goods {}          // gift paper around anything

static long price(Goods g) {
    return switch (g) {
        case Item(var name, var cents) -> cents;
        case Fresh(var name, var cents, var days) when days == 0 -> cents / 2;
        case Fresh(var name, var cents, var days) -> cents;
        case Box(var contents) -> contents.stream().mapToLong(GoodsJobs::price).sum();
        case Gift(Fresh f, var paper) -> price(f);                    // nested pattern: food is wrapped for free
        case Gift(var inside, var paper) -> price(inside) + 150;      // wrapping anything else costs 1.50
    };
}

static String label(Goods g) {                                       // a new job: one new function, no class touched
    return switch (g) {
        case Item i -> i.name();
        case Fresh f -> f.name() + " (" + f.daysLeft() + " days left)";
        case Box b -> "box of " + b.contents().size();
        case Gift(var inside, var paper) -> label(inside) + " in " + paper + " paper";
    };
}"""},
  "kotlin": {"title": "GoodsJobs.kt", "src": """sealed interface Goods
data class Item(val name: String, val cents: Long) : Goods
data class Fresh(val name: String, val cents: Long, val daysLeft: Int) : Goods
data class Box(val contents: List<Goods>) : Goods
data class Gift(val inside: Goods, val paper: String) : Goods        // gift paper around anything

fun price(g: Goods): Long = when (g) {
    is Item -> g.cents
    is Fresh if g.daysLeft == 0 -> g.cents / 2
    is Fresh -> g.cents
    is Box -> g.contents.sumOf { price(it) }
    is Gift if g.inside is Fresh -> price(g.inside)                  // no nested patterns: a guard says it
    is Gift -> price(g.inside) + 150                                 // wrapping anything else costs 1.50
}

fun label(g: Goods): String = when (g) {                             // a new job: one new function, no class touched
    is Item -> g.name
    is Fresh -> "${g.name} (${g.daysLeft} days left)"
    is Box -> "box of ${g.contents.size}"
    is Gift -> "${label(g.inside)} in ${g.paper} paper"
}"""},
  "note": "Both delete the visitor interface and every `accept` method, and both make a new job a single function. The difference is how far the patterns reach. Java 21 record patterns nest, so `Gift(Fresh f, var paper)` matches \"a gift with fresh food inside\" in one case and takes the parts out as it goes. Kotlin's `when` matches on the type and smart-casts (after `is Gift`, the compiler treats `g` as a `Gift`), but it has no patterns that take a record apart, so the same rule is a guard: `is Gift if g.inside is Fresh`. Guards in `when` are stable since Kotlin 2.2.0. In both, adding a kind such as `Frozen` breaks every function that switches over `Goods`, which is the compiler listing your work."
 },
 "worked": {
  "title": "Retire a visitor in four steps",
  "steps": [
   {"say": "The shop prices and labels its goods with a classic visitor. Now it sells gift-wrapped goods too: a `Gift` holds any other goods and the paper around them. Before reading on, list every file a `Gift` touches in this design.",
    "code": """interface GoodsVisitor<R> { R visitItem(Item i); R visitFresh(Fresh f); R visitBox(Box b); }

sealed interface Goods permits Item, Fresh, Box { <R> R accept(GoodsVisitor<R> v); }
// Item, Fresh, Box: each record implements accept(v) by calling its own visitXxx(this)

final class Price implements GoodsVisitor<Long> { /* three visit methods */ }
final class Label implements GoodsVisitor<String> { /* three visit methods */ }
// ...and any visitor someone else wrote against GoodsVisitor""", "lang": "java",
    "alt_code": """interface GoodsVisitor<R> { fun visitItem(i: Item): R; fun visitFresh(f: Fresh): R; fun visitBox(b: Box): R }

sealed interface Goods { fun <R> accept(v: GoodsVisitor<R>): R }
// Item, Fresh, Box: each data class implements accept(v) by calling its own visitXxx(this)

object Price : GoodsVisitor<Long> { /* three visit methods */ }
object Label : GoodsVisitor<String> { /* three visit methods */ }
// ...and any visitor someone else wrote against GoodsVisitor""", "alt_lang": "kotlin"},
   {"say": "`Gift` needs a `visitGift` on the interface, an `accept` on itself, and a new method in `Price`, `Label` and every other visitor. The set of kinds is closed and ours, so retire the machinery first: drop `accept` and the interface, and write each job as a switch. Behavior doesn't change, so the old tests still pass.",
    "code": """sealed interface Goods permits Item, Fresh, Box {}                 // 1. no accept, no visitor interface
record Item(String name, long cents) implements Goods {}
record Fresh(String name, long cents, int daysLeft) implements Goods {}
record Box(List<Goods> contents) implements Goods {}

static String label(Goods g) {                                     // 2. each visitor becomes one function
    return switch (g) {
        case Item i -> i.name();
        case Fresh f -> f.name() + " (" + f.daysLeft() + " days left)";
        case Box b -> "box of " + b.contents().size();
    };
}""", "lang": "java",
    "alt_code": """sealed interface Goods                                             // 1. no accept, no visitor interface
data class Item(val name: String, val cents: Long) : Goods
data class Fresh(val name: String, val cents: Long, val daysLeft: Int) : Goods
data class Box(val contents: List<Goods>) : Goods

fun label(g: Goods): String = when (g) {                           // 2. each visitor becomes one function
    is Item -> g.name
    is Fresh -> "${g.name} (${g.daysLeft} days left)"
    is Box -> "box of ${g.contents.size}"
}""", "alt_lang": "kotlin"},
   {"say": "Now add the kind, and compile before writing any logic. The errors are the to-do list: one per function that switches over `Goods`.",
    "code": """sealed interface Goods permits Item, Fresh, Box, Gift {}
record Gift(Goods inside, String paper) implements Goods {}        // 3. the new kind

// javac: error: the switch expression does not cover all possible input values   (price)
// javac: error: the switch expression does not cover all possible input values   (label)""", "lang": "java",
    "alt_code": """data class Gift(val inside: Goods, val paper: String) : Goods      // 3. the new kind

// kotlinc: 'when' expression must be exhaustive. Add the 'is Gift' branch or an 'else' branch.   (price)
// kotlinc: 'when' expression must be exhaustive. Add the 'is Gift' branch or an 'else' branch.   (label)""", "alt_lang": "kotlin"},
   {"say": "Fill in one branch per function. A brand-new job, counting how many things the inspector must check, is one more function, and no type changes at all.",
    "code": """case Gift(var inside, var paper) -> price(inside) + 150;                        // 4. in price
case Gift(var inside, var paper) -> label(inside) + " in " + paper + " paper";  //    in label

static int count(Goods g) {                                        // 5. a new job: one function
    return switch (g) {
        case Item i -> 1;
        case Fresh f -> 1;
        case Box b -> b.contents().stream().mapToInt(GoodsJobs::count).sum();
        case Gift(var inside, var paper) -> count(inside);
    };
}""", "lang": "java",
    "alt_code": """is Gift -> price(g.inside) + 150                                   // 4. in price
is Gift -> "${label(g.inside)} in ${g.paper} paper"                //    in label

fun count(g: Goods): Int = when (g) {                              // 5. a new job: one function
    is Item, is Fresh -> 1
    is Box -> g.contents.sumOf { count(it) }
    is Gift -> count(g.inside)
}""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A lazy stock list and a shelf with undo",
  "minutes": 13,
  "files": [f"{lab}/main/{K}/Paging.kt", f"{lab}/main/{K}/ShelfLayout.kt"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l10.*'",
  "steps": [
   "Run the tests once: all nine fail.",
   "In `Paging.kt`, write `pagedSequence` with the `sequence {}` builder: start at cursor 0, fetch a page, hand out its items, and follow `next` until it is null.",
   "In `ShelfLayout`, add a private data class that implements `Memento` and holds the slots and the sign. `save()` stores copies; `restore` checks the type with `require`, then copies the slots back into the shelf's own list.",
   "Write `ShelfHistory`: keep mementos in an `ArrayDeque`, drop the oldest when there are more than `limit`, and restore the newest on `undo`.",
   "Run the tests until all nine pass. Then read the test that restores the same memento twice, and say which line of your `restore` makes it pass."
  ],
  "hints": [
   "Inside `sequence {}`, an ordinary `while` loop and `yieldAll(page.items)` are all you need. An empty page yields nothing, and the loop carries on to the next cursor.",
   "After `require(m is Photo) { \"...\" }`, Kotlin smart-casts `m` to `Photo` for the rest of the function. A private nested class may implement a public nested interface.",
   "In `restore`, `slots.clear()` and then `slots.addAll(m.slots)` keep the memento's list untouched. Pointing the shelf at the memento's list instead would let the next change alter the memento."
  ],
  "done_when": "All nine tests in `IteratorMementoTest` pass."
 },
 "drill": {
  "title": "A paging iterator in Java, from memory",
  "minutes": 5,
  "prompt": "Close this page. Write the Java version: `static Iterator<String> stock(Function<Integer, StockPage> fetch)`, where `StockPage(List<String> items, Integer next)` and `next` is null on the last page. It must skip empty pages and fetch nothing until `hasNext` is called. Then write the Kotlin `sequence {}` version and compare how much state each one keeps.",
  "answer": {"lang": "java", "src": """static Iterator<String> stock(Function<Integer, StockPage> fetch) {
    return new Iterator<>() {
        private Iterator<String> current = Collections.emptyIterator();
        private Integer cursor = 0;                              // null = no more pages

        @Override public boolean hasNext() {
            while (!current.hasNext() && cursor != null) {       // while, not if: skip empty pages
                StockPage page = fetch.apply(cursor);
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
   "alt": {"lang": "kotlin", "title": "Kotlin", "src": """fun stock(fetch: (Int) -> StockPage): Sequence<String> = sequence {
    var cursor: Int? = 0                                         // the only state you write
    while (cursor != null) {
        val page = fetch(cursor)
        yieldAll(page.items)                                     // an empty page yields nothing
        cursor = page.next
    }
}"""}}
 },
 "recap": [
  "The expression problem: ordinary methods make new kinds cheap, Visitor makes new jobs cheap. Sealed types plus `switch` or `when` give Visitor's side with no `accept` and no visitor interface.",
  "Retire visitors for closed sets of kinds you own. Keep Visitor for open hierarchies or library APIs, such as annotation processing and tools that read compiled classes.",
  "Kotlin's `sequence {}` turns a plain loop into a lazy iterator. Java needs a hand-written `Iterator`, with `while`, not `if`, in `hasNext`.",
  "Memento: save a private, immutable snapshot that copies every changeable part, restore by copying back in, and bound the history. An immutable record is its own memento.",
  "Mediator: colleagues talk only to a hub that holds the rules about who reacts to what. Keep it to routing.",
  "The limit: a built sequence is cold and may stop early, so its work reruns on every walk and a `finally` inside may never run; it also can't call suspending functions, which need a `Flow`. And a memento lives in memory, so it dies with the program."
 ],
 "closing": "We started with an inspector in the breakfast box, a stock list in pages, a town dispatcher and a photo of a shelf. The checklists became one function per job over a sealed type, the pages a lazy sequence that fetches only what you read, and the photo a private record that copies the shelf's list.\n\nNow look in your own code for a `save()` or `snapshot()` that keeps a list or a map without copying it. Each one is a window, not a photo.\n\nNext, we'll put the patterns to work on a busy Saturday, with many threads in one shop. Which patterns keep a program correct when everyone arrives at once?",
 "quiz": [
  {"q": "Your team owns a sealed `Goods` hierarchy with four kinds, and keeps adding jobs: price, label, weigh, inspect. Which design makes each new job cheapest?",
   "options": ["A classic Visitor with an `accept` method on each record", "An abstract method per job on the sealed interface", "One function per job with an exhaustive `switch` or `when`", "`instanceof` chains with a final `else` that throws"],
   "answer": 2,
   "why": "Jobs are the side that grows, so you want each job to be a single function: a sealed switch gives that, with the compiler checking that each one covers all four kinds. A Visitor makes the same trade with more machinery. Abstract methods make each new job touch all four records, and an `instanceof` chain loses the compiler's check."},
  {"q": "A Java paging iterator has `if (!current.hasNext() && cursor != null)` in `hasNext`. The pages are `[rye bread, jam]`, then an empty page, then `[tea]`. What does a full walk return?",
   "options": ["`[rye bread, jam]`", "`[rye bread, jam, tea]`", "It throws `NoSuchElementException`", "It loops forever"],
   "answer": 0,
   "why": "After the jam, `hasNext` fetches the empty page once, finds nothing, and returns false, because `if` doesn't try again. The walk ends early and the tea is never seen, with no error. `while` keeps fetching until it finds an item or runs out of pages."},
  {"q": "`val stock = pagedSequence(fetch)` uses the `sequence {}` builder. The code calls `stock.count()` and then `stock.first()`. How many times is page 0 fetched?",
   "options": ["Once: a sequence keeps the pages it fetched", "Twice: each walk runs the block again from the top", "Never: sequences are lazy", "Once, but only if the pages are small"],
   "answer": 1,
   "why": "A sequence from `sequence {}` is cold: every new walk starts the block over. `count()` walks all the pages, and `first()` starts again from page 0. If you need the items twice, collect them once with `toList()`, or accept the second round of fetches."},
  {"q": "`Shelf.save()` returns `new Photo(items, sign)`, where `items` is the shelf's own `ArrayList`. The shopkeeper saves, adds jam, and restores. What does she get?",
   "options": ["The shelf as it was at save time", "An `UnsupportedOperationException`", "A `ConcurrentModificationException`", "Not the old shelf: the photo shares the live list, so the jam is in the \"saved\" state too"],
   "answer": 3,
   "why": "The record holds a reference to the same list the shelf keeps changing, so the jam is in the photo too. Depending on how `restore` copies, you get the present back, or even an empty shelf. Copy every changeable part on save (`List.copyOf`) and on restore."},
  {"q": "From *Observer and Command*: the shelf needs undo both for \"restock 12 loaves\" and for \"rearrange the shelf for the autumn sale\", which has no simple opposite. Which approach handles both?",
   "options": ["A command stack where every command implements `undo()`", "A memento saved before each change, restored on undo", "A StateFlow of the shelf that collectors can rewind", "A chain of undo handlers"],
   "answer": 1,
   "why": "Undo by command needs an opposite for every command, and \"rearrange the shelf\" doesn't have a clean one. A snapshot taken before any change can always be restored, whatever the change did. The two combine well: commands for the log, mementos for the undo. A StateFlow keeps only the latest value, so there is nothing to rewind to.",
   "from": "pat-08"}
 ],
 "flashcards": [
  {"front": "What is the expression problem, in one line each?", "back": "Ordinary methods: new kinds are cheap, new jobs touch every class. Visitor (or sealed + switch): new jobs are cheap, new kinds touch every job."},
  {"front": "When does Visitor still fit in modern Java or Kotlin?", "back": "For hierarchies open to code you don't compile, or when a library hands you one, such as annotation processing or tools that read compiled classes."},
  {"front": "Java pattern for \"a gift with fresh food inside\"? And Kotlin?", "back": "Java 21: `case Gift(Fresh f, var paper)`, a nested record pattern. Kotlin: `is Gift if g.inside is Fresh`, a guard (no nested patterns)."},
  {"front": "Why `while`, not `if`, in a paging iterator's `hasNext`?", "back": "An empty page must not end the walk; `while` keeps fetching until it finds an item or runs out of pages."},
  {"front": "Walking a `sequence {}` twice: what happens to the work inside it?", "back": "It runs again from the top: sequences built that way are cold. Collect them with `toList()` if you need the items twice."},
  {"front": "Why can a `finally` inside `sequence {}` or `iterator {}` fail to run?", "back": "If the consumer stops early, the rest of the block never runs. Open resources where you call the sequence, with `use {}`."},
  {"front": "What makes a memento safe?", "back": "It copies every changeable part on save, restore copies back in, only the originator can read it, and the history is bounded."}
 ],
 "terms": [
  {"term": "Visitor", "plain": "One class per job, with a method per kind of element, called through `accept` on each element."},
  {"term": "Double dispatch", "plain": "Choosing code by two runtime types at once: `accept` picks the kind, `visit` picks the job."},
  {"term": "Expression problem", "plain": "No plain design makes both new kinds and new jobs cheap; you pick the side that grows."},
  {"term": "Iterator", "plain": "An object that hands out a collection's items one at a time without showing how they are stored."},
  {"term": "Cold sequence", "plain": "A sequence whose work runs again, from the start, every time someone walks it."},
  {"term": "Memento", "plain": "An opaque snapshot of an object's state that only that object can read and restore."},
  {"term": "Mediator", "plain": "A hub that holds the rules for how several parts react to each other, so they don't call each other."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to add a Visitor to the sealed `Goods` hierarchy \"so we can add jobs without touching the classes\". Explain what you would do instead, and when you would agree with them.",
  "answer": "We own the hierarchy and it's sealed, so we already get what a visitor gives: we can add a job without touching the records by writing one function with a `switch` (or `when`) over the kinds. The compiler checks that each function covers every kind, and Java's record patterns let us match nested shapes, such as a gift with fresh food inside, that a visitor can't express easily. A visitor would add an interface with a method per kind and an `accept` on every record, and nothing else. The cost is the same either way when a new kind arrives: every job must handle it, but with sealed types the compiler lists each one. I'd agree to a visitor if the hierarchy were open to other modules we can't recompile, or if we were plugging into a library that already speaks visitors, such as an annotation processor."
 },
 "deeper": {
  "minutes": 10,
  "body": """Kotlin's `sequence {}` is built on the same machinery as coroutines, but with limits. Its block runs on a `SequenceScope`, which allows only `yield` and `yieldAll` to pause, so you can't call `delay` or another suspending function inside it. For pages that arrive over the network, where each fetch should wait without holding a thread, use `flow {}` and `emit` instead: a `Flow` is the suspending cousin of a sequence, cold in the same way, as in *Flow basics: cold streams and operators* in the coroutines track.

Java's `Iterator` has an optional `remove()`, and its Javadoc says iterators \"allow the caller to remove elements from the underlying collection during the iteration with well-defined semantics\". That's why `iterator.remove()` is safe inside a loop where `list.remove(x)` throws `ConcurrentModificationException`. For paging iterators, leave `remove()` unsupported, which is the default.

Visitor and Composite often travel together: a visitor walks a composite tree. With sealed types, the walk is plain recursion in each function, as in *Composite, Bridge and Flyweight*. If a tree gets deep enough to overflow the stack, an explicit stack in an iterator (or a `sequence {}` that pushes children) turns the recursion into a loop.

Memento meets long histories in snapshots. When an object's state is rebuilt by replaying every change since the start, as in the deeper notes of *State and Chain of Responsibility*, replaying ten thousand changes on every load is slow. So the program saves a snapshot every few hundred changes, and loading means restoring the newest snapshot and replaying what came after it. The snapshot's format then becomes a promise between versions of your program, so give it a version number from the start."""
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
