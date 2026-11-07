import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/modernjava/src"
P = "java/workbench/modernjava/l02"
D = "java/workbench/modernjava/l02/demo"
K = "kotlin/workbench/modernjava/l02/demo"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :modernjava:demo -Pmain=workbench.modernjava.l02.demo."


def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{D}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{D}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{K}/{name}.kt"}}


FIG = (
    '<svg viewBox="0 0 700 300" role="img" aria-label="A sealed PaymentMethod with four branches: Card and Wallet are final records, '
    'BankTransfer is sealed with Sepa and Swift below it, and PartnerMethod is non-sealed, so GiftCard and any other class may implement it">'
    '<rect class="box-a" x="230" y="14" width="240" height="44" rx="8"/>'
    '<text class="t t-code" x="350" y="41" text-anchor="middle">sealed PaymentMethod</text>'
    '<line class="ln" x1="350" y1="58" x2="95" y2="108" marker-end="url(#arr)"/>'
    '<line class="ln" x1="350" y1="58" x2="265" y2="108" marker-end="url(#arr)"/>'
    '<line class="ln" x1="350" y1="58" x2="435" y2="108" marker-end="url(#arr)"/>'
    '<line class="ln" x1="350" y1="58" x2="605" y2="108" marker-end="url(#arr)"/>'
    '<rect class="box" x="20" y="110" width="150" height="50" rx="8"/>'
    '<text class="t-s t-code" x="95" y="131" text-anchor="middle">record Card</text>'
    '<text class="t-s t-m" x="95" y="150" text-anchor="middle">final</text>'
    '<rect class="box-a" x="190" y="110" width="150" height="50" rx="8"/>'
    '<text class="t-s t-code" x="265" y="131" text-anchor="middle">sealed BankTransfer</text>'
    '<text class="t-s t-m" x="265" y="150" text-anchor="middle">closed list below</text>'
    '<rect class="box" x="360" y="110" width="150" height="50" rx="8"/>'
    '<text class="t-s t-code" x="435" y="131" text-anchor="middle">record Wallet</text>'
    '<text class="t-s t-m" x="435" y="150" text-anchor="middle">final</text>'
    '<rect class="box-b" x="530" y="110" width="150" height="50" rx="8"/>'
    '<text class="t-s t-b" x="605" y="131" text-anchor="middle">non-sealed</text>'
    '<text class="t-s t-code" x="605" y="150" text-anchor="middle">PartnerMethod</text>'
    '<line class="ln" x1="265" y1="160" x2="225" y2="208" marker-end="url(#arr)"/>'
    '<line class="ln" x1="265" y1="160" x2="305" y2="208" marker-end="url(#arr)"/>'
    '<rect class="box" x="188" y="210" width="74" height="40" rx="8"/>'
    '<text class="t-s t-code" x="225" y="235" text-anchor="middle">Sepa</text>'
    '<rect class="box" x="268" y="210" width="74" height="40" rx="8"/>'
    '<text class="t-s t-code" x="305" y="235" text-anchor="middle">Swift</text>'
    '<line class="ln" x1="605" y1="160" x2="555" y2="208" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="605" y1="160" x2="650" y2="208" marker-end="url(#arr)"/>'
    '<rect class="box" x="510" y="210" width="90" height="40" rx="8"/>'
    '<text class="t-s t-code" x="555" y="235" text-anchor="middle">GiftCard</text>'
    '<rect class="box-dim" x="608" y="210" width="84" height="40" rx="8"/>'
    '<text class="t-s t-m" x="650" y="235" text-anchor="middle">any class</text>'
    '<text class="t-s t-m" x="95" y="190" text-anchor="middle">no subtypes</text>'
    '<text class="t-s t-m" x="435" y="190" text-anchor="middle">no subtypes</text>'
    '<text class="t-s" x="265" y="282" text-anchor="middle">one case BankTransfer covers both</text>'
    '<text class="t-s" x="600" y="282" text-anchor="middle">one case PartnerMethod covers all</text>'
    '</svg>'
)

