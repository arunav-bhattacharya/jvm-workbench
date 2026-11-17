import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/modernjava/src"
P = "kotlin/workbench/modernjava/l04"
D = "java/workbench/modernjava/l04/demo"
K = "kotlin/workbench/modernjava/l04/demo"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :modernjava:demo -Pmain=workbench.modernjava.l04.demo."


def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{D}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{D}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{K}/{name}.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 680 260" role="img" aria-label="The expression problem as a grid: with methods on each class, adding a type is local and '
    'adding an operation edits every class; with sealed types and switches, adding an operation is local and adding a type breaks every switch, which the compiler lists">'
    '<text class="t t-a" x="300" y="34" text-anchor="middle">methods on each class</text>'
    '<text class="t t-a" x="545" y="34" text-anchor="middle">sealed types + switch</text>'
    '<text class="t" x="92" y="92" text-anchor="middle">add a type</text>'
    '<text class="t-s t-m" x="92" y="112" text-anchor="middle">e.g. Lost</text>'
    '<text class="t" x="92" y="182" text-anchor="middle">add an operation</text>'
    '<text class="t-s t-m" x="92" y="202" text-anchor="middle">e.g. sendsReceipt</text>'
    '<rect class="box-ok" x="190" y="55" width="220" height="72" rx="8"/>'
    '<text class="t" x="300" y="86" text-anchor="middle">one new class</text>'
    '<text class="t-s t-m" x="300" y="108" text-anchor="middle">nothing else changes</text>'
    '<rect class="box-b" x="430" y="55" width="230" height="72" rx="8"/>'
    '<text class="t" x="545" y="86" text-anchor="middle">every switch breaks</text>'
    '<text class="t-s t-m" x="545" y="108" text-anchor="middle">the compiler lists each one</text>'
    '<rect class="box-bad" x="190" y="145" width="220" height="72" rx="8"/>'
    '<text class="t" x="300" y="176" text-anchor="middle">edit every class</text>'
    '<text class="t-s t-m" x="300" y="198" text-anchor="middle">or every Visitor</text>'
    '<rect class="box-ok" x="430" y="145" width="230" height="72" rx="8"/>'
    '<text class="t" x="545" y="176" text-anchor="middle">one new function</text>'
    '<text class="t-s t-m" x="545" y="198" text-anchor="middle">nothing else changes</text>'
    '<text class="t-s t-m" x="425" y="246" text-anchor="middle">library data gains operations far more often than it gains types</text>'
    '</svg>'
)

OPENING = """When a member reserves a book this library doesn't own, the request goes to the regional catalogue, a program run by another organization that knows what every library nearby holds. Its answer comes back as text fields: a status, and a few boxes that should be filled in only for some statuses. A ready book has a pickup code and a hold shelf. An unavailable one has a reason. A waiting-list place has an expected wait.

Picture it as one paper form with every box printed on it. Nothing stops someone from ticking Ready and also writing "Reason: lost". The form allows 48 combinations, and 3 of them make sense. The easy trap is to trust the notes beside the boxes, not the shape of the form.

The last three lessons gave us records, sealed types and a clerk who sorts by shape. In this lesson, we'll put them together: forms that can't be filled in wrong, one door where outside answers are checked, and the rules kept in one place. Then we'll look at Project Valhalla, which wants to print small forms straight onto the page. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_DTO = """public class HoldReplyDto {
    String status;               // "READY", "UNAVAILABLE" or "WAITLISTED"
    String pickupCode;           // only when ready
    Integer holdShelf;           // only when ready
    String reasonCode;           // only when unavailable
    Integer waitDays;            // only when waitlisted
}"""
K_DTO = """data class HoldReplyDto(
    val status: String?,         // "READY", "UNAVAILABLE" or "WAITLISTED"
    val pickupCode: String?,     // only when ready
    val holdShelf: Int?,         // only when ready
    val reasonCode: String?,     // only when unavailable
    val waitDays: Int?,          // only when waitlisted
)"""
J_MODEL = """public sealed interface HoldResult permits Ready, Unavailable, Waitlisted {}
public record Ready(PickupCode code, int shelf) implements HoldResult {}
public record Unavailable(Reason reason) implements HoldResult {}
public record Waitlisted(Duration expectedWait) implements HoldResult {}"""
K_MODEL = """sealed interface HoldResult {
    data class Ready(val code: PickupCode, val shelf: Int) : HoldResult
    data class Unavailable(val reason: Reason) : HoldResult
    data class Waitlisted(val expectedWait: Duration) : HoldResult
}"""

S0 = """Here is how the catalogue's answer usually arrives in a program: one class, every field optional.

""" + pair(J_DTO, K_DTO) + """

A DTO, short for data transfer object, is a class whose only job is to hold the fields of a message as they arrived. Count what this one allows. Three statuses, times four optional fields that are each set or null, gives 48 shapes. Three of them make sense. The other 45, such as ready with no pickup code, or ready with a reason code, can be built, stored and passed around. The comments are the only place that says which fields go together. Every piece of code that reads the DTO has to check that again, and one of them won't. The `IllegalStates` demo hands a broken reply to the code that prints pickup slips:

```text
shapes the DTO allows: 48, shapes that make sense: 3
DTO consumer:    print slip: shelf 12, code null
```

A member now holds a slip with no code on it, and the desk can't hand over the book. Model the three outcomes instead, each with only its own fields:

""" + pair(J_MODEL, K_MODEL) + """

