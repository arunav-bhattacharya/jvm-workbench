import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/modernjava/src"
P = "java/workbench/modernjava/l01"
D = "java/workbench/modernjava/l01/demo"
K = "kotlin/workbench/modernjava/l01/demo"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :modernjava:demo -Pmain=workbench.modernjava.l01.demo."


def demo(name, kt_name=None):
    kt_name = kt_name or name
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{D}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{D}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{kt_name}.kt", "src": read(f"{lab}/demo/{K}/{kt_name}.kt"),
                    "run": DEMO + kt_name + "Kt", "file": f"{lab}/demo/{K}/{kt_name}.kt"}}


FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="From one record header, javac generates private final fields, '
    'a canonical constructor and public accessors, plus equals, hashCode and toString that read the fields through ObjectMethods.bootstrap">'
    '<rect class="box-a" x="120" y="14" width="440" height="40" rx="8"/>'
    '<text class="t t-code" x="340" y="39" text-anchor="middle">record Money(long minor, String currency) {}</text>'
    '<line class="ln" x1="300" y1="54" x2="120" y2="96" marker-end="url(#arr)"/>'
    '<line class="ln" x1="340" y1="54" x2="340" y2="96" marker-end="url(#arr)"/>'
    '<line class="ln" x1="380" y1="54" x2="560" y2="96" marker-end="url(#arr)"/>'
    '<rect class="box" x="15" y="100" width="210" height="64" rx="8"/>'
    '<text class="t-s t-code" x="120" y="126" text-anchor="middle">final long minor</text>'
    '<text class="t-s t-code" x="120" y="148" text-anchor="middle">final String currency</text>'
    '<rect class="box" x="235" y="100" width="210" height="64" rx="8"/>'
    '<text class="t-s t-code" x="340" y="126" text-anchor="middle">Money(long, String)</text>'
    '<text class="t-s t-m" x="340" y="148" text-anchor="middle">canonical constructor</text>'
    '<rect class="box" x="455" y="100" width="210" height="64" rx="8"/>'
    '<text class="t-s t-code" x="560" y="126" text-anchor="middle">minor()  currency()</text>'
    '<text class="t-s t-m" x="560" y="148" text-anchor="middle">public accessors</text>'
    '<line class="ln-a" x1="120" y1="212" x2="120" y2="170" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="130" y="196">reads the fields</text>'
    '<rect class="box-b" x="15" y="214" width="650" height="72" rx="8"/>'
    '<text class="t t-code" x="340" y="238" text-anchor="middle">equals   hashCode   toString</text>'
    '<text class="t-s" x="340" y="258" text-anchor="middle">each one invokedynamic call to ObjectMethods.bootstrap,</text>'
    '<text class="t-s t-m" x="340" y="276" text-anchor="middle">passed "minor;currency" and a getter for each private field (not the accessors)</text>'
    '</svg>'
)

S1 = """Here is a small value class written by hand, the way a lot of Java code still has them:

```java
public final class Money {
    private final long minor;
    private final String currency;                  // added in the last sprint

    public Money(long minor, String currency) { this.minor = minor; this.currency = currency; }
    public long minor() { return minor; }
    public String currency() { return currency; }

    @Override public boolean equals(Object o) {
        return o instanceof Money m && m.minor == minor;   // nobody updated this
    }
    @Override public int hashCode() { return Long.hashCode(minor); }
    @Override public String toString() { return "Money[minor=" + minor + "]"; }
}
```

```kotlin
class Money(val minor: Long, val currency: String) {     // currency added in the last sprint
    override fun equals(other: Any?) = other is Money && other.minor == minor   // nobody updated this
    override fun hashCode() = minor.hashCode()
    override fun toString() = "Money(minor=$minor)"
}
```

It compiles, and `new Money(1000, "EUR").equals(new Money(1000, "USD"))` is true. A refund matcher that compares amounts now matches across currencies, and the log line doesn't even show the currency. The class says "these fields are the value" in four places, and the four drifted apart.

A record says it once. You list its components, the values that make up the record, in the header, and javac writes the rest from that list:

```java
public record Money(long minor, String currency) {}
```

```kotlin
data class Money(val minor: Long, val currency: String)
```

From that header javac generates a private final field per component, a public accessor per component (`minor()` and `currency()`, with no `get` prefix), a canonical constructor that takes the components in order, and `equals`, `hashCode` and `toString`. The class is final and extends `java.lang.Record`. Records have been final since JDK 16 (JEP 395), so everything in this lesson works on the JDK 21 the labs compile for.

The `Record` Javadoc calls a record "a shallowly immutable, transparent carrier for a fixed set of values". Each part of that phrase is a rule you will run into. The component list is fixed: you can't add instance fields, and `private int cache;` in the body fails with `field declaration must be static`. Static fields, methods and nested types are fine. Transparent means the state is the API. Every component gets a public accessor, and `equals` and `toString` use every component. A record can implement interfaces but can't extend a class, because it already extends `Record`. And shallowly immutable means the fields are final while the objects they point to may not be. Section 3 is about that.

The generated methods are not what you would write by hand. `javap` shows that `equals`, `hashCode` and `toString` are each a single `invokedynamic` instruction. `invokedynamic` is a call whose target the JVM decides at run time: the first time it runs, the JVM calls a bootstrap method, here `java.lang.runtime.ObjectMethods.bootstrap`, and links in whatever method that returns. javac passes it the component names as one string (`minor;currency`) and a direct getter for each private field, and the JDK builds the method bodies from that list. That is why the Javadoc says the exact `hashCode` algorithm and `toString` format may change: never parse a record's `toString`. kotlinc does it the older way and writes `equals` and `hashCode` out as ordinary bytecode in your class.

A record is still an ordinary object with its own identity: every `new` makes a distinct object, and `==` and `synchronized` can tell it apart from an equal one. `new Point(3, 4) == new Point(3, 4)` is `false`, and `synchronized` on a record compiles and runs. Objects without identity are what Project Valhalla adds, as a preview feature scheduled for JDK 28. Lesson 4 of this track covers where that stands."""

