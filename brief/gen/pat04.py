import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l04"
K = "kotlin/workbench/patterns/l04"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l04.{cls}"


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def pair_kj(kotlin, java):
    """A Kotlin fence first, then its Java twin (the site still shows Java first)."""
    return f"```kotlin\n{kotlin}\n```\n\n```java\n{java}\n```"


def code(lang, name, cls, alt_lang, alt_name, alt_cls):
    d1 = J if lang == "java" else K
    d2 = J if alt_lang == "java" else K
    return {"lang": lang, "title": name, "src": read(f"{lab}/demo/{d1}/{name}"), "run": demo(cls), "file": f"{lab}/demo/{d1}/{name}",
            "alt": {"lang": alt_lang, "title": alt_name, "src": read(f"{lab}/demo/{d2}/{alt_name}"), "run": demo(alt_cls), "file": f"{lab}/demo/{d2}/{alt_name}"}}


FIG = """<svg viewBox="0 0 700 270" role="img" aria-label="Callers make one call to OrderDesk, which uses three ports; each port has an adapter on the edge that talks to the old warehouse program, a database or a mail server">
<rect class="box-dim" x="132" y="14" width="318" height="246" rx="8"/>
<text class="t-s t-m" x="291" y="32" text-anchor="middle">the shop's own code: no foreign words</text>
<rect class="box" x="10" y="110" width="104" height="50" rx="8"/>
<text class="t" x="62" y="132" text-anchor="middle">callers</text>
<text class="t-s t-m" x="62" y="150" text-anchor="middle">web, phone</text>
<rect class="box-a" x="145" y="110" width="135" height="50" rx="8"/>
<text class="t t-code" x="212" y="140" text-anchor="middle">OrderDesk</text>
<rect class="box" x="305" y="50" width="132" height="40" rx="8"/>
<text class="t-s t-code" x="371" y="75" text-anchor="middle">Warehouse</text>
<rect class="box" x="305" y="115" width="132" height="40" rx="8"/>
<text class="t-s t-code" x="371" y="140" text-anchor="middle">OrderBook</text>
<rect class="box" x="305" y="180" width="132" height="40" rx="8"/>
<text class="t-s t-code" x="371" y="205" text-anchor="middle">Notifier</text>
<rect class="box-b" x="465" y="50" width="125" height="40" rx="8"/>
<text class="t-s" x="527" y="75" text-anchor="middle">WarehouseAdapter</text>
<rect class="box-b" x="465" y="115" width="125" height="40" rx="8"/>
<text class="t-s" x="527" y="140" text-anchor="middle">DbOrderBook</text>
<rect class="box-b" x="465" y="180" width="125" height="40" rx="8"/>
<text class="t-s" x="527" y="205" text-anchor="middle">MailNotifier</text>
<rect class="box-dim" x="605" y="50" width="88" height="40" rx="8"/>
<text class="t-s t-m" x="649" y="75" text-anchor="middle">old program</text>
<rect class="box-dim" x="605" y="115" width="88" height="40" rx="8"/>
<text class="t-s t-m" x="649" y="140" text-anchor="middle">database</text>
<rect class="box-dim" x="605" y="180" width="88" height="40" rx="8"/>
<text class="t-s t-m" x="649" y="205" text-anchor="middle">mail server</text>
<line class="ln-a" x1="114" y1="135" x2="141" y2="135" marker-end="url(#arr)"/>
<line class="ln" x1="280" y1="125" x2="302" y2="75" marker-end="url(#arr)"/>
<line class="ln" x1="280" y1="135" x2="302" y2="135" marker-end="url(#arr)"/>
<line class="ln" x1="280" y1="145" x2="302" y2="198" marker-end="url(#arr)"/>
<line class="ln-d" x1="437" y1="70" x2="462" y2="70" marker-end="url(#arr)"/>
<line class="ln-d" x1="437" y1="135" x2="462" y2="135" marker-end="url(#arr)"/>
<line class="ln-d" x1="437" y1="200" x2="462" y2="200" marker-end="url(#arr)"/>
<line class="ln" x1="590" y1="70" x2="602" y2="70" marker-end="url(#arr)"/>
<line class="ln" x1="590" y1="135" x2="602" y2="135" marker-end="url(#arr)"/>
<line class="ln" x1="590" y1="200" x2="602" y2="200" marker-end="url(#arr)"/>
<text class="t-s t-b" x="527" y="248" text-anchor="middle">adapters: translate</text>
</svg>""".replace("\n", "")