Now there are three shapes, and "ready with a reason" can't even be written down. In the paperwork picture, the one form with every box has become three forms, each with only its own boxes. The checks that are left move into the constructors: a pickup code is six letters or digits, and hold shelves start at 1. (The component is `expectedWait`, not `wait`; lesson 1's aside showed why Java refuses that name.)

That's what "make illegal states unrepresentable" means in practice: the types and the canonical constructors refuse the bad values once, so no reader has to. Brian Goetz calls this style **data-oriented programming**: model the data as immutable records and sealed types, and write the logic as functions over them. He wrote it up in a 2022 InfoQ article, "Data Oriented Programming in Java".

His 2019 design note on records and sealed types gives the vocabulary. A record is a product type: a `Ready` is a code *and* a shelf, and its API models "the state, the whole state, and nothing but the state". A sealed interface is a sum type, "a discriminated union of a fixed set of types": a `HoldResult` is ready *or* unavailable *or* waitlisted. Most messages a program handles have exactly this shape, a few alternatives, each a fixed set of fields.

**A shape that can't be built can't be mishandled. Give each valid combination its own record.**

Three clean forms help only if every answer from outside is copied onto one of them. That copying needs a place."""

# ---------------------------------------------------------------- section 1
J_PARSE = """static Parsed parse(HoldReplyDto raw) {
    try {
        return switch (raw.status) {
            case "READY" -> raw.pickupCode == null || raw.holdShelf == null
                    ? new Rejected("ready without a code or a shelf")
                    : new Ok(new Ready(new PickupCode(raw.pickupCode), raw.holdShelf));
            case "UNAVAILABLE" -> new Ok(new Unavailable(Reason.fromCode(raw.reasonCode)));
            case "WAITLISTED" -> raw.waitDays == null
                    ? new Rejected("waiting list without a wait")
                    : new Ok(new Waitlisted(Duration.ofDays(raw.waitDays)));
            case null, default -> new Rejected("unknown status: " + raw.status);
        };
    } catch (IllegalArgumentException e) {
        return new Rejected(e.getMessage());          // a constructor refused a value
    }
}"""
K_PARSE = """fun parse(raw: HoldReplyDto): Parsed = try {
    when (raw.status) {
        "READY" ->
            if (raw.pickupCode == null || raw.holdShelf == null) Rejected("ready without a code or a shelf")
            else Ok(Ready(PickupCode(raw.pickupCode), raw.holdShelf))
        "UNAVAILABLE" -> Ok(Unavailable(Reason.fromCode(raw.reasonCode)))
        "WAITLISTED" ->
            if (raw.waitDays == null) Rejected("waiting list without a wait")
            else Ok(Waitlisted(Duration.ofDays(raw.waitDays.toLong())))
        else -> Rejected("unknown status: ${raw.status}")
    }
} catch (e: IllegalArgumentException) {
    Rejected(e.message ?: "invalid reply")            // a constructor refused a value
}"""

S1 = """The sealed model helps only if untrusted data can't get in around it. So the program turns raw input into the model in exactly one place, at its edge: the code that reads the catalogue's message. Everything behind the edge works only with model values. In the picture, letters from outside arrive in any handwriting. One clerk at the door copies each onto the right form, or sends it back with a polite note saying what was wrong.

""" + pair(J_PARSE, K_PARSE) + """

Read `parse` from the top. It switches on the status string. A ready reply needs its code and its shelf, or it's rejected with a reason. An unavailable reply looks up its code in a small table of reasons. A waiting-list reply needs its days. Anything else, `null` included, is rejected. The tricky part is the `try` around it all: it catches the `IllegalArgumentException` a constructor throws when it refuses a value, and turns it into a `Rejected` too.

Two details make this work. The function never throws. A reply the model refuses comes back as `Rejected` with a reason. The caller decides what that means (log it, ask the catalogue again, tell the member to ask at the desk), and no exception escapes from somewhere deep inside. And the constructors stay the final check: `parse` doesn't repeat the pickup-code rule, it calls `new PickupCode(...)` and reports the refusal.

Behind the edge, nothing checks again. A method that takes a `Ready` knows it has a valid code and a real shelf, because no other kind of `Ready` can exist. Records and sealed types make this cheap: the model is a dozen lines, the edge is one function, and the compiler checks every switch in between. The lab builds exactly this, in Kotlin, including a case the snippets above skip: a ready reply that also carries a reason code contradicts itself, and must be rejected.

**Check outside data once, at the door. Behind the door, trust the types.**

Only good forms get in now. The next question is where the rules that read them should live."""

# ---------------------------------------------------------------- section 2
J_MSG = """static String screenMessage(HoldResult r) {
    return switch (r) {
        case Ready(var code, var shelf) -> "Your book is waiting on hold shelf " + shelf + ".";
        case Unavailable(var reason) when reason == Reason.ACCOUNT_BLOCKED -> "Please ask at the desk.";
        case Unavailable u -> "This title is not available right now.";
        case Waitlisted(var wait) -> "You're on the waiting list. Expected wait: " + wait.toDays() + " days.";
    };
}"""
K_MSG = """fun screenMessage(r: HoldResult): String = when (r) {
    is Ready -> "Your book is waiting on hold shelf ${r.shelf}."
    is Unavailable if r.reason == Reason.ACCOUNT_BLOCKED -> "Please ask at the desk."
    is Unavailable -> "This title is not available right now."
    is Waitlisted -> "You're on the waiting list. Expected wait: ${r.expectedWait.toDays()} days."
}"""

S2 = """In classic object-oriented design, behavior lives in the classes: `result.screenMessage()`, `result.nextStep()`, `result.reminderText()`, each written three times, across `Ready`, `Unavailable` and `Waitlisted`. Data-oriented code keeps the records plain and writes each operation as one function with a switch. In the picture, the forms stay plain, and the rules live in one binder at the desk:

