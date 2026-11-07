import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """By the end of this track you can model payment data the way modern Java intends: records whose compact constructors make invalid values impossible, sealed hierarchies the compiler can check, and pattern switches with nested record patterns and guards that take that data apart. You will know exactly where each guarantee stops (shallow immutability, `null`, subtypes added after compilation) and you can say, with versions, what Project Valhalla has and hasn't shipped. Every lesson sets the Java feature next to its Kotlin counterpart (data classes, sealed interfaces, `when` with guards, `@JvmInline value class`) and says honestly which side is better at what.

You need only the syntax of both languages; the track starts from zero on records and sealed types. Install JDK 25. Records, sealed types, pattern switches and record patterns are all final in JDK 21, so the labs compile with `--release 21`. Anything newer is marked with its JDK: unnamed patterns (`_`) need JDK 22, flexible constructor bodies JDK 25, primitive patterns are still a preview, and value objects exist only as a preview in JDK 28 builds.

The labs live in `labs/modernjava`, one package per lesson (`workbench.modernjava.l01` to `l04`). Lessons 1 to 3 are in Java and lesson 4 is in Kotlin. Two of the lesson 2 tests run `javac` inside the test through `javax.tools`, so Gradle must run on a full JDK. Run `./gradlew :modernjava:test --tests 'workbench.modernjava.lNN.*'` from `labs/` until it passes, and `./gradlew :modernjava:solutionTest` to run the same tests on the reference answers. Demos for newer JDKs sit in `labs/modernjava/preview` (run them with `java preview/File.java`), and two compile-it-yourself experiments sit in `labs/modernjava/javac`."""

CHEAT = """## Which JDK has what

| Feature | Status |
|---|---|
| Records (JEP 395) | final since JDK 16 |
| Sealed classes and interfaces (JEP 409) | final since JDK 17 |
| `instanceof` patterns (JEP 394) | final since JDK 16 |
| Pattern `switch`, `case null`, guards (JEP 441) | final since JDK 21 |
| Record patterns (JEP 440) | final since JDK 21 |
| Unnamed variables and patterns, `_` | preview in 21, final from JDK 22 |
| Flexible constructor bodies (statements before `this(...)`) | final from JDK 25 |
| Primitive types in patterns | preview in every JDK from 23 to 27, still preview |
| Derived record creation, `r with { ... }` (JEP 468) | Candidate JEP, on hold, in no JDK |
| Value objects, `value record` (JEP 401) | preview in JDK 28 (in development, scheduled March 2027) |
| "missing patterns:" list in exhaustiveness errors | javac from JDK 27 |

## Records

```java
public record Money(long minor, String currency) {
    public Money {                                          // compact canonical constructor
        Objects.requireNonNull(currency, "currency");
        currency = currency.trim().toUpperCase(Locale.ROOT);    // reassign the parameter
        if (minor < 0) throw new IllegalArgumentException("negative amount");
    }                                                       // javac assigns the fields here
    public Money withMinor(long m) { return new Money(m, currency); }   // a wither
}
record Batch(String id, List<String> ids) { Batch { ids = List.copyOf(ids); } }   // defensive copy
```

```kotlin
data class Money(val minor: Long, val currency: String) {
    init { require(minor >= 0) { "negative amount" } }      // runs on every construction and copy()
    companion object { fun of(minor: Long, ccy: String) = Money(minor, ccy.trim().uppercase()) }   // normalize here
}
val smaller = money.copy(minor = 500)                       // generated, shallow, runs init
```

- Generated: private final fields, accessors (`minor()`, no `get`), one canonical constructor, `equals`/`hashCode`/`toString`.
- No instance fields in the body, no `extends`. Static members, methods and nested types are fine.
- `equals` compares every component: `Objects.equals` for references, `compare` for primitives (`NaN` equals `NaN`, `0.0` doesn't equal `-0.0`). Arrays compare by reference.
- Shallow: copy `List`, `Set` and `Map` components with `copyOf`, or a mutated key is lost in a `HashSet`.
- The generated methods read fields, not accessors. To hide a secret, override `toString`.
- Java deserialization runs a record's canonical constructor. It skips a Kotlin data class's `init`, unless the class is `@JvmRecord`.
- Records are identity objects: `==` compares references, `synchronized` works.

## Sealed types

| Subtype modifier | Meaning |
|---|---|
| `final` (records, enums are already) | no subtypes |
| `sealed ... permits ...` | a closed list one level down |
| `non-sealed` | open again; one case still covers the branch |

| Rule | Java | Kotlin |
|---|---|---|
| Where subtypes live | same module; on the class path, same package | same package and same module |
| The list | `permits`, or inferred from one source file | whatever is declared in that package and module |
| Concrete parent | possible, and it is a value of its own: make it abstract | a sealed class is always abstract |
| Enforced by | javac, and the JVM at load time (`PermittedSubclasses`) | kotlinc; with a JDK 17+ target the same class-file attribute |

## Pattern switch

```java
return switch (charge) {
    case Charge(Money(long m, var ccy), Card(var net, var corp), var r) when net == Network.AMEX -> bps(m, 350);
    case Charge(Money(long m, var ccy), Card c, var r) -> bps(m, 150);   // unguarded: closes the Card family
    case Charge(var a, BankTransfer t, var r) -> 20;
    case Charge(var a, Wallet w, var r) -> 0;
};                                                                       // no default over a sealed type
```

```kotlin
return when (val method = charge.method) {
    is Card if method.network == Network.AMEX -> bps(charge.amount.minor, 350)   // guard: Kotlin 2.2+
    is Card -> bps(charge.amount.minor, 150)
    is BankTransfer -> 20
    is Wallet -> 0
}
```

- Cases run top to bottom; the first match wins. Guards never count toward exhaustiveness.
- A null selector throws `NullPointerException` unless there is `case null`. `default` doesn't catch null.
- A nested type pattern (`Point p`) matches a null component; a nested record pattern (`Point(var x, var y)`) doesn't.
- An old client meeting a subtype or enum constant added later throws `MatchException` (Kotlin: `NoWhenBranchMatchedException`).
- Several patterns in one arm only with `_`: `case Capture _, Refund _ ->` (JDK 22+).
- Kotlin destructuring `val (a, b) = x` goes by position and swaps silently. kotlinc has no dominance check.

| javac says | It means |
|---|---|
| `the switch expression does not cover all possible input values` | a permitted subtype (or combination) has no unguarded case |
| `this case label is dominated by a preceding case label` | an earlier unguarded case already matches everything this one could |
| `illegal fall-through from a pattern` | several patterns with bindings in one arm |
| `class is not allowed to extend sealed class: X (as it is not listed in its 'permits' clause)` | a subtype missing from `permits` |
| `sealed, non-sealed or final modifiers expected` | a permitted subtype without its modifier |
| `class X in unnamed module cannot extend a sealed class in a different package` | split packages on the class path |

## Data-oriented design checklist

- One record per valid combination, under a sealed interface. No shared bag of nullable fields.
- Constructors refuse bad values; the type system refuses bad shapes.
- Parse untrusted input once, at the edge, into the model or a rejection. Trust the types behind the edge.
- Business operations are functions with one exhaustive switch each. Keep methods for open, plug-in hierarchies and for behavior about the value itself.
- Don't depend on record identity, so `value` (JDK 28 preview) can be a one-word change later."""