OPENING = """You arrive at a hotel in another country with a phone charger from home. The socket in the wall has the wrong shape, so you push a travel plug adapter into it. The socket stays the same, the charger stays the same, and the little block in between makes them fit. Downstairs, the reception desk does a different job. You ask for breakfast at seven and fresh towels, and the desk talks to the kitchen and to housekeeping for you.

The corner shop has both problems. Its warehouse runs an old program, bought years ago, that speaks in item numbers and two-digit codes. And placing one order takes several steps across several parts of the program. The easy trap is to let the old program's codes leak into every class, and to let every caller repeat the steps in its own slightly different order.

In the last lesson, we built our own objects. In this lesson, we'll fit someone else's: an adapter that keeps an old program's words to itself, Kotlin's extension functions as light adapters, and a facade, one front desk for a job with several steps. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_PORT = """interface Courier {
    String book(String address, int grams);
}"""
K_PORT = """fun interface Courier {
    fun book(address: String, grams: Int): String
}"""
J_ADAPT = """record OldCourierAdapter(OldCourierClient old) implements Courier {
    public String book(String address, int grams) {
        String xml = "<parcel grams='" + grams + "' to='" + address + "'/>";
        try {
            String answer = old.submit(xml);
            return answer.substring(answer.indexOf("ref='") + 5, answer.lastIndexOf("'"));   // their format ends here
        } catch (IOException e) {
            throw new CourierUnavailable("courier unreachable", e);                          // our exception, not theirs
        }
    }
}"""
K_ADAPT = """class OldCourierAdapter(private val old: OldCourierClient) : Courier {
    override fun book(address: String, grams: Int): String {
        val xml = "<parcel grams='$grams' to='$address'/>"
        try {
            val answer = old.submit(xml)
            return answer.substringAfter("ref='").substringBefore("'")         // their format ends here
        } catch (e: IOException) {
            throw CourierUnavailable("courier unreachable", e)                 // our exception, not theirs
        }
    }
}"""

S0 = """An **adapter** makes a class you can't change fit the interface your code expects. That's the travel plug: the hotel's socket is the class you can't change, your charger is your own code, and the adapter sits between them.

The first thing the shop has to fit is a courier company's old client library. It speaks XML, a text format of tags in angle brackets, and it throws `IOException` when the courier's office is closed. `IOException` is a **checked exception**, one the Java compiler makes you catch or declare. The shop's code should see none of that. It should see its own **port**: an interface, in the shop's own words, that the rest of the code depends on.

""" + pair(J_PORT, K_PORT) + """

The adapter implements the port and holds the old client. All the translation happens inside it, in both directions: the shop's words into the client's on the way in, and the client's answers and errors into the shop's on the way out.

""" + pair(J_ADAPT, K_ADAPT) + """

First we write the request in their format, then we call them, then we cut our booking reference out of their answer. The tricky line is the `catch`. Their `IOException` stops there, and the caller gets the shop's own `CourierUnavailable` instead. `XmlAdapterDemo`, in the Try it, books one parcel and then tries an address the courier can't reach:

```text
booked, ref R-2500
caller sees CourierUnavailable: courier unreachable
lambda adapter: QUICK-990
```

The most common adapter bug is a leaky one. If `IOException`, the old client's codes or its classes show up in the shop's other classes, every caller now depends on that courier. Switching couriers then means changing all of them. That's where the travel plug picture breaks. A plug either fits or it doesn't, but a software adapter must also translate failures. A leaky one passes the foreign voltage straight through.

Java's checked exceptions help here, almost by accident. The port doesn't declare `IOException`, so the Java compiler won't let the client's exception escape the adapter. Kotlin has no checked exceptions, so the same leak compiles without a word. In Kotlin, the discipline is yours.

**Translate at the edge, in both directions. Let nothing foreign through.**

When the port has one method, as `Courier` does, you don't even need a class. A lambda or a method reference is the adapter, in both languages, and that's the third line of the output. For plain data, Kotlin has a lighter adapter still."""

# ---------------------------------------------------------------- section 1
K_EXT = """fun SupplierItem.toProduct(): Product {
    val perUnit = when (unit) {
        "KG" -> 1_000.0
        "LB" -> 453.59237                       // the supplier abroad still weighs in pounds
        else -> error("unknown unit $unit")
    }
    return Product(
        code = code,
        grams = (qty.toDouble() * perUnit).roundToLong(),
        inStock = avail == "Y",
    )
}

val products = fromSupplier.map { it.toProduct() }"""
J_EXT = """// Java has no extension functions: the same adapter is a static method
static Product toProduct(SupplierItem item) {
    double perUnit = switch (item.unit()) {
        case "KG" -> 1_000.0;
        case "LB" -> 453.59237;                 // the supplier abroad still weighs in pounds
        default -> throw new IllegalStateException("unknown unit " + item.unit());
    };
    return new Product(item.code(),
            Math.round(Double.parseDouble(item.qty()) * perUnit),
            item.avail().equals("Y"));
}

List<Product> products = fromSupplier.stream().map(Adapters::toProduct).toList();"""

S1 = """The shop buys tea and spices from a supplier abroad. The supplier's price list arrives as rows with the supplier's own names: `qty`, `unit` and `avail`. One of its units is the pound (`LB`), while the shop weighs everything in grams. We want our own `Product`. Write the mapping once, as an extension on the supplier's type:

""" + pair_kj(K_EXT, J_EXT) + """

An **extension function** lets you call a function as if it were a method of a type you don't own. It isn't part of the class. It compiles to a static method that takes the receiver, the object before the dot, as its first parameter, which is exactly the Java twin. What changes is how the call reads, `item.toProduct()`, and where the editor offers it: type `item.` and it appears next to the supplier's own properties. The demo printed:

```text
Product(code=T-1001, grams=2500, inStock=true)
Product(code=T-1002, grams=680, inStock=true)
Product(code=T-1003, grams=10000, inStock=false)
```

The 1.5 pounds came in as 680 grams, and the rest of the shop never has to know that pounds exist. That's the plug adapter at its simplest: the same thing in a different shape, translated once, at the edge.