S2 = """Validation in a static factory is easy to get around. `Money.of(...)` can check the amount all it likes, and `new Money(-5, "eur")` walks straight past it. A record gives you a place nobody can walk past. It has exactly one canonical constructor: the one whose parameters match the components. Every other constructor must call it first, and so does every static factory, every wither, and Java deserialization. That makes it the one place for validation and normalization. Write it in the compact form, with no parameter list:

```java
public record Money(long minor, String currency) {
    public Money {
        Objects.requireNonNull(currency, "currency");
        if (minor < 0) throw new IllegalArgumentException("negative amount: " + minor);
        currency = currency.toUpperCase(Locale.ROOT);    // reassign the parameter
    }                                                    // javac assigns the fields here

    public Money(long minor) { this(minor, "EUR"); }     // must delegate first
}
```

```kotlin
data class Money(val minor: Long, val currency: String) {
    init {
        require(minor >= 0) { "negative amount: $minor" }
        require(currency == currency.uppercase()) { "currency must be upper case: $currency" }
    }

    constructor(minor: Long) : this(minor, "EUR")        // must delegate first
}
```

In the compact form the parameters are ordinary local variables. You can reassign them, and javac copies their final values into the fields after your code runs. You can't touch the fields yourself: `this.minor = minor;` fails with `cannot assign a value to final variable minor`. A non-canonical constructor that doesn't start with `this(...)` fails on JDK 21 with `constructor is not canonical, so its first statement must invoke another constructor of class Money`. JDK 25 made flexible constructor bodies final, so there you may run plain statements, such as parsing `"12.50 EUR"`, before the `this(...)` call.

The Kotlin version shows a real difference. `init` runs on every construction, and `copy()` runs it too. But a data class can't change a constructor parameter before it becomes a property. It can reject `"eur"`, but it can't turn it into `"EUR"`. Normalizing moves into a factory function, and the public constructor still accepts the raw value.

Deserialization is where the canonical constructor pays off. The `Record` Javadoc says the canonical constructor is invoked during deserialization, and that `readObject` and `writeObject` are ignored for records. An ordinary class needs a hand-written `readObject` to recheck its invariants, and most classes don't have one. A record gets the check for free. A Kotlin data class does not: Java deserialization never runs its `init` block, unless you mark the class `@JvmRecord` so it compiles to a real record. The Try it below tampers with a byte stream to show both."""