""" + pair(J_MSG, K_MSG) + """

Everything about the screen at the self-service desk sits in one function. The records don't depend on screen text, and the next operation, say the text message sent to the member's phone, is a new function that touches nothing else. Note the account-blocked line: the screen stands in a public place, so it never says what's wrong with an account.

That's one side of the **expression problem**, which *Visitor, Iterator, Mediator and Memento* in the patterns track introduced. It says that no design makes both kinds of change cheap: adding a new type, and adding a new operation. With methods on the classes, adding a type is local, and adding an operation means editing every class. With sealed types and switches it's the other way round: a new operation is one function, and a new type breaks every switch until you handle it. The figure shows the grid. Choose by the change you expect more often.

For the library's data (hold results, desk events, loans, copy statuses) the set of types changes rarely, and new operations keep arriving: a new report, a new reminder, a new screen. So the data-oriented side wins there. For open hierarchies that others extend, such as the partner libraries' `PartnerItem` from lesson 2, keep an interface with methods. And behavior that's about the value itself, like `Shelfmark.next()`, belongs on the record. Keep the library's rules out of the records; small methods that compute with the value itself can stay.

The `ExpressionProblem` demo lets you pay both costs. Its `Activity` records what happened on a member's account, a book borrowed, returned or renewed, and two functions switch over it:

```text
borrowed Dune for 21 days
borrowed Emma for 21 days
returned Dune
renewed  Emma for 14 more days
books out: 1
```

Adding a third function changes no existing line. Adding a `Lost` activity breaks both switches, and the compiler lists each one.

**Plain data, rules in functions. A new rule then touches one place, and a new type is found by the compiler.**

Records and sealed types settle how the data is shaped. How the JVM stores that data is the last part of the story."""

# ---------------------------------------------------------------- section 3
J_VALUE = """value record Shelf(short floor, short row) {}        // JDK 28 early-access builds, --enable-preview"""
K_VALUE = """@JvmInline
value class Isbn(val value: String)                  // Kotlin today: one property, compiled away"""

S3 = """Records are identity objects, and lesson 1 showed what that means: `==` compares references, you can lock on a record, and every `new` makes a separate object. The `IdentityDemo` shows one more consequence. An array of records is an array of references, each pointing at a separate object on the heap, the memory where Java keeps its objects:

```text
equals: true, ==: false
shelf[0] == shelf[2]: true, shelf[0] == shelf[1]: false
```

In the paperwork picture, each record is a form in its own envelope, and the array is a list of where the envelopes are. Reading a form means walking to its envelope and opening it. **Project Valhalla**, a long-running OpenJDK project, wants small forms printed straight onto the page instead, with no envelope. Its first feature lets a class give up identity:

""" + pair(J_VALUE, K_VALUE) + """

The status is often misreported, so here it is precisely. JEP 401, Value Objects (Preview), is the JDK Enhancement Proposal for this feature. Together with JEP 539 (strict field initialization in the JVM), it was integrated into the JDK's main code line on 31 July 2026. JDK 27 had already branched off, so the feature ships in JDK 28, scheduled for 23 March 2027, and early-access builds of JDK 28 have it now. It's a preview: it needs `--enable-preview` and can still change. JDK 25, 26 and 27 don't have it.

The Valhalla docs define value objects as immutable objects that lack identity, "distinguished solely by the values of their fields". `==` compares two value objects by their fields, and identity operations such as `synchronized` fail. Two identical printed lines are interchangeable, and you can't seal an envelope that isn't there. In return, the JVM may store them flat. In JDK 28 that means two optimizations. **Flattening** stores a value's fields directly inside the field or array element that holds it, with no separate object and no reference. Scalarization lets code compiled by the JIT (the part of the JVM that turns busy code into machine code) keep the fields in registers and skip creating the object at all.

Here the picture breaks: you don't choose what gets printed onto the page, the JVM does, and only small forms qualify. Flattened values are read and written atomically, in one piece, and must allow null, so value objects with 64 bits or more of field data "cannot normally be flattened". By that rule, a record with a `long` and anything else is already too big. Scalarization only happens once C2, the JIT's optimizing compiler, has compiled the code, and variables of a general type, including those in generic APIs, aren't flattened. Records whose fields add up to less than 64 bits, such as two `short` fields, gain first.

With the preview on, 28 JDK classes become value classes, among them `Integer`, `Long`, `Optional`, `LocalDate`, `Instant` and `Duration`. Synchronizing on an `Integer` then throws `IdentityException`. Null-restricted types, the other thing people expect from Valhalla, are still draft JEPs.

Kotlin's `@JvmInline value class` is an older, different trick. It holds one property and is erased to that property where the compiler can: `javap`, the JDK's class-file reader, shows that `describeIsbn(Isbn)` compiles to `describeIsbn-3aCjwxg(java.lang.String)`, a plain `String` under a mangled name. It's boxed, that is, wrapped in a real `Isbn` object, when used as a generic `T`, an interface or a nullable type; the demo prints `in a List, the element is a Isbn`. Kotlin's design notes say the annotation leaves room for real Valhalla value classes later. No such mode has shipped, so a Kotlin data class on JDK 28 is still an identity object.

**Don't lean on a record's identity. Then `value` can be a one-word change later.**

In practice that means no `==` between records, no `synchronized` on them, and no maps keyed on identity."""