Two rules keep these adapters honest. Keep them next to the code that talks to the supplier, not in a shared `utils` file, because they're part of the translation layer. And use them for data, not for behavior. An extension can't hold state, can't implement your port, and can't be swapped for a fake in a test. When you need something your code depends on, write a port and a class.

**Extensions translate data. Ports and classes carry behavior.**

The other light adapter in Kotlin is the `fun interface`, an interface with one method that a lambda can implement. `Courier { _, grams -> "QUICK-$grams" }` built the third line of the first section's output, the same way a Java lambda implements an interface with one method.

So far each adapter wraps one thing. Placing an order touches several."""

# ---------------------------------------------------------------- section 2
J_DESK = """record FrontDesk(Stock stock, Vans vans, Notifier notifier) {
    String order(String product, String address, String email) {
        if (!stock.reserve(product)) throw new IllegalStateException("out of stock: " + product);   // 1. reserve
        String booking;
        try {
            booking = vans.book(product, address);                                               // 2. book a van
        } catch (RuntimeException e) {
            stock.release(product);                                                              // 3. undo the reservation
            throw e;
        }
        notifier.send(email, "on its way, booking " + booking);                                  // 4. tell the customer
        return booking;
    }
}"""
K_DESK = """class FrontDesk(
    private val stock: Stock,
    private val vans: Vans,
    private val notifier: Notifier,
) {
    fun order(product: String, address: String, email: String): String {
        check(stock.reserve(product)) { "out of stock: $product" }               // 1. reserve
        val booking = try {
            vans.book(product, address)                                         // 2. book a van
        } catch (e: RuntimeException) {
            stock.release(product)                                              // 3. undo the reservation
            throw e
        }
        notifier.send(email, "on its way, booking $booking")                    // 4. tell the customer
        return booking
    }
}"""

S2 = """Back at the hotel, you asked the reception desk for breakfast at seven, and the desk did the rest. A **facade** is that desk in code: one simple entry point to a job that takes several parts of the program.

Placing an order at the corner shop takes three steps: reserve the stock, book a van, and tell the customer. If every caller (the website, the phone line, the shop counter) makes those calls itself, each one gets the order of the steps and the failure handling slightly different. Put the sequence in one class:

""" + pair(J_DESK, K_DESK) + """

The desk owns two decisions: the order of the steps, and what a failure at each step means. Booking a van before reserving would send a van for flour the shop doesn't have. A van that can't go somewhere must give the stock back. `FrontDeskDemo`, in the Try it, places one order to Mill Lane and one to Gull Island, where no van goes:

```text
booking: V-flour
failed: no van goes to Gull Island; still reserved: [flour]
```

The sugar for Gull Island went back on the shelf. Those rules now live in one tested place, and each caller is one line.

Nothing in either language replaces Facade. Records and constructor parameters only make it shorter. The risk is growth. A facade should orchestrate, that is, call the parts in the right order, and nothing else: no unit math and no warehouse codes. A front desk that also cooks, cleans and does the laundry is no longer a desk. It's the whole hotel with one door.

That's also where the picture breaks. A clerk can improvise when something new comes up, and a facade only knows the steps it was written with. When one grows to forty methods, split it by job, such as an `OrderDesk` and a `ReturnsDesk`.

**A facade owns the order of the steps and the undo. Nothing else.**

One Java gotcha showed up while writing this example. A record component can't be called `notify`. The Java compiler says "illegal record component name", because the accessor method `notify()` would clash with `Object.notify()`. The same goes for `wait`, `hashCode`, `toString`, `getClass` and the other `Object` methods that take no arguments. A Kotlin property named `notify` compiles to `getNotify()` and is fine.

We have adapters on the edge and a desk at the front. Let's put them on one picture."""

# ---------------------------------------------------------------- section 3
S3 = """Adapter and Facade both wrap something, and so do Decorator, Proxy and Bridge, which you'll meet in the next two lessons. Their structure looks much the same, so intent tells them apart:

| Pattern | Wraps | Offers | Why |
|---|---|---|---|
| Adapter | one object you can't change | a different interface: yours | make it fit your port |
| Facade | several objects | a new, simpler interface | hide a sequence of calls |
| Decorator | one object | the same interface | add behavior (*Decorator and Proxy*, lesson 5 of this track) |
| Proxy | one object | the same interface | control access (lesson 5 of this track) |
| Bridge | an implementation you pick | your abstraction | vary two things separately (lesson 6 of this track) |

In a program built with **ports and adapters**, a layout often called hexagonal architecture, you see Adapter and Facade on one picture. The shop's own logic sits in the middle and talks only to ports: `Warehouse`, `OrderBook`, `Notifier`. Adapters sit on the edge, one for each outside system: the old warehouse program, a database, a mail server. The facade is the front door, where the website or the phone line makes one call. The figure shows the lab laid out this way.

That layout pays off twice. Switching warehouses means writing one new adapter, and nothing in the middle changes. And the middle can be tested with lambdas: `new OrderDesk((product, grams) -> new Reserved("H1"), orderBook, notifier)` needs no warehouse, no database and no mail server.

Domain-driven design, a well-known way of organizing business software, calls a thick layer of adapters an **anti-corruption layer**: the place where an outside system's model is translated into yours, so it never spreads. The shop's old warehouse program needs one. It answers every request with a two-digit code and a pipe (`|`), like a clerk who stopped speaking in full sentences years ago. `00|H4711` means "held, and here's the hold id", and `51|` means "out of stock". If you find `"51"` anywhere outside the adapter, the layer has a hole.

The lab is that layer in miniature. `WarehouseAdapter` keeps the old program's item numbers, kilograms and codes to itself, and `OrderDesk` lets the website place an order without knowing the steps.

**Keep foreign words at the edge. The middle speaks only your own.**

Check yourself. The shop replaces its warehouse, and the new program throws `TimeoutException` where the old one threw `WarehouseException`. In a program laid out this way, which files change? (Only the new warehouse adapter, which catches the new exception and returns the same `Unavailable`. The desk, the shop's logic and their tests don't change, because they never saw `WarehouseException` either.)"""

