import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/modernjava/src"
P = "java/workbench/modernjava/l03"
D = "java/workbench/modernjava/l03/demo"
K = "kotlin/workbench/modernjava/l03/demo"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :modernjava:demo -Pmain=workbench.modernjava.l03.demo."


def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{D}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{D}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{K}/{name}.kt"}}


FIG = (
    '<svg viewBox="0 0 700 270" role="img" aria-label="The record pattern Charge(Money(long m, var ccy), Card(var net, var corp), var r) '
    'matched against a charge: each nested pattern reads one component through its accessor and binds m, ccy, net, corp and r">'
    '<text class="t-s t-code" x="350" y="24" text-anchor="middle">case Charge(Money(long m, var ccy), Card(var net, var corp), var r)</text>'
    '<rect class="box-a" x="290" y="46" width="120" height="38" rx="8"/>'
    '<text class="t t-code" x="350" y="70" text-anchor="middle">Charge</text>'
    '<line class="ln" x1="330" y1="84" x2="125" y2="130" marker-end="url(#arr)"/>'
    '<line class="ln" x1="350" y1="84" x2="350" y2="130" marker-end="url(#arr)"/>'
    '<line class="ln" x1="370" y1="84" x2="575" y2="130" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="205" y="102" text-anchor="middle">amount()</text>'
    '<text class="t-s t-m" x="358" y="112">method()</text>'
    '<text class="t-s t-m" x="500" y="102" text-anchor="middle">region()</text>'
    '<rect class="box" x="20" y="132" width="210" height="44" rx="8"/>'
    '<text class="t-s t-code" x="125" y="159" text-anchor="middle">Money(10_000, "EUR")</text>'
    '<rect class="box" x="250" y="132" width="200" height="44" rx="8"/>'
    '<text class="t-s t-code" x="350" y="159" text-anchor="middle">Card(AMEX, false)</text>'
    '<rect class="box" x="470" y="132" width="210" height="44" rx="8"/>'
    '<text class="t-s t-code" x="575" y="159" text-anchor="middle">Region.EEA</text>'
    '<line class="ln-a" x1="125" y1="176" x2="125" y2="196" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="350" y1="176" x2="350" y2="196" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="575" y1="176" x2="575" y2="196" marker-end="url(#arr)"/>'
    '<text class="t-s t-ok" x="125" y="214" text-anchor="middle">m = 10000, ccy = "EUR"</text>'
    '<text class="t-s t-ok" x="350" y="214" text-anchor="middle">net = AMEX, corp = false</text>'
    '<text class="t-s t-ok" x="575" y="214" text-anchor="middle">r = EEA</text>'
    '<text class="t-s t-m" x="350" y="252" text-anchor="middle">each nested pattern calls one accessor, checks the type, and binds the parts</text>'
    '</svg>'
)

S1 = """Pattern matching came to Java in steps. JDK 16 made `instanceof` patterns final (JEP 394): the type test and the cast become one, and the binding is in scope wherever the test is known to have passed.

```java
if (!(o instanceof Card c)) return "not a card";
return "last four: " + c.last4();          // c is in scope: the test can't have failed here
```

```kotlin
if (o !is Method.Card) return "not a card"
return "last four: ${o.last4}"             // smart cast: o is a Card from here on
```

JDK 21 made pattern `switch` final (JEP 441), together with record patterns (JEP 440). It's tempting to read a pattern switch as a tidier `if`/`else if` chain. It is more than that, and the differences are the reason to prefer it:

- javac checks that it is exhaustive. An `instanceof` chain that forgets `Wallet` compiles without a word and falls into its final `else`. The switch that forgets it fails with `the switch expression does not cover all possible input values`. A pattern switch used as a statement must be exhaustive too, and the message then says `switch statement`.
- javac checks dominance: a case that can never match is a compile error (section 3).
- It has defined `null` rules (section 4).
- It compiles to one `invokedynamic` call to `SwitchBootstraps.typeSwitch`, which picks the case, plus a synthetic arm that throws `MatchException` if no case matches at run time.

Kotlin has had most of this for years. A `when` with a subject checks exhaustiveness over a sealed type, whether you use it as an expression or a statement, and smart casts merge the `is` check and the cast. With the JDK 21 target, kotlinc 2.4 even compiles that `when` to the same `typeSwitch` call; its fallback arm throws `NoWhenBranchMatchedException` instead. What Kotlin doesn't have is the subject of the next section."""