S1 = """Any class, in any package, can implement an ordinary interface. So code that handles "each kind of command" can never know it handled them all: someone adds a `Void` command next week, it compiles, and the `if`/`else` chain that dispatches commands quietly skips it. Before JDK 17 the only fix was by hand: an abstract class with a package-private constructor, so that only classes in its own package can extend it. That closes the hierarchy, but the compiler still doesn't know the list, so it can't check a switch against it.

A sealed type is a class or interface that names its permitted subtypes, the only classes allowed to extend it directly. Add `sealed` and a `permits` clause, and the list becomes part of the type:

```java
public sealed interface Command permits Authorize, Capture, Refund {}

public record Authorize(String authCode, long amountMinor) implements Command {}
public record Capture() implements Command {}
public record Refund(long amountMinor) implements Command {}
```

```kotlin
sealed interface Command {
    data class Authorize(val authCode: String, val amountMinor: Long) : Command
    data object Capture : Command
    data class Refund(val amountMinor: Long) : Command
}
```

Sealed classes and interfaces have been final since JDK 17 (JEP 409). javac checks the list from both sides. A class that implements `Command` without being on it fails with `class is not allowed to extend sealed class: Command (as it is not listed in its 'permits' clause)`. javac also writes the list into the class file, as a `PermittedSubclasses` attribute (a table the JVM reads), and the JVM checks it when it loads a class. A subclass compiled against an older, unsealed `Command` fails to load with `IncompatibleClassChangeError: class Void cannot implement sealed interface Command`.

You can leave `permits` out when every subtype is declared in the same source file as the sealed type. javac then takes the subtypes it finds there. Reflection shows the result: `Command.class.isSealed()` is true, and `getPermittedSubclasses()` returns the three records.

Kotlin has no `permits` clause. Its rule is location: any class in the same package and the same module may extend a sealed type, and a class anywhere else fails with `a class can only extend a sealed class or interface declared in the same package`. With the JDK 21 target these labs use, kotlinc 2.4 writes the same `PermittedSubclasses` attribute as javac. So Java code sees a Kotlin sealed interface as sealed: a Java switch over it needs no `default`, and javac rejects a Java class that tries to implement it.

Sealing restricts direct subtypes only. `Refund.class.isSealed()` is false, and what happens below each permitted subtype is the subject of the next section."""

S2 = """Every permitted subtype of a sealed type must say how its own branch ends, with exactly one of three modifiers. If a class says nothing, javac stops with `sealed, non-sealed or final modifiers expected`. An interface can't be final, so for one the message is `sealed or non-sealed modifiers expected`.

`final` ends the branch. Records and enums are implicitly final, so a record needs no modifier, which is one reason sealed interfaces and records fit together so well. `sealed` continues the closed list one level down, with its own `permits`. `non-sealed` reopens the branch on purpose: anyone may extend it, in any package.

```java
public sealed interface PaymentMethod permits Card, BankTransfer, PartnerMethod {}
public record Card(String network) implements PaymentMethod {}                      // final
public sealed interface BankTransfer extends PaymentMethod permits Sepa, Swift {}   // closed below
public non-sealed interface PartnerMethod extends PaymentMethod {                   // open below
    String partnerId();
}
```

```kotlin
sealed interface PaymentMethod {
    data class Card(val network: String) : PaymentMethod                             // final by default
    sealed interface BankTransfer : PaymentMethod                                     // closed below
    interface PartnerMethod : PaymentMethod { val partnerId: String }                 // open below
}
```

`non-sealed` sounds like it defeats the point of sealing. It doesn't, because the compiler still knows the shape of the tree. A switch covers the open branch with one `case PartnerMethod p`, and that case matches every partner class, including ones a partner team writes next year. Your switch stays exhaustive and the partner team stays free. Kotlin has no `non-sealed` keyword: a plain interface or an `open class` under a sealed parent plays the same role.

So "sealed means final" is wrong: a sealed type has subtypes by definition, and a `non-sealed` branch can have any number. The trap that catches people in code review is a third one. A sealed class that isn't abstract is itself a possible value. With `sealed class Fee permits Flat, Percent` and no `abstract`, `new Fee()` is legal, so a switch with cases for `Flat` and `Percent` fails with `the switch expression does not cover all possible input values`. Make the parent `abstract`, or make it an interface. Kotlin avoids the trap entirely: its docs say a sealed class is always abstract."""

S3 = """Sealing ties a hierarchy to one place, and Java and Kotlin draw the boundary slightly differently.

In Java the permitted subtypes must be in the same module as the sealed type. A module here means a JPMS module: a set of packages described by a `module-info.java`. If your code isn't in a named module, the subtypes must be in the same package. A typical Quarkus or Spring service runs on the class path, in the unnamed module, so the package rule is the one you will meet. Split a sealed interface and its record across `pay.api` and `pay.card` and javac refuses:

```text
error: class PaymentMethod in unnamed module cannot extend a sealed class in a different package
public sealed interface PaymentMethod permits pay.card.Card {}
```

The wording is clumsy, since it names the sealed interface as the class doing the extending, but the rule is clear. Add a `module-info.java` that puts both packages in one module, and the same files compile.

Kotlin's rule is the same package and the same module, whether or not you use JPMS modules. So for the code most of us write, the two languages agree: keep a sealed hierarchy in one package. That is rarely a burden. The subtypes are usually small records or data classes that read best next to each other, often nested inside the sealed type itself, which also lets Java infer `permits`.

The restriction makes sense once you see what sealing promises. The author of a sealed type says "this is the complete list", and the compiler can only hold everyone to that if the whole list is compiled and shipped as one unit. A subtype in some other module could be released on its own schedule, and the list every switch was checked against would quietly go stale."""

