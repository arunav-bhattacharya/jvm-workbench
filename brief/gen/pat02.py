import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l02"
K = "kotlin/workbench/patterns/l02"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l02.{cls}"


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


FIG = """<svg viewBox="0 0 660 270" role="img" aria-label="Shipping asks the CourierServices factory for one family; the Pedal Post family and the Big Blue Vans family each create their own booker and tracker">
<rect class="box" x="15" y="110" width="120" height="44" rx="8"/>
<text class="t" x="75" y="137" text-anchor="middle">Shipping</text>
<rect class="box-a" x="190" y="110" width="180" height="44" rx="8"/>
<text class="t t-code" x="280" y="137" text-anchor="middle">CourierServices</text>
<text class="t-s t-m" x="280" y="176" text-anchor="middle">forCourier(courier)</text>
<line class="ln-a" x1="135" y1="132" x2="186" y2="132" marker-end="url(#arr)"/>
<text class="t-s t-m" x="160" y="104" text-anchor="middle">once</text>
<rect class="box-b" x="420" y="15" width="225" height="110" rx="8"/>
<text class="t t-b" x="532" y="40" text-anchor="middle">Pedal Post (bike)</text>
<rect class="box" x="432" y="58" width="98" height="44" rx="8"/>
<text class="t-s" x="481" y="85" text-anchor="middle">booker()</text>
<rect class="box" x="537" y="58" width="98" height="44" rx="8"/>
<text class="t-s" x="586" y="85" text-anchor="middle">tracker()</text>
<rect class="box-b" x="420" y="145" width="225" height="110" rx="8"/>
<text class="t t-b" x="532" y="170" text-anchor="middle">Big Blue Vans (van)</text>
<rect class="box" x="432" y="188" width="98" height="44" rx="8"/>
<text class="t-s" x="481" y="215" text-anchor="middle">booker()</text>
<rect class="box" x="537" y="188" width="98" height="44" rx="8"/>
<text class="t-s" x="586" y="215" text-anchor="middle">tracker()</text>
<line class="ln" x1="370" y1="124" x2="416" y2="72" marker-end="url(#arr)"/>
<line class="ln" x1="370" y1="140" x2="416" y2="196" marker-end="url(#arr)"/>
<text class="t-s t-m" x="280" y="230" text-anchor="middle">both products come from</text>
<text class="t-s t-m" x="280" y="248" text-anchor="middle">the same family, so they match</text>
</svg>""".replace("\n", "")

OPENING = """Walk into the town bakery and ask for "a loaf for sandwiches". You don't name a recipe, and you don't pick an oven. The baker hears what you need and decides: today it's the white tin loaf. Next door, the furniture maker takes orders for dining sets. Ask for one in oak, and the table and the chairs come from the same workshop, so they match.

Code makes objects all day, usually with `new`, which names the exact class every time. That's fine until the choice depends on something: the weight of a parcel, a setting, whether we're in a test. Then the `new` calls spread through the program, each one deciding on its own, and one day a parcel booked with one courier gets tracked with the other.

In the last lesson, a private constructor and one `getInstance()` decided how many objects exist. In this lesson, we'll let a factory decide which object you get: static factories with names, factory methods passed around as functions, factories that return a sealed result instead of throwing, and an abstract factory for a set that must match. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Start with the counter at the bakery. You say what you want, and the baker hands over something that fits. You never see the kitchen. A **static factory method** is that counter in code: a static method that returns an instance of its class, or of some class behind an interface. Effective Java, the best-known book of Java advice, opens with it (item 1: consider static factory methods instead of constructors). The JDK, the libraries that come with Java, is full of them: `List.of`, `Duration.ofMinutes`, `Integer.valueOf`, `Thread.ofVirtual`.

A constructor can do one thing: make a new object of exactly its own class. A static factory can do four things a constructor can't.

1. It has a name. `Duration.ofMinutes(2)` and `Duration.ofSeconds(2)` both take a `long`. Two constructors with the same parameter types can't exist, and `new Duration(2)` would say nothing anyway.
2. It can return an object it made earlier. `Integer.valueOf(100)` hands back the same cached object every time.
3. It can return any subtype, chosen from the input. `List.of(1)` and `List.of(1, 2, 3)` return two different private classes. `EnumSet.noneOf` picks a set backed by a single `long` when the enum has 64 constants or fewer, and a bigger one otherwise.
4. The class it returns doesn't have to exist when the factory is written. JDBC, in `java.sql`, is Java's standard way to talk to a database, and each database company ships its own driver. `DriverManager.getConnection(url)` returns a connection from whichever driver on the classpath (the list of places the JVM loads classes from) accepts the URL, and those drivers were written long after `java.sql`.

The warm-up was the third point. `FactoriesInTheJdk`, in the Try it, asks each factory what it handed back. On JDK 21 it printed:

```text
List.of(1)            -> List12
List.of(1, 2, 3)      -> ListN
EnumSet of TimeUnit   -> RegularEnumSet (7 constants)
EnumSet of scripts    -> JumboEnumSet (164 constants)
```

Same method, different classes, and you can't write any of those class names in your own code. The factory is the only door.

The downsides are small. A class with only private constructors can't have subclasses, which pushes you toward composition (building a class out of other objects instead of extending one) and costs little. Factories are also harder to spot than constructors, so stick to the usual names: `of`, `from`, `valueOf`, `parse`, `newX`, `create`.

For the shop's own value types, make this the default. Picture a `Price` with a private constructor and two doors, `Price.ofCents(450)` and `Price.parse("4.50")`. With the constructor private, every `Price` in the program went through your checks. The compare block at the end of this lesson writes it out in both languages.

**A constructor can only say `new`. A factory can say what you mean, and choose.**

A static factory makes its choice inside its own class. The next step moves the choice out, away from the code that uses the object."""