S2 = """A type pattern tests a type and binds one variable. A record pattern also takes the record apart, through its accessors, and each part can be a pattern too. Here is the first fee rule from this lesson's lab, next to the closest Kotlin:

```java
return switch (charge) {
    case Charge(Money(long m, var ccy), Card(var net, var corp), var r) when net == Network.AMEX -> bps(m, 350);
    case Charge(Money(long m, var ccy), Card(var net, var corp), var r) when corp -> bps(m, 290);
    // ...
};
```

```kotlin
val m = charge.amount.minor
return when (val method = charge.method) {    // pick the nested part out first
    is Card if method.network == Network.AMEX -> bps(m, 350)
    is Card if method.corporate -> bps(m, 290)
    // ...
}
```

Read the Java label from the outside in. The selector must be a `Charge`. Its `amount()` must match `Money(long m, var ccy)`, which binds `m` and `ccy`. Its `method()` must be a `Card`, which binds `net` and `corp`. And `region()` binds to `r`. With `var`, javac infers each type from the record's components. Patterns are positional and type-checked: put `String x` where a record has an `int` and javac stops with `incompatible types: int cannot be converted to String`. Generic records work too. Over `sealed interface Result<T>`, the case `Ok<T>(var v)` binds `v` as a `T`. Record patterns also work in `instanceof`, as in `if (o instanceof Line(Point(var x, var y), var to) && x == 0)`.

Kotlin has no record patterns. The closest tools are smart casts on nested properties, as in the twin above, and positional destructuring, `val (from, to) = line`, through `component1()` and `component2()`. Destructuring has a trap Java's patterns mostly avoid: it goes by position, not by name. With `data class Payment(val id: String, val amountMinor: Long)`, the line `val (amountMinor, id) = payment` compiles without a warning and puts the id into `amountMinor`. Kotlin 2.3.20 added name-based destructuring as an Experimental feature, behind `-Xname-based-destructuring`; its `name-mismatch` mode warns about exactly this line. Java's record patterns are positional as well, but every component is type-checked, so most swaps fail to compile. Two `var` bindings of the same type can still be swapped silently, so keep the record header in front of you."""

S3 = """Cases are tried from the top, and the first one whose pattern matches and whose guard is true wins. The guard is the `when` clause after the pattern. That makes order part of the meaning. A corporate AMEX card matches both of the first two lines below, so whichever comes first sets its fee:

```java
case CardCharge(var net, var corp, var amt) when net == Network.AMEX -> amt * 350 / 10_000;
case CardCharge(var net, var corp, var amt) when corp -> amt * 290 / 10_000;
case CardCharge(var net, var corp, var amt) -> amt * 30 / 10_000;
```

```kotlin
is Charge.Card if c.network == Network.AMEX -> c.amountMinor * 350 / 10_000
is Charge.Card if c.corporate -> c.amountMinor * 290 / 10_000
is Charge.Card -> c.amountMinor * 30 / 10_000
```

Guards don't count toward exhaustiveness, in either language. The compiler can't prove that a set of guards covers every value, so a family of guarded cases must end with an unguarded case of the same pattern. Delete the last line above and javac says the switch doesn't cover all possible input values, while kotlinc asks you to `Add the 'is Card' branch`.

javac also rejects a case that can never be reached: `this case label is dominated by a preceding case label`. That happens when an earlier unguarded case already matches everything the later one could: `case String s` after `case CharSequence cs`, `case Integer i when i > 0` after an unguarded `case Integer i`, a constant `case 1` after `case Integer i`, or any pattern after `default`. A guarded case never dominates, which is why javac accepts the two guarded card rules in either order. Only your tests notice the difference. kotlinc has no dominance check at all: put the unguarded `is Charge.Card` first and it compiles without a warning, and every card pays 0.3%. Kotlin guards (`is T if condition`) have been stable since Kotlin 2.2; one limit is that a guard can't follow several conditions joined by commas.

Several patterns can share one arm only if they bind nothing. On JDK 21 that rule makes such arms awkward: `case Capture c, Refund r ->` fails with `illegal fall-through from a pattern`, so you write two arms. JDK 22 made unnamed patterns final, and `case Capture _, Refund _ ->` is legal. `_` also stands in for a component you don't need, as in `case Authorize(var code, _)`. On JDK 21 it is a preview feature, and javac stops with `unnamed variables are a preview feature and are disabled by default`."""

