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


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 700 270" role="img" aria-label="The record pattern Loan(Member(var id, int age), Book(var format, var isNew), var b) '
    'matched against a loan: each nested pattern reads one component through its accessor and binds id, age, format, isNew and b">'
    '<text class="t-s t-code" x="350" y="24" text-anchor="middle">case Loan(Member(var id, int age), Book(var format, var isNew), var b)</text>'
    '<rect class="box-a" x="290" y="46" width="120" height="38" rx="8"/>'
    '<text class="t t-code" x="350" y="70" text-anchor="middle">Loan</text>'
    '<line class="ln" x1="330" y1="84" x2="125" y2="130" marker-end="url(#arr)"/>'
    '<line class="ln" x1="350" y1="84" x2="350" y2="130" marker-end="url(#arr)"/>'
    '<line class="ln" x1="370" y1="84" x2="575" y2="130" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="205" y="102" text-anchor="middle">member()</text>'
    '<text class="t-s t-m" x="358" y="112">item()</text>'
    '<text class="t-s t-m" x="500" y="102" text-anchor="middle">branch()</text>'
    '<rect class="box" x="20" y="132" width="210" height="44" rx="8"/>'
    '<text class="t-s t-code" x="125" y="159" text-anchor="middle">Member("M-1042", 34)</text>'
    '<rect class="box" x="250" y="132" width="200" height="44" rx="8"/>'
    '<text class="t-s t-code" x="350" y="159" text-anchor="middle">Book(LARGE_PRINT, false)</text>'
    '<rect class="box" x="470" y="132" width="210" height="44" rx="8"/>'
    '<text class="t-s t-code" x="575" y="159" text-anchor="middle">Branch.BUS</text>'
    '<line class="ln-a" x1="125" y1="176" x2="125" y2="196" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="350" y1="176" x2="350" y2="196" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="575" y1="176" x2="575" y2="196" marker-end="url(#arr)"/>'
    '<text class="t-s t-ok" x="125" y="214" text-anchor="middle">id = "M-1042", age = 34</text>'
    '<text class="t-s t-ok" x="350" y="214" text-anchor="middle">format = LARGE_PRINT, isNew = false</text>'
    '<text class="t-s t-ok" x="575" y="214" text-anchor="middle">b = BUS</text>'
    '<text class="t-s t-m" x="350" y="252" text-anchor="middle">each nested pattern calls one accessor, checks the type, and binds the parts</text>'
    '</svg>'
)

OPENING = """At the lending desk, a clerk picks up each item a member wants to borrow, looks at it once, and stamps a due date. A large-print book gets six weeks. A new release gets one week, because other people are waiting for it. A box set of DVDs gets two. One look tells the clerk what kind of item it is and reads the stickers on its label at the same time. The clerk works down a printed instruction sheet, and the first line that fits wins.

Java code used to sort things the slow way: `instanceof`, a cast, a getter, then another `instanceof`. It works, and it hides two traps. Nothing checks that the chain covers every kind of item, and nothing checks that a line further down can ever be reached.

Sealed types, in the last lesson, gave the compiler the complete list of kinds. In this lesson, we'll give that list to a clerk who can use it: a switch the compiler checks, record patterns that read several boxes in one look, guards that decide the order, and the odd things that happen with null. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_FLOW = """if (!(o instanceof Book b)) return "not a book";
return "by " + b.author();               // b is in scope: the test can't have failed here"""
K_FLOW = """if (o !is Item.Book) return "not a book"
return "by ${o.author}"                  // smart cast: o is a Book from here on"""
J_CHAIN = """// an if-chain: javac never checks that it covers every Item
if (i instanceof Book b) return "book " + b.title() + " by " + b.author();
else if (i instanceof Disc d) return "disc " + d.title() + ", " + d.minutes() + " min";
else if (i instanceof Magazine m) return "magazine " + m.title() + " #" + m.issue();
else throw new IllegalStateException("unreachable?");

// a pattern switch: javac checks that every Item is covered
return switch (i) {
    case Book b -> "book " + b.title() + " by " + b.author();
    case Disc d -> "disc " + d.title() + ", " + d.minutes() + " min";
    case Magazine m -> "magazine " + m.title() + " #" + m.issue();
};"""
K_CHAIN = """// an if-chain: kotlinc never checks that it covers every Item
if (i is Item.Book) "book ${i.title} by ${i.author}"
else if (i is Item.Disc) "disc ${i.title}, ${i.minutes} min"
else if (i is Item.Magazine) "magazine ${i.title} #${i.issue}"
else throw IllegalStateException("unreachable?")

// when with a subject: kotlinc checks that every Item is covered
when (i) {
    is Item.Book -> "book ${i.title} by ${i.author}"
    is Item.Disc -> "disc ${i.title}, ${i.minutes} min"
    is Item.Magazine -> "magazine ${i.title} #${i.issue}"
}"""