# ---------------------------------------------------------------- section 1
J_GOF = """abstract class OrderNotices {
    protected abstract Messenger createMessenger();          // the factory method
    final String orderLeft(String customer) {
        return createMessenger().send(customer, "your order is on its way");
    }
}
class SmsNotices extends OrderNotices {
    protected Messenger createMessenger() { return new SmsMessenger(); }
}"""
K_GOF = """abstract class OrderNotices {
    protected abstract fun createMessenger(): Messenger        // the factory method
    fun orderLeft(customer: String) = createMessenger().send(customer, "your order is on its way")
}
class SmsNotices : OrderNotices() {
    override fun createMessenger(): Messenger = SmsMessenger()
}"""
J_FN = """record OrderNotices(Supplier<? extends Messenger> messengers) {
    String orderLeft(String customer) {
        return messengers.get().send(customer, "your order is on its way");
    }
}
new OrderNotices(SmsMessenger::new);    // the real program
new OrderNotices(FakeMessenger::new);   // a test"""
K_FN = """class OrderNotices(private val messengers: () -> Messenger) {
    fun orderLeft(customer: String) = messengers().send(customer, "your order is on its way")
}
OrderNotices(::SmsMessenger)    // the real program
OrderNotices(::FakeMessenger)   // a test"""
J_OF = """static Messenger of(Channel c) {
    return switch (c) {            // no default branch, on purpose
        case SMS -> new SmsMessenger();
        case EMAIL -> new EmailMessenger();
        case FAKE -> new FakeMessenger();
    };
}"""
K_OF = """fun messengerOf(c: Channel): Messenger = when (c) {   // no else branch, on purpose
    Channel.SMS -> SmsMessenger()
    Channel.EMAIL -> EmailMessenger()
    Channel.FAKE -> FakeMessenger()
}"""

S1 = """Here's the problem in the shop. When an order leaves, the shop tells the customer, by text message (SMS) or by email. Tests use a fake messenger that sends nothing. The code that writes the notice shouldn't decide which messenger it gets, or every test run would text real customers.

The **Factory Method** from the Gang of Four (GoF) book on design patterns is the classic answer. A class needs to create something, but it doesn't pick the concrete class. In the book's version, an abstract class declares a creation hook, the factory method, and subclasses override it:

""" + pair(J_GOF, K_GOF) + """

That works, and it's still a fair design when the subclass has other reasons to exist. But here it costs one subclass per product, just to pick a constructor. Since Java 8, a function does the same job. A `Supplier<Messenger>` (in Kotlin, a `() -> Messenger`) is a factory: call it, and you get a messenger. A constructor reference such as `FakeMessenger::new`, read as "call this constructor", is the shortest way to write one:

""" + pair(J_FN, K_FN) + """

That's the bakery counter in code: `OrderNotices` asks for "a messenger" and never names a class. The real program and the test each hand in their own way to make one.

When the choice depends on data, such as a setting or the customer's preference, put it in one static factory over a sealed family. A sealed interface lists every class that may implement it, so the compiler knows them all:

""" + pair(J_OF, K_OF) + """

Leave out `default` (`else` in Kotlin). Say the shop, in a burst of nostalgia, adds `PIGEON` to the enum. The switch stops compiling, and the compiler points at the one place that needs a new messenger:

```text
MessengerFactory.java:14: error: the switch expression does not cover all possible input values
```

The compiler is a strict foreman here: it won't build the program until every case has a product. Now add a catch-all branch that returns `FakeMessenger`, and the build stays green while every pigeon notice goes to the fake. Nothing warns you. That's where the bakery picture breaks. A baker improvises when you ask for something new, and a factory with a default branch improvises too, badly.

**A factory's switch gets no default. Let the compiler find the new case.**

People mix up the two names, so let's keep them apart. A static factory is about how one class hands out its own instances. Factory Method is about who decides the concrete class: not the code that uses the object.

Kotlin has no `static` keyword at all, though. So where do its factories live?"""

ASIDE1 = {
    "title": "Does my framework write factory methods for me?",
    "body": "If you write web services, it probably calls them. In Spring, a method marked `@Bean` builds an object; in Quarkus, a method marked `@Produces` does the same. The framework calls that method and passes the result to every class that asks for the interface, so the rest of the code never names the concrete class. The framework calls it when it creates the object, not once per request. A choice that depends on the current request, such as the weight of this parcel, still needs a factory you call yourself."
}