S4 = """`switch` has always thrown `NullPointerException` on a null selector, and a pattern switch keeps that rule unless you opt in with `case null`:

```java
return switch (currency) {
    case null -> "missing";
    case "EUR" -> "euro";
    default -> "other";          // default alone does not catch null
};
```

```kotlin
return when (currency) {         // currency is a String?
    null -> "missing"
    "EUR" -> "euro"
    else -> "other"              // without the null branch, null lands here
}
```

`case null, default ->` handles both in one arm. For most code, the OpenJDK guide on sealed switches prefers something simpler: reject null before the switch with `Objects.requireNonNull`, because a null that reaches business logic is a bug somewhere upstream. Kotlin settles the question in the type system. A `when` over a `String?` must handle null somewhere (kotlinc says `Add the 'null' branch or an 'else' branch.` if it doesn't), and nothing throws.

Inside a record pattern, null follows a rule that surprises everyone once. A nested record pattern never matches null, but a nested type pattern that covers the whole component type does. So with `case Line(Point(var x1, var y1), Point(var x2, var y2)) when x1 == x2` first and `case Line(Point from, Point to)` second, a `Line` whose start is null skips the first case and lands in the second, with `from` bound to null. Change the second case to `Line(Point(var a, var b), Point to)` and javac still calls the switch exhaustive, but that `Line` now matches nothing and the switch throws `MatchException`.

That points at the bigger limit: exhaustive is a compile-time promise. javac checks the switch against the subtypes it can see when it compiles. The values it can't see, which the Amber design notes call the remainder, are handled at run time. Compile a client against `Status permits Active, Closed`, then recompile only the hierarchy with a third status, `Frozen`, and run the old client: its switch throws `java.lang.MatchException`. An enum switch with no default does the same when it meets a constant added later. The old Kotlin `when` throws `kotlin.NoWhenBranchMatchedException`. You don't write code for the remainder, but in a deployment that mixes old and new jars, this is the exception you will see. Recompile the client and javac turns it back into a compile error."""