S3 = """`equals` on a record returns true when the other object is the same record class and every component is equal. For a reference component that means `Objects.equals`. For a primitive it means the wrapper's `compare` returns 0, which has two surprises for a `double`. A record holding `NaN` equals another one holding `NaN`, though `NaN == NaN` is false. And `0.0` and `-0.0` are not equal, though `0.0 == -0.0` is true. Kotlin data classes behave the same way. Keep money in a `long` of minor units and neither will bite you.

Arrays are worse. An `int[]` component compares by reference, so two records with equal arrays are not equal, and `toString` prints something like `[I@1b6d3586`. Use a `List`.

A `List` component brings the real trap. The record holds a reference to whatever list the caller passed in, and if the caller keeps changing that list, the record changes too:

```java
record Batch(String id, List<String> paymentIds) {}

var ids = new ArrayList<>(List.of("pay_1", "pay_2"));
var batch = new Batch("b-7", ids);
var sent = new HashSet<>(Set.of(batch));
ids.add("pay_3");
sent.contains(batch);              // false: the hashCode changed under the set
```

```kotlin
data class Batch(val id: String, val paymentIds: List<String>)

val ids = mutableListOf("pay_1", "pay_2")
val batch = Batch("b-7", ids)
val sent = hashSetOf(batch)
ids += "pay_3"
batch in sent                      // false: the hashCode changed under the set
```

The batch is still in the set. The set just looks for it in the wrong bucket. The fix is one line in the compact constructor: `paymentIds = List.copyOf(paymentIds);`. It makes an unmodifiable copy, and it throws `NullPointerException` for a null element. That is what you want for domain data, and a surprise for JSON lists that contain nulls. Kotlin's `List<String>` is a read-only view, not an immutable list, so a data class needs the same copy, made in a factory. *Don't share: immutability, confinement, ThreadLocal* in the concurrency track made the same point about sharing between threads. Here the cost is a lost key, even on one thread.

The last trap looks like a fix. To keep a card number out of the logs, someone overrides the accessor so `card()` returns `****1111`. The logs don't change. The generated `toString` reads the field directly (that is what the getters in the bootstrap arguments are), so it still prints the full number. The override also breaks the record contract that `new Masked(m.card())` equals `m`. Record patterns, which lesson 3 covers, do call the accessor, so different parts of your code now see different data. To hide a component, override `toString`, or keep the secret out of any record that gets logged."""

S4 = """Kotlin engineers reach for `copy()` first and find Java has none. A record that needs "the same refund with a smaller amount" gets a hand-written wither:

```java
record Refund(String paymentId, long amountMinor, List<String> reasons) {
    Refund withAmount(long newAmount) {
        return new Refund(paymentId, newAmount, reasons);   // through the canonical constructor
    }
}
```

```kotlin
data class Refund(val paymentId: String, val amountMinor: Long, val reasons: List<String>)

val part = full.copy(amountMinor = 2_000)                  // generated, and it runs init
```

Both go through validation, which is the point: there is no path to an invalid `Refund`. The cost on the Java side is typing, and it grows with the record. In a 2020 design draft, Brian Goetz pointed out that while a class has O(n) getters, it "could conceivably have O(2^n) withers", and asked that hand-written withers not become a best practice. Write withers only for the changes your domain actually makes.

A language fix exists on paper. JEP 468, derived record creation, proposes `refund with { amountMinor = 2_000; }`. It would take the record apart, run the block, and call the canonical constructor with the result. It is a Candidate JEP, no JDK has shipped it, and in January 2026 Goetz wrote that it "has been 'on hold' for a while". Don't plan around it.

The other differences matter more day to day. A data class may declare properties in its body, and Kotlin leaves those out of `equals`, `hashCode`, `toString` and `copy()`, so two objects that differ only there are equal. A record can't have body state at all. A data class can't be `open`, `abstract` or `sealed`, and a record is always final. Kotlin destructures with `val (id, amount) = refund`, through `componentN()` functions, while Java destructures with record patterns in `switch` and `instanceof` (lesson 3).

Where the two languages meet, Kotlin reads a Java record's accessors as properties (`money.minor`), and `@JvmRecord` on a data class emits a real `java.lang.Record` that Java code sees as one. The Kotlin docs warn that adding `@JvmRecord` to an existing class is not a binary-compatible change, so decide when you create the class."""