# ---------------------------------------------------------------- section 2
K_PARCEL = """class Parcel private constructor(val courier: Courier, val grams: Int) {
    companion object {
        fun parse(raw: String): ParcelResult { /* check, then Parcel(courier, grams) */ }
    }
}"""
J_PARCEL = """public final class Parcel {
    private final Courier courier;
    private final int grams;
    private Parcel(Courier courier, int grams) { this.courier = courier; this.grams = grams; }

    public static ParcelResult parse(String raw) { /* check, then new Parcel(courier, grams) */ }
}"""
K_RESULT = """sealed interface ParcelResult {
    data class Valid(val parcel: Parcel) : ParcelResult
    data class Invalid(val reason: String) : ParcelResult
}

when (val r = Parcel.parse(input)) {      // no else
    is ParcelResult.Valid -> book(r.parcel)
    is ParcelResult.Invalid -> askAgain(r.reason)
}"""
J_RESULT = """public sealed interface ParcelResult {
    record Valid(Parcel parcel) implements ParcelResult {}
    record Invalid(String reason) implements ParcelResult {}
}

switch (Parcel.parse(input)) {             // no default
    case ParcelResult.Valid v -> book(v.parcel());
    case ParcelResult.Invalid i -> askAgain(i.reason());
}"""

S2 = """Kotlin's factories live in three other places.

The **companion object** is the direct translation of a Java static factory: make the constructor private, and put the factory next to it. Here's the lab's `Parcel`. The shop sends light parcels with a bike courier and heavy ones by van, so a parcel knows its weight and which courier can carry it:

""" + pair_kj(K_PARCEL, J_PARCEL) + """

`Parcel.parse("2.5 kg")` both checks the text and picks the courier. That's the bakery again: you say the weight, and the factory decides who carries it.

An `operator fun invoke` on the companion lets callers write what looks like a constructor call, `Fee(250)`. Behind it runs a factory that can check the value or return a cached one. `invoke` is the function Kotlin calls when you put parentheses after an object. Use it sparingly, because readers expect `Fee(250)` to make a new object.

The third shape is a top-level function named like the type. Kotlin's coding conventions allow a factory function to share the name of the abstract type it returns, and the kotlinx.coroutines library does exactly that: `Job()` and `MutableStateFlow(0)` are functions that return a private class.

What a factory returns matters as much as where it lives. A parser that throws makes every caller remember a `try`. A factory that returns a **sealed result**, a sealed set of possible answers, makes the compiler remember for them:

""" + pair_kj(K_RESULT, J_RESULT) + """

`CompanionFactories`, in the Try it, uses all three shapes on a delivery slot, a day and an hour. Its parser returns one of three results, and it printed:

```text
parse("sat 10") -> ok: SAT 10:00
parse("FRI 23") -> we deliver from 8 to 19, not at 23
parse("MOON 9") -> no such day 'MOON'
```

Add a fourth result later, say `Closed` for a day the shop doesn't deliver, and every `when` without an `else` stops compiling until it handles it. Java 21 gives the same check with a sealed interface, records (classes that only carry data) and a `switch` whose cases match on the type, as the Java twin shows.

**Throw for bugs and broken machinery. Return a sealed result for answers the caller must handle.**

A mistyped weight is an answer, not a bug, so `Parcel.parse` returns one. We now have a factory that picks a courier for each parcel. But a courier is more than a booking: the shop also has to ask where the parcel is."""

# ---------------------------------------------------------------- section 3
K_AF = """interface CourierServices {
    val courier: Courier
    fun booker(): Booker
    fun tracker(): Tracker

    companion object {
        fun forCourier(courier: Courier): CourierServices = when (courier) {
            Courier.BIKE -> PretendServices(Courier.BIKE, "Pedal Post", "PP")
            Courier.VAN -> PretendServices(Courier.VAN, "Big Blue Vans", "BB")
        }
    }
}"""
J_AF = """public interface CourierServices {
    Courier courier();
    Booker booker();
    Tracker tracker();

    static CourierServices forCourier(Courier courier) {
        return switch (courier) {
            case BIKE -> new PretendServices(Courier.BIKE, "Pedal Post", "PP");
            case VAN -> new PretendServices(Courier.VAN, "Big Blue Vans", "BB");
        };
    }
}"""

S3 = """Back to the furniture maker. You order a dining set in oak, and one workshop makes the table and the chairs, so they match. Nobody pairs an oak table with pine chairs from the shop down the road.

The shop's couriers need the same care. Each courier company gives the shop two services: one books a pickup, and one tells you where a parcel is. Pedal Post carries light parcels by bike, and Big Blue Vans carries heavy ones. A Pedal Post booking reference means nothing to Big Blue Vans. Let every part of the program pick its own booker and tracker, and sooner or later some rarely used path books with the bike courier. Then it asks the van company where the parcel went.

**Abstract Factory** puts that choice in one place. One interface creates every product of the family, and there's one implementation per family:

""" + pair_kj(K_AF, J_AF) + """

Callers ask for the family once and take both products from it, as the figure shows. In the lab, `Shipping` is handed the factory as a function called `servicesFor`, and asks `servicesFor(parcel.courier)`. Callers can't mix families, because they never pick a product directly. That's the furniture maker in code: one order, one workshop, a matching set.

Each family here is one small class built from settings (the courier, the company's name and the prefix of its references), not a `PedalPostBooker` plus a `PedalPostTracker`. When the products are interfaces with one method, a family is just a class, or a Java record, of functions. The GoF diagram with two parallel class hierarchies is the worst case, not a requirement.

The weakness runs the other way, and it's where the furniture picture breaks too. A new family is cheap: one more implementation, like one more workshop. A new product, say a `Canceller` that cancels a booking, changes the interface and every family. In the town, every workshop would have to learn to make sideboards before anyone could order one.

**Make the family the unit of choice. Then a mismatch can't be written.**

You may not need a factory at all when the whole program uses one family. A test setup and a real setup, chosen once when the program starts, are a single `if` in `main`. Write the factory yourself when the choice depends on data that changes from call to call, such as the weight of this parcel.

Check yourself. The shop buys a cargo bike and adds `CARGO_BIKE` to `Courier`. Where does the build fail, and which callers change? (It fails in `forCourier`, because its `when` and `switch` have no `else` or `default`, so you add a branch with the new family's settings. No caller changes: callers only ask for a family and never name a product class.)"""