S0 = """A **pattern** is a test with a binding. `Book b` asks "is this value a `Book`?" and, if it is, gives you a new variable `b` of type `Book`. Pattern matching came to Java in steps. JDK 16 made `instanceof` patterns final (JEP 394): the type test and the cast become one, and the binding is in scope wherever the test is known to have passed:

""" + pair(J_FLOW, K_FLOW) + """

JDK 21 made pattern `switch` final (JEP 441), together with record patterns (JEP 440). Here are two ways to describe an item at the desk, both from the `PatternBasics` demo:

""" + pair(J_CHAIN, K_CHAIN) + """

Both print the same three lines, starting with `book Emma by Jane Austen`. It's tempting to read the switch as a tidier chain, but the differences are the reason to prefer it. Delete the `Magazine` line from the chain, and it still compiles; the run reaches the magazine and dies in the chain's `IllegalStateException`. Delete the `Magazine` case from the switch, and javac refuses: `the switch expression does not cover all possible input values`. A pattern switch used as a statement must be exhaustive too.

javac checks two more things the chain never gets: dominance, that is, whether each case can ever be reached (the third section), and fixed rules for `null` (the fourth). One level down, javac compiles the switch to one `invokedynamic` call to `SwitchBootstraps.typeSwitch`, which works out the first matching case, plus a hidden last arm that throws `MatchException` if nothing matches at run time. Hold on to that hidden arm; it comes back at the end of the lesson.

Kotlin has had most of this for years. A `when` with a subject checks exhaustiveness over a sealed type, whether you use it as an expression or a statement, and a smart cast merges the `is` check with the cast. `javap` shows that kotlinc 2.4, with the JDK 21 target, compiles that `when` to the same `typeSwitch` call; its hidden arm throws `NoWhenBranchMatchedException` instead.

In the paperwork picture, the switch is a clerk whose printed sheet lists every kind of item the library has. The chain is a clerk who remembers the kinds. Mostly.

**A chain of instanceof checks can't be checked. Switch over the sealed type instead.**

What Kotlin doesn't have is the subject of the next section: reading the boxes inside the item, in the same look."""

# ---------------------------------------------------------------- section 1
J_LOAN = """return switch (loan) {
    case Loan(var m, Book(var format, var isNew), var b) when format == Format.LARGE_PRINT -> 42;
    case Loan(var m, Book(var format, var isNew), var b) when isNew -> 7;
    case Loan(var m, Book book, var b) when b == Branch.BUS -> 28;
    // ...
};"""
K_LOAN = """val item = loan.item                         // pick the nested part out first
return when (item) {
    is Book if item.format == Format.LARGE_PRINT -> 42
    is Book if item.newRelease -> 7
    is Book if loan.branch == Branch.BUS -> 28
    // ...
}"""

S1 = """A type pattern tests a type and binds one variable. A **record pattern** also takes a record apart, through its accessors, and each part can be a pattern too. In the picture, the clerk reads several boxes in one look, including the boxes on a smaller form clipped inside the first.

The lab's loan rules show it. A `Loan` records who borrows (a `Member`), what (an `Item`), and from which branch (a `Branch`, where `BUS` is the library bus that comes back every four weeks). Here are the first rules, next to the closest Kotlin. The `when` after each pattern is a guard, an extra condition that the next section covers:

""" + pair(J_LOAN, K_LOAN) + """

Read the Java label from the outside in. The selector, the value in `switch (...)`, must be a `Loan`. Its `member()` binds to `m`. Its `item()` must match `Book(var format, var isNew)`, which binds the book's two boxes. Its `branch()` binds to `b`. With `var`, javac infers each type from the record's components. The figure shows one pattern that reads every box at once, three levels deep.

Patterns are positional and type-checked. Put `String x2` where a record has an `int`, as the Try it does, and javac stops with `incompatible types: int cannot be converted to String`. Generic records work too: over `sealed interface Result<T>`, the case `Ok<T>(var v)` binds `v` as a `T`. Record patterns also work in `instanceof`, as in `if (o instanceof Line(Point(var x, var y), var to) && x == 0)`.

Kotlin has no record patterns. The closest tools are smart casts on nested properties, as in the twin above, and positional destructuring, `val (from, to) = line`, through `component1()` and `component2()`. Destructuring has a trap that Java's patterns mostly avoid: it goes by position, not by name. With `data class Book(val title: String, val pages: Int)`, the line `val (pages, title) = book` compiles without a warning. The demo prints `swapped names: pages=Dune title=412`, a very long book with a very short title.

Kotlin 2.3.20 added name-based destructuring as an Experimental feature, behind `-Xname-based-destructuring`; its `name-mismatch` mode warns about exactly that line. Java's record patterns are positional too, but every component is type-checked, so most swaps fail to compile. Two `var` bindings of the same type can still be swapped silently, so keep the record header in front of you.

One look now reads every box. The clerk still needs to know which line of the sheet to try first."""

# ---------------------------------------------------------------- section 2
J_GUARD = """case Book(var format, var isNew) when format == Format.LARGE_PRINT -> 42;   // 1
case Book(var format, var isNew) when isNew -> 7;                          // 2
case Book(var format, var isNew) -> 21;                                    // 3"""
K_GUARD = """is LoanItem.Book if i.format == Format.LARGE_PRINT -> 42   // 1
is LoanItem.Book if i.newRelease -> 7                      // 2
is LoanItem.Book -> 21                                     // 3"""