L = {
 "id": "dop-01",
 "title": "Records: transparent carriers for data",
 "minutes": 35,
 "goal": "By the end you can write a record whose compact constructor validates and normalizes every instance, explain what javac generates for it, and say exactly where its equality and immutability stop.",
 "warmup": {
  "q": "`record Masked(String card)` overrides its accessor so that `card()` returns `\"****1111\"` for the card 4111111111111111. What does `toString()` return?",
  "options": ["`Masked[card=****1111]`, because toString calls the accessor",
              "`Masked[card=4111111111111111]`",
              "Nothing: it doesn't compile, because record accessors can't be overridden",
              "`Masked@1b6d3586`, because overriding an accessor turns off the generated toString"],
  "answer": 1,
  "why": "The generated `toString`, `equals` and `hashCode` read the private field directly, not the accessor, so the full number reaches the log. Overriding an accessor is legal as long as the return type matches. To hide a component, override `toString` itself, as the lab does."
 },
 "sections": [
  {
   "h": "A record is its components, and javac writes the rest",
   "body": S1,
   "figure": {"svg": FIG, "caption": "One header line becomes fields, a constructor and accessors. The three Object methods are built at run time and read the fields, not the accessors."},
   "try": {
    "title": "Look inside a record",
    "minutes": 4,
    "steps": [
     "Run `RecordAnatomy` (or its Kotlin twin) with the command below. Predict the `==` line before you look.",
     "From `labs/`, print the bytecode of the nested record: `javap -p -c 'modernjava/build/classes/java/demo/workbench/modernjava/l01/demo/RecordAnatomy$Point.class'`. Find the three `invokedynamic` lines.",
     "Run `javap -v` on the same file and scroll to `BootstrapMethods`. Then run `javap -p modernjava/build/classes/kotlin/demo/workbench/modernjava/l01/demo/Point.class` and compare what kotlinc generated."
    ],
    "code": demo("RecordAnatomy"),
    "expect": "The demo prints `Point[x=3, y=4]`, `equals: true`, `==: false`, `isRecord: true` and the components `[int x, int y]`. The Kotlin twin prints `isRecord: false` for the plain data class and `true` for the `@JvmRecord` one. Under `BootstrapMethods` there is one `ObjectMethods.bootstrap` entry whose arguments are the class, `x;y`, and two `REF_getField` handles on the private fields. The Kotlin class has `getX()`, `component1()`, `copy(int, int)` and `copy$default(...)` instead."
   },
   "refs": [
    {"title": "Record (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Record.html", "kind": "docs"},
    {"title": "JEP 395: Records", "url": "https://openjdk.org/jeps/395", "kind": "read"}
   ]
  },
  {
   "h": "The compact constructor is the only way in",
   "body": S2,
   "try": {
    "title": "Go through every door",
    "minutes": 5,
    "steps": [
     "Run `CompactConstructorDemo`. Read the last line of output before you read the code that produced it.",
     "Run the Kotlin twin, `CompactConstructorDemoKt`. Which tampered range got through?",
     "In the Java demo, add `this.minor = minor;` inside the compact constructor of `Money` and run again. Read the compiler error, then undo the change.",
     "If you have JDK 25, run `java preview/FlexibleConstructor.java` from `labs/modernjava`. Then run the same file with JDK 21 and read the two errors."
    ],
    "code": demo("CompactConstructorDemo"),
    "expect": "The Java demo prints `Money[minor=1250, currency=EUR]`, `Money[minor=5, currency=EUR]`, `Money[minor=300, currency=USD]`, `IAE: negative amount: -1`, `NPE: currency` and finally `tampered stream rejected: lo > hi: 5 > 1`: deserialization called the compact constructor, it threw, and `ObjectInputStream` wrapped that in an `InvalidObjectException`. The Kotlin twin prints `tampered stream gave: RangeK(lo=5, hi=1)` for the plain data class, an object its own `init` forbids, and rejects the `@JvmRecord` one. The field assignment fails with `cannot assign a value to final variable minor`. On JDK 25 the preview file parses `12.50 eur` into `Money[minor=1250, currency=EUR]`; JDK 21 rejects it."
   },
   "refs": [
    {"title": "Records in Kotlin: @JvmRecord", "url": "https://kotlinlang.org/docs/jvm-records.html", "kind": "docs"}
   ]
  },
  {
   "h": "Equality and immutability go one level deep",
   "body": S3,
   "try": {
    "title": "Lose a key, leak a card",
    "minutes": 4,
    "steps": [
     "Predict the `sent.contains` line, then run `ShallowDemo`.",
     "Give `Batch` a compact constructor that copies its list, as `SafeBatch` does. Run it again.",
     "Run the Kotlin twin and look at the `copy shares list` line. Did `copy()` copy the list?"
    ],
    "code": demo("ShallowDemo"),
    "expect": "`hashCode changed: true` and `sent.contains: false`. After your fix the batch keeps two ids and the set finds it. The masked record prints `accessor: ****1111` but `toString: Masked[card=4111111111111111]`, and `copy equals orig: false`. The `NaN` records are equal and the `0.0`/`-0.0` ones are not. In Kotlin, the copy shows `pay_4`, which was added after the copy was made: `copy()` copies references, not the objects behind them."
   }
  },
  {
   "h": "Records, data classes and the missing copy()",
   "body": S4,
   "try": {
    "title": "Wither versus copy()",
    "minutes": 4,
    "steps": [
     "Run `WitherDemo` and its twin `WitherDemoKt`. Compare the four lines each prints.",
     "Add a `withPaymentId(String id)` wither to the Java record and call it with `\" \"`. Should that be rejected? Add the check where every wither will get it.",
     "In `WitherDemo.kt`, add `var note = \"\"` to the body of `RefundRequest`, set `full.note = \"called twice\"`, and print `full == full.copy()` and `full.copy().note`."
    ],
    "code": demo("WitherDemo"),
    "expect": "Both versions print the original, the changed refund, `same reasons list object: true` and a rejected negative amount. Withers and `copy()` both reuse the component references, which is safe here only because the list can't change. The blank-id check belongs in the compact constructor, so every wither inherits it. In Kotlin, `full == full.copy()` is `true` and the copy's `note` is empty: body properties are ignored by `equals` and not copied."
   },
   "refs": [
    {"title": "Data classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/data-classes.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A record is like a line on a printed bank statement: date, amount, reference. Anyone can read every field, two lines with the same values mean the same thing, and to change one you print a new line. The bank checks the line before it prints it, which is the compact constructor's job. The analogy breaks at one point: a printed line can't point at anything that changes later, while a record's `List` component can be someone else's list that keeps growing after the record was made.",
 "in_your_world": "Your Quarkus services already move records around: REST request and response bodies, Kafka event payloads, Temporal activity inputs. Each of those is a boundary where outside data becomes a value, and the compact constructor is where you check it once: three-letter currency codes, non-negative amounts, idempotency keys of the right length. After that, any `Money` the service holds is a valid one. Two places need care. A `List` component in a Kafka event must be copied, or a producer that reuses its buffer list changes events it has already handed off. And a record that holds a PAN, an IBAN or an access token must override `toString`, because the generated one prints every component into every log line and exception message that touches the record.",
 "mistake": "The common mistake is treating a record as deeply immutable and using it as a map or set key while one of its components is a mutable list or map. It works in tests, because nothing mutates the list there. In production a caller reuses its `ArrayList`, the record's `hashCode` changes, and `HashMap.get` returns null for a key that is still in the map. Copy every collection component in the compact constructor with `List.copyOf`, `Set.copyOf` or `Map.copyOf`, and don't use arrays as components.",
 "compare": {
  "title": "A validated money value in Java and Kotlin",
  "java": {"title": "Money.java", "src": "public record Money(long minor, String currency) {\n    private static final Pattern ISO = Pattern.compile(\"[A-Z]{3}\");\n\n    public Money {\n        Objects.requireNonNull(currency, \"currency\");\n        currency = currency.trim().toUpperCase(Locale.ROOT);   // normalize in place\n        if (!ISO.matcher(currency).matches()) throw new IllegalArgumentException(\"bad currency: \" + currency);\n        if (minor < 0) throw new IllegalArgumentException(\"negative amount: \" + minor);\n    }\n\n    public Money plus(Money other) {\n        if (!currency.equals(other.currency)) throw new IllegalArgumentException(\"currency mismatch\");\n        return new Money(Math.addExact(minor, other.minor), currency);\n    }\n}"},
  "kotlin": {"title": "Money.kt", "src": "data class Money(val minor: Long, val currency: String) {\n    init {\n        require(ISO.matches(currency)) { \"bad currency: $currency\" }   // can reject, can't normalize\n        require(minor >= 0) { \"negative amount: $minor\" }\n    }\n\n    operator fun plus(other: Money): Money {\n        require(currency == other.currency) { \"currency mismatch\" }\n        return Money(Math.addExact(minor, other.minor), currency)\n    }\n\n    companion object {\n        private val ISO = Regex(\"[A-Z]{3}\")\n        fun of(minor: Long, currency: String) = Money(minor, currency.trim().uppercase())\n    }\n}"},
  "note": "Both give you `equals`, `hashCode` and `toString` over all components, final fields, and a validation hook that every construction goes through, including Kotlin's `copy()`. Three things differ. Java's compact constructor can normalize a parameter before it becomes a field; a data class can only reject it, so normalizing lives in a factory and the public constructor stays open to raw input. Java deserialization rebuilds a record through its canonical constructor but skips a data class's `init` (`@JvmRecord` closes that gap). And Kotlin has `copy()` with named arguments, while Java has hand-written withers until JEP 468 ships, which it hasn't."
 },
 "worked": {
  "title": "Turn a mutable request class into a record",
  "steps": [
   {"say": "A capture request in a payment service is a JavaBean: setters, a mutable list, and sixty lines of hand-written `equals`, `hashCode` and `toString` that nobody updated when `currency` was added. Any code can change it after it was checked.",
    "code": "public class CaptureRequest {\n    private String paymentId;\n    private long amountMinor;\n    private String currency;\n    private List<String> lineItems = new ArrayList<>();\n\n    public void setAmountMinor(long amountMinor) { this.amountMinor = amountMinor; }\n    public List<String> getLineItems() { return lineItems; }   // hands out the live list\n    // ... more setters, getters, equals, hashCode, toString\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class CaptureRequest {\n    var paymentId: String? = null\n    var amountMinor: Long = 0\n    var currency: String? = null\n    val lineItems: MutableList<String> = mutableListOf()       // hands out the live list\n}"},
   {"say": "Write the header. The components are the whole state, and every setter is gone. Recompile: each place that called a setter is now a compile error, which is your list of code that mutated a request after it was built.",
    "code": "// 1. the components are the state\npublic record CaptureRequest(String paymentId, Money amount, List<String> lineItems) {}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "// 1. the properties are the state\ndata class CaptureRequest(val paymentId: String, val amount: Money, val lineItems: List<String>)"},
   {"say": "Add the compact constructor. Reject what can't be valid, then copy the list so the caller can't change it later. `amount` is a `Money`, which validates itself, so the request doesn't repeat those checks.",
    "code": "public record CaptureRequest(String paymentId, Money amount, List<String> lineItems) {\n    public CaptureRequest {\n        Objects.requireNonNull(paymentId, \"paymentId\");                     // 2. reject\n        Objects.requireNonNull(amount, \"amount\");\n        if (paymentId.isBlank()) throw new IllegalArgumentException(\"blank paymentId\");\n        lineItems = List.copyOf(lineItems);                                   // 3. copy\n        if (lineItems.isEmpty()) throw new IllegalArgumentException(\"no line items\");\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "data class CaptureRequest(val paymentId: String, val amount: Money, val lineItems: List<String>) {\n    init {\n        require(paymentId.isNotBlank()) { \"blank paymentId\" }                // 2. reject\n        require(lineItems.isNotEmpty()) { \"no line items\" }\n    }\n\n    companion object {\n        fun of(paymentId: String, amount: Money, lineItems: List<String>) =\n            CaptureRequest(paymentId, amount, java.util.List.copyOf(lineItems))   // 3. copy\n    }\n}"},
   {"say": "Add only the wither the domain needs. Partial captures happen, so `withAmount` earns its place. It calls the canonical constructor, so a partial capture can't skip the checks. In Kotlin, `copy(amount = ...)` already exists and runs `init`.",
    "code": "    // 4. one wither, through the canonical constructor\n    public CaptureRequest withAmount(Money partial) {\n        return new CaptureRequest(paymentId, partial, lineItems);\n    }", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "    // 4. no wither to write: copy() is generated and runs init\n    val partial = request.copy(amount = Money.of(2_000, \"eur\"))"}
  ]
 },
 "lab": {
  "title": "Payment value records",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/Money.java", f"{lab}/main/{P}/Refund.java", f"{lab}/main/{P}/CardNumber.java"],
  "run": "./gradlew :modernjava:test --tests 'workbench.modernjava.l01.*'",
  "steps": [
   "Run the tests once. All eight fail. Read the test names in `PaymentRecordsTest`: they are the spec.",
   "In `Money`, write the compact constructor (TODO 1) and `plus` (TODO 2).",
   "In `Refund`, write the compact constructor with a defensive copy of the reasons (TODO 3), then `withAmount` (TODO 4).",
   "In `CardNumber`, validate and strip spaces (TODO 5), override `toString` (TODO 6) and write `last4` (TODO 7).",
   "Run the tests until all eight pass. Then compare your code with the reference answers in `src/solution`."
  ],
  "hints": [
   "In a compact constructor you assign the parameter: `currency = currency.trim().toUpperCase(Locale.ROOT);`. Writing `this.currency = ...` doesn't compile.",
   "Order matters in `Money`: normalize first, then check for three letters, or `\" eur \"` fails the check.",
   "`List.copyOf(reasons)` throws `NullPointerException` for a null list, so it does that null check for you.",
   "`withAmount` is one line. Call the canonical constructor and the checks run by themselves.",
   "Don't touch the `digits()` accessor. The test checks that `new CardNumber(c.digits())` still equals `c`."
  ],
  "done_when": "All eight tests in `PaymentRecordsTest` pass."
 },
 "drill": {
  "title": "A validated key from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `record IdempotencyKey(String value)` that rejects null, trims the value, and then rejects anything that isn't 16 to 64 letters, digits or `-`. Then write the Kotlin version. Which of the two can store the trimmed value without a factory?",
  "answer": {"lang": "java", "src": "public record IdempotencyKey(String value) {\n    private static final Pattern SHAPE = Pattern.compile(\"[A-Za-z0-9-]{16,64}\");\n\n    public IdempotencyKey {\n        Objects.requireNonNull(value, \"value\");\n        value = value.trim();                                   // normalize first\n        if (!SHAPE.matcher(value).matches()) {\n            throw new IllegalArgumentException(\"bad idempotency key\");\n        }\n    }\n}",
             "alt": {"lang": "kotlin", "src": "data class IdempotencyKey(val value: String) {\n    init {\n        require(SHAPE.matches(value)) { \"bad idempotency key\" }   // can reject, can't trim\n    }\n\n    companion object {\n        private val SHAPE = Regex(\"[A-Za-z0-9-]{16,64}\")\n        fun of(raw: String) = IdempotencyKey(raw.trim())         // so trimming lives here\n    }\n}"}}
 },
 "recap": [
  "A record is a final class with private final fields, public accessors, one canonical constructor and generated `equals`, `hashCode` and `toString`. It can't add instance fields or extend a class.",
  "Validate and normalize in the compact constructor. Every path goes through it: `new`, factories, other constructors, withers and Java deserialization.",
  "Equality compares every component: `Objects.equals` for references and `compare` for primitives, so `NaN` equals `NaN` and `0.0` doesn't equal `-0.0`. Arrays compare by reference.",
  "Records are only shallowly immutable. Copy collection components with `List.copyOf`, or a mutated key gets lost in a `HashSet`.",
  "The generated methods read fields, not accessors. To hide a secret, override `toString`.",
  "Kotlin has `copy()` and Java has hand-written withers, because JEP 468 is on hold. Java deserialization skips a data class's `init` unless the class is `@JvmRecord`."
 ],
 "quiz": [
  {"q": "`record Batch(String id, List<String> ids)` is a key in a `HashMap<Batch, Status>`. The producer that built it later calls `ids.add(\"pay_9\")` on its own list. What does `map.get(batch)` most likely return now?",
   "options": ["The status, because records are immutable", "`null`, because the key's hashCode changed and the map looks in the wrong bucket", "It throws ConcurrentModificationException", "The status, because HashMap compares record keys with =="],
   "answer": 1, "why": "The record's fields are final, but the list they point to is the producer's list. `hashCode` includes the list, so it changes, and the map searches a bucket where the entry isn't. Nothing throws. Copying the list in the compact constructor prevents it."},
  {"q": "Which of these makes `new Money(5, \"usd\")` equal to `new Money(5, \"USD\")`?",
   "options": ["`public Money { this.currency = currency.toUpperCase(); }`", "`public String currency() { return currency.toUpperCase(); }`", "`public Money { currency = currency.toUpperCase(); }`", "`public Money(long minor, String currency) { currency = currency.toUpperCase(); }`"],
   "answer": 2, "why": "In the compact form you reassign the parameter and javac assigns the field afterwards. Assigning `this.currency` doesn't compile. The accessor override leaves the fields different, and `equals` compares fields. The full canonical constructor in the last option never assigns the fields, so it doesn't compile either."},
  {"q": "A Kotlin `data class Range(val lo: Int, val hi: Int) : Serializable` checks `lo <= hi` in `init`. A cache deserializes a tampered stream that says lo = 5, hi = 1. What happens?",
   "options": ["You get `Range(lo=5, hi=1)`: Java deserialization doesn't run `init`", "`InvalidObjectException`, because `init` runs during deserialization", "`IllegalArgumentException` from `require`", "`ClassCastException`, because the stream no longer matches the class"],
   "answer": 0, "why": "Java deserialization builds a plain serializable class without calling its constructor, so `init` never runs and the invalid object comes back. A Java record, or the same data class marked `@JvmRecord`, is rebuilt through its canonical constructor, and the stream is rejected with `InvalidObjectException`."},
  {"q": "From the memory model track: `record RateCard(Map<String, Long> fees)` copies the map with `Map.copyOf` in its compact constructor. A new `RateCard` is published through a plain, non-volatile field. What is guaranteed for a thread that reads the new reference?",
   "options": ["Nothing: without volatile it may see a null map", "It may see a half-built map", "Nothing, because records have no final fields", "It sees the map as the constructor left it, because record fields are final, though it may keep reading the old reference for a while"],
   "answer": 3, "why": "Record fields are private final, so final-field semantics apply: a thread that sees the reference sees the fields, and the map built in the constructor, as the constructor left them. A plain field doesn't promise when the new reference becomes visible. Publish it through a volatile field if readers must see updates promptly.",
   "from": "jmm-04"},
  {"q": "`data class Payment(val id: String) { var status = \"NEW\" }`. Payment `a` has status NEW, payment `b` has the same id and status CAPTURED. What is `a == b`?",
   "options": ["`false`, because the statuses differ", "`true`", "It doesn't compile: data classes can't have body properties", "It depends on which object was created first"],
   "answer": 1, "why": "Only primary-constructor properties take part in a data class's `equals`, `hashCode`, `toString` and `copy()`. `status` lives in the body, so Kotlin ignores it. A Java record can't have body state at all, so the question can't arise there."}
 ],
 "flashcards": [
  {"front": "What does javac generate for `record Point(int x, int y)`?", "back": "Private final fields, accessors `x()` and `y()`, a canonical constructor `Point(int, int)`, and `equals`, `hashCode` and `toString`. The class is final and extends `java.lang.Record`."},
  {"front": "In a compact constructor, how do you normalize a component?", "back": "Reassign the parameter: `currency = currency.trim();`. javac assigns the fields after the body. `this.currency = ...` doesn't compile."},
  {"front": "A record overrides its accessor to mask a card number. What does `toString` print?", "back": "The full number. The generated `toString`, `equals` and `hashCode` read the fields, not the accessors. Override `toString` instead."},
  {"front": "`record R(double d)`: is `new R(Double.NaN).equals(new R(Double.NaN))` true?", "back": "Yes. Primitive components compare with `Double.compare`, which treats NaN as equal to itself. And `0.0` doesn't equal `-0.0`."},
  {"front": "How do you make a record with a `List` component safe as a map key?", "back": "Copy it in the compact constructor: `items = List.copyOf(items);`. The copy is unmodifiable and rejects null elements."},
  {"front": "Does Java deserialization run a Kotlin data class's `init` block?", "back": "No, so a tampered stream can build an invalid object. A Java record, or a data class marked `@JvmRecord`, is rebuilt through its canonical constructor."},
  {"front": "Can you write `refund with { amount = 200; }` in Java today?", "back": "No. Derived record creation (JEP 468) is a Candidate JEP, on hold as of January 2026, and in no JDK. Write withers by hand."}
 ],
 "terms": [
  {"term": "Record component", "plain": "One of the values in a record's header. Each one gets a private final field and a public accessor."},
  {"term": "Canonical constructor", "plain": "The constructor whose parameters match the components in order. Every other way of making the record goes through it."},
  {"term": "Compact constructor", "plain": "The canonical constructor written without a parameter list. Its parameters are locals you can check and reassign; javac assigns the fields at the end."},
  {"term": "Accessor", "plain": "The generated public method that returns a component. It is named after the component: `currency()`, not `getCurrency()`."},
  {"term": "Shallow immutability", "plain": "The fields can't be reassigned, but the objects they point to may still change."},
  {"term": "Wither", "plain": "A method that returns a copy of a record with one component changed. Java has no generated ones."},
  {"term": "@JvmRecord", "plain": "A Kotlin annotation that compiles a data class to a real `java.lang.Record`."}
 ],
 "explain_back": {
  "prompt": "A teammate says: \"Our `Payout(String iban, long amount, List<String> tags)` record is immutable, so it's safe to keep in a `HashSet` and to log as it is.\" Explain, in your own words, the two ways that can go wrong and what you would change.",
  "answer": "A record is only shallowly immutable. Its fields can't be reassigned, but `tags` points to whatever list the caller passed, and if the caller keeps changing that list the record's `hashCode` changes and the set can't find it any more. Copy the list in the compact constructor with `List.copyOf`. Logging is the second problem: the generated `toString` prints every component, so the full IBAN goes into the logs. Overriding the `iban()` accessor doesn't help, because `toString` reads the field directly. Override `toString` and print a masked IBAN there."
 },
 "deeper": {
  "minutes": 10,
  "body": """Two details round out the picture.

A Java record can't hide its canonical constructor. The `Record` Javadoc says it "must provide at least as much access as the record class", and javac enforces it:

```java
public record Key(String v) { private Key { } }
// error: invalid canonical constructor in record Key
//   (attempting to assign stronger access privileges; was public)
```

```kotlin
data class Key private constructor(val v: String) {
    companion object { fun of(raw: String) = Key(raw.trim()) }
}
// warning (Kotlin 2.4): non-public primary constructor is exposed via the generated 'copy()' method
```

So validation must live inside the constructor, where nobody can bypass it. Kotlin lets you make a data class constructor private and force callers through a factory that normalizes, but `copy()` still exposes it. Kotlin 2.4.21 warns about this, says the warning becomes an error in language version 2.5, and offers `@ConsistentCopyVisibility` to make `copy()` as private as the constructor.

The second detail is about what comes after records. In a January 2026 design note, "Data-Oriented Programming for Java: Beyond Records", Brian Goetz describes the cliff you fall off when a class is almost a record: one derived field or one private cache, and you are back to writing everything by hand. The note sketches *carrier classes*, written like `class Point(int x, int y) { ... }`: a normal class with a record-style state description. The language would require the canonical constructor and the accessors and give the class a deconstruction pattern, while the class declares its own fields and need not be final. It is a design note and no JEP exists yet, so treat it as a direction for now."""
 },
 "sources": [
  {"title": "Record (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Record.html"},
  {"title": "JEP 395: Records", "url": "https://openjdk.org/jeps/395"},
  {"title": "Brian Goetz, Data Classes and Sealed Types for Java (2019)", "url": "https://github.com/openjdk/amber-docs/blob/master/site/design-notes/records-and-sealed-classes.md"},
  {"title": "Data classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/data-classes.html"},
  {"title": "Records in Kotlin (@JvmRecord)", "url": "https://kotlinlang.org/docs/jvm-records.html"}
 ]
}
out = ROOT / "content/lessons/dop-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