S4 = """Sealing pays off in a `switch`. Over a sealed type, javac knows every possible subtype, so a switch with one case per subtype is exhaustive (its cases cover every possible value) and needs no `default`. javac checks that the cases really do cover every subtype:

```java
static long ledgerImpact(Dispute d) {
    return switch (d) {                            // no default
        case Opened o -> -o.amountMinor();
        case EvidenceSent e -> 0;
        case Won w -> 0;
        case Lost l -> -l.amountMinor();
    };
}
```

```kotlin
fun ledgerImpact(d: Dispute): Long = when (d) {    // no else
    is Dispute.Opened -> -d.amountMinor
    is Dispute.EvidenceSent -> 0
    is Dispute.Won -> 0
    is Dispute.Lost -> -d.amountMinor
}
```

Now the card schemes add an arbitration stage, and you add `Arbitration` to `Dispute`. Every switch over `Dispute` without a `default` stops compiling. On JDK 21 to 26 the error is the bare `the switch expression does not cover all possible input values`, pointing at the `switch`. JDK 27 adds the cases you're missing:

```text
error: the switch expression does not cover all possible input values
        return switch (d) {
               ^
  missing patterns:
      Arbitration _
```

kotlinc has always been specific: `'when' expression must be exhaustive. Add the 'is Arbitration' branch or an 'else' branch.` Either way, the build hands you the list of code to update.

A `default` throws that list away. It means "and anything else", so `Arbitration` drops into it without a word and gets whatever the default returns. The OpenJDK team's 2026 guide to switching over sealed types has a section titled "By default, avoid `default`", because a default "sweeps errors, both present and future, under the rug". Use `default` only where you really mean "everything else", such as the illegal (state, event) pairs in a state machine, as *State and Chain of Responsibility* in the patterns track did.

The same guide asks authors to say in the Javadoc why a type is sealed. It names two reasons: the type models a closed domain, like dispute stages, or the author only wants to control who implements it. Say which, and whether you expect to add subtypes, so the people switching over it know what to expect. Exhaustive also doesn't mean unbreakable at run time: a client compiled against the old list can still meet an `Arbitration` from a newer jar. Lesson 3 shows what happens then."""