L = {
 "id": "dop-03",
 "title": "Pattern matching with switch and record patterns",
 "minutes": 40,
 "goal": "By the end you can write an exhaustive switch with nested record patterns and guards in the right order, predict what it does with null and with a subtype added after compilation, and read javac's exhaustiveness and dominance errors.",
 "warmup": {
  "q": "A switch has these cases, in this order: `case Card c when c.corporate() -> 290;`, then `case Card c when c.network() == AMEX -> 350;`, then `case Card c -> 30;`. What fee does a corporate AMEX card get?",
  "options": ["350, because the more specific rule wins",
              "290, because cases are tried from the top and the first match wins",
              "It doesn't compile: two guarded cases for the same type are ambiguous",
              "It doesn't compile: the AMEX case is dominated by the corporate case"],
  "answer": 1,
  "why": "Java tries the cases in order and runs the first one whose pattern matches and whose guard is true. Both guards are true for a corporate AMEX card, so the corporate rule wins. javac doesn't compare guards, so it can't tell that the AMEX rule is shadowed for corporate cards: a guarded case never dominates another. Put the AMEX rule first."
 },
 "sections": [
  {
   "h": "A pattern switch is checked, an instanceof chain is not",
   "body": S1,
   "try": {
    "title": "See which one the compiler catches",
    "minutes": 5,
    "steps": [
     "Run `PatternBasics` (or `PatternBasicsKt`) with the command below.",
     "Delete the `Wallet` line from `viaChain` and run. Put it back, then delete the `Wallet` case from `viaSwitch` and run again. Which mistake did the compiler catch?",
     "From `labs/`, run `javap -c -p modernjava/build/classes/java/demo/workbench/modernjava/l03/demo/PatternBasics.class` and find `typeSwitch` and `MatchException` in `viaSwitch`.",
     "Run the same `javap` on `modernjava/build/classes/kotlin/demo/workbench/modernjava/l03/demo/PatternBasicsKt.class` and look at `viaWhen`."
    ],
    "code": demo("PatternBasics"),
    "expect": "Both versions print the same three lines and `last four: 1111, not a card`. Without its `Wallet` branch the chain still compiles, and the run crashes on the wallet with the chain's `IllegalStateException`. Without its `Wallet` case the switch doesn't compile: `the switch expression does not cover all possible input values` (kotlinc: `Add the 'is Wallet' branch or an 'else' branch.`). In the bytecode, `viaSwitch` has `invokedynamic ... typeSwitch` and `new java/lang/MatchException`; the Kotlin `viaWhen` has the same `typeSwitch` call and `new kotlin/NoWhenBranchMatchedException`."
   },
   "refs": [
    {"title": "JEP 441: Pattern Matching for switch", "url": "https://openjdk.org/jeps/441", "kind": "read"}
   ]
  },
  {
   "h": "Record patterns take the data apart in the label",
   "body": S2,
   "figure": {"svg": FIG, "caption": "One record pattern, three levels deep: the charge, its components, and the parts of each component, all bound in the case label."},
   "try": {
    "title": "Take a line apart",
    "minutes": 4,
    "steps": [
     "Predict the third line of output, then run `RecordPatterns`.",
     "In `describe`, change `Point(int x2, int y2)` to `Point(String x2, int y2)` and run. Read the error, then undo it.",
     "Run the Kotlin twin, `RecordPatternsKt`, and read its last line."
    ],
    "code": demo("RecordPatterns"),
    "expect": "`vertical at x=1 len 5`, `horizontal at y=3`, `diagonal Point[x=0, y=0]->Point[x=2, y=2]`, then `ok [1, 2]`, `err boom caused by RuntimeException` and `from origin to Point[x=9, y=9]`. The `String` change fails with `incompatible types: int cannot be converted to String`. The Kotlin twin prints the same results with smart casts, and then `swapped names: amountMinor=p1 id=500`: positional destructuring put the id into `amountMinor` without a warning."
   },
   "refs": [
    {"title": "JEP 440: Record Patterns", "url": "https://openjdk.org/jeps/440", "kind": "read"},
    {"title": "Destructuring declarations (Kotlin docs)", "url": "https://kotlinlang.org/docs/destructuring-declarations.html", "kind": "docs"}
   ]
  },
  {
   "h": "Guards, order and dominance",
   "body": S3,
   "try": {
    "title": "Reorder the fee rules",
    "minutes": 6,
    "steps": [
     "Run `GuardsDemo` and note the fee for the corporate AMEX card.",
     "Swap the lines marked `// 1` and `// 2`. Predict which fee changes, then run.",
     "Undo. Move line `// 3` above line `// 1` and run. Do the same in `GuardsDemoKt`.",
     "Undo. Delete line `// 3` and run both versions.",
     "If you have JDK 22 or newer, run `java preview/UnnamedPatterns.java` from `labs/modernjava`, then try the same file on JDK 21."
    ],
    "code": demo("GuardsDemo"),
    "expect": "The corporate AMEX card pays 350. After the swap it pays 290 and nothing else changes: the corporate rule now matches it first. With line 3 on top, javac rejects lines 1 and 2 with `this case label is dominated by a preceding case label`, while the Kotlin version compiles and charges every card 30. Without line 3, javac reports `the switch expression does not cover all possible input values` and kotlinc asks for `the 'is Card' branch`. On JDK 22+ the preview file prints `authorize with A1B2C3`, `fail: insufficient funds` and `not allowed yet` twice; JDK 21 rejects the `_`."
   },
   "refs": [
    {"title": "Guard conditions in when expressions (Kotlin docs)", "url": "https://kotlinlang.org/docs/control-flow.html", "kind": "docs"}
   ]
  },
  {
   "h": "Null, default and the remainder",
   "body": S4,
   "try": {
    "title": "Feed a switch null, then a stranger",
    "minutes": 6,
    "steps": [
     "Run `NullDemo` and `NullDemoKt` and compare their first lines.",
     "In the Java `describe`, change `case Line(Point from, Point to)` to `case Line(Point(var a, var b), Point to)` (and use `a` and `b` in the text). Predict: does it compile? What happens to the line with a null start?",
     "Run the separate-compilation experiment in `labs/modernjava/javac/remainder`. The five commands are at the top of `Client.java`."
    ],
    "code": demo("NullDemo"),
    "expect": "Java prints `plain(null): NullPointerException`; Kotlin prints `plainWhen(null): other`, because its `when` compares with `equals` and the type allowed null. Both print `missing`, then `null or other` twice, then a line whose start is `null`. After the change in step 2 the switch still compiles, and the null-start line throws `java.lang.MatchException`. The experiment prints `active, priority 1`, then `sealed switch: java.lang.MatchException` and `enum switch: java.lang.MatchException` from the old client; recompiling it gives two `does not cover all possible input values` errors."
   },
   "refs": [
    {"title": "MatchException (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/MatchException.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A pattern switch is the routing table in a card network's switch centre. Each row says \"if the message looks like this, with these fields, send it there\", and messages are checked against the rows from the top. Record patterns let a row look inside the message (BIN range, currency, merchant category) instead of only at its type, and a guard is an extra condition on a row. The network also proves that every possible message has a row, so nothing is dropped. The analogy breaks at the edges: a real routing table can fall back to a default route without anyone noticing a gap, while javac refuses a switch with a gap, and a message type invented after the table was built makes the Java switch throw instead of routing it somewhere.",
 "in_your_world": "Most code that consumes payment events or issuer responses is a dispatch on shape: \"a refund of a card payment over 500 EUR goes to manual review\", \"a decline with a retryable code goes back on the queue\". Written as nested `instanceof` checks and casts, those rules hide gaps; written as one switch with record patterns, javac finds the missing shapes and the order of the rules is visible in one place. Two production habits follow from this lesson. Validate non-null at the edge (the REST resource, the Kafka deserializer) with `Objects.requireNonNull`, so switches never see null. And treat a `MatchException` in the logs after a deploy as \"a service was built against an older version of a shared model jar\": rebuild it, and the compiler will show you the cases to add.",
 "mistake": "The mistake that ships is a guarded rule placed after a broader guarded rule, such as the corporate-card rate above the AMEX rate. Both cases are guarded, so javac accepts either order and reports nothing, and every corporate AMEX card is charged the corporate fee. People make it because they read the switch as a set of rules, when it is an ordered list. Write the most specific rule first, end each family with an unguarded case, and give every rule a test case that matches more than one guard, as the lab's `ruleOrder` test does.",
 "compare": {
  "title": "The fee rules in Java and Kotlin",
  "java": {"title": "Fees.java", "src": "static long fee(Charge charge) {\n    return switch (charge) {\n        case Charge(Money(long m, var ccy), Card(var net, var corp), var r) when net == Network.AMEX -> bps(m, 350);\n        case Charge(Money(long m, var ccy), Card(var net, var corp), var r) when corp -> bps(m, 290);\n        case Charge(Money(long m, var ccy), Card c, var r) when r == Region.EEA || r == Region.UK -> bps(m, 30);\n        case Charge(Money(long m, var ccy), Card c, var r) -> bps(m, 150);\n        case Charge(var amount, BankTransfer(var instant), var r) when instant -> 50;\n        case Charge(var amount, BankTransfer t, var r) -> 20;\n        case Charge(Money(long m, var ccy), Wallet w, var r) when m < 1_000 -> 0;\n        case Charge(Money(long m, var ccy), Wallet w, var r) -> bps(m, 100);\n    };\n}"},
  "kotlin": {"title": "Fees.kt", "src": "fun fee(charge: Charge): Long {\n    val m = charge.amount.minor\n    val r = charge.region\n    return when (val method = charge.method) {\n        is Card if method.network == Network.AMEX -> bps(m, 350)\n        is Card if method.corporate -> bps(m, 290)\n        is Card if r == Region.EEA || r == Region.UK -> bps(m, 30)\n        is Card -> bps(m, 150)\n        is BankTransfer if method.instant -> 50\n        is BankTransfer -> 20\n        is Wallet if m < 1_000 -> 0\n        is Wallet -> bps(m, 100)\n    }\n}"},
  "note": "The rules, the order and the exhaustiveness check are the same in both: the first matching branch wins, guards don't count toward exhaustiveness, and neither version needs a default. The difference is where the data comes apart. Java's record patterns reach into `Charge`, `Money` and `Card` in the label and bind the parts. Kotlin can only test the type of the value it switches on, so the twin pulls `method` out first, switches on that, and reads `charge.amount.minor` by hand. javac also checks dominance, which kotlinc doesn't, and Java's switch has explicit null rules, where Kotlin leaves null to the type system."
 },
 "worked": {
  "title": "Rewrite a refund router as one switch",
  "steps": [
   {"say": "This code decides how a refund is paid back. It compiles, it has tests, and it has a bug the compiler can't see. Read it and look for a payment method it forgets.",
    "code": "static String refundRoute(Event event) {\n    if (event instanceof Refund r) {\n        if (r.payment().method() instanceof Card c) {\n            if (c.network() == Network.AMEX && r.amountMinor() > 50_000) return \"manual review\";\n            return \"card refund\";\n        }\n        if (r.payment().method() instanceof BankTransfer) return \"bank refund\";\n    }\n    return \"ignore\";\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "fun refundRoute(event: Event): String {\n    if (event is Refund) {\n        val method = event.payment.method\n        if (method is Card) {\n            if (method.network == Network.AMEX && event.amountMinor > 50_000) return \"manual review\"\n            return \"card refund\"\n        }\n        if (method is BankTransfer) return \"bank refund\"\n    }\n    return \"ignore\"\n}"},
   {"say": "Name the shapes you care about, most specific first, and let each label take the event apart. `Event` is sealed (`Refund`, `Capture`) and so is `Method`, so the switch needs no default.",
    "code": "static String refundRoute(Event event) {\n    return switch (event) {\n        // 1. the special case first\n        case Refund(Payment(var id, Card(var net, var corp)), long amt) when net == Network.AMEX && amt > 50_000 -> \"manual review\";\n        // 2. then the general cases, one per method\n        case Refund(Payment(var id, Card c), long amt) -> \"card refund\";\n        case Refund(Payment(var id, BankTransfer t), long amt) -> \"bank refund\";\n        // 3. events that need no refund\n        case Capture c -> \"ignore\";\n    };\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "fun refundRoute(event: Event): String = when (event) {\n    is Refund -> when (val method = event.payment.method) {\n        // 1. the special case first\n        is Card if method.network == Network.AMEX && event.amountMinor > 50_000 -> \"manual review\"\n        // 2. then the general cases, one per method\n        is Card -> \"card refund\"\n        is BankTransfer -> \"bank refund\"\n    }\n    // 3. events that need no refund\n    is Capture -> \"ignore\"\n}"},
   {"say": "That doesn't compile, in either language: `the switch expression does not cover all possible input values` (kotlinc: `Add the 'is Wallet' branch`). A refund of a wallet payment matches no case. The old chain had the same gap and returned \"ignore\", so wallet refunds were silently never paid. The compiler found the bug the tests missed. Add the case.",
    "code": "        case Refund(Payment(var id, Wallet w), long amt) -> \"wallet refund\";   // the case the chain forgot", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "        is Wallet -> \"wallet refund\"                                         // the case the chain forgot"},
   {"say": "On JDK 22 or newer, replace the bindings you never use with `_`, so a reader sees at a glance which parts each rule depends on. Kotlin's version already names only what it reads.",
    "code": "// JDK 22+\ncase Refund(Payment(_, Card(var net, _)), long amt) when net == Network.AMEX && amt > 50_000 -> \"manual review\";\ncase Refund(Payment(_, Card _), _) -> \"card refund\";\ncase Refund(Payment(_, BankTransfer _), _) -> \"bank refund\";\ncase Refund(Payment(_, Wallet _), _) -> \"wallet refund\";\ncase Capture _ -> \"ignore\";", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "// Kotlin uses _ only for unused lambda parameters and destructured components\nval (_, amountMinor) = refund      // skip the payment, keep the amount"}
  ]
 },
 "lab": {
  "title": "A fee calculator over a sealed hierarchy",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/Fees.java"],
  "run": "./gradlew :modernjava:test --tests 'workbench.modernjava.l03.*'",
  "steps": [
   "Run the tests: all eight fail. Read the rule list in the Javadoc of `fee`. The order of the rules is the order of your cases.",
   "Write `fee` as one `switch` over the `Charge`, with record patterns and guards and no `default`. Start with the AMEX rule, and run the tests after every two or three cases.",
   "Write `label`. It needs a `case null`, and the wallet needs care: what does `Wallet(String p)` bind when the provider is null?",
   "When all eight pass, swap your AMEX and corporate cases and run the tests again. Which test catches it? Swap them back.",
   "Delete your last, unguarded card case and compile. Read the error, then put it back."
  ],
  "hints": [
   "The first case can be `case Charge(Money(long m, var ccy), Card(var net, var corp), var r) when net == Network.AMEX -> bps(m, 350);`.",
   "Each method family must end with an unguarded case: one for `Card`, one for `BankTransfer`, one for `Wallet`. Otherwise javac says the switch doesn't cover all possible input values.",
   "`fee` doesn't need `case null`: a pattern switch without one throws `NullPointerException`, which is what the test expects.",
   "`Wallet(String p)` matches a wallet whose provider is null, with `p` bound to null. Put `case Wallet(String p) when p == null` before the general wallet case."
  ],
  "done_when": "All eight tests in `FeesTest` pass."
 },
 "drill": {
  "title": "A guarded switch from memory",
  "minutes": 5,
  "prompt": "Close this page. Given `sealed interface Settlement permits Settled, Failed`, `record Settled(long amountMinor)` and `record Failed(String code, boolean retryable)`, write `nextStep(Settlement s)`: settlements of 1,000,000 minor units or more return `\"review\"`, other settlements `\"done\"`, retryable failures `\"retry\"`, and other failures `\"alert\"`. No `default`. Then write it in Kotlin with `when` guards.",
  "answer": {"lang": "java", "src": "static String nextStep(Settlement s) {\n    return switch (s) {\n        case Settled(long amt) when amt >= 1_000_000 -> \"review\";\n        case Settled st -> \"done\";                       // unguarded: closes the Settled family\n        case Failed(var code, var retryable) when retryable -> \"retry\";\n        case Failed f -> \"alert\";                        // unguarded: closes the Failed family\n    };\n}",
             "alt": {"lang": "kotlin", "src": "fun nextStep(s: Settlement): String = when (s) {\n    is Settlement.Settled if s.amountMinor >= 1_000_000 -> \"review\"\n    is Settlement.Settled -> \"done\"                    // unguarded: closes the Settled family\n    is Settlement.Failed if s.retryable -> \"retry\"\n    is Settlement.Failed -> \"alert\"                    // unguarded: closes the Failed family\n}"}}
 },
 "recap": [
  "A pattern switch is checked for exhaustiveness and dominance and has defined null rules. An `instanceof` chain gets none of that.",
  "Record patterns take records apart in the case label, nested, through the accessors, with `var` inference and type checks.",
  "Cases run top to bottom and the first match wins. Guards don't count toward exhaustiveness, so end each guarded family with an unguarded case.",
  "A null selector throws unless you write `case null`, and `default` doesn't catch it. A nested type pattern matches a null component; a nested record pattern doesn't.",
  "Exhaustive is a compile-time promise. A subtype or enum constant added later makes an old client throw `MatchException` (`NoWhenBranchMatchedException` in Kotlin).",
  "JDK 21's exhaustiveness errors are generic and JDK 27 lists the missing patterns. `_` needs JDK 22, and primitive patterns are still a preview feature."
 ],
 "quiz": [
  {"q": "The switch is `case Line(Point(var x1, var y1), Point(var x2, var y2)) when x1 == x2 -> \"vertical\"; case Line(Point from, Point to) -> \"other\";`. What does it return for `new Line(null, new Point(1, 1))`?",
   "options": ["It throws NullPointerException", "`\"other\"`, with `from` bound to null", "It throws MatchException", "`\"vertical\"`"],
   "answer": 1, "why": "The nested record pattern `Point(var x1, var y1)` never matches null, so the first case is skipped. The type pattern `Point from` covers the whole component type, so it matches null and binds it. If the second case were also a record pattern, the switch would still compile and would throw MatchException for this line."},
  {"q": "Which pair of cases, in this order, does javac reject with `this case label is dominated by a preceding case label`?",
   "options": ["`case Integer i -> ...` then `case Integer i when i > 0 -> ...`", "`case Integer i when i > 0 -> ...` then `case Integer i -> ...`", "`case Integer i when i > 0 -> ...` then `case 1 -> ...`", "`case Card c when c.corporate() -> ...` then `case Card c when c.network() == AMEX -> ...`"],
   "answer": 0, "why": "An unguarded `case Integer i` matches every Integer, so the guarded case after it can never run. A guarded case never dominates anything, which is why the other three orders compile. The last pair compiles but is probably a bug: corporate AMEX cards never reach the AMEX rule."},
  {"q": "Kotlin: `data class Payment(val id: String, val amountMinor: Long)`. What does `val (amountMinor, id) = Payment(\"p1\", 500)` do on Kotlin 2.4 with default settings?",
   "options": ["It fails to compile because the names don't match the properties", "It binds by name: `amountMinor = 500`, `id = \"p1\"`", "It compiles without a warning and binds `amountMinor = \"p1\"`, `id = 500`", "It compiles with a warning about swapped names"],
   "answer": 2, "why": "Destructuring calls `component1()` and `component2()` in order, whatever you call the variables. Here the types even differ, but each variable just takes its component's type. Name-based destructuring exists only as an Experimental feature (2.3.20+, `-Xname-based-destructuring`)."},
  {"q": "From lesson 1: `record Masked(String card)` overrides `card()` to return `\"****\"` plus the last four digits. For the card 4111111111111111, what does `switch (m) { case Masked(var c) -> c; }` return?",
   "options": ["`4111111111111111`, because patterns read the field like toString does", "`****1111`, because record patterns call the accessor", "It doesn't compile: records with overridden accessors can't be deconstructed", "`null`"],
   "answer": 1, "why": "Record patterns extract components through the accessors, while the generated `toString` and `equals` read the fields. So this record shows `****1111` to patterns and the full number to `toString`: one more reason not to mask in the accessor.",
   "from": "dop-01"},
  {"q": "A switch over `String currency` has `case \"EUR\" -> ...` and `default -> ...`. An upstream parser sometimes passes null. What does the OpenJDK sealed-switch guide prefer?",
   "options": ["Add `case null` to every switch that might see it", "Nothing: `default` already catches null", "Wrap the switch in try/catch for NullPointerException", "Reject null before the switch with `Objects.requireNonNull(currency)`"],
   "answer": 3, "why": "`default` doesn't match null, so today the switch throws NPE. The guide allows `case null` but prefers `Objects.requireNonNull` before the switch: it fails where the bad value enters, with a clear message, instead of spreading null-handling into every switch."}
 ],
 "flashcards": [
  {"front": "Do guarded cases count toward exhaustiveness?", "back": "No, in Java or Kotlin. End each family of guarded cases with an unguarded case of the same pattern."},
  {"front": "When does javac say `this case label is dominated by a preceding case label`?", "back": "When an earlier unguarded case already matches everything the later case could, such as `case String s` after `case CharSequence cs`, or `case 1` after `case Integer i`."},
  {"front": "What does a pattern switch do with a null selector?", "back": "It throws `NullPointerException` unless it has `case null` (or `case null, default`). `default` alone doesn't catch null."},
  {"front": "`case Line(Point from, Point to)` and the line's `from` is null. Does it match?", "back": "Yes. A nested type pattern that covers the component's type matches null. A nested record pattern such as `Point(var x, var y)` doesn't."},
  {"front": "An old client's exhaustive switch meets a subtype added after it was compiled. What happens?", "back": "Java throws `MatchException`; a Kotlin `when` throws `NoWhenBranchMatchedException`. Recompiling turns it into a compile error."},
  {"front": "How do you put several patterns in one switch arm?", "back": "Only with unnamed patterns, from JDK 22: `case Capture _, Refund _ ->`. With named bindings javac says `illegal fall-through from a pattern`."},
  {"front": "Kotlin `val (a, b) = payment`: by name or by position?", "back": "By position, through `component1()` and `component2()`. Swapped names compile without a warning. Name-based destructuring is Experimental since 2.3.20."}
 ],
 "terms": [
  {"term": "Type pattern", "plain": "`Card c`: matches if the value is a `Card`, and binds it to `c`."},
  {"term": "Record pattern", "plain": "`Card(var net, var corp)`: matches a `Card` and binds its components, which can be patterns too."},
  {"term": "Guard", "plain": "The `when` condition after a pattern (`if` in Kotlin). The case matches only if the guard is true."},
  {"term": "Dominance", "plain": "A case is dominated when an earlier case already matches everything it could. javac rejects it."},
  {"term": "Remainder", "plain": "The values an exhaustive switch doesn't cover at run time: nested nulls and subtypes added after compilation."},
  {"term": "MatchException", "plain": "What Java throws when an exhaustive switch meets a value from its remainder (since JDK 21)."},
  {"term": "Unnamed pattern", "plain": "`_` in a pattern: matches anything and binds nothing. Final from JDK 22."}
 ],
 "explain_back": {
  "prompt": "A teammate asks: \"If the switch over our sealed `PaymentEvent` compiles with no default, it can never fail at run time, right?\" Explain, in your own words, when it can, and what you would do about each case.",
  "answer": "Exhaustive is checked at compile time, against the subtypes javac could see then. At run time two things can still slip through. First, null: a null selector throws `NullPointerException` unless there is a `case null`, and a null inside a nested record pattern can make the switch throw `MatchException`. I'd reject nulls at the boundary with `Objects.requireNonNull` so they never reach the switch. Second, separate compilation: if the event library adds a subtype and our service runs the new jar without being recompiled, the old switch throws `MatchException` for the new event. The fix is to rebuild against the new version, and then the compiler shows every switch that needs a case. Adding a default to hide it would be worse, because the new event would quietly take the default branch."
 },
 "deeper": {
  "minutes": 10,
  "body": """Two newer features build on this lesson. Neither belongs in the labs, which compile for JDK 21.

Primitive types in patterns have been a preview feature in every JDK from 23 to 27, and they are still a preview in the JDK 28 builds. They let a switch over an `int` use type patterns and guards, and let `instanceof` ask whether a value fits another primitive type exactly:

```java
// JDK 25: java --enable-preview --source 25 preview/PrimitivePatterns.java
static String riskBand(int score) {
    return switch (score) {
        case 0 -> "no score";
        case int s when s < 300 -> "high risk (" + s + ")";
        case int s -> "low or medium risk (" + s + ")";
    };
}
```

```kotlin
// Kotlin has always allowed conditions on any subject
fun riskBand(score: Int): String = when {
    score == 0 -> "no score"
    score < 300 -> "high risk ($score)"
    else -> "low or medium risk ($score)"
}
```

Without the preview flags, JDK 25 stops with `primitive patterns are a preview feature and are disabled by default`. Treat the syntax as likely to change until it is final.

The second feature is better error messages. JDK 27's javac lists what a non-exhaustive switch is missing, under a `missing patterns:` line, in the form `Rect _` for a type and `Pair(Red _,Green _)` for a nested record pattern. That one change makes nested exhaustiveness errors much easier to read: on JDK 21 the same `Pair` switch only says it doesn't cover all possible input values, and you work out the missing combination yourself.

One habit to avoid: don't write `case _ when ...`. JDK 25's javac accepts it, but the JLS doesn't allow it, and a fix in JDK 28 development (JDK-8385488) makes javac reject it. Write `default` or a real type pattern instead."""
 },
 "sources": [
  {"title": "JEP 441: Pattern Matching for switch", "url": "https://openjdk.org/jeps/441"},
  {"title": "JEP 440: Record Patterns", "url": "https://openjdk.org/jeps/440"},
  {"title": "MatchException (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/MatchException.html"},
  {"title": "Conditions and loops: when and guard conditions (Kotlin docs)", "url": "https://kotlinlang.org/docs/control-flow.html"},
  {"title": "Preparing for Change: Safe Switching over Sealed APIs (OpenJDK Amber, 2026)", "url": "https://github.com/openjdk/amber-docs/blob/master/site/guides/exhaustiveness-guide.md"}
 ]
}
out = ROOT / "content/lessons/dop-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