RECAP = [
 "A record is a final, transparent carrier: javac generates fields, accessors, one canonical constructor and the Object methods from the header, so they can't drift apart.",
 "The compact constructor is the one door: `new`, factories, other constructors, withers and Java deserialization all go through it. Kotlin's `init` is the twin, but it can't normalize a parameter and Java deserialization skips it.",
 "Records are only shallowly immutable and their generated methods read fields: copy collections with `copyOf`, and mask secrets in `toString`, not in the accessor.",
 "A sealed type names its permitted subtypes; each one is final, sealed or non-sealed. On the class path they must share a package. A concrete sealed parent is a value of its own.",
 "A switch over a sealed type with no default is checked by the compiler, so adding a subtype turns every forgotten switch into a compile error. A default hides it.",
 "Record patterns take data apart in the case label. Cases run in order, guards don't count toward exhaustiveness, and javac rejects dominated cases, which kotlinc doesn't.",
 "Exhaustive is a compile-time promise: null needs `case null`, and a subtype added after compilation makes an old switch throw `MatchException`.",
 "Data-oriented code models closed domains as records and sealed types, validates at the edge, and writes operations as functions. It makes new operations cheap and new types loud.",
 "Project Valhalla's value objects are a preview in JDK 28, not in 25 to 27. Records are identity objects; JEP 468 withers are on hold; null-restricted types are still drafts."
]