S2 = """Cases are tried from the top, and the first one whose pattern matches and whose guard is true wins. The **guard** is the `when` clause after a pattern (`if` in Kotlin). That makes order part of the meaning, exactly as on the clerk's sheet. A new large-print book matches both of the first two lines of the `GuardsDemo`, so whichever comes first sets its loan:

""" + pair(J_GUARD, K_GUARD) + """

The demo prints `42 days` for it. Swap lines `// 1` and `// 2`, and it prints `7 days`, and nothing else changes. javac accepts both orders, because a guarded case never dominates another. Only a test that sends a new large-print book through the switch can tell you which order you meant.

Guards don't count toward exhaustiveness, in either language. The compiler can't prove that a set of guards covers every value, so a family of guarded cases must end with an unguarded case of the same pattern. Delete line `// 3`, and javac says the switch doesn't cover all possible input values, while kotlinc asks you to `Add the 'is Book' branch`.

You can predict javac's verdict yourself. List the permitted subtypes of the selector's type, and cross off each one that has an unguarded case, or that sits under a sealed parent with one. Inside record patterns, check combinations, not columns. With `Pair(Red a, Red b)` and `Pair(Green a, Light b)`, the `Red` cases cover only `Red` in second place, so `Pair(Red, Green)` is missing. Whatever is left over is what JDK 27 prints under `missing patterns:`.

javac also rejects a case that can never be reached, with `this case label is dominated by a preceding case label`. That happens when an earlier unguarded case already matches everything the later one could. Move line `// 3` above line `// 1`, and javac rejects both guarded lines. Other examples are `case String s` after `case CharSequence cs`, and a constant `case 1` after an unguarded `case Integer i`.

kotlinc has no dominance check at all. Put the unguarded `is LoanItem.Book` first, and it compiles without a warning; every book then gets 21 days, large print and new releases included. Here kotlinc shrugs where javac objects. Kotlin guards (`is T if condition`) have been stable since Kotlin 2.2.

**The sheet is read from the top. Put the most specific rule first, and end each family with an unguarded case.**

Several patterns can share one arm only if they bind nothing. On JDK 21 that makes such arms awkward: `case Return ret, Renew ren ->` fails with `illegal fall-through from a pattern`, so you write two arms. JDK 22 made unnamed patterns final, and `case Return _, Renew _ ->` is legal. `_` also stands in for a component you don't need, as in `case Borrow(var member, _)`. On JDK 21 it's a preview feature, and javac stops with `unnamed variables are a preview feature and are disabled by default`.

The sheet now has the right lines in the right order. What happens when the clerk is handed a blank sheet, or a form that didn't exist when the sheet was printed?"""

# ---------------------------------------------------------------- section 3
J_NULL = """return switch (section) {
    case null -> "missing";
    case "FIC" -> "fiction";
    default -> "other";          // default alone does not catch null
};"""
K_NULL = """return when (section) {         // section is a String?
    null -> "missing"
    "FIC" -> "fiction"
    else -> "other"              // without the null branch, null lands here
}"""

S3 = """`switch` has always thrown `NullPointerException` on a null selector, and a pattern switch keeps that rule unless you opt in with `case null`. In the picture, a blank sheet handed over the counter stops the clerk, unless the instruction sheet has a line for blank sheets:

""" + pair(J_NULL, K_NULL) + """

`default` alone doesn't catch null, and `case null, default ->` handles both in one arm. For most code, the OpenJDK guide on sealed switches prefers something simpler: reject null before the switch, with `Objects.requireNonNull`, because a null that reaches the rules is a bug somewhere upstream. Kotlin settles the question in the type system. A `when` over a nullable subject must handle null somewhere (kotlinc says `Add the 'null' branch or an 'else' branch.` if it doesn't), and nothing throws. So the `NullDemo` prints `plain(null): NullPointerException` in Java and `plainWhen(null): other` in Kotlin.

Inside a record pattern, null follows a rule that surprises everyone once. A nested record pattern never matches null, but a nested type pattern that covers the whole component type does. Take `case Line(Point(var x1, var y1), Point(var x2, var y2)) when x1 == x2` first and `case Line(Point from, Point to)` second. A `Line` whose start is null skips the first case and lands in the second, with `from` bound to null. Change the second case to `Line(Point(var a, var b), Point to)`, and javac still calls the switch exhaustive. But that `Line` now matches nothing, and the switch throws `MatchException`.

That points at the bigger limit: exhaustive is a compile-time promise. javac checks the switch against the subtypes it can see when it compiles. The values it can't see, which the Amber design notes call the **remainder**, are left to that hidden last arm at run time. The `javac/remainder` experiment compiles a client against `Status permits Active, Closed`, a member's account status. Then it recompiles only the hierarchy, with a third status, `Frozen`, and runs the old client:

```text
active, priority 1
sealed switch: java.lang.MatchException
enum switch:   java.lang.MatchException
```

The old switch met a status it had never heard of, and the hidden arm threw. An enum switch with no default does the same when it meets a constant added later, and an old Kotlin `when` throws `kotlin.NoWhenBranchMatchedException`. You don't write code for the remainder, but in a program that mixes old and new jars, this is the exception you'll see. Recompile the client, and javac turns it back into a compile error, `the switch expression does not cover all possible input values`, twice.

**Exhaustive means exhaustive for the list javac saw. Recompile when the list changes.**

In the picture, this is a new kind of form printed after the clerk's sheet was written. Here the picture breaks: a real clerk would ask a colleague. The switch can't ask anyone, so it stops loudly, which beats guessing quietly."""