L = {
 "id": "pat-02",
 "title": "Factory Method and Abstract Factory",
 "minutes": 35,
 "goal": "By the end you can replace constructor calls with named static or companion factories that check their input and return sealed results, pass factories around as functions, and group matching products behind an abstract factory.",
 "opening": OPENING,
 "warmup": {
  "q": "`List.of(1)` and `List.of(1, 2, 3)` both return a `List<Integer>`. What do you expect `getClass()` to say for each?",
  "options": ["Both are `ArrayList`", "Both are the same private class", "Two different private classes, chosen by the factory from the number of elements", "`List` itself, since `List.of` is defined on the interface"],
  "answer": 2,
  "why": "`List.of` is a static factory, so it can return any class it likes. In JDK 21 it returns `List12` for one or two elements and `ListN` for more, both private. A constructor could never do that: `new X()` always gives you an `X`. And an interface can't be created at all, so `List` itself is impossible. The first section shows the JDK's factories choosing, with real output."
 },
 "sections": [
  {
   "h": "Static factory methods: constructors with names",
   "body": S0,
   "try": {
    "title": "Watch the JDK's factories choose",
    "minutes": 4,
    "steps": [
     "Read `FactoriesInTheJdk`. For each of the first four lines, predict the class name you'll see. The Kotlin twin adds three lines for Kotlin's own `listOf`.",
     "Run it from the `labs/` folder with the command below.",
     "Type `RegularEnumSet` in your editor, as if you wanted to use it. Can you?"
    ],
    "code": code("java", "FactoriesInTheJdk.java", "FactoriesInTheJdk", "kotlin", "FactoriesInTheJdk.kt", "FactoriesInTheJdkKt"),
    "expect": "`List12` for one element and `ListN` for three. `RegularEnumSet` for `TimeUnit` (7 constants) and `JumboEnumSet` for `Character.UnicodeScript` (164 constants on JDK 21). Both `same object?` lines print `true`, because the factories handed back cached objects. None of these classes is public, so your editor won't let you name them: the factory is the only door. Kotlin's `listOf` plays the same game, returning `EmptyList`, `Collections$SingletonList` or `Arrays$ArrayList` depending on how many elements you pass."
   },
   "refs": [
    {"title": "DriverManager (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.sql/java/sql/DriverManager.html", "kind": "docs"}
   ]
  },
  {
   "h": "Factory Method: let someone else choose the class",
   "body": S1,
   "aside": ASIDE1,
   "try": {
    "title": "Break a factory on purpose",
    "minutes": 5,
    "steps": [
     "Run `MessengerFactory` with the command below.",
     "Add `PIGEON` to the `Channel` enum and run it again. Read the compiler error.",
     "Now add a catch-all as the last branch (`default -> new FakeMessenger();` in Java, `else -> FakeMessenger()` in Kotlin), keep `PIGEON`, and run again. Where does the pigeon notice go?",
     "Undo both changes."
    ],
    "code": code("java", "MessengerFactory.java", "MessengerFactory", "kotlin", "MessengerFactory.kt", "MessengerFactoryKt"),
    "expect": "The first run prints one line per channel, then `test notices -> fake: nothing sent`. With `PIGEON` added, the build fails at the factory: javac says `error: the switch expression does not cover all possible input values`, and kotlinc says `'when' expression must be exhaustive. Add the 'PIGEON' branch or an 'else' branch.` With a catch-all branch it compiles and prints `PIGEON -> fake: nothing sent`. A real customer's notice would go to the fake, and nothing warns you."
   }
  },
  {
   "h": "Kotlin factories: companion objects, invoke and sealed results",
   "body": S2,
   "try": {
    "title": "Let the compiler find the missing case",
    "minutes": 4,
    "steps": [
     "Run `CompanionFactories` (Kotlin, or its Java twin) with the command below, and read the three `parse` lines.",
     "Add a fourth result: `data class Closed(val day: String) : SlotResult` in Kotlin, or `record Closed(String day) implements SlotResult {}` in Java. Predict what happens, then run.",
     "Fix it by adding a branch for `Closed` to `describe`, not an `else` or `default`."
    ],
    "code": code("kotlin", "CompanionFactories.kt", "CompanionFactoriesKt", "java", "CompanionFactoriesJava.java", "CompanionFactoriesJava"),
    "expect": "The first run prints `ok: SAT 10:00`, `we deliver from 8 to 19, not at 23` and `no such day 'MOON'`, then `true` for the cached `Fee` of 250 cents and `false` for 400. Java has no `operator invoke`, so its twin needs a named factory, `Fee.of(250)`. After adding `Closed`, the build stops: kotlinc says `'when' expression must be exhaustive. Add the 'is Closed' branch or an 'else' branch.`, and javac says `the switch expression does not cover all possible input values`. The compiler found the one place that needs the new case."
   },
   "refs": [
    {"title": "Coding conventions: naming rules (Kotlin docs)", "url": "https://kotlinlang.org/docs/coding-conventions.html", "kind": "docs"},
    {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html", "kind": "docs"}
   ]
  },
  {
   "h": "Abstract Factory: one choice for a whole matching set",
   "body": S3,
   "figure": {"svg": FIG, "caption": "Shipping asks for a family once. Both products come from that family, so a Pedal Post booking is never tracked at Big Blue Vans."}
  }
 ],
 "compare": {
  "title": "A checking factory that returns a sealed result",
  "java": {"title": "Price.java", "src": """public final class Price {
    private final long cents;
    private Price(long cents) { this.cents = cents; }

    public static Price ofCents(long cents) {                       // named, and it checks
        if (cents < 0) throw new IllegalArgumentException("negative price");
        return new Price(cents);
    }

    public sealed interface Parsed permits Ok, Bad {}
    public record Ok(Price price) implements Parsed {}
    public record Bad(String reason) implements Parsed {}

    public static Parsed parse(String text) {                       // "4.50"
        try {
            long cents = new BigDecimal(text.trim()).movePointRight(2).longValueExact();
            return cents < 0 ? new Bad("negative price") : new Ok(new Price(cents));
        } catch (ArithmeticException | NumberFormatException e) {
            return new Bad("not a price: " + text);
        }
    }
}

// caller: the compiler checks both cases are handled
String shown = switch (Price.parse(input)) {
    case Price.Ok(Price p) -> "saved " + p;
    case Price.Bad(String why) -> "try again: " + why;
};"""},
  "kotlin": {"title": "Price.kt", "src": """class Price private constructor(val cents: Long) {
    companion object {
        @JvmStatic fun ofCents(cents: Long): Price {
            require(cents >= 0) { "negative price" }
            return Price(cents)
        }

        @JvmStatic fun parse(text: String): Parsed {                 // "4.50"
            val cents = text.trim().toBigDecimalOrNull()
                ?.movePointRight(2)
                ?.runCatching { longValueExact() }?.getOrNull()
                ?: return Parsed.Bad("not a price: $text")
            return if (cents < 0) Parsed.Bad("negative price") else Parsed.Ok(Price(cents))
        }
    }
}

sealed interface Parsed {
    data class Ok(val price: Price) : Parsed
    data class Bad(val reason: String) : Parsed
}

// caller
val shown = when (val p = Price.parse(input)) {
    is Parsed.Ok -> "saved ${p.price}"
    is Parsed.Bad -> "try again: ${p.reason}"
}"""},
  "note": "The shape is the same in both: a private constructor, named factories, a sealed result and an exhaustive `switch` or `when` at the call site. Java 21 takes the result apart with record patterns (`case Price.Ok(Price p)`), and Kotlin smart-casts it, treating it as that type once `is` has checked it. The real difference is where the factory lives. Kotlin has no `static`: `ofCents` is a function on the companion object, so Java callers would write `Price.Companion.ofCents(...)` without `@JvmStatic`. Kotlin also gives you `operator fun invoke` and top-level factory functions, and its named arguments remove a lot of the constructor confusion that pushes Java code toward factories in the first place."
 },
 "worked": {
  "title": "Replace look-alike constructors with named factories",
  "steps": [
   {"say": "The shop's `Delivery` class grew four constructors: an order can go to the door or be collected in the shop, with or without a note. Look at the last line and decide what it creates before reading on.",
    "code": """public class Delivery {
    public Delivery(String orderId, int grams) { ... }                 // to the door
    public Delivery(String orderId) { ... }                            // collect in the shop
    public Delivery(String orderId, int grams, String note) { ... }    // to the door, with a note
    public Delivery(String orderId, String note) { ... }               // collect, with a note
}

new Delivery("o-1", "after 5pm");   // ?""", "lang": "java",
    "alt_code": """class Delivery {
    constructor(orderId: String, grams: Int) { ... }                   // to the door
    constructor(orderId: String) { ... }                               // collect in the shop
    constructor(orderId: String, grams: Int, note: String) { ... }     // to the door, with a note
    constructor(orderId: String, note: String) { ... }                 // collect, with a note
}

Delivery("o-1", "after 5pm")   // ?""", "alt_lang": "kotlin"},
   {"say": "It's a collection with a note, but only the parameter types say so. Adding delivery to a neighbor would mean a fifth constructor with yet another mix of types. Give each kind a name, check there, and make the constructor private so every `Delivery` goes through a factory.",
    "code": """public final class Delivery {
    private final String orderId;
    private final OptionalInt grams;         // empty = collected in the shop
    private final String note;

    private Delivery(String orderId, OptionalInt grams, String note) {
        this.orderId = orderId; this.grams = grams; this.note = note;
    }

    public static Delivery collect(String orderId, String note) {                 // 1. the name says what you get
        return new Delivery(orderId, OptionalInt.empty(), note);
    }

    public static Delivery toDoor(String orderId, int grams, String note) {
        if (grams <= 0) throw new IllegalArgumentException("a parcel needs a weight");   // 2. check per kind
        return new Delivery(orderId, OptionalInt.of(grams), note);
    }
}

Delivery.collect("o-1", "after 5pm");
Delivery.toDoor("o-2", 2_500, "blue gate");""", "lang": "java",
    "alt_code": """class Delivery private constructor(
    val orderId: String,
    val grams: Int?,                          // null = collected in the shop
    val note: String,
) {
    companion object {
        fun collect(orderId: String, note: String) = Delivery(orderId, null, note)     // 1. the name says what you get

        fun toDoor(orderId: String, grams: Int, note: String): Delivery {
            require(grams > 0) { "a parcel needs a weight" }                          // 2. check per kind
            return Delivery(orderId, grams, note)
        }
    }
}

Delivery.collect("o-1", "after 5pm")
Delivery.toDoor("o-2", 2_500, "blue gate")""", "alt_lang": "kotlin"},
   {"say": "Later in the day, a parcel for the door needs a van and a collection needs a shelf behind the till. When the kinds behave differently, let the same factories return different records (or data classes) behind a sealed interface. Callers don't change, and code that handles deliveries can switch over the two cases with the compiler checking it covers both. In Kotlin, `@JvmStatic` keeps `Delivery.collect(...)` working for Java callers, and Kotlin callers could also write `Delivery.ToDoor(orderId = \"o-2\", grams = 2_500, note = \"blue gate\")`: named arguments already remove the confusion that started this.",
    "code": """public sealed interface Delivery permits Collect, ToDoor {
    String orderId();

    static Delivery collect(String orderId, String note) { return new Collect(orderId, note); }
    static Delivery toDoor(String orderId, int grams, String note) {
        return new ToDoor(orderId, grams, note);                                  // 3. the factory picks the record
    }
}

record Collect(String orderId, String note) implements Delivery {}
record ToDoor(String orderId, int grams, String note) implements Delivery {
    ToDoor {                                                                      // 4. the rule lives in the record
        if (grams <= 0) throw new IllegalArgumentException("a parcel needs a weight");
    }
}""", "lang": "java",
    "alt_code": """sealed interface Delivery {
    val orderId: String

    data class Collect(override val orderId: String, val note: String) : Delivery
    data class ToDoor(override val orderId: String, val grams: Int, val note: String) : Delivery {
        init { require(grams > 0) { "a parcel needs a weight" } }               // 4. the rule lives in the class
    }

    companion object {
        @JvmStatic fun collect(orderId: String, note: String): Delivery = Collect(orderId, note)
        @JvmStatic fun toDoor(orderId: String, grams: Int, note: String): Delivery =
            ToDoor(orderId, grams, note)                                         // 3. the factory picks the class
    }
}""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A parcel factory, a courier family, and shipping that only knows interfaces",
  "minutes": 13,
  "files": [f"{lab}/main/{K}/Parcel.kt", f"{lab}/main/{K}/CourierServices.kt", f"{lab}/main/{K}/Shipping.kt"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l02.*'",
  "steps": [
   "Open the three files. `Parcel` is a parcel that knows its weight and its courier, `CourierServices` is the family of a courier company's two services, and `Shipping` books a parcel for an order.",
   "Run the tests. All nine fail with `NotImplementedError`, the error Kotlin's `TODO()` throws.",
   "Write `Parcel.parse` in `Parcel.kt`. Apply the three checks from its KDoc comment (Kotlin's documentation comment) in order, and return `ParcelResult.Invalid(reason)` with the exact reason strings. Only `parse` may call the private constructor.",
   "Write `CourierServices.forCourier`. One private class built from settings (courier, company name, prefix) can serve both families. Use `require` for the checks that refuse to mix couriers, and an exhaustive `when` with no `else`.",
   "Write `Shipping.ship` as a `when` over `Parcel.parse(weight)`. Call `servicesFor` only for a valid parcel.",
   "Run the tests until all nine pass."
  ],
  "hints": [
   "`raw.trim().split(\" \")` gives you the number and the unit. `toDoubleOrNull()` returns `null` for text that isn't a number, and `roundToInt()` (import `kotlin.math.roundToInt`) turns `2500.0` into `2500`.",
   "Multiply kilograms by 1,000 before you round: \"2.5 kg\" is 2,500 g. Check `grams <= 0` after rounding, so \"0 g\" and \"-1 kg\" both give `weight`.",
   "`Booker` and `Tracker` are `fun interface`s, so `Booker { parcel, orderId -> ... }` builds one from a lambda.",
   "`require(condition) { \"message\" }` throws `IllegalArgumentException` when the condition is false."
  ],
  "done_when": "All nine tests in `FactoryTest` pass."
 },
 "drill": {
  "title": "A sealed-result factory from memory",
  "minutes": 5,
  "prompt": "Close this page. In Kotlin (or Java, with a static `parse`), write `Email` with a private constructor and a companion `parse(raw: String): EmailResult`. It returns `Ok(email)` when the trimmed text has exactly one `@` with something on both sides, and `Invalid(reason)` otherwise. Then write a caller that uses `when` (or `switch`) with no `else` or `default`.",
  "answer": {"lang": "kotlin", "src": """class Email private constructor(val value: String) {
    companion object {
        fun parse(raw: String): EmailResult {
            val parts = raw.trim().split("@")
            return if (parts.size == 2 && parts.all { it.isNotEmpty() }) EmailResult.Ok(Email(raw.trim()))
            else EmailResult.Invalid("expected name@domain")
        }
    }
}

sealed interface EmailResult {
    data class Ok(val email: Email) : EmailResult
    data class Invalid(val reason: String) : EmailResult
}

fun confirmationTarget(raw: String): String = when (val r = Email.parse(raw)) {
    is EmailResult.Ok -> "sending confirmation to ${r.email.value}"
    is EmailResult.Invalid -> "skipped: ${r.reason}"
}""",
   "alt": {"lang": "java", "title": "Java", "src": """public final class Email {
    private final String value;
    private Email(String value) { this.value = value; }
    public String value() { return value; }

    public static EmailResult parse(String raw) {
        String[] parts = raw.trim().split("@", -1);
        return parts.length == 2 && !parts[0].isEmpty() && !parts[1].isEmpty()
                ? new EmailResult.Ok(new Email(raw.trim()))
                : new EmailResult.Invalid("expected name@domain");
    }
}

public sealed interface EmailResult {
    record Ok(Email email) implements EmailResult {}
    record Invalid(String reason) implements EmailResult {}
}

static String confirmationTarget(String raw) {
    return switch (Email.parse(raw)) {
        case EmailResult.Ok ok -> "sending confirmation to " + ok.email().value();
        case EmailResult.Invalid bad -> "skipped: " + bad.reason();
    };
}"""}}
 },
 "recap": [
  "A static factory is a constructor with a name. It can return a cached object or any subtype, and pick the class from its input (`List.of`, `EnumSet.noneOf`, `DriverManager.getConnection`).",
  "Make the constructor private and check the input in the factory, so every instance in the program is a good one.",
  "The GoF Factory Method, a subclass that overrides a creation hook, is now usually a `Supplier<T>` or `() -> T`, often a constructor reference such as `FakeMessenger::new`. A factory's `switch` or `when` over a sealed type or enum gets no `default` or `else`.",
  "Kotlin factories live in the companion object, in `operator fun invoke`, or in a top-level function named like the type (`Job()`, `MutableStateFlow(0)`). Return a sealed result for answers callers must handle.",
  "Abstract Factory makes a family of matching products from one choice, so callers can't mix one courier's booker with another's tracker.",
  "The limit: an abstract factory makes new families cheap and new products expensive, because adding a product changes the interface and every family."
 ],
 "closing": "We started at the bakery counter and the furniture maker's workshop. In code, the counter became a static factory with a name, and the baker's choice became a function passed in. The workshop became one interface that makes a matching booker and tracker, and the compiler checked every switch.\n\nNow search your own code for `default ->` or `else ->` in a `switch` or `when` that creates objects. Each is a place where a new case slips through without a word. If the type is sealed or an enum, delete the branch and see what the compiler says.\n\nNext, we'll meet objects with many optional parts. When a constructor needs ten arguments, how do you build one that anyone can read?",
 "quiz": [
  {"q": "Which of these can a static factory do that a constructor can never do?",
   "options": ["Return an instance of a subtype chosen from its arguments", "Check its arguments", "Be called from another package", "Throw a checked exception"],
   "answer": 0,
   "why": "Constructors can check their arguments, be public and throw checked exceptions too. Only a factory can return a cached object or a different class, like `List.of` returning `List12` or `ListN` depending on how many elements you pass."},
  {"q": "A factory has `switch (channel) { case SMS -> ...; case EMAIL -> ...; default -> new FakeMessenger(); }`. A teammate adds `POST`, for letters by post, to the enum. What happens?",
   "options": ["A compile error in the factory", "A `MatchException` at run time", "Notices by post silently go to the fake messenger", "The switch throws `NullPointerException`"],
   "answer": 2,
   "why": "The `default` branch catches every new constant, so the build stays green and letters by post go to the fake. Without `default`, a switch expression over an enum must cover every constant, and adding `POST` would be a compile error at exactly this line."},
  {"q": "Which Kotlin shape lets callers write `Fee(250)` while you return a cached instance?",
   "options": ["A secondary constructor", "`operator fun invoke` in the companion object", "An `init` block", "A `data class` with a default argument"],
   "answer": 1,
   "why": "A constructor always makes a new object, primary or secondary. `operator fun invoke(cents: Int): Fee` on the companion turns `Fee(250)` into a function call that can return anything, including a cached instance. Readers expect a new object from that syntax, so use it with care."},
  {"q": "You have `interface CourierServices { Booker booker(); Tracker tracker(); }` with a bike family and a van family. Now you need a `Canceller` product too. What does that cost?",
   "options": ["Nothing: add one new class", "Only the van family changes", "You have to switch to Factory Method", "The interface and every existing family change"],
   "answer": 3,
   "why": "Abstract Factory makes new families cheap and new products expensive: every family must now produce a canceller, including any fake family your tests use. Weigh that before you add a product to the interface."},
  {"q": "From lesson 1 of this track: a Kotlin `companion object` holds a factory `of(...)` and `val cache = loadPrices()`. When does `loadPrices()` run?",
   "options": ["When the outer class is loaded, like a Java static initializer", "Lazily, the first time `cache` is read, under a lock", "Every time `of` is called", "At program startup, for every class on the classpath"],
   "answer": 0,
   "why": "A companion object is initialized when its outer class is loaded, which matches a Java static initializer, so `loadPrices()` runs then even if nobody reads `cache`. If you want it on first read, write `val cache by lazy { loadPrices() }`.",
   "from": "pat-01"}
 ],
 "flashcards": [
  {"front": "Name two things a static factory can do that a constructor can't.", "back": "Return a cached instance, and return a subtype chosen from its arguments (`List.of` gives `List12` or `ListN`). It also has a name."},
  {"front": "Why leave out `default` in a factory's switch over a sealed type or enum?", "back": "So adding a new case is a compile error at the factory. With `default`, the new case silently takes the default branch."},
  {"front": "What replaced the GoF Factory Method's creator subclass in modern Java?", "back": "A function: a `Supplier<Messenger>`, usually written as a constructor reference such as `SmsMessenger::new`."},
  {"front": "Kotlin has no `static`. Where does a class's named factory usually live?", "back": "In its `companion object`: `companion object { fun parse(raw: String): ParcelResult }`."},
  {"front": "What name may a Kotlin factory function have, by the coding conventions?", "back": "The same name as the abstract type it returns, like `fun Job(): Job` or `MutableStateFlow(0)`."},
  {"front": "When should a factory return a sealed result instead of throwing?", "back": "When the failure is an answer the caller is expected to handle, like a mistyped weight. Keep exceptions for bugs and broken machinery."},
  {"front": "Abstract Factory: what is cheap to add, and what is expensive?", "back": "A new family is cheap (one implementation). A new product is expensive (the interface and every family change)."}
 ],
 "terms": [
  {"term": "Static factory method", "plain": "A static method that returns an instance, used instead of a public constructor."},
  {"term": "Factory Method (GoF)", "plain": "A creation hook that lets something other than the caller pick the concrete class. Now often a `Supplier<T>` or `() -> T`."},
  {"term": "Abstract Factory", "plain": "An interface that creates a whole family of matching objects, with one implementation per family."},
  {"term": "Product family", "plain": "Objects that must be used together, such as one courier company's booker and tracker."},
  {"term": "Sealed result", "plain": "A sealed set of answers (`Valid`, `Invalid`) returned instead of throwing. A `switch` or `when` must handle every case."},
  {"term": "Companion object", "plain": "A Kotlin object tied to a class, and the usual home for that class's factories."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why `CourierServices.forCourier(courier)` has no `else` branch, and why `Shipping` takes a `(Courier) -> CourierServices` instead of calling `forCourier` directly.",
  "answer": "With no `else`, the `when` has to name every `Courier`. When someone adds `CARGO_BIKE`, the factory stops compiling until they decide which family it gets, instead of quietly falling into a default. The function parameter keeps `Shipping` from knowing which families exist and how they're built. The real program passes `CourierServices::forCourier`, and a test passes a lambda that returns a fake family and records which courier was asked for. So the choice of concrete classes lives in one place, and the shipping logic can be tested without any courier at all."
 },
 "deeper": {
  "minutes": 10,
  "body": """`DriverManager` is a factory whose products didn't exist when it was written. On first use, it asks `ServiceLoader` for every `java.sql.Driver` that a JAR on the classpath lists in a `META-INF/services/java.sql.Driver` file. `getConnection(url)` then offers the URL to each driver until one accepts it. You can build the same plug-in mechanism yourself: define an interface, list the implementations in `META-INF/services/<interface name>`, and call `ServiceLoader.load(YourInterface.class)`. The module system adds `provides ... with ...` and `uses ...` declarations for the same thing.

Effective Java lists the usual factory names, and sticking to them makes factories easy to find: `from` for a one-argument conversion (`Date.from(instant)`), `of` for gathering several values (`EnumSet.of(...)`), `valueOf`, `getInstance` or `instance`, `create` or `newInstance` when each call returns a new object, `getType` and `newType` when the factory lives in another class (`Files.newBufferedReader`), and a bare `type` (`Collections.list`).

From Java, a Kotlin companion factory is `Price.Companion.parse(...)`. Mark it with `@JvmStatic` and Java callers can write `Price.parse(...)`. If Java code uses your Kotlin library, do it for every public factory. The same goes for `@JvmOverloads` on functions with default arguments, which you'll meet in *Builder and Prototype* (lesson 3 of this track)."""
 },
 "sources": [
  {"title": "Object declarations and companion objects (Kotlin docs)", "url": "https://kotlinlang.org/docs/object-declarations.html"},
  {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html"},
  {"title": "JEP 441: Pattern Matching for switch", "url": "https://openjdk.org/jeps/441"},
  {"title": "DriverManager (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.sql/java/sql/DriverManager.html"}
 ]
}

out = ROOT / "content/lessons/pat-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