L = {
 "id": "dop-02",
 "title": "Sealed types: hierarchies the compiler can check",
 "minutes": 35,
 "goal": "By the end you can declare a sealed hierarchy with the right modifier on every subtype, say where its subtypes may live, and use it so that adding a subtype turns every switch you forgot into a compile error.",
 "warmup": {
  "q": "`sealed class Fee permits Flat, Percent {}` is not abstract, and `Flat` and `Percent` are its final subclasses. A switch expression over a `Fee` has `case Flat f` and `case Percent p` and no `default`. Does it compile?",
  "options": ["Yes: the permits list is complete, so the switch is exhaustive",
              "No: `new Fee()` is also a possible value, so the switch misses a case",
              "No: only interfaces can be sealed",
              "Yes, but a plain `Fee` throws MatchException at run time"],
  "answer": 1,
  "why": "A concrete sealed class can be instantiated itself, so a `Fee` that is neither `Flat` nor `Percent` can exist, and javac reports `the switch expression does not cover all possible input values`. Make `Fee` abstract, or an interface, and the two cases cover it. Kotlin sidesteps the trap: a sealed class there is always abstract."
 },
 "sections": [
  {
   "h": "A sealed type closes the list of direct subtypes",
   "body": S1,
   "try": {
    "title": "Break the list on purpose",
    "minutes": 4,
    "steps": [
     "Run `SealedBasics` (or `SealedBasicsKt`) with the command below.",
     "In the Java demo, uncomment `static final class Void implements Command {}` and run again. Read the error.",
     "Add `Void` to the `permits` clause and delete `final` from it. Run again. Then put `final` back.",
     "Now delete the whole `permits ...` clause and run. What does `getPermittedSubclasses()` print?",
     "In the Kotlin twin, uncomment `class Void : Command`. Does it compile? Why is that different from Java?"
    ],
    "code": demo("SealedBasics"),
    "expect": "The first run prints `isSealed(): true`, the three records marked `(final)`, and `Refund.isSealed(): false`. The unlisted class fails with `class is not allowed to extend sealed class: Command (as it is not listed in its 'permits' clause)`. Listed but without a modifier, it fails with `sealed, non-sealed or final modifiers expected`. With no `permits` clause, javac infers all four from the file and prints `Void` too. In Kotlin, `class Void : Command` compiles: the list is whatever sits in the same package and module."
   },
   "refs": [
    {"title": "JEP 409: Sealed Classes", "url": "https://openjdk.org/jeps/409", "kind": "read"}
   ]
  },
  {
   "h": "final, sealed or non-sealed: every branch has to choose",
   "body": S2,
   "figure": {"svg": FIG, "caption": "Each permitted subtype ends its branch: final has no subtypes, sealed keeps a closed list, non-sealed lets anyone in. A switch still needs only one case per branch."},
   "try": {
    "title": "Reopen one branch, close the trap",
    "minutes": 4,
    "steps": [
     "Run `NonSealedDemo`. `GiftCard` is partner code: which modifier lets it exist?",
     "Delete `non-sealed` from `PartnerMethod`, leaving a plain `interface`, and run. Read the error, then put it back.",
     "Delete `abstract` from `sealed abstract static class Fee` and run again."
    ],
    "code": demo("NonSealedDemo"),
    "expect": "The demo prints `card VISA`, `bank transfer Sepa[iban=...]`, `partner giftly`, `PartnerMethod.isSealed(): false` and `fee: 290 and 35`. Without a modifier, javac says `sealed or non-sealed modifiers expected` (an interface can't be final, so `final` isn't offered). Without `abstract`, the `fee` switch fails with `the switch expression does not cover all possible input values`: a plain `Fee` is now a possible value. The Kotlin twin can't show that trap, because its sealed class is always abstract."
   },
   "refs": [
    {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html", "kind": "docs"}
   ]
  },
  {
   "h": "Where the subtypes may live",
   "body": S3,
   "try": {
    "title": "Split a hierarchy across packages",
    "minutes": 4,
    "steps": [
     "The folder `labs/modernjava/javac/sealed-packages` holds a sealed `PaymentMethod` in `pay.api`, a `Card` record in `pay.card`, and a `module-info.java`. Gradle doesn't compile it; you run `javac` yourself.",
     "Run the first command. Read the error and the line it points at.",
     "Run the second command, which adds the module descriptor.",
     "Predict, then check: move `Card.java` into `pay/api/`, change its package line to `pay.api`, change the permits clause to `permits Card`, and run the first command again."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "cd labs/modernjava/javac/sealed-packages\n\n# 1. class path, unnamed module: two packages are not allowed\njavac -d ../../build/sealed-packages pay/api/PaymentMethod.java pay/card/Card.java\n\n# 2. one named module: two packages are fine\njavac -d ../../build/sealed-packages module-info.java pay/api/PaymentMethod.java pay/card/Card.java", "run": ""},
    "expect": "The first command fails with `class PaymentMethod in unnamed module cannot extend a sealed class in a different package`, pointing at `pay.card.Card` in the permits clause. The second compiles with no output, because both packages belong to module `pay`. After the move, the first command compiles too: on the class path, one package is enough."
   }
  },
  {
   "h": "Let the compiler find every switch, and keep default out",
   "body": S4,
   "try": {
    "title": "Add a stage to the dispute flow",
    "minutes": 5,
    "steps": [
     "Run `DisputeSwitches` once and look at the three functions: `label`, `ledgerImpact` and `slaDays`. Which one has a `default`?",
     "Add `Arbitration` to the `permits` clause and uncomment the `Arbitration` record. Before you run, predict which functions javac will report.",
     "Run it, then make it compile again by handling `Arbitration` where javac asked. What does `slaDays` return for an arbitration case now? Is that right?",
     "Do the same in the Kotlin twin, `DisputeSwitchesKt`."
    ],
    "code": demo("DisputeSwitches"),
    "expect": "javac reports two errors, `the switch expression does not cover all possible input values`, one in `label` and one in `ledgerImpact`. On JDK 27 each also says `missing patterns: Arbitration _`. `slaDays` compiles silently and returns 0 for arbitration, which is probably wrong (arbitration has deadlines too), and nothing told you. kotlinc reports the same two functions with `Add the 'is Arbitration' branch or an 'else' branch.`"
   },
   "refs": [
    {"title": "Preparing for Change: Safe Switching over Sealed APIs (OpenJDK Amber, 2026)", "url": "https://github.com/openjdk/amber-docs/blob/master/site/guides/exhaustiveness-guide.md", "kind": "read"}
   ]
  }
 ],
 "analogy": "A sealed type is like the list of settlement currencies in your merchant contract. The contract names them, so finance can write one procedure per currency and know the procedures are complete. Adding a currency means amending the contract, and then every procedure that branches on currency has to be checked, which is exactly what you want. A `non-sealed` branch is the clause that says \"plus any currency a partner bank agrees to handle\": you can't list those, but one procedure (send it to the partner) covers them all. The analogy breaks on enforcement: nobody stops a sales rep from quoting a currency that isn't in the contract, while javac and the JVM both refuse a subtype that isn't on the list.",
 "in_your_world": "Payment services are full of closed lists: payment methods, authorization outcomes, dispute stages, ledger entry kinds, the event types on one Kafka topic. Make each of them a sealed interface of records, and the consumer that handles a topic becomes one switch with no `default`. The day someone adds `RefundReversed` to the event schema, the consumer, the projection that builds the read model and the metrics tagging all fail to compile until they handle it. That is better than finding out from a dead-letter queue. Keep each hierarchy in one package: on the class path, which is how Quarkus services usually run, javac won't let you split it.",
 "mistake": "The usual mistake is adding `default -> throw new IllegalStateException()` to a switch over your own sealed type, \"to be safe\". It feels defensive, but it switches off the one check sealing gives you. When a new subtype arrives, the switch still compiles, the new case goes to the default branch, and you find out at run time, from a failed payment. Leave the default out and let the build fail. Keep `default` for switches where \"everything else\" really is one answer.",
 "compare": {
  "title": "The dispute hierarchy in Java and Kotlin",
  "java": {"title": "Dispute.java", "src": "public sealed interface Dispute permits Opened, EvidenceSent, Won, Lost {}\n\nrecord Opened(String caseId, long amountMinor) implements Dispute {}\nrecord EvidenceSent(String caseId) implements Dispute {}\nrecord Won(String caseId) implements Dispute {}\nrecord Lost(String caseId, long amountMinor) implements Dispute {}\n\nstatic String label(Dispute d) {\n    return switch (d) {                 // no default\n        case Opened o -> \"opened\";\n        case EvidenceSent e -> \"evidence sent\";\n        case Won w -> \"won\";\n        case Lost l -> \"lost\";\n    };\n}"},
  "kotlin": {"title": "Dispute.kt", "src": "sealed interface Dispute {\n    data class Opened(val caseId: String, val amountMinor: Long) : Dispute\n    data class EvidenceSent(val caseId: String) : Dispute\n    data class Won(val caseId: String) : Dispute\n    data class Lost(val caseId: String, val amountMinor: Long) : Dispute\n}\n\nfun label(d: Dispute): String = when (d) {   // no else\n    is Dispute.Opened -> \"opened\"\n    is Dispute.EvidenceSent -> \"evidence sent\"\n    is Dispute.Won -> \"won\"\n    is Dispute.Lost -> \"lost\"\n}"},
  "note": "The idea is the same and so is the bytecode: both compilers write a `PermittedSubclasses` attribute, so each language sees the other's sealed types as sealed. Three things differ. Java names the subtypes in `permits` (or infers them from one source file) and makes every subtype choose `final`, `sealed` or `non-sealed`; Kotlin's list is whatever is declared in the same package and module, and subtypes are final unless you open them. Java's location rule is the module, or the package on the class path; Kotlin's is always package and module. And Kotlin has `data object` for a stateless case, where Java uses a record with no components or an enum."
 },
 "worked": {
  "title": "Seal the events a Kafka consumer handles",
  "steps": [
   {"say": "A ledger consumer handles three event types with an `instanceof` chain. Someone adds a fourth type, `Adjusted`, to the producer. This compiles with no warning, and the consumer starts throwing on the new events in production.",
    "code": "public interface LedgerEvent {}\n\nvoid handle(LedgerEvent e) {\n    if (e instanceof Posted p) post(p);\n    else if (e instanceof Reversed r) reverse(r);\n    else throw new IllegalArgumentException(\"unknown event \" + e);   // Adjusted lands here\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "interface LedgerEvent\n\nfun handle(e: LedgerEvent) {\n    if (e is Posted) post(e)\n    else if (e is Reversed) reverse(e)\n    else throw IllegalArgumentException(\"unknown event $e\")      // Adjusted lands here\n}"},
   {"say": "Seal the event type and make each event a record in the same package. Records are final, so they need no modifier.",
    "code": "// 1. close the list\npublic sealed interface LedgerEvent permits Posted, Reversed, Adjusted {}\n\npublic record Posted(String entryId, long amountMinor) implements LedgerEvent {}\npublic record Reversed(String entryId, String reason) implements LedgerEvent {}\npublic record Adjusted(String entryId, long deltaMinor) implements LedgerEvent {}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "// 1. close the list\nsealed interface LedgerEvent {\n    data class Posted(val entryId: String, val amountMinor: Long) : LedgerEvent\n    data class Reversed(val entryId: String, val reason: String) : LedgerEvent\n    data class Adjusted(val entryId: String, val deltaMinor: Long) : LedgerEvent\n}"},
   {"say": "Replace the chain with a switch that has no `default`. The chain could never be checked; the switch is checked on every build, and the `else throw` disappears because there is no \"else\" left.",
    "code": "// 2. one case per event, no default\nvoid handle(LedgerEvent e) {\n    switch (e) {\n        case Posted p -> post(p);\n        case Reversed r -> reverse(r);\n        case Adjusted a -> adjust(a);\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "// 2. one branch per event, no else\nfun handle(e: LedgerEvent) = when (e) {\n    is LedgerEvent.Posted -> post(e)\n    is LedgerEvent.Reversed -> reverse(e)\n    is LedgerEvent.Adjusted -> adjust(e)\n}"},
   {"say": "A switch *statement* with patterns must be exhaustive too, so the `void` version is checked just like the expression. Last, write down why the type is sealed, so the next person knows that adding an event is expected and that consumers must be updated, not given a default.",
    "code": "/**\n * Every event on the ledger topic. Sealed because consumers must handle each one.\n * New events will be added: expect your switch to stop compiling, and handle the new case.\n */\npublic sealed interface LedgerEvent permits Posted, Reversed, Adjusted {}   // 3. say why", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "/**\n * Every event on the ledger topic. Sealed because consumers must handle each one.\n * New events will be added: expect your when to stop compiling, and handle the new case.\n */\nsealed interface LedgerEvent   // 3. say why"}
  ]
 },
 "lab": {
  "title": "Seal the payment methods",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/PaymentMethod.java", f"{lab}/main/{P}/Settlement.java"],
  "run": "./gradlew :modernjava:test --tests 'workbench.modernjava.l02.*'",
  "steps": [
   "Run the tests. All seven fail. Two of them run `javac` inside the test, through `javax.tools`, against your classes: read the Java source they compile.",
   "In `PaymentMethod`, seal the interface, seal `BankTransfer`, and give `PartnerMethod` the modifier that keeps it open to partners (TODO 1 to 3). Run the tests: four should pass now.",
   "In `Settlement`, write `daysToSettle` with one case per type and no `default` (TODO 4).",
   "Write `rail` with a single case for all bank transfers (TODO 5). Run until all seven tests pass.",
   "Add `record Crypto(String chain) implements PaymentMethod {}` to the hierarchy and to `permits`, then run `./gradlew :modernjava:compileJava`. Which lines does javac point at? Remove it again."
  ],
  "hints": [
   "Types nested in an interface are implicitly `public static`. Write `permits PaymentMethod.Card, ...`, or leave `permits` out, since every subtype is in this one file.",
   "A sealed sub-interface looks like `sealed interface BankTransfer extends PaymentMethod permits Sepa, Swift {}`.",
   "`sealed or non-sealed modifiers expected` means a permitted interface has no modifier; an interface can't be final. Records are final already.",
   "The tests call `ToolProvider.getSystemJavaCompiler()`. If it returns null, Gradle is running on a JRE: point it at a full JDK."
  ],
  "done_when": "All seven tests in `SealedHierarchyTest` pass."
 },
 "drill": {
  "title": "Seal a hierarchy from memory",
  "minutes": 5,
  "prompt": "Close this page. Write a sealed `RefundOutcome` with three results: `Issued(String refundId)`, `Rejected(String reason)` and `Pending`, where `Pending` is itself sealed, with `AwaitingIssuer` and `AwaitingReview(String queue)` below it. Then write `label(RefundOutcome)` with no `default`, using one case for everything pending. Java first, then Kotlin.",
  "answer": {"lang": "java", "src": "sealed interface RefundOutcome permits Issued, Rejected, Pending {}\nrecord Issued(String refundId) implements RefundOutcome {}\nrecord Rejected(String reason) implements RefundOutcome {}\nsealed interface Pending extends RefundOutcome permits AwaitingIssuer, AwaitingReview {}\nrecord AwaitingIssuer() implements Pending {}\nrecord AwaitingReview(String queue) implements Pending {}\n\nstatic String label(RefundOutcome o) {\n    return switch (o) {\n        case Issued i -> \"issued \" + i.refundId();\n        case Rejected r -> \"rejected: \" + r.reason();\n        case Pending p -> \"pending\";          // one case covers the sealed branch\n    };\n}",
             "alt": {"lang": "kotlin", "src": "sealed interface RefundOutcome {\n    data class Issued(val refundId: String) : RefundOutcome\n    data class Rejected(val reason: String) : RefundOutcome\n    sealed interface Pending : RefundOutcome\n    data object AwaitingIssuer : Pending\n    data class AwaitingReview(val queue: String) : Pending\n}\n\nfun label(o: RefundOutcome): String = when (o) {\n    is RefundOutcome.Issued -> \"issued ${o.refundId}\"\n    is RefundOutcome.Rejected -> \"rejected: ${o.reason}\"\n    is RefundOutcome.Pending -> \"pending\"    // one branch covers the sealed branch\n}"}}
 },
 "recap": [
  "`sealed ... permits` fixes the list of direct subtypes. javac checks it, and the JVM refuses to load a subclass that isn't on it.",
  "Each permitted subtype is `final` (records already are), `sealed` (closed one level down) or `non-sealed` (open again, and still covered by one case).",
  "A sealed class that isn't abstract is itself a possible value, so its subtypes don't cover it. Make it abstract or an interface.",
  "Java subtypes must share the module, or the package on the class path. Kotlin subtypes must share the package and the module.",
  "A switch over a sealed type with no `default` is checked: add a subtype and every such switch fails to compile. JDK 27 also lists the missing patterns.",
  "Keep `default` off the dimension that grows. It hides the new subtype instead of reporting it."
 ],
 "quiz": [
  {"q": "You seal `PaymentMethod`. Partner teams must be able to add their own payment types under `PartnerMethod`, in their own packages. Which declaration fits?",
   "options": ["`final interface PartnerMethod extends PaymentMethod`", "`sealed interface PartnerMethod extends PaymentMethod`", "`non-sealed interface PartnerMethod extends PaymentMethod`", "`interface PartnerMethod extends PaymentMethod`, with no modifier"],
   "answer": 2, "why": "`non-sealed` reopens the branch, so any class in any package may implement it, and a switch still covers it with one case. An interface can't be final, `sealed` would close it again, and no modifier at all fails with `sealed or non-sealed modifiers expected`."},
  {"q": "`PaymentMethod` is sealed with `Card`, `BankTransfer` (sealed: `Sepa`, `Swift`), `Wallet` and `PartnerMethod` (non-sealed). A switch has cases for `Card`, `Sepa`, `Wallet` and `PartnerMethod`, and no default. What happens?",
   "options": ["It compiles, because PartnerMethod is open anyway", "javac reports that the switch doesn't cover all possible input values: `Swift` is missing", "javac demands a default, because a non-sealed branch can never be covered", "It compiles, and a Swift transfer throws MatchException"],
   "answer": 1, "why": "`Sepa` alone doesn't cover the sealed `BankTransfer` branch, so `Swift` is uncovered and the switch is rejected (JDK 27 prints `missing patterns:` with `Swift _`). The non-sealed branch is fine: `case PartnerMethod p` matches every implementation, known or not."},
  {"q": "Your Quarkus service runs on the class path, with no `module-info.java`. You put `sealed interface PaymentEvent` in `com.acme.events` and its records in `com.acme.events.card`. What happens?",
   "options": ["It compiles, because the packages share a prefix", "It compiles, but the JVM refuses to load the records", "It compiles if the permits clause uses fully qualified names", "javac rejects it: in the unnamed module, permitted subtypes must be in the same package"],
   "answer": 3, "why": "Packages have no hierarchy in Java, so `com.acme.events.card` is simply a different package. Without a named module, javac requires the same package and reports `cannot extend a sealed class in a different package`. Move the records into `com.acme.events`, or put both packages in one named module."},
  {"q": "From *State and Chain of Responsibility*: the `transition` function's inner switches over the event end in `default -> throw illegal(s, e)`. Someone adds a `Chargeback` event to the sealed `PaymentEvent`. What does the compiler tell you about those inner switches?",
   "options": ["Nothing: they have a default, so `Chargeback` is silently treated as illegal in every state", "Every inner switch fails to compile until it handles `Chargeback`", "Only the outer switch over states fails", "The build passes, but every transition throws MatchException"],
   "answer": 0, "why": "A default covers every event, including new ones, so the compiler has nothing to report. That was a deliberate choice there, because most (state, event) pairs are illegal, but it means a new event needs a manual review of each state. The outer switch is over states, which didn't change.",
   "from": "pat-09"},
  {"q": "A Kotlin module defines `sealed interface Outcome` with three data classes. Java code in the same project switches over an `Outcome` with three cases and no `default`. What happens?",
   "options": ["javac requires a default, because Java can't see Kotlin's sealing", "It compiles: kotlinc writes the PermittedSubclasses attribute, so javac treats `Outcome` as sealed", "It compiles only if the data classes are marked `@JvmRecord`", "It compiles, and Java code may still add a fourth implementation"],
   "answer": 1, "why": "With a JDK 17+ target such as the labs' 21, kotlinc emits the same class-file attribute javac does. javac then checks the switch for exhaustiveness and rejects a Java class that tries to implement `Outcome`. `@JvmRecord` is about records, not sealing."}
 ],
 "flashcards": [
  {"front": "Which modifiers can a permitted subtype of a sealed type have?", "back": "Exactly one of `final`, `sealed` or `non-sealed`. Records and enums are implicitly final, so they need none."},
  {"front": "What does `non-sealed` do?", "back": "It reopens that branch: anyone may extend it. A switch still covers the whole branch with one case for the non-sealed type."},
  {"front": "Why don't `case Flat` and `case Percent` cover `sealed class Fee permits Flat, Percent` when `Fee` isn't abstract?", "back": "`new Fee()` is a possible value too. Make `Fee` abstract or an interface."},
  {"front": "Where may a Java sealed type's permitted subtypes live?", "back": "In the same module. On the class path (the unnamed module), in the same package."},
  {"front": "Where may a Kotlin sealed type's direct subtypes live?", "back": "In the same package and the same module."},
  {"front": "When can you leave out `permits`?", "back": "When every subtype is declared in the same source file as the sealed type. javac infers the list."},
  {"front": "Why avoid `default` in a switch over your own sealed type?", "back": "It stops the compiler from reporting the switch when a subtype is added. The new subtype silently takes the default branch."}
 ],
 "terms": [
  {"term": "Sealed type", "plain": "A class or interface that lists which classes may extend it directly."},
  {"term": "Permitted subtype", "plain": "A class on a sealed type's list. It must be final, sealed or non-sealed."},
  {"term": "non-sealed", "plain": "The modifier that reopens one branch of a sealed hierarchy to any subclass."},
  {"term": "Exhaustive switch", "plain": "A switch whose cases cover every possible value of its selector, so it needs no default."},
  {"term": "PermittedSubclasses", "plain": "The class-file attribute that records a sealed type's list, checked by the JVM when a class loads."},
  {"term": "Unnamed module", "plain": "Where code on the class path lives when it has no `module-info.java`. Most services run here."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to add `default -> throw new IllegalStateException(\"unknown method\")` to every switch over your sealed `PaymentMethod`, \"to be safe\". Explain, in your own words, what that costs and when a default is the right call.",
  "answer": "Over a sealed type, a switch with no default is checked by the compiler: it knows every subtype, and the build fails if a case is missing. That is the main reason to seal the type. Adding a default tells the compiler \"anything else goes here\", so when someone adds a new payment method, every switch still compiles and the new method throws at run time instead, probably on a real payment. Leave the default out and the build gives you the list of switches to update. A default is right only when \"everything else\" really has one answer, such as rejecting most event types in a given state. For an open branch, use a `non-sealed` subtype and one case for it, not a default."
 },
 "deeper": {
  "minutes": 8,
  "body": """Sealing is enforced in three places, and it helps to know which one you are looking at.

javac enforces it at compile time, with the errors in this lesson. The JVM enforces it at load time, from the `PermittedSubclasses` attribute. Compile `final class B implements S` against an old, unsealed `S`, then run it next to a newer `S` that is sealed and doesn't list `B`, and class loading fails with `java.lang.IncompatibleClassChangeError: class B cannot implement sealed interface S`. That stops a stray jar from smuggling a subtype into your hierarchy. And reflection reports it: `Class.isSealed()` and `Class.getPermittedSubclasses()`, both added with sealed classes, are what the tests in this lesson's lab use.

None of the three stops you from adding a subtype yourself, and that is on purpose. The 2026 Amber guide calls adding a permitted subtype "a permissible and compatible evolution" of a sealed API. Clients compiled against the old list keep loading and running; only their switches change behavior. Recompiled, those switches fail to build. Not recompiled, they meet the new subtype at run time and throw `MatchException`. The guide calls this how Java balances "safety with resilience": you find out either at build time or loudly at run time, never silently. Lesson 3 runs that experiment, and shows that the same thing happens for an enum constant added after the switch was compiled.

For Kotlin interop, one detail is worth checking in your own build. The `PermittedSubclasses` attribute only exists in class files for JDK 17 and later, so Java sees a Kotlin sealed type as sealed only when kotlinc targets 17 or higher. With the JDK 21 target the labs use, kotlinc 2.4 writes it, and javac rejects `final class Bad implements Status {}` against a Kotlin sealed `Status` with the usual `not listed in its 'permits' clause` error."""
 },
 "sources": [
  {"title": "JEP 409: Sealed Classes", "url": "https://openjdk.org/jeps/409"},
  {"title": "Class (Java SE 25 API): isSealed and getPermittedSubclasses", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Class.html"},
  {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html"},
  {"title": "Preparing for Change: Safe Switching over Sealed APIs (Bimpoudis, Buckley, Goetz, 2026)", "url": "https://github.com/openjdk/amber-docs/blob/master/site/guides/exhaustiveness-guide.md"}
 ]
}
out = ROOT / "content/lessons/dop-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