L = {
 "id": "dop-04",
 "title": "Data-oriented programming, and Project Valhalla",
 "minutes": 40,
 "goal": "By the end you can model a reply from outside so that contradictory states can't be built, parse untrusted input into that model at the edge, keep the rules in functions apart from the data, and say exactly what Project Valhalla has shipped and what it means for your records.",
 "opening": OPENING,
 "warmup": {
  "q": "In which JDK can you compile `value record Shelf(short floor, short row) {}` today?",
  "options": ["JDK 21: records are value types already, so `value` is just allowed",
              "JDK 25 LTS, with `--enable-preview`",
              "JDK 27, where value classes became final",
              "Only early-access builds of JDK 28, with `--enable-preview`"],
  "answer": 3,
  "why": "JEP 401 (value objects, preview) was integrated into the JDK's main code line after JDK 27 had branched off, so it arrives in JDK 28, scheduled for March 2027; early-access builds have it now. JDK 25, 26 and 27 don't. Records are identity objects on every released JDK: `==` compares references, and you can synchronize on them. The last section covers it."
 },
 "sections": [
  {
   "h": "Make illegal states unrepresentable",
   "body": S0,
   "try": {
    "title": "Count the shapes, then build a bad one",
    "minutes": 4,
    "steps": [
     "Run `IllegalStates` (or `IllegalStatesKt`). Read the `DTO consumer` line: what will the member find on the slip?",
     "In the Java demo, try to build a `Ready` with a reason code. There is no constructor for it: the shape doesn't exist.",
     "In the Kotlin twin, change `HoldResult.Ready(\"\", 12)` to `HoldResult.Ready(null, 12)` and run. Which tool stopped you this time?"
    ],
    "code": demo("IllegalStates"),
    "expect": "Both print `shapes the DTO allows: 48, shapes that make sense: 3`, then `DTO consumer:    print slip: shelf 12, code null`: nothing stopped a ready reply with no code. The sealed model refuses it (`pickupCode is required`), and the valid hold prints `print slip: shelf 12, code K7P2QX`. In Kotlin, `Ready(null, 12)` doesn't compile at all, because the property is a non-null `String`: the type system did the constructor's job."
   },
   "refs": [
    {"title": "Brian Goetz, Data Oriented Programming in Java (InfoQ, 2022)", "url": "https://www.infoq.com/articles/data-oriented-programming-java/", "kind": "read"}
   ]
  },
  {
   "h": "Parse at the edge, then trust the types",
   "body": S1,
   "try": {
    "title": "Predict what the door does",
    "minutes": 3,
    "steps": [
     "The catalogue sends `status: \"READY \"` (with a trailing space), pickup code `K7P2QX` and hold shelf 12. Which arm of `parse` takes it, and what does the pickup desk see?",
     "It sends a waiting-list reply with `waitDays: 0`. Does `parse` or a constructor produce the result?",
     "A teammate adds `if (ready.shelf() < 1) return;` inside the code that prints slips. Can that line ever run?"
    ],
    "expect": "The trailing space matches no status string, so `case null, default` returns `Rejected(\"unknown status: READY \")`, and the pickup desk never sees the reply: a strict door turns a sloppy reply into a visible rejection instead of a slip with bad data. The zero wait gets past `parse`, because the field isn't null, and is refused by the `Waitlisted` constructor once it has the range check (as the lab's does); the `catch` turns that refusal into `Rejected`. The teammate's line is dead code: a `Ready` with a shelf below 1 can't be built, so the check can never be true."
   }
  },
  {
   "h": "Keep the rules in one place: operations live outside the data",
   "body": S2,
   "figure": {"svg": FIG, "caption": "The expression problem: each style makes one kind of change local and the other kind expensive. Sealed types at least make the compiler find every place to change."},
   "try": {
    "title": "Pay both costs",
    "minutes": 6,
    "steps": [
     "Run `ExpressionProblem` (or `ExpressionProblemKt`).",
     "Write operation 3 where the comment says: `sendsReceipt`, true for borrowing and renewing (the member gets the new due date), false for returns. How many existing lines did you change?",
     "Add the `Lost` record (in Java, add it to `permits` too) and run. List the places the compiler asks you to change.",
     "Decide what a lost book does to the count of books out and to the history line, and handle it in each function."
    ],
    "code": demo("ExpressionProblem"),
    "expect": "The demo prints four history lines and `books out: 1`. Adding `sendsReceipt` changed no existing line. Adding `Lost` makes javac report each switch over `Activity` (`booksOutDelta`, `historyLine` and your new one) with `does not cover all possible input values`, and kotlinc asks for `the 'is Lost' branch` in each `when`. A new operation cost one function; a new type cost one edit per operation, and the compiler found every one."
   }
  },
  {
   "h": "Project Valhalla: forms printed straight onto the page",
   "body": S3,
   "try": {
    "title": "Look at identity, then at a Kotlin value class",
    "minutes": 4,
    "steps": [
     "Run `IdentityDemo`. Which of its lines would change if `Copy` were a value record?",
     "Run `IdentityDemoKt`.",
     "From `labs/`, run `javap -p modernjava/build/classes/kotlin/demo/workbench/modernjava/l04/demo/IdentityDemoKt.class`. What parameter type does `describeIsbn` take?"
    ],
    "code": demo("IdentityDemo"),
    "expect": "`equals: true, ==: false`, different identity hash codes, a successful `synchronized`, `Integer 127 == 127: true, 128 == 128: false`, and `shelf[0] == shelf[2]: true, shelf[0] == shelf[1]: false`. With a value record, `==` would compare fields, so `a == b` and `shelf[0] == shelf[1]` would be true, and `synchronized` would be refused. In Kotlin, `javap` shows `describeIsbn-3aCjwxg(java.lang.String)`: the value class is erased to a `String` under a mangled name, and the demo shows it boxed back into an `Isbn` when stored as `Any` or in a `List`."
   },
   "refs": [
    {"title": "JEP 401: Value Objects (Preview)", "url": "https://openjdk.org/jeps/401", "kind": "read"},
    {"title": "Inline value classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-classes.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "One model and one operation in Java and Kotlin",
  "java": {"title": "HoldResult.java", "src": """public record PickupCode(String value) {
    public PickupCode {
        if (value == null || !value.matches("[A-Z0-9]{6}")) throw new IllegalArgumentException("bad pickup code");
    }
}

public sealed interface HoldResult permits Ready, Unavailable, Waitlisted {}
public record Ready(PickupCode code, int shelf) implements HoldResult {
    public Ready {
        if (shelf < 1) throw new IllegalArgumentException("hold shelves start at 1");
    }
}
public record Unavailable(Reason reason) implements HoldResult {}
public record Waitlisted(Duration expectedWait) implements HoldResult {}

static String screenMessage(HoldResult r) {
    return switch (r) {
        case Ready(var code, var shelf) -> "Your book is waiting on hold shelf " + shelf + ".";
        case Unavailable(var reason) when reason == Reason.ACCOUNT_BLOCKED -> "Please ask at the desk.";
        case Unavailable u -> "This title is not available right now.";
        case Waitlisted(var wait) -> "You're on the waiting list. Expected wait: " + wait.toDays() + " days.";
    };
}"""},
  "kotlin": {"title": "HoldResult.kt", "src": """@JvmInline
value class PickupCode(val value: String) {
    init { require(value.matches(Regex("[A-Z0-9]{6}"))) { "bad pickup code" } }
}

sealed interface HoldResult {
    data class Ready(val code: PickupCode, val shelf: Int) : HoldResult {
        init { require(shelf >= 1) { "hold shelves start at 1" } }
    }
    data class Unavailable(val reason: Reason) : HoldResult
    data class Waitlisted(val expectedWait: Duration) : HoldResult
}

fun screenMessage(r: HoldResult): String = when (r) {
    is HoldResult.Ready -> "Your book is waiting on hold shelf ${r.shelf}."
    is HoldResult.Unavailable if r.reason == Reason.ACCOUNT_BLOCKED -> "Please ask at the desk."
    is HoldResult.Unavailable -> "This title is not available right now."
    is HoldResult.Waitlisted -> "You're on the waiting list. Expected wait: ${r.expectedWait.toDays()} days."
}"""},
  "note": "The design is identical: a closed set of outcomes, each with only its own fields, constructors that refuse bad values, and an operation written as one exhaustive switch outside the data. Two things differ. Java's switch takes `Ready` and `Unavailable` apart in the label, while Kotlin tests the type and reads `r.shelf` after a smart cast. And `PickupCode` is a record in Java, a full object with identity, while Kotlin's `@JvmInline value class` is usually erased to a plain `String`. With JDK 28's preview, Java could write `value record PickupCode(String value)` and give up identity at the JVM level, which Kotlin's value class doesn't do today."
 },
 "worked": {
  "title": "From the delivery van's report to a closed model",
  "steps": [
   {"say": "A van carries crates of books between the branches, and the van company's system sends a report at each stop. Its docs say: a `DELIVERED` report has an arrival date, a `DELAYED` report has a reason, and a `DAMAGED` report says how many books were damaged. The DTO encodes none of that.",
    "code": """public record VanReportDto(String type, String crateId, LocalDate arrivalDate,
                           String delayReason, Integer damagedBooks) {}""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """data class VanReportDto(val type: String?, val crateId: String?, val arrivalDate: LocalDate?,
                        val delayReason: String?, val damagedBooks: Int?)"""},
   {"say": "Write one record per row of the van company's docs. Every field is required, so a record can't be half a `DELIVERED` report.",
    "code": """// 1. one record per valid combination
public sealed interface VanReport permits Delivered, Delayed, Damaged {}
public record Delivered(String crateId, LocalDate arrivalDate) implements VanReport {}
public record Delayed(String crateId, String reason) implements VanReport {}
public record Damaged(String crateId, int books) implements VanReport {
    public Damaged {
        if (books <= 0) throw new IllegalArgumentException("a damage report needs at least one book");
    }
}""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """// 1. one class per valid combination, with non-null properties
sealed interface VanReport {
    data class Delivered(val crateId: String, val arrivalDate: LocalDate) : VanReport
    data class Delayed(val crateId: String, val reason: String) : VanReport
    data class Damaged(val crateId: String, val books: Int) : VanReport {
        init { require(books > 0) { "a damage report needs at least one book" } }
    }
}"""},
   {"say": "Write the edge. It's the only code that looks at the DTO, and it checks that each type carries its own field. A null where the docs promise a value becomes a clear error here, not a `NullPointerException` three methods later.",
    "code": """// 2. the edge: DTO in, model out
static VanReport toReport(VanReportDto d) {
    Objects.requireNonNull(d.crateId(), "crateId");
    return switch (d.type()) {
        case "DELIVERED" -> new Delivered(d.crateId(), Objects.requireNonNull(d.arrivalDate(), "arrivalDate"));
        case "DELAYED" -> new Delayed(d.crateId(), Objects.requireNonNull(d.delayReason(), "delayReason"));
        case "DAMAGED" -> new Damaged(d.crateId(), Objects.requireNonNull(d.damagedBooks(), "damagedBooks"));
        case null, default -> throw new IllegalArgumentException("unknown van report: " + d.type());
    };
}""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """// 2. the edge: DTO in, model out
fun toReport(d: VanReportDto): VanReport {
    val id = requireNotNull(d.crateId) { "crateId" }
    return when (d.type) {
        "DELIVERED" -> VanReport.Delivered(id, requireNotNull(d.arrivalDate) { "arrivalDate" })
        "DELAYED" -> VanReport.Delayed(id, requireNotNull(d.delayReason) { "delayReason" })
        "DAMAGED" -> VanReport.Damaged(id, requireNotNull(d.damagedBooks) { "damagedBooks" })
        else -> throw IllegalArgumentException("unknown van report: ${d.type}")
    }
}"""},
   {"say": "Now the code that acts on a report. The old version was thirty lines of `if (\"DELIVERED\".equals(type) && arrivalDate != null)`. The new one is a switch with no default, so a new kind of report from the van company shows up as a compile error, not as a report that is silently ignored.",
    "code": """// 3. behind the edge: trust the types
static void apply(VanReport r, Catalogue catalogue) {
    switch (r) {
        case Delivered(var id, var date) -> catalogue.markArrived(id, date);
        case Delayed(var id, var reason) -> catalogue.tellBranch(id, reason);
        case Damaged(var id, int books) -> catalogue.orderReplacements(id, books);
    }
}""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """// 3. behind the edge: trust the types
fun apply(r: VanReport, catalogue: Catalogue) = when (r) {
    is VanReport.Delivered -> catalogue.markArrived(r.crateId, r.arrivalDate)
    is VanReport.Delayed -> catalogue.tellBranch(r.crateId, r.reason)
    is VanReport.Damaged -> catalogue.orderReplacements(r.crateId, r.books)
}"""}
  ]
 },
 "lab": {
  "title": "Parse a catalogue reply into a model with no illegal states",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/HoldModel.kt", f"{lab}/main/{P}/HoldReplies.kt"],
  "run": "./gradlew :modernjava:test --tests 'workbench.modernjava.l04.*'",
  "steps": [
   "Run the tests: all ten fail. This lab is in Kotlin. The model is in `HoldModel.kt`, and the edge and the operation are in `HoldReplies.kt`.",
   "Make the model refuse what can't be real: write the `init` checks in `PickupCode`, `Ready` and `Waitlisted` (TODO 1 to 3). Three tests should pass now.",
   "Write `parse` (TODO 4) as one `when` on the status. Let the constructors do their own checks, and turn their `IllegalArgumentException` into `Rejected`.",
   "Write `screenMessage` (TODO 5) as one `when` with guards and no `else`.",
   "When all ten pass, add `data class Transferring(val fromBranch: String) : HoldResult` to the model and run `./gradlew :modernjava:compileKotlin`. Which function does kotlinc point at? Remove it again."
  ],
  "hints": [
   "A value class may have an `init` block: `init { require(Regex(\"[A-Z0-9]{6}\").matches(value)) { \"bad pickup code: $value\" } }`.",
   "`Duration` is `Comparable`, so `expectedWait >= Duration.ofDays(1) && expectedWait <= Duration.ofDays(365)` works in Kotlin.",
   "Wrap the whole `when` in `try { ... } catch (e: IllegalArgumentException) { Rejected(e.message ?: \"invalid reply\") }`. `Duration.ofDays(0)` is fine; it's `Waitlisted` that refuses it.",
   "After a branch like `raw.pickupCode == null -> Rejected(...)`, Kotlin smart-casts `raw.pickupCode` to `String` in the later branches, because it's a `val` of a class in the same module.",
   "A guard looks like `is Unavailable if result.reason == Reason.ACCOUNT_BLOCKED -> ...`."
  ],
  "done_when": "All ten tests in `HoldModelTest` pass."
 },
 "drill": {
  "title": "Model a reply from memory",
  "minutes": 5,
  "prompt": "Close this page. A renewal reply has a `type` (`\"GRANTED\"`, `\"REFUSED\"` or `\"QUEUED\"`), a `loanId`, and a `refusalCode` that is present only when the renewal was refused. Write the sealed model in Java so that a refusal can't lack its code, and a `parse(type, loanId, refusalCode)` that throws `IllegalArgumentException` for an unknown or missing type. Then write the Kotlin version.",
  "answer": {"lang": "java", "src": """sealed interface RenewalReply permits Granted, Refused, Queued {}
record Granted(String loanId) implements RenewalReply {}
record Refused(String loanId, String refusalCode) implements RenewalReply {
    Refused { Objects.requireNonNull(refusalCode, "refusalCode"); }   // a refusal always has a code
}
record Queued(String loanId) implements RenewalReply {}

static RenewalReply parse(String type, String loanId, String refusalCode) {
    return switch (type) {
        case "GRANTED" -> new Granted(loanId);
        case "REFUSED" -> new Refused(loanId, refusalCode);
        case "QUEUED" -> new Queued(loanId);
        case null, default -> throw new IllegalArgumentException("unknown renewal reply: " + type);
    };
}""",
             "alt": {"lang": "kotlin", "src": """sealed interface RenewalReply {
    data class Granted(val loanId: String) : RenewalReply
    data class Refused(val loanId: String, val refusalCode: String) : RenewalReply   // non-null: always has a code
    data class Queued(val loanId: String) : RenewalReply
}

fun parse(type: String?, loanId: String, refusalCode: String?): RenewalReply = when (type) {
    "GRANTED" -> RenewalReply.Granted(loanId)
    "REFUSED" -> RenewalReply.Refused(loanId, requireNotNull(refusalCode) { "refusalCode" })
    "QUEUED" -> RenewalReply.Queued(loanId)
    else -> throw IllegalArgumentException("unknown renewal reply: $type")
}"""}}
 },
 "recap": [
  "Model each valid combination as its own record under a sealed interface, and check values in the constructors. A shape that can't be written down can't reach your code.",
  "Records are product types (this and that) and sealed interfaces are sum types (this or that). Most messages are a few alternatives, each a fixed set of fields.",
  "Parse untrusted input into the model once, at the edge, and return a result instead of throwing. Behind the edge, trust the types.",
  "Write the rules as functions that switch over the data. A new operation is one function; a new type breaks every switch, and the compiler lists them. Keep interfaces with methods for hierarchies others extend.",
  "Valhalla's value objects are a preview in JDK 28 (early-access builds now, release scheduled for March 2027), not in JDK 25, 26 or 27. Records are identity objects, so don't depend on their identity.",
  "The limit: the model is only as good as its edge. Data that skips `parse`, or a nullable status field sneaked back into the records, brings the 48 shapes back."
 ],
 "closing": "We started with one form for the catalogue's answer and 48 ways to fill it in. Three records under a sealed interface left only the 3 that make sense, one clerk at the door checked everything from outside, and the rules moved into functions with one switch each. Valhalla may one day print small forms straight onto the page, but today a record is still a form in its own envelope.\n\nNow look in your own code for a class with a status field and several nullable fields beside it. Count its shapes.\n\nThat ends this track. Next, we'll start Advanced Kotlin with inline functions. What happens when the compiler pastes a function and its lambda straight into the caller?",
 "quiz": [
  {"q": "The catalogue's DTO has a `status` and four nullable fields, and its docs list three valid combinations. What does a sealed model with three records give you that careful checks in every reader of the DTO don't?",
   "options": ["Faster JSON reading", "Invalid combinations can't be built, so no code behind the edge can receive one", "Nothing, as long as every reader checks", "Smaller objects on the heap"],
   "answer": 1, "why": "With the sealed model the bad shapes don't exist, and the constructors refuse bad values once. Checking in every reader works only until one reader forgets, and the DTO keeps letting 45 nonsense shapes travel through the program. Neither the reading speed nor the object size changes."},
  {"q": "New partner libraries join the regional network every month, each with its own module, and each must answer `loanDays()` for the items it lends. Which design fits?",
   "options": ["An enum listing all partner libraries", "A sealed interface of records, with one switch in the library's own module", "An interface `PartnerItem` with a `loanDays()` method that each partner implements", "A sealed interface whose switch has a `default` branch for partners it doesn't know"],
   "answer": 2, "why": "Here the set of types grows and the operation stays the same, and the types live in other modules: the object-oriented side of the expression problem. A sealed hierarchy would force every new partner into the library's module and break its switch each month. A default would just hide the new partners."},
  {"q": "Which statement about Project Valhalla is accurate?",
   "options": ["JDK 25 LTS ships value classes as a preview", "Records became value objects in JDK 27", "Null-restricted types such as `String!` are final in JDK 28", "JEP 401 value objects are a preview feature of JDK 28; JDK 25, 26 and 27 don't have them"],
   "answer": 3, "why": "JEP 401 was integrated after JDK 27 branched off, so it ships in JDK 28 (scheduled for March 2027) as a preview. Records are still identity objects; `value record` is only legal under that preview. Null-restricted types are still draft JEPs."},
  {"q": "From *Visitor, Iterator, Mediator and Memento*: you replaced a Visitor over a sealed `Expr` with switch functions. Now a new node type, `Pow`, arrives. What does each design make you do?",
   "options": ["Visitor: add `visitPow` to the interface and to every visitor. Switches: every switch fails to compile until it handles `Pow`", "Visitor: nothing. Switches: nothing, because sealed types accept new records", "Visitor: one new class. Switches: one new function", "Both: only add the new record"],
   "answer": 0, "why": "Visitor and sealed switches sit on the same side of the expression problem: adding a type is the expensive change in both. The difference is that the switches need no `accept` and no visitor interface, and the compiler points at each switch to fix.",
   "from": "pat-10"},
  {"q": "`@JvmInline value class Isbn(val value: String)` and `fun describe(i: Isbn)`. What does the JVM see for `describe(isbn)` and for `listOf(isbn)`?",
   "options": ["Two ordinary `Isbn` objects, like any class", "A `String` in both places", "`describe` takes a `String` under a mangled name, and the list holds a boxed `Isbn`", "A Valhalla value object, flattened in both places"],
   "answer": 2, "why": "Kotlin erases the value class to its one property where it can, so `describe` compiles to something like `describe-XXXX(String)`. Used as a generic `T`, as in a `List`, it must be boxed into a real `Isbn` object. None of this uses Valhalla: it's compile-time work, and it runs on any JVM."}
 ],
 "flashcards": [
  {"front": "What does \"make illegal states unrepresentable\" mean in Java and Kotlin?", "back": "Model each valid combination as its own record (or data class) under a sealed type, and check values in the constructors, so an invalid value can't be built."},
  {"front": "Record and sealed interface, in algebraic terms?", "back": "A record is a product type: this and that. A sealed interface is a sum type: this or that."},
  {"front": "Where should untrusted input be checked?", "back": "Once, at the edge: one parse function turns the DTO into the model or a rejection. Code behind the edge trusts the types."},
  {"front": "With sealed types and switches, what does adding an operation cost? And a type?", "back": "An operation is one new function. A type breaks every exhaustive switch over the hierarchy, and the compiler lists each one."},
  {"front": "When do you keep an interface with methods instead of a sealed type?", "back": "For open hierarchies that others extend (plug-ins, partner libraries' items), and for behavior about the value itself, like `Shelfmark.next()`."},
  {"front": "Which JDK has JEP 401 value objects?", "back": "JDK 28, as a preview feature (scheduled for March 2027; early-access builds now). Not JDK 25, 26 or 27."},
  {"front": "Why won't `value record Copy(long isbn13, int number)` normally be flattened in JDK 28?", "back": "Flattened values must be read and written atomically and allow null, so values with 64 bits or more of field data aren't normally flattened. The `long` alone is 64 bits."}
 ],
 "terms": [
  {"term": "Data-oriented programming", "plain": "Modeling data as immutable records and sealed types, and writing the rules as functions that switch over them."},
  {"term": "Product type", "plain": "A type whose value is several values together, like a record: a code and a shelf."},
  {"term": "Sum type", "plain": "A type whose value is one of a fixed set of alternatives, like a sealed interface: ready, unavailable or waitlisted."},
  {"term": "Illegal state", "plain": "A combination of field values that can't happen in real life, such as ready with a reason code."},
  {"term": "Expression problem", "plain": "No design makes both new types and new operations cheap; you pick the side that matches how your code changes."},
  {"term": "Value object", "plain": "Valhalla's object without identity: compared by its fields, and free for the JVM to copy or flatten. Preview in JDK 28."},
  {"term": "Flattening", "plain": "Storing a value object's fields directly inside the field or array that holds it, instead of a reference to a separate object."}
 ],
 "explain_back": {
  "prompt": "Your team lead asks: \"Should we move the library's data to records and sealed types now, or wait for Valhalla to make it fast?\" Answer in your own words: what the data-oriented style gives you today, where you would and wouldn't use it, and what Valhalla changes.",
  "answer": "The data-oriented style pays off today, with no new JDK: records and sealed types are standard since JDK 17, and pattern switches since 21. Modeling each valid outcome as its own record means contradictory states can't be built, parsing at the edge means only valid values get in, and exhaustive switches mean the compiler tells us every place to update when a type is added. I'd use it for closed data such as hold results, desk events and copy statuses, and keep ordinary interfaces for things others extend, like the partner libraries' items. Valhalla changes performance and identity; it doesn't change this design. JEP 401 is only a preview in JDK 28, and even there, a record with a `long` and anything else wouldn't normally be flattened. So we shouldn't wait for it; we should just avoid depending on record identity, so that adding `value` later is easy."
 },
 "deeper": {
  "minutes": 8,
  "body": """Brian Goetz's January 2026 design note, "Data-Oriented Programming for Java: Beyond Records", says where Project Amber, the OpenJDK project behind records and patterns, goes next. It calls records, sealed classes and record patterns "the first feature arc of 'data-oriented programming' for Java", and announces the next arc: *carrier classes* and carrier interfaces. A carrier class is a normal class with a record-style state description in its header. It would declare its own fields and need not be final, yet still have a canonical constructor, accessors and a deconstruction pattern. So data that is almost a record (one cached field, one derived value) wouldn't force you back to writing everything by hand.

The note also describes reconstruction, the `with` expression from JEP 468, and points out how much its block resembles a compact constructor body: the component variables start with the old values, your block changes some of them, and the canonical constructor builds the new value, so the checks still run. Goetz explains that JEP 468 has been "on hold" until there was a path to extend it beyond records. The note also mentions an upcoming pattern assignment statement, for taking a record apart in an ordinary assignment.

None of this is in a JDK or a JEP you can use. The design direction is useful anyway: it says the language will keep making "model the data with records and sealed types, switch over it" cheaper, so code written in that style today is code the platform is moving toward.

On the Valhalla side, the next pieces on the project page are null-restricted storage, array improvements, unifying primitives with classes, and a JVM that can specialize generic code for each type it's used with. Only the first piece, value objects, has a JEP that has been integrated, and it's a preview."""
 },
 "sources": [
  {"title": "Brian Goetz, Data Oriented Programming in Java (InfoQ, 2022)", "url": "https://www.infoq.com/articles/data-oriented-programming-java/"},
  {"title": "Brian Goetz, Data Classes and Sealed Types for Java (2019)", "url": "https://github.com/openjdk/amber-docs/blob/master/site/design-notes/records-and-sealed-classes.md"},
  {"title": "Brian Goetz, Data-Oriented Programming for Java: Beyond Records (2026)", "url": "https://github.com/openjdk/amber-docs/blob/master/site/design-notes/beyond-records.md"},
  {"title": "Project Valhalla (OpenJDK)", "url": "https://openjdk.org/projects/valhalla/"},
  {"title": "Inline value classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-classes.html"}
 ]
}
out = ROOT / "content/lessons/dop-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