QUIZ = [
 {"q": "A `record Payout(String iban, long amountMinor)` is logged in full at every retry. A teammate overrides `iban()` to return a masked value. What do the logs show now?",
  "options": ["The masked IBAN, because toString calls the accessor", "The full IBAN, because the generated toString reads the field", "Nothing: overriding an accessor turns off the generated toString", "A compile error: accessors can't be overridden"],
  "answer": 1, "why": "The generated `toString`, `equals` and `hashCode` get the private fields directly, so masking the accessor changes nothing in the logs and breaks the copy rule of `equals`. Override `toString` instead."},
 {"q": "Which is the right place to turn `\" eur \"` into `\"EUR\"` so that no `Money` anywhere holds the raw value?",
  "options": ["A static factory `Money.of`", "The compact canonical constructor, by reassigning the parameter", "The `currency()` accessor", "A Jackson deserializer"],
  "answer": 1, "why": "Every construction goes through the canonical constructor, including `new`, withers and Java deserialization. A factory can be bypassed with `new`, the accessor leaves the field raw (and `equals` compares fields), and a deserializer covers only one entry point."},
 {"q": "A Kotlin `data class Range(val lo: Int, val hi: Int) : Serializable` checks `lo <= hi` in `init`. A tampered Java-serialized stream says lo = 5, hi = 1. Which change makes deserialization reject it?",
  "options": ["Mark the class `@JvmRecord`", "Add `@Volatile` to both properties", "Make the class `open`", "Nothing can: Java deserialization never runs constructors"],
  "answer": 0, "why": "Java deserialization skips a plain data class's `init`, but a `@JvmRecord` data class is a real record, and records are rebuilt through their canonical constructor, so the check runs and the stream is rejected with `InvalidObjectException`."},
 {"q": "Partner teams must be able to add payment methods in their own packages, while your switches over `PaymentMethod` stay exhaustive with no default. How do you declare the partner branch?",
  "options": ["`final class PartnerMethod`", "`sealed interface PartnerMethod` with an empty permits list", "`non-sealed interface PartnerMethod extends PaymentMethod`", "Drop `sealed` from `PaymentMethod` altogether"],
  "answer": 2, "why": "`non-sealed` reopens one branch to any class, and a single `case PartnerMethod p` still covers every partner implementation, so the switch stays exhaustive. Dropping `sealed` would lose exhaustiveness for every branch."},
 {"q": "Your service runs on the class path. `sealed interface LedgerEvent` is in `com.acme.ledger` and its records are in `com.acme.ledger.events`. What happens?",
  "options": ["It compiles: the packages share a prefix", "javac rejects it: in the unnamed module the permitted subtypes must be in the same package", "It compiles, but the JVM won't load the records", "It compiles only with fully qualified names in `permits`"],
  "answer": 1, "why": "Java packages have no hierarchy, so these are two unrelated packages. Without a named module javac reports that the class `cannot extend a sealed class in a different package`. Move the records, or put both packages in one module."},
 {"q": "The cases are `case Card c when c.corporate() -> 290;`, `case Card c when c.network() == AMEX -> 350;`, `case Card c -> 30;`. What does javac do, and what fee does a corporate AMEX card get?",
  "options": ["javac rejects the second case as dominated; no fee", "It compiles, and the card pays 350 because the AMEX rule is more specific", "It compiles, and the card pays 290 because the first matching case wins", "javac rejects the switch as not exhaustive"],
  "answer": 2, "why": "Guarded cases never dominate, so javac accepts any order of them, and the switch is exhaustive thanks to the unguarded `case Card c`. At run time the first case whose pattern and guard both match wins: the corporate rule."},
 {"q": "`case Line(Point(var x1, var y1), Point to) -> ...` is the only case of an exhaustive switch over `Line`. What happens for `new Line(null, new Point(1, 1))`?",
  "options": ["The case matches with x1 and y1 left at 0", "NullPointerException from the accessor", "MatchException, because a nested record pattern never matches null", "It doesn't compile: the switch isn't exhaustive"],
  "answer": 2, "why": "javac treats a null nested inside the selector as part of the remainder, so the switch compiles. At run time `Point(var x1, var y1)` doesn't match null, no case matches, and the switch throws `MatchException`. A type pattern `Point from` in that position would have matched the null."},
 {"q": "A client jar was compiled against `enum Level { LOW, HIGH }` and switches over it with no default. Production runs a newer library where `Level` also has `CRITICAL`. The client gets `CRITICAL`. What happens?",
  "options": ["The switch returns the value of its last case", "MatchException", "The JVM refuses to load the client class", "NullPointerException"],
  "answer": 1, "why": "An exhaustive switch over an enum, like one over a sealed type, has a synthetic arm for values it didn't know at compile time, and that arm throws `MatchException`. Recompiling the client turns the gap into a compile error."},
 {"q": "Every month the team adds a new report over the five fixed kinds of ledger entry: a tax export, a reconciliation view, a fee summary. Which design keeps each new report to one place?",
  "options": ["A method per report on every entry class", "A sealed interface of records, with each report as one function that switches over the entries", "One class with a `type` string and nullable fields", "A `default` branch in every switch for future entry kinds"],
  "answer": 1, "why": "The operations grow and the types don't, so the data-oriented side of the expression problem wins: each report is a new function that touches no existing code. Methods on the classes would mean editing all five classes for every report."},
 {"q": "Your team wants to mark `Money` as a `value record` for performance on the JDK 25 servers. What is accurate?",
  "options": ["It works on JDK 25 with `--enable-preview`", "Value objects are only a preview in JDK 28 builds; and a `long` plus a reference is 64 bits or more of fields, which JDK 28 doesn't normally flatten anyway", "Records are already value objects, so it changes nothing", "It works on JDK 25, but only in Kotlin with `@JvmInline`"],
  "answer": 1, "why": "JEP 401 isn't in JDK 25, 26 or 27; it is a preview in JDK 28, which is still in development. Even there, flattened values must be read atomically and allow null, so values with 64 bits or more of field data are not normally flattened. Kotlin's `@JvmInline value class` is a separate compile-time trick with one property."}
]

T = {"id": "dop", "intro": INTRO, "cheatsheet": CHEAT, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/dop.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