L = {
 "id": "dop-03",
 "title": "Pattern matching with switch and record patterns",
 "minutes": 40,
 "goal": "By the end you can write an exhaustive switch with nested record patterns and guards in the right order, predict what it does with null and with a subtype added after compilation, and read javac's exhaustiveness and dominance errors.",
 "opening": OPENING,
 "warmup": {
  "q": "The clerk's rules are written as a switch, in this order: `case Book b when b.newRelease() -> 7;`, then `case Book b when b.format() == LARGE_PRINT -> 42;`, then `case Book b -> 21;`. How many days does a new large-print book get?",
  "options": ["42, because the more specific rule wins",
              "7, because cases are tried from the top and the first match wins",
              "It doesn't compile: two guarded cases for the same type are ambiguous",
              "It doesn't compile: the large-print case is dominated by the new-release case"],
  "answer": 1,
  "why": "Java tries the cases in order and runs the first one whose pattern matches and whose guard is true. Both guards are true for a new large-print book, so the new-release rule wins. javac doesn't compare guards, so it can't tell that the large-print rule is shadowed for new releases: a guarded case never dominates another. Put the large-print rule first, as the section on guards shows."
 },
 "sections": [
  {
   "h": "A pattern switch is checked, an instanceof chain is not",
   "body": S0,
   "try": {
    "title": "See which one the compiler catches",
    "minutes": 5,
    "steps": [
     "Run `PatternBasics` (or `PatternBasicsKt`) with the command below.",
     "Delete the `Magazine` line from `viaChain` and run. Put it back, then delete the `Magazine` case from `viaSwitch` and run again. Which mistake did the compiler catch?",
     "From `labs/`, run `javap -c -p modernjava/build/classes/java/demo/workbench/modernjava/l03/demo/PatternBasics.class` and find `typeSwitch` and `MatchException` in `viaSwitch`.",
     "Run the same `javap` on `modernjava/build/classes/kotlin/demo/workbench/modernjava/l03/demo/PatternBasicsKt.class` and look at `viaWhen`."
    ],
    "code": demo("PatternBasics"),
    "expect": "Both versions print the same three lines and `by Jane Austen, not a book`. Without its `Magazine` branch the chain still compiles, and the run crashes on the magazine with the chain's `IllegalStateException`. Without its `Magazine` case the switch doesn't compile: `the switch expression does not cover all possible input values` (kotlinc: `Add the 'is Magazine' branch or an 'else' branch.`). In the bytecode, `viaSwitch` has `invokedynamic ... typeSwitch` and `new java/lang/MatchException`; the Kotlin `viaWhen` has the same `typeSwitch` call and `new kotlin/NoWhenBranchMatchedException`."
   },
   "refs": [
    {"title": "JEP 441: Pattern Matching for switch", "url": "https://openjdk.org/jeps/441", "kind": "read"}
   ]
  },
  {
   "h": "Record patterns read several boxes in one look",
   "body": S1,
   "figure": {"svg": FIG, "caption": "One record pattern, three levels deep: the loan, its components, and the parts of each component, all bound in the case label."},
   "try": {
    "title": "Take a line apart",
    "minutes": 4,
    "steps": [
     "Predict the third line of output, then run `RecordPatterns`.",
     "In `describe`, change `Point(int x2, int y2)` to `Point(String x2, int y2)` and run. Read the first error, then undo it.",
     "Run the Kotlin twin, `RecordPatternsKt`, and read its last line."
    ],
    "code": demo("RecordPatterns"),
    "expect": "`vertical at x=1 len 5`, `horizontal at y=3`, `diagonal Point[x=0, y=0]->Point[x=2, y=2]`, then `ok [1, 2]`, `err boom caused by RuntimeException` and `from origin to Point[x=9, y=9]`. The `String` change fails with `incompatible types: int cannot be converted to String` (and a second error, because `x1 == x2` now compares an `int` with a `String`). The Kotlin twin prints the same results with smart casts, and then `swapped names: pages=Dune title=412`: positional destructuring put the title into `pages` without a warning."
   },
   "refs": [
    {"title": "JEP 440: Record Patterns", "url": "https://openjdk.org/jeps/440", "kind": "read"},
    {"title": "Destructuring declarations (Kotlin docs)", "url": "https://kotlinlang.org/docs/destructuring-declarations.html", "kind": "docs"}
   ]
  },
  {
   "h": "Guards, order and dominance: the sheet is read from the top",
   "body": S2,
   "try": {
    "title": "Reorder the loan rules",
    "minutes": 6,
    "steps": [
     "Run `GuardsDemo` and note the loan for the new large-print book, `Book[format=LARGE_PRINT, newRelease=true]`.",
     "Swap the lines marked `// 1` and `// 2`. Predict which loan changes, then run.",
     "Undo. Move line `// 3` above line `// 1` and run. Do the same in `GuardsDemoKt`.",
     "Undo. Delete line `// 3` and run both versions.",
     "If you have JDK 22 or newer, run `java preview/UnnamedPatterns.java` from `labs/modernjava`, then try the same file on JDK 21."
    ],
    "code": demo("GuardsDemo"),
    "expect": "The new large-print book gets 42 days. After the swap it gets 7, and nothing else changes: the new-release rule now matches it first. With line 3 on top, javac rejects lines 1 and 2 with `this case label is dominated by a preceding case label`, while the Kotlin version compiles and gives every book 21 days. Without line 3, javac reports `the switch expression does not cover all possible input values` and kotlinc asks for `the 'is Book' branch`. On JDK 22 or newer the preview file prints `lend to M-1042`, `take off the shelf: water damage` and `not on loan` twice; JDK 21 rejects the `_`."
   },
   "refs": [
    {"title": "Guard conditions in when expressions (Kotlin docs)", "url": "https://kotlinlang.org/docs/control-flow.html", "kind": "docs"}
   ]
  },
  {
   "h": "Null, default and the remainder",
   "body": S3,
   "try": {
    "title": "Feed a switch null, then a stranger",
    "minutes": 6,
    "steps": [
     "Run `NullDemo` and `NullDemoKt` and compare their first lines.",
     "In the Java `describe`, change `case Line(Point from, Point to)` to `case Line(Point(var a, var b), Point to)` (and use `a` and `b` in the text). Predict: does it compile? What happens to the line with a null start?",
     "Run the separate-compilation experiment in `labs/modernjava/javac/remainder`. The five commands are at the top of `Client.java`."
    ],
    "code": demo("NullDemo"),
    "expect": "Java prints `plain(null): NullPointerException`; Kotlin prints `plainWhen(null): other`, because its `when` compares with `equals` and the type allowed null. Both print `missing`, then `null or other` twice, then a line whose start is `null`. After the change in step 2 the switch still compiles, and the null-start line throws `java.lang.MatchException`. In the experiment, the first run prints `active, priority 1`, `sealed switch: closed` and `enum switch:   priority 2`. After only the hierarchy is recompiled, the same old client prints `active, priority 1`, then `sealed switch: java.lang.MatchException` and `enum switch:   java.lang.MatchException`. Recompiling the client gives two `does not cover all possible input values` errors."
   },
   "refs": [
    {"title": "MatchException (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/MatchException.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "The loan rules in Java and Kotlin",
  "java": {"title": "LoanRules.java", "src": """static int loanDays(Loan loan) {
    return switch (loan) {
        case Loan(var m, Book(var format, var isNew), var b) when format == Format.LARGE_PRINT -> 42;
        case Loan(var m, Book(var format, var isNew), var b) when isNew -> 7;
        case Loan(var m, Book book, var b) when b == Branch.BUS -> 28;
        case Loan(var m, Book book, var b) -> 21;
        case Loan(var m, Disc(var boxSet), var b) when boxSet -> 14;
        case Loan(var m, Disc disc, var b) -> 7;
        case Loan(Member(var id, int age), Magazine mag, var b) when age < 12 -> 14;
        case Loan(Member member, Magazine mag, var b) -> 7;
    };
}"""},
  "kotlin": {"title": "LoanRules.kt", "src": """fun loanDays(loan: Loan): Int {
    val age = loan.member.age
    return when (val item = loan.item) {
        is Book if item.format == Format.LARGE_PRINT -> 42
        is Book if item.newRelease -> 7
        is Book if loan.branch == Branch.BUS -> 28
        is Book -> 21
        is Disc if item.boxSet -> 14
        is Disc -> 7
        is Magazine if age < 12 -> 14
        is Magazine -> 7
    }
}"""},
  "note": "The rules, the order and the exhaustiveness check are the same in both: the first matching branch wins, guards don't count toward exhaustiveness, and neither version needs a default. The difference is where the data comes apart. Java's record patterns reach into `Loan`, `Member` and `Book` in the label and bind the parts. Kotlin can only test the type of the value it switches on, so the twin pulls `item` out first, switches on that, and reads `loan.member.age` and `loan.branch` by hand. javac also checks dominance, which kotlinc doesn't, and Java's switch has explicit null rules, where Kotlin leaves null to the type system."
 },
 "worked": {
  "title": "Rewrite the shelving rules as one switch",
  "steps": [
   {"say": "When an item comes back, this code decides where it goes next. It compiles, it has tests, and it has a bug the compiler can't see. Read it and look for a kind of item it forgets.",
    "code": """static String shelveTo(DeskEvent event) {
    if (event instanceof Returned r) {
        if (r.item() instanceof Book b) {
            if (b.newRelease()) return "reservations desk";
            return "book trolley";
        }
        if (r.item() instanceof Disc) return "disc shelf";
    }
    return "nowhere";
}""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """fun shelveTo(event: DeskEvent): String {
    if (event is Returned) {
        val item = event.item
        if (item is Book) {
            if (item.newRelease) return "reservations desk"
            return "book trolley"
        }
        if (item is Disc) return "disc shelf"
    }
    return "nowhere"
}"""},
   {"say": "Name the shapes you care about, most specific first, and let each label take the event apart. `DeskEvent` is sealed (`Returned`, `Borrowed`) and so is `Item`, so the switch needs no default.",
    "code": """static String shelveTo(DeskEvent event) {
    return switch (event) {
        // 1. the special case first
        case Returned(Book(var format, var isNew), int late) when isNew -> "reservations desk";
        // 2. then the general cases, one per kind of item
        case Returned(Book b, int late) -> "book trolley";
        case Returned(Disc d, int late) -> "disc shelf";
        // 3. events that need no shelving
        case Borrowed b -> "nowhere";
    };
}""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """fun shelveTo(event: DeskEvent): String = when (event) {
    is Returned -> when (val item = event.item) {
        // 1. the special case first
        is Book if item.newRelease -> "reservations desk"
        // 2. then the general cases, one per kind of item
        is Book -> "book trolley"
        is Disc -> "disc shelf"
    }
    // 3. events that need no shelving
    is Borrowed -> "nowhere"
}"""},
   {"say": "That doesn't compile, in either language: `the switch expression does not cover all possible input values` (kotlinc: `Add the 'is Magazine' branch`). A returned magazine matches no case. The old chain had the same gap and returned \"nowhere\", so returned magazines were never put back. The compiler found the bug the tests missed. Add the case.",
    "code": """        case Returned(Magazine m, int late) -> "reading room";   // the case the chain forgot""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """        is Magazine -> "reading room"                         // the case the chain forgot"""},
   {"say": "On JDK 22 or newer, replace the bindings you never use with `_`, so a reader sees at a glance which parts each rule depends on. Kotlin's version already names only what it reads.",
    "code": """// JDK 22+
case Returned(Book(_, var isNew), _) when isNew -> "reservations desk";
case Returned(Book _, _) -> "book trolley";
case Returned(Disc _, _) -> "disc shelf";
case Returned(Magazine _, _) -> "reading room";
case Borrowed _ -> "nowhere";""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """// Kotlin uses _ only for unused lambda parameters and destructured components
val (_, daysLate) = returned      // skip the item, keep the days late"""}
  ]
 },
 "lab": {
  "title": "Loan rules over a sealed hierarchy",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/LoanRules.java"],
  "run": "./gradlew :modernjava:test --tests 'workbench.modernjava.l03.*'",
  "steps": [
   "Run the tests: all eight fail. Read the rule list in the Javadoc of `loanDays`. The order of the rules is the order of your cases.",
   "Write `loanDays` as one `switch` over the `Loan`, with record patterns and guards and no `default`. Start with the large-print rule, and run the tests after every two or three cases.",
   "Write `label`. It needs a `case null`, and the magazine needs care: what does `Magazine(String t)` bind when the title is null?",
   "When all eight pass, swap your large-print and new-release cases and run the tests again. Which test catches it? Swap them back.",
   "Delete your last, unguarded book case and compile. Read the error, then put it back."
  ],
  "hints": [
   "The first case can be `case Loan(var m, Book(var format, var isNew), var b) when format == Format.LARGE_PRINT -> 42;`.",
   "Each kind of item must end with an unguarded case: one for `Book`, one for `Disc`, one for `Magazine`. Otherwise javac says the switch doesn't cover all possible input values.",
   "`loanDays` doesn't need `case null`: a pattern switch without one throws `NullPointerException`, which is what the test expects.",
   "For the child rule, take the member apart too: `Loan(Member(var id, int age), Magazine mag, var b) when age < 12`. Close the magazine family with the type pattern `Member member`, which covers every member.",
   "`Magazine(String t)` matches a magazine whose title is null, with `t` bound to null. Put `case Magazine(String t) when t == null` before the general magazine case."
  ],
  "done_when": "All eight tests in `LoanRulesTest` pass."
 },
 "drill": {
  "title": "A guarded switch from memory",
  "minutes": 5,
  "prompt": "Close this page. Given `sealed interface Check permits Returned, Damaged`, `record Returned(int daysLate)` and `record Damaged(String part, boolean repairable)`, write `nextStep(Check c)`: items returned 30 or more days late get `\"send a letter\"`, other returns `\"reshelve\"`, repairable damage `\"repair\"`, and other damage `\"replace\"`. No `default`. Then write it in Kotlin with `when` guards.",
  "answer": {"lang": "java", "src": """static String nextStep(Check c) {
    return switch (c) {
        case Returned(int late) when late >= 30 -> "send a letter";
        case Returned r -> "reshelve";                         // unguarded: closes the Returned family
        case Damaged(var part, var repairable) when repairable -> "repair";
        case Damaged d -> "replace";                           // unguarded: closes the Damaged family
    };
}""",
             "alt": {"lang": "kotlin", "src": """fun nextStep(c: Check): String = when (c) {
    is Check.Returned if c.daysLate >= 30 -> "send a letter"
    is Check.Returned -> "reshelve"                        // unguarded: closes the Returned family
    is Check.Damaged if c.repairable -> "repair"
    is Check.Damaged -> "replace"                          // unguarded: closes the Damaged family
}"""}}
 },
 "recap": [
  "A pattern switch is checked for exhaustiveness and dominance and has fixed null rules. An `instanceof` chain gets none of that.",
  "Record patterns take records apart in the case label, nested, through the accessors, with `var` inference and type checks. Kotlin has smart casts and positional destructuring instead.",
  "Cases run top to bottom and the first match wins. Guards don't count toward exhaustiveness, so end each guarded family with an unguarded case. kotlinc doesn't check dominance.",
  "A null selector throws unless you write `case null`, and `default` doesn't catch it. A nested type pattern matches a null component; a nested record pattern doesn't.",
  "The limit: exhaustive is a compile-time promise. A subtype or enum constant added later makes an old program throw `MatchException` (`NoWhenBranchMatchedException` in Kotlin).",
  "Pattern switch and record patterns are final from JDK 21, `_` from JDK 22, JDK 27 lists the missing patterns, and primitive patterns are still a preview."
 ],
 "closing": "We started at the lending desk, with a clerk who reads each item in one look and works down a printed sheet. A pattern switch is that clerk: javac checks that the sheet covers every kind of item, record patterns read the boxes inside each record, and the order of the guards is the order of the rules.\n\nNow look in your own code for `instanceof` followed by a cast or a getter on the next line. Each one is a chain that a switch could check.\n\nNext, we'll put records, sealed types and switches together into one way of designing programs. What does a program look like when the forms can't be filled in wrong?",
 "quiz": [
  {"q": "The switch is `case Line(Point(var x1, var y1), Point(var x2, var y2)) when x1 == x2 -> \"vertical\"; case Line(Point from, Point to) -> \"other\";`. What does it return for `new Line(null, new Point(1, 1))`?",
   "options": ["It throws NullPointerException", "`\"other\"`, with `from` bound to null", "It throws MatchException", "`\"vertical\"`"],
   "answer": 1, "why": "The nested record pattern `Point(var x1, var y1)` never matches null, so the first case is skipped. The type pattern `Point from` covers the whole component type, so it matches null and binds it. If the second case were also a record pattern, the switch would still compile and would throw MatchException for this line."},
  {"q": "Which pair of cases, in this order, does javac reject with `this case label is dominated by a preceding case label`?",
   "options": ["`case Integer i -> ...` then `case Integer i when i > 0 -> ...`", "`case Integer i when i > 0 -> ...` then `case Integer i -> ...`", "`case Integer i when i > 0 -> ...` then `case 1 -> ...`", "`case Book b when b.newRelease() -> ...` then `case Book b when b.format() == LARGE_PRINT -> ...`"],
   "answer": 0, "why": "An unguarded `case Integer i` matches every Integer, so the guarded case after it can never run. A guarded case never dominates anything, which is why the other three orders compile. The last pair compiles but is probably a bug: new large-print books never reach the large-print rule."},
  {"q": "Kotlin: `data class Book(val title: String, val pages: Int)`. What does `val (pages, title) = Book(\"Dune\", 412)` do on Kotlin 2.4 with default settings?",
   "options": ["It fails to compile because the names don't match the properties", "It binds by name: `pages = 412`, `title = \"Dune\"`", "It compiles without a warning and binds `pages = \"Dune\"`, `title = 412`", "It compiles with a warning about swapped names"],
   "answer": 2, "why": "Destructuring calls `component1()` and `component2()` in order, whatever you call the variables. Here the types even differ, but each variable just takes its component's type. Name-based destructuring exists only as an Experimental feature (2.3.20 and later, `-Xname-based-destructuring`)."},
  {"q": "From lesson 1: `record Masked(String phone)` overrides `phone()` to return `\"****\"` plus the last four digits. For the number 01614960123, what does `switch (m) { case Masked(var p) -> p; }` return?",
   "options": ["`01614960123`, because patterns read the field like toString does", "`****0123`, because record patterns call the accessor", "It doesn't compile: records with overridden accessors can't be taken apart", "`null`"],
   "answer": 1, "why": "Record patterns read components through the accessors, while the generated `toString` and `equals` read the fields. So this record shows `****0123` to patterns and the full number to `toString`: one more reason not to mask in the accessor.",
   "from": "dop-01"},
  {"q": "A switch over `String section` has `case \"FIC\" -> ...` and `default -> ...`. The barcode scanner upstream sometimes passes null. What does the OpenJDK sealed-switch guide prefer?",
   "options": ["Add `case null` to every switch that might see it", "Nothing: `default` already catches null", "Wrap the switch in try/catch for NullPointerException", "Reject null before the switch with `Objects.requireNonNull(section)`"],
   "answer": 3, "why": "`default` doesn't match null, so today the switch throws NPE. The guide allows `case null` but prefers `Objects.requireNonNull` before the switch: it fails where the bad value enters, with a clear message, instead of spreading null handling into every switch."}
 ],
 "flashcards": [
  {"front": "Do guarded cases count toward exhaustiveness?", "back": "No, in Java or Kotlin. End each family of guarded cases with an unguarded case of the same pattern."},
  {"front": "When does javac say `this case label is dominated by a preceding case label`?", "back": "When an earlier unguarded case already matches everything the later case could, such as `case String s` after `case CharSequence cs`, or `case 1` after `case Integer i`."},
  {"front": "What does a pattern switch do with a null selector?", "back": "It throws `NullPointerException` unless it has `case null` (or `case null, default`). `default` alone doesn't catch null."},
  {"front": "`case Line(Point from, Point to)` and the line's `from` is null. Does it match?", "back": "Yes. A nested type pattern that covers the component's type matches null. A nested record pattern such as `Point(var x, var y)` doesn't."},
  {"front": "An old program's exhaustive switch meets a subtype added after it was compiled. What happens?", "back": "Java throws `MatchException`; a Kotlin `when` throws `NoWhenBranchMatchedException`. Recompiling turns it into a compile error."},
  {"front": "How do you put several patterns in one switch arm?", "back": "Only with unnamed patterns, from JDK 22: `case Return _, Renew _ ->`. With named bindings javac says `illegal fall-through from a pattern`."},
  {"front": "Kotlin `val (a, b) = book`: by name or by position?", "back": "By position, through `component1()` and `component2()`. Swapped names compile without a warning. Name-based destructuring is Experimental since 2.3.20."}
 ],
 "terms": [
  {"term": "Type pattern", "plain": "`Book b`: matches if the value is a `Book`, and binds it to `b`."},
  {"term": "Record pattern", "plain": "`Book(var format, var isNew)`: matches a `Book` and binds its components, which can be patterns too."},
  {"term": "Guard", "plain": "The `when` condition after a pattern (`if` in Kotlin). The case matches only if the guard is true."},
  {"term": "Dominance", "plain": "A case is dominated when an earlier case already matches everything it could. javac rejects it."},
  {"term": "Remainder", "plain": "The values an exhaustive switch doesn't cover at run time: nested nulls, and subtypes added after compilation."},
  {"term": "MatchException", "plain": "What Java throws when an exhaustive switch meets a value from its remainder (since JDK 21)."},
  {"term": "Unnamed pattern", "plain": "`_` in a pattern: matches anything and binds nothing. Final from JDK 22."}
 ],
 "explain_back": {
  "prompt": "A teammate asks: \"If the switch over our sealed `CopyStatus` compiles with no default, it can never fail at run time, right?\" Explain, in your own words, when it can, and what you would do about each case.",
  "answer": "Exhaustive is checked at compile time, against the subtypes javac could see then. At run time two things can still slip through. First, null: a null selector throws `NullPointerException` unless there is a `case null`, and a null inside a nested record pattern can make the switch throw `MatchException`. I'd reject nulls at the edge with `Objects.requireNonNull`, so they never reach the switch. Second, separate compilation: if the library that defines `CopyStatus` adds `InRepair` and our program runs the new jar without being recompiled, the old switch throws `MatchException` for the new status. The fix is to rebuild against the new version, and then the compiler shows every switch that needs a case. Adding a default to hide it would be worse, because the new status would quietly take the default branch."
 },
 "deeper": {
  "minutes": 10,
  "body": """Two newer features build on this lesson. Neither belongs in the labs, which compile for JDK 21.

Primitive types in patterns have been a preview feature in every JDK from 23 to 27, and they are still a preview in the JDK 28 builds. They let a switch over an `int` use type patterns and guards, and let `instanceof` ask whether a value fits another primitive type exactly:

```java
// JDK 25: java --enable-preview --source 25 preview/PrimitivePatterns.java
static String length(int pages) {
    return switch (pages) {
        case 0 -> "no pages";
        case int p when p < 100 -> "short (" + p + " pages)";
        case int p -> "medium or long (" + p + " pages)";
    };
}
```

```kotlin
// Kotlin has always allowed conditions on any subject
fun length(pages: Int): String = when {
    pages == 0 -> "no pages"
    pages < 100 -> "short ($pages pages)"
    else -> "medium or long ($pages pages)"
}
```

Without the preview flags, JDK 25 stops with `primitive patterns are a preview feature and are disabled by default`. Treat the syntax as likely to change until it is final.

The second feature is better error messages. JDK 27's javac lists what a non-exhaustive switch is missing, under a `missing patterns:` line, in the form `Rect _` for a type and `Pair(Red _,Green _)` for a nested record pattern. That one change makes nested exhaustiveness errors much easier to read: on JDK 21 the same `Pair` switch only says it doesn't cover all possible input values, and you work out the missing combination yourself.

One habit to avoid: don't write `case _ when ...`. JDK 25's javac accepts it, but the language specification doesn't allow it, and a fix in JDK 28 development (JDK-8385488) makes javac reject it. Write `default` or a real type pattern instead."""
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