L = {
 "id": "pat-04",
 "title": "Adapter and Facade",
 "minutes": 36,
 "goal": "By the end you can wrap an outside program in an adapter that keeps its types, codes and exceptions to itself, use Kotlin extension functions as light adapters for data, and put a multi-step order behind a facade that owns the order of the steps and the failure rules.",
 "opening": OPENING,
 "warmup": {
  "q": "A Kotlin adapter implements `fun interface Courier { fun book(address: String): String }` and calls an old client method that throws `IOException`, with no try/catch. What happens when the old client throws?",
  "options": ["It doesn't compile: the `IOException` must be caught or declared", "The `IOException` travels straight through the port to whoever called `book`", "Kotlin wraps it in an `UndeclaredThrowableException`", "The exception is swallowed and `book` returns an empty string"],
  "answer": 1,
  "why": "Kotlin has no checked exceptions, so the code compiles, and the client's `IOException` reaches the shop's code through a port that never mentioned it. In Java the same adapter wouldn't compile, because the port's method doesn't declare `IOException`. So in Kotlin, translating foreign errors at the edge is a habit you have to keep yourself. The first section's Try it shows both languages side by side."
 },
 "sections": [
  {
   "h": "Adapter: make their interface fit your port",
   "body": S0,
   "try": {
    "title": "Let the old client's exception leak",
    "minutes": 4,
    "steps": [
     "Run `XmlAdapterDemo` in either language with the command below. Read the three lines.",
     "In the Java version, delete the `try`/`catch` in `OldCourierAdapter.book`, keeping the two lines inside the `try`. Predict, then run.",
     "Do the same in the Kotlin version. Predict, then run. Restore both files."
    ],
    "code": code("java", "XmlAdapterDemo.java", "XmlAdapterDemo", "kotlin", "XmlAdapterDemo.kt", "XmlAdapterDemoKt"),
    "expect": "Both versions print `booked, ref R-2500`, `caller sees CourierUnavailable: courier unreachable` and `lambda adapter: QUICK-990`. Without the catch, Java refuses to compile: `unreported exception IOException; must be caught or declared to be thrown`. Kotlin compiles and prints `caller sees IOException: courier office closed: 503`: the old client's exception walked straight through your port."
   },
   "refs": [
    {"title": "Functional (SAM) interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/fun-interfaces.html", "kind": "docs"}
   ]
  },
  {
   "h": "Extension functions are Kotlin's light adapters",
   "body": S1,
   "try": {
    "title": "Turn a supplier's rows into products",
    "minutes": 3,
    "steps": [
     "Read `ExtensionAdapters.kt` (or its Java twin). Predict the three products, and look hard at the one in pounds.",
     "Run it with the command below.",
     "Add `SupplierItem(\"T-1004\", \"0.5\", \"LB\", \"N\")` to the list (`new SupplierItem(...)` in Java) and predict its `grams` and `inStock` before you run."
    ],
    "code": code("kotlin", "ExtensionAdapters.kt", "ExtensionAdaptersKt", "java", "ExtensionAdaptersJava.java", "ExtensionAdaptersJava"),
    "expect": "2,500 g in stock, 680 g in stock (1.5 pounds is 680.4 grams, rounded), and 10,000 g not in stock. The new row is `grams=227, inStock=false`: half a pound is 226.8 grams. The Kotlin call site reads `it.toProduct()`, and the Java one reads `toProduct(item)`. Underneath, both are the same static method."
   },
   "refs": [
    {"title": "Extensions (Kotlin docs)", "url": "https://kotlinlang.org/docs/extensions.html", "kind": "docs"}
   ]
  },
  {
   "h": "Facade: one front desk for a job with several steps",
   "body": S2,
   "try": {
    "title": "Break the desk's undo rule",
    "minutes": 5,
    "steps": [
     "Run `FrontDeskDemo` in either language, and read the `still reserved` line.",
     "Remove the `try`/`catch` around the van booking, so a failed booking no longer gives the stock back. Predict the `still reserved` line, then run.",
     "Restore it. In the Java version only, rename the record component `notifier` to `notify` (and its use inside `order`). Compile."
    ],
    "code": code("java", "FrontDeskDemo.java", "FrontDeskDemo", "kotlin", "FrontDeskDemo.kt", "FrontDeskDemoKt"),
    "expect": "The first run mails a confirmation for the flour, then prints `failed: no van goes to Gull Island; still reserved: [flour]`: the failed order gave the sugar back. Without the catch, the line ends `[flour, sugar]`, so a failed booking holds stock until someone notices. The rename gives `error: illegal record component name notify`. The Kotlin class can have a property called `notify`."
   },
   "refs": [
    {"title": "JLS chapter 8.10: Record classes", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-8.html#jls-8.10", "kind": "docs"}
   ]
  },
  {
   "h": "Ports and adapters: where the translation lives",
   "body": S3,
   "figure": {"svg": FIG, "caption": "Callers make one call to the desk. The shop's own code talks only to ports, and adapters on the edge translate for each outside system."}
  }
 ],
 "compare": {
  "title": "An anti-corruption adapter for the courier's status messages",
  "java": {"title": "CourierUpdateAdapter.java", "src": """// the courier's status message, with the courier's names
record CourierUpdate(String type, String ref, String info) {}

// our model of what happened
sealed interface DeliveryEvent {
    record Delivered(String bookingRef) implements DeliveryEvent {}
    record Missed(String bookingRef, String reason) implements DeliveryEvent {}
    record Ignored(String why) implements DeliveryEvent {}
}

final class CourierUpdateAdapter {
    private CourierUpdateAdapter() {}

    static DeliveryEvent toEvent(CourierUpdate u) {
        return switch (u.type()) {          // their strings are an open set, so a default is right here
            case "parcel.delivered" -> new DeliveryEvent.Delivered(u.ref());
            case "parcel.missed" -> new DeliveryEvent.Missed(u.ref(), u.info().toLowerCase());
            default -> new DeliveryEvent.Ignored("unhandled courier update " + u.type());
        };
    }
}"""},
  "kotlin": {"title": "CourierUpdateAdapter.kt", "src": """// the courier's status message, with the courier's names
data class CourierUpdate(val type: String, val ref: String, val info: String)

// our model of what happened
sealed interface DeliveryEvent {
    data class Delivered(val bookingRef: String) : DeliveryEvent
    data class Missed(val bookingRef: String, val reason: String) : DeliveryEvent
    data class Ignored(val why: String) : DeliveryEvent
}

// the adapter as an extension: reads like a method on the courier's type
fun CourierUpdate.toEvent(): DeliveryEvent = when (type) {   // an open set of their strings: else is right
    "parcel.delivered" -> DeliveryEvent.Delivered(ref)
    "parcel.missed" -> DeliveryEvent.Missed(ref, info.lowercase())
    else -> DeliveryEvent.Ignored("unhandled courier update $type")
}"""},
  "note": "The courier's system sends a short status message whenever a parcel's state changes, in the courier's words. The translation is the same in both languages: their strings in, a sealed event of our own out. Kotlin writes it as an extension on their type, so call sites read `update.toEvent()`. Java needs a static method on a holder class, so call sites read `CourierUpdateAdapter.toEvent(update)`, and in bytecode the two are the same static method. Both use a catch-all branch on purpose. The courier's message types are an open set you don't control, unlike your own sealed types, where a missing case should break the build. Code that uses `DeliveryEvent` then switches over it with no default. Neither language makes Adapter unnecessary; Kotlin just makes the data-mapping kind cheaper to write."
 },
 "worked": {
  "title": "Wrap a map service behind a port, then test without it",
  "steps": [
   {"say": "The shop prices a delivery by distance: 2.00 plus 0.50 for every kilometer. Its pricer calls an outside map service directly. The service answers with text like `\"dist=4.2km;eta=11min\"` and throws a checked `RouteException`. Before reading on, list every detail of the map service that leaks into `priceCents`.",
    "code": """class DeliveryPricer {
    private final RouteClient routes = new RouteClient("https://maps.vendor.example");

    long priceCents(String address) throws RouteException {
        String raw = routes.distance("SHOP", address);                     // their format: "dist=4.2km;eta=11min"
        double km = Double.parseDouble(raw.substring(raw.indexOf('=') + 1, raw.indexOf("km")));
        return 200 + Math.round(km * 50);
    }
}""", "lang": "java",
    "alt_code": """class DeliveryPricer {
    private val routes = RouteClient("https://maps.vendor.example")

    fun priceCents(address: String): Long {
        val raw = routes.distance("SHOP", address)                         // their format; RouteException leaks unseen
        val km = raw.substringAfter('=').substringBefore("km").toDouble()
        return 200 + (km * 50).roundToLong()
    }
}""", "alt_lang": "kotlin"},
   {"say": "Four leaks: the `\"SHOP\"` name the service wants, its answer format, its checked exception, and its hard-wired address. Define the port in the shop's words first. It says nothing about text formats or vendors, and an empty answer means \"no distance right now\".",
    "code": """interface Distances {
    OptionalDouble km(String from, String to);      // 1. our words: places in, kilometers or nothing out
}

class DeliveryPricer {
    private final Distances distances;
    DeliveryPricer(Distances distances) { this.distances = distances; }

    OptionalLong priceCents(String address) {
        OptionalDouble km = distances.km("SHOP", address);
        return km.isPresent() ? OptionalLong.of(200 + Math.round(km.getAsDouble() * 50)) : OptionalLong.empty();
    }
}""", "lang": "java",
    "alt_code": """fun interface Distances {
    fun km(from: String, to: String): Double?          // 1. our words: places in, kilometers or null out
}

class DeliveryPricer(private val distances: Distances) {
    fun priceCents(address: String): Long? =
        distances.km("SHOP", address)?.let { 200 + (it * 50).roundToLong() }
}""", "alt_lang": "kotlin"},
   {"say": "Now the adapter. Everything the map service knows lives here: how it wants places named, how it packs its answers, and which exception it throws. Why return empty instead of rethrowing on `RouteException`? Because the port promised \"kilometers or nothing\", and the pricer decides what nothing means.",
    "code": """final class MapDistances implements Distances {
    private final RouteClient routes;
    MapDistances(RouteClient routes) { this.routes = routes; }

    public OptionalDouble km(String from, String to) {
        try {
            String raw = routes.distance(from, to);                                     // 2. our places, their format
            return OptionalDouble.of(Double.parseDouble(raw.substring(raw.indexOf('=') + 1, raw.indexOf("km"))));
        } catch (RouteException | RuntimeException e) {                                // 3. their failure, our answer
            return OptionalDouble.empty();
        }
    }
}""", "lang": "java",
    "alt_code": """class MapDistances(private val routes: RouteClient) : Distances {
    override fun km(from: String, to: String): Double? =
        try {
            val raw = routes.distance(from, to)                                           // 2. our places, their format
            raw.substringAfter('=').substringBefore("km").toDouble()
        } catch (e: RouteException) {                                                     // 3. their failure, our answer
            null
        } catch (e: RuntimeException) {
            null
        }
}""", "alt_lang": "kotlin"},
   {"say": "Test the two halves separately. The pricer gets a lambda. The adapter gets a fake map service, a subclass of the client that returns a canned answer, which is how the lab tests its warehouse adapter.",
    "code": """// 4. the shop's logic, with no map service at all
assertThat(new DeliveryPricer((from, to) -> OptionalDouble.of(4.0)).priceCents("12 Mill Lane")).hasValue(400);

// 5. the adapter, against a fake of the client class
RouteClient fake = new RouteClient("unused") {
    @Override public String distance(String from, String to) { return "dist=4.2km;eta=11min"; }
};
assertThat(new MapDistances(fake).km("SHOP", "12 Mill Lane")).hasValue(4.2);""", "lang": "java",
    "alt_code": """// 4. the shop's logic, with no map service at all
assertThat(DeliveryPricer { _, _ -> 4.0 }.priceCents("12 Mill Lane")).isEqualTo(400L)

// 5. the adapter, against a fake of the client class (open in the library, or use an interface)
val fake = object : RouteClient("unused") {
    override fun distance(from: String, to: String) = "dist=4.2km;eta=11min"
}
assertThat(MapDistances(fake).km("SHOP", "12 Mill Lane")).isEqualTo(4.2)""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A warehouse adapter and an order desk",
  "minutes": 13,
  "files": [f"{lab}/main/{J}/WarehouseAdapter.java", f"{lab}/main/{J}/OrderDesk.java"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l04.*'",
  "steps": [
   "Read `OldWarehouseSystem.java` (the old program you can't change), `Warehouse.java` (the shop's port) and `Units.java` (two helpers). They're given; don't edit them. Run the tests: all ten fail.",
   "Write `WarehouseAdapter.reserve`. Call `old.hold` with `Units.itemNumber` and `Units.toKilos`, catch `WarehouseException` and return `Unavailable(e.getMessage())`, then split the answer on `|` and map the code with a `switch`.",
   "Write `OrderDesk.place` as a `switch` over the `StockResult`. Reserved: write it in the order book, send the confirmation (catching a failing notifier), and return `Placed`. Refused: send the sorry note and return `Refused`. Unavailable: return `RetryLater`.",
   "Run the tests until all ten pass."
  ],
  "hints": [
   "`raw.split(\"\\\\|\", -1)` splits on a real `|` and keeps the empty hold id in `\"51|\"`. The pipe must be escaped, because `split` takes a regular expression.",
   "A `switch` over the sealed `StockResult` with `case StockResult.Reserved ok -> ...` needs no `default`: the compiler checks all three cases. In a switch expression, use `yield` to return a value from a block.",
   "Wrap only the notifier call in try/catch. If the order book throws, let it travel up: a reserved order that isn't written down is a problem someone must see, not one to hide."
  ],
  "done_when": "All ten tests in `AdapterFacadeTest` pass."
 },
 "drill": {
  "title": "An adapter from memory",
  "minutes": 5,
  "prompt": "Close this page. An outside `PostcodeClient` has `String lookup(String postcode) throws LookupException`, returning text like `\"Mill Lane;OLD TOWN\"`. Your port is `interface DistrictOf { Optional<String> district(String postcode); }` (in Kotlin, `fun interface DistrictOf { fun district(postcode: String): String? }`). Write the adapter so the client's exception never escapes, and an empty or malformed answer gives no district.",
  "answer": {"lang": "java", "src": """final class PostcodeDistricts implements DistrictOf {
    private final PostcodeClient client;
    PostcodeDistricts(PostcodeClient client) { this.client = client; }

    @Override
    public Optional<String> district(String postcode) {
        try {
            String raw = client.lookup(postcode);                  // their format: "Mill Lane;OLD TOWN"
            if (raw == null) return Optional.empty();
            String[] parts = raw.split(";", 2);
            if (parts.length < 2 || parts[1].isBlank()) return Optional.empty();
            return Optional.of(parts[1].trim());
        } catch (LookupException e) {
            return Optional.empty();                               // their failure stops here
        }
    }
}""",
   "alt": {"lang": "kotlin", "title": "Kotlin", "src": """class PostcodeDistricts(private val client: PostcodeClient) : DistrictOf {
    override fun district(postcode: String): String? =
        try {
            client.lookup(postcode)                                // their format: "Mill Lane;OLD TOWN"
                ?.split(';', limit = 2)
                ?.getOrNull(1)
                ?.trim()
                ?.takeIf { it.isNotEmpty() }
        } catch (e: LookupException) {
            null                                                   // their failure stops here
        }
}"""}}
 },
 "recap": [
  "An adapter makes a class you can't change fit your port. It translates arguments on the way in, and answers and errors on the way out.",
  "Keep an outside system's types, codes and exceptions inside its adapter. A `\"51\"` or a `WarehouseException` anywhere else is a leak. Java's checked exceptions stop an `IOException` from escaping a port that doesn't declare it; Kotlin compiles the same leak without a word.",
  "For a one-method port, a lambda or a `fun interface` is the adapter. For data, a Kotlin extension such as `SupplierItem.toProduct()` is the light adapter; in Java it's a static method.",
  "A facade gives callers one call for a job with several steps, and owns the order of the steps and what each failure means. Keep it to orchestration only.",
  "In ports and adapters, the shop's logic talks only to ports, adapters on the edge translate, and the facade is the front door.",
  "The limit: neither pattern makes an outside system reliable. An adapter can only translate the failures it knows about, and a facade only knows the steps it was written with."
 ],
 "closing": "We started in a hotel with a travel plug and a reception desk. In the shop, the plug became an adapter that keeps the old warehouse program's codes to itself. The desk became one call that reserves, writes down and tells the customer, in the right order.\n\nNow look in your own code for an outside system's words outside its adapter: a status code compared as a string, or a library's exception caught far from the call that threw it. Each one is foreign voltage leaking past the plug.\n\nNext, we'll wrap an object and keep its interface exactly as it is. What can a wrapper add when it doesn't change the shape at all?",
 "quiz": [
  {"q": "The warehouse adapter catches `WarehouseException` and rethrows it wrapped in a `RuntimeException`. The order desk catches that and checks `getCause() instanceof WarehouseException` to decide whether to retry. What's wrong?",
   "options": ["Nothing, since the exception is unchecked now", "The foreign type still leaks: the desk depends on the old program, so replacing the warehouse breaks it", "A `RuntimeException` can't wrap a checked exception", "Retry decisions belong inside the old warehouse program"],
   "answer": 1,
   "why": "Wrapping changed the exception's type, not who depends on it. The desk still imports `WarehouseException`, so it's tied to this one warehouse program. Translate inside the adapter into your own result (`Unavailable`) or your own exception type that says whether a retry makes sense. A `RuntimeException` can wrap anything, so that option is simply false."},
  {"q": "Which statement about an adapter written in Kotlin is true?",
   "options": ["An `IOException` thrown inside it can pass through your port without any compile error", "The compiler forces you to catch the old client's checked exceptions", "Extension functions can implement your port interface", "`fun interface` ports can't be implemented with a lambda"],
   "answer": 0,
   "why": "Kotlin has no checked exceptions, so nothing stops the client's `IOException` from reaching callers of your port. Java would refuse to compile the same adapter. Extensions can't implement interfaces, and a `fun interface` exists precisely so that a lambda can implement it."},
  {"q": "Three parts of the shop's program (the website, the phone line and the shop counter) each reserve stock, book a van, write the order book and send an email, each with slightly different failure handling. Which pattern fits?",
   "options": ["Adapter", "Decorator", "Facade", "Singleton"],
   "answer": 2,
   "why": "A facade puts the sequence and its failure rules in one place, and each caller makes one call. An adapter changes one object's interface, a decorator adds behavior behind the same interface, and a singleton is about how many instances exist, not about running steps in order."},
  {"q": "Which is the best use of a Kotlin extension function as an adapter?",
   "options": ["`fun OldWarehouseSystem.reserve(...)`, which callers use instead of a `Warehouse` port", "A global `fun Any.toJson()` in a shared utils file", "An extension that caches the supplier's rows in a top-level map", "`fun SupplierItem.toProduct(): Product`, kept next to the code that talks to the supplier"],
   "answer": 3,
   "why": "Turning a supplier's row into your own type is pure data translation, which is what extensions are good at, and keeping it next to the supplier code keeps the supplier's model contained. An extension on the old program makes callers depend on that program and can't be swapped in a test. A global utils extension spreads everywhere, and caching in a top-level map is hidden shared state."},
  {"q": "From *Factory Method and Abstract Factory*: the shop now has one adapter for Pedal Post's old client and one for Big Blue Vans'. Where should the choice between them live?",
   "options": ["In each caller, with an `if` on the parcel's weight", "In one factory, a `switch` or `when` over the courier with no default, passed into the desk", "Inside the desk's `place`, as string checks on the address", "In the adapters: each checks whether the parcel belongs to it"],
   "answer": 1,
   "why": "Choosing which product to make is a factory's job: one exhaustive `switch` or `when` over a sealed or enum `Courier`, so adding a courier is a compile error in one place. Spreading weight checks over callers or the desk copies the rule, and adapters checking ownership turns every call into a guessing game.",
   "from": "pat-02"}
 ],
 "flashcards": [
  {"front": "What does an adapter do?", "back": "Makes an object you can't change fit the interface (port) your code expects, translating arguments, answers and errors."},
  {"front": "What is a leaky adapter?", "back": "One that lets the outside system's types, codes or exceptions (a `WarehouseException`, the code \"51\") reach your own code."},
  {"front": "A Kotlin adapter calls a method that throws `IOException` and has no catch. Does it compile?", "back": "Yes. Kotlin has no checked exceptions, so the `IOException` passes through your port silently. Java would refuse."},
  {"front": "What does a Kotlin extension function compile to?", "back": "A static method whose first parameter is the receiver. `item.toProduct()` is `toProduct(item)` in bytecode."},
  {"front": "What does a facade own?", "back": "The order of the steps in a job with several steps, and what a failure at each step means. Not math, codes or database queries."},
  {"front": "Can a Java record component be named `notify`?", "back": "No: \"illegal record component name\". Its accessor would clash with `Object.notify()`. The same goes for `wait`, `hashCode`, `toString` and the other no-argument `Object` methods."},
  {"front": "Adapter vs Facade, one line each?", "back": "Adapter: one object, given a different interface (yours). Facade: several objects behind one new, simpler interface."}
 ],
 "terms": [
  {"term": "Adapter", "plain": "A wrapper that makes an existing object fit the interface your code expects."},
  {"term": "Port", "plain": "An interface in your own words that your core code depends on, such as `Warehouse`."},
  {"term": "Checked exception", "plain": "An exception the Java compiler makes you catch or declare, such as `IOException`. Kotlin has none."},
  {"term": "Anti-corruption layer", "plain": "The adapters where an outside system's model is translated into yours, so it never spreads into your code."},
  {"term": "Facade", "plain": "One simple entry point that runs a job with several steps across several parts of the program."},
  {"term": "Extension function", "plain": "A Kotlin function called like a method on a type it doesn't belong to; a static method underneath."},
  {"term": "Ports and adapters", "plain": "A layout where core logic talks only to ports, and adapters on the edge connect each port to one outside system. Also called hexagonal architecture."}
 ],
 "explain_back": {
  "prompt": "Explain to a new teammate why `WarehouseAdapter` returns `Unavailable` instead of letting `WarehouseException` through, and why `OrderDesk` ignores a failing confirmation email but not a failing order-book write.",
  "answer": "The adapter is the only class allowed to know the old warehouse program. If `WarehouseException` escaped, every caller would import the old program's type and make decisions on its status codes, and replacing the warehouse would mean changing all of them. So the adapter turns it into our own result, `Unavailable`, and the desk turns that into `RetryLater`. In the desk, the order matters. Once the stock is reserved, the order must be written down, so if the order book fails, that's a problem someone must see, and it travels up. The confirmation email is a courtesy. A broken mail server shouldn't turn a placed order into an error the customer retries, which could reserve the stock twice."
 },
 "deeper": {
  "minutes": 10,
  "body": """The JDK has adapters you use every day. `InputStreamReader` adapts a stream of bytes into a stream of characters; its Javadoc calls it a bridge from byte streams to character streams, which shows how loosely the pattern names get used. `Arrays.asList` adapts an array into a fixed-size `List` that writes through to the array. `Collections.enumeration` and `Enumeration.asIterator()` (Java 9) adapt between the old and new ways of walking through a collection.

The GoF book describes two kinds of adapter. An object adapter holds the foreign object and delegates to it, as in this lesson. A class adapter inherits from the foreign class and implements your interface at the same time. Java and Kotlin allow the second only when the foreign class is open to subclassing, and it's usually worse: your adapter inherits every public method of the foreign class, so callers can go around your translation. Prefer the object adapter.

Kotlin's `by` delegation (in *Decorator and Proxy*, lesson 5 of this track) can build an adapter that forwards most of an interface unchanged and overrides the few methods that need translating. That works when the two interfaces are almost the same, such as two versions of your own API. For an outside system with a different model, write the translation out; it's the part that deserves a careful review.

Facades and slow calls mix badly in one way. Suppose a facade starts a database transaction, a group of database changes that succeed or fail together, and then calls a slow outside system inside it. The transaction holds a database connection for as long as the outside system takes. With a pool of 20 connections and a courier service that takes 120 ms to answer, a busy afternoon runs out of connections. Call the slow system first, outside the transaction, then write to the database in a short one."""
 },
 "sources": [
  {"title": "Extensions (Kotlin docs)", "url": "https://kotlinlang.org/docs/extensions.html"},
  {"title": "Functional (SAM) interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/fun-interfaces.html"},
  {"title": "JLS chapter 8.10: Record classes", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-8.html#jls-8.10"},
  {"title": "InputStreamReader (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/io/InputStreamReader.html"}
 ]
}

out = ROOT / "content/lessons/pat-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
