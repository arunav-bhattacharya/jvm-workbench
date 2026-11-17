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


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 700 300" role="img" aria-label="A sealed LibraryItem with four branches: Book and Magazine are final records, '
    'Disc is sealed with Dvd and AudioCd below it, and PartnerItem is non-sealed, so ArchiveBox and any other class may implement it">'
    '<rect class="box-a" x="230" y="14" width="240" height="44" rx="8"/>'
    '<text class="t t-code" x="350" y="41" text-anchor="middle">sealed LibraryItem</text>'
    '<line class="ln" x1="350" y1="58" x2="95" y2="108" marker-end="url(#arr)"/>'
    '<line class="ln" x1="350" y1="58" x2="265" y2="108" marker-end="url(#arr)"/>'
    '<line class="ln" x1="350" y1="58" x2="435" y2="108" marker-end="url(#arr)"/>'
    '<line class="ln" x1="350" y1="58" x2="605" y2="108" marker-end="url(#arr)"/>'
    '<rect class="box" x="20" y="110" width="150" height="50" rx="8"/>'
    '<text class="t-s t-code" x="95" y="131" text-anchor="middle">record Book</text>'
    '<text class="t-s t-m" x="95" y="150" text-anchor="middle">final</text>'
    '<rect class="box-a" x="190" y="110" width="150" height="50" rx="8"/>'
    '<text class="t-s t-code" x="265" y="131" text-anchor="middle">sealed Disc</text>'
    '<text class="t-s t-m" x="265" y="150" text-anchor="middle">closed list below</text>'
    '<rect class="box" x="360" y="110" width="150" height="50" rx="8"/>'
    '<text class="t-s t-code" x="435" y="131" text-anchor="middle">record Magazine</text>'
    '<text class="t-s t-m" x="435" y="150" text-anchor="middle">final</text>'
    '<rect class="box-b" x="530" y="110" width="150" height="50" rx="8"/>'
    '<text class="t-s t-b" x="605" y="131" text-anchor="middle">non-sealed</text>'
    '<text class="t-s t-code" x="605" y="150" text-anchor="middle">PartnerItem</text>'
    '<line class="ln" x1="265" y1="160" x2="225" y2="208" marker-end="url(#arr)"/>'
    '<line class="ln" x1="265" y1="160" x2="305" y2="208" marker-end="url(#arr)"/>'
    '<rect class="box" x="188" y="210" width="74" height="40" rx="8"/>'
    '<text class="t-s t-code" x="225" y="235" text-anchor="middle">Dvd</text>'
    '<rect class="box" x="268" y="210" width="74" height="40" rx="8"/>'
    '<text class="t-s t-code" x="305" y="235" text-anchor="middle">AudioCd</text>'
    '<line class="ln" x1="605" y1="160" x2="555" y2="208" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="605" y1="160" x2="650" y2="208" marker-end="url(#arr)"/>'
    '<rect class="box" x="510" y="210" width="90" height="40" rx="8"/>'
    '<text class="t-s t-code" x="555" y="235" text-anchor="middle">ArchiveBox</text>'
    '<rect class="box-dim" x="608" y="210" width="84" height="40" rx="8"/>'
    '<text class="t-s t-m" x="650" y="235" text-anchor="middle">any class</text>'
    '<text class="t-s t-m" x="95" y="190" text-anchor="middle">no subtypes</text>'
    '<text class="t-s t-m" x="435" y="190" text-anchor="middle">no subtypes</text>'
    '<text class="t-s" x="265" y="282" text-anchor="middle">one case Disc covers both</text>'
    '<text class="t-s" x="600" y="282" text-anchor="middle">one case PartnerItem covers all</text>'
    '</svg>'
)

OPENING = """Back at the library desk, the request form has a line near the top: Item type, with four boxes to tick. Book, Disc, Magazine, From another library. Because the form lists every possible answer, the clerk's instruction sheet can have one line per box, and the clerk knows the sheet is complete. Now picture a form where the item type is a blank line instead. Someone writes "board game". The sheet has no line for it, and nobody notices until a board game turns up at the counter.

An ordinary Java interface is that blank line: any class, anywhere, can implement it. So code that handles "each kind of item" can never know it handled them all. The trap is easy to fall into, because the code compiles, the tests pass with today's four kinds, and the fifth kind arrives months later.

Last lesson, a record fixed which boxes one form has. In this lesson, we'll fix which kinds of form exist: seal a type, choose how each branch ends, see where the subtypes may live, and let the compiler find every switch when the list grows. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_REQ = """public sealed interface Request permits Borrow, Renew, Return {}

public record Borrow(String isbn, int days) implements Request {}
public record Renew(int extraDays) implements Request {}
public record Return() implements Request {}"""
K_REQ = """sealed interface Request {
    data class Borrow(val isbn: String, val days: Int) : Request
    data class Renew(val extraDays: Int) : Request
    data object Return : Request
}"""

S0 = """Start with the requests a member can make at the desk: borrow a book, renew a loan, return it. Written as an ordinary interface, `Request` has three implementations today. Any class in any package can add a fourth, say a `Donate` next week, and it compiles. Every `if`/`else` chain that handles requests skips the newcomer without a word and lands in its final `else`.

Before JDK 17, the only fix was a trick: an abstract class with a package-private constructor, so that only classes in its own package can extend it. That closes the list, but the compiler still doesn't know what's on it, so it can't check a switch against it.

A **sealed type** is a class or interface that names its permitted subtypes, the only classes allowed to extend it directly. Add `sealed` and a `permits` clause, and the list becomes part of the type:

""" + pair(J_REQ, K_REQ) + """

In the paperwork picture, a sealed type is a form with a fixed set of boxes to tick. The boxes are printed on the form, so the clerk knows every possible answer.

Sealed classes and interfaces have been a standard feature since JDK 17 (JEP 409, the JDK Enhancement Proposal that added them). javac, the Java compiler, checks the list from both sides. Uncomment `Donate` in the `SealedBasics` demo without adding it to the list, and javac stops:

```text
error: class is not allowed to extend sealed class: Request (as it is not listed in its 'permits' clause)
```

javac also writes the list into the class file, as a `PermittedSubclasses` attribute, a small table the JVM (the program that runs Java code) reads when it loads a class. So the JVM checks it too: a class compiled against an older, unsealed `Request` fails to load with `IncompatibleClassChangeError` next to the sealed one. Nobody gets to scribble a fifth box in the margin.

You can leave `permits` out when every subtype is declared in the same source file. javac then takes the subtypes it finds there. Reflection, the API a program uses to look at its own classes, shows the result: `Request.class.isSealed()` is true, and `getPermittedSubclasses()` returns the three records.

Kotlin has no `permits` clause. Its rule is location: any class in the same package and the same module may extend a sealed type. So `class Donate : Request` in that package compiles, and the list grows by itself. The same line in another package fails with `a class can only extend a sealed class or interface declared in the same package`. With the JDK 21 target these labs use, kotlinc 2.4, the Kotlin compiler, writes the same `PermittedSubclasses` attribute as javac. Java code therefore sees a Kotlin sealed interface as sealed: a Java switch over it needs no `default`, and javac rejects a Java class that tries to implement it.

Sealing restricts direct subtypes only. `Renew.class.isSealed()` is false. What may sit below each permitted subtype is the next question."""

# ---------------------------------------------------------------- section 1
J_TREE = """public sealed interface LibraryItem permits Book, Disc, Magazine, PartnerItem {}
public record Book(String isbn, String title) implements LibraryItem {}            // final
public sealed interface Disc extends LibraryItem permits Dvd, AudioCd {}          // closed below
public record Magazine(String title, int issue) implements LibraryItem {}         // final
public non-sealed interface PartnerItem extends LibraryItem {                     // open below
    String partnerId();
}"""
K_TREE = """sealed interface LibraryItem {
    data class Book(val isbn: String, val title: String) : LibraryItem            // final by default
    sealed interface Disc : LibraryItem                                            // closed below
    data class Magazine(val title: String, val issue: Int) : LibraryItem
    interface PartnerItem : LibraryItem { val partnerId: String }                  // open below
}"""

S1 = """Every permitted subtype of a sealed type must say how its own branch ends, with exactly one of three modifiers. A class that says nothing stops javac with `sealed, non-sealed or final modifiers expected`. An interface can't be final, so for one the message is `sealed or non-sealed modifiers expected`.

`final` ends the branch. Records and enums are final already, so a record needs no modifier, which is one reason sealed interfaces and records fit together so well. `sealed` continues the closed list one level down, with its own `permits`. `non-sealed` reopens the branch on purpose: anyone may extend it, in any package.

The library's own list uses all three. Books and magazines are records. Discs are a sealed branch with exactly two kinds, DVDs and audio CDs. And some items are lent to us by partner libraries, which describe them in their own code:

""" + pair(J_TREE, K_TREE) + """

On the form, `non-sealed` is the box marked "From another library: ______", with a blank line after it. The clerk can't list every partner's items, but one instruction covers them all: send it back to the library named on the line.

`non-sealed` sounds as if it defeats the point. It doesn't, because the compiler still knows the shape of the tree. A switch covers the open branch with one `case PartnerItem p`, and that case matches every partner's class, including ones a partner writes next year. Your switch stays complete, and the partners stay free. Kotlin has no `non-sealed` keyword: a plain interface, or an `open class`, under a sealed parent plays the same role.

So "sealed means final" is wrong: a sealed type has subtypes by definition, and a `non-sealed` branch can have any number. The trap that catches people in code review is a third one. A sealed class that isn't abstract is itself a possible value. The `NonSealedDemo` has a sealed class `Extension`, the rule for how many days a renewal adds, with two final subclasses, `FixedDays` and `SameAgain`. Delete `abstract`, and `new Extension()` becomes legal. The switch with one case per subclass then fails with `the switch expression does not cover all possible input values`, because a plain `Extension` matches neither case. Make the parent abstract, or make it an interface. Kotlin avoids the trap entirely: its docs say a sealed class is always abstract.

**Every branch of a sealed tree ends in final, sealed or non-sealed. Choose each one on purpose.**

We know how each branch ends. The next question is where the branches may be written down."""

# ---------------------------------------------------------------- section 2
S2 = """Sealing ties a hierarchy to one place, and Java and Kotlin draw the boundary slightly differently.

In Java, the permitted subtypes must be in the same module as the sealed type. A module here is a named group of packages, described by a `module-info.java` file. If your code isn't in a named module, the subtypes must be in the same package. Split the sealed interface and its record across two packages, `library.api` and `library.book`, and javac refuses:

```text
error: class LibraryItem in unnamed module cannot extend a sealed class in a different package
public sealed interface LibraryItem permits library.book.Book {}
```

The wording is clumsy, since it names the sealed interface as the class doing the extending, but the rule is clear. Add a `module-info.java` that puts both packages in one module, and the same files compile.

Kotlin's rule is the same package and the same module, whether or not you use Java modules. So for most code the two languages agree: keep a sealed hierarchy in one package. That's rarely a burden. The subtypes are usually small records or data classes that read best next to each other, often nested inside the sealed type itself, which also lets Java infer `permits`.

The rule makes sense once you see what sealing promises. The author of a sealed type says "this is the complete list", and the compiler can only hold everyone to that if the whole list is compiled and shipped together. In the picture, the form and all its boxes come from one print shop. A box printed somewhere else could be reprinted on its own schedule, and every instruction sheet checked against the old form would quietly go stale.

**A sealed list must be compiled together. Keep it in one package.**

With the list closed and kept in one place, the compiler can finally put it to work."""

ASIDE2 = {
    "title": "Is my program in a module?",
    "body": "Probably not. A named module exists only when there's a `module-info.java` at the root of the source tree. Most applications, including most web services, run from the class path, a plain list of jar files and folders, and everything on it belongs to one unnamed module. So the package rule is the one you'll usually meet. Libraries that ship as modules may split a sealed hierarchy across their own packages."
}

# ---------------------------------------------------------------- section 3
J_SW = """static boolean canLendToday(CopyStatus s) {
    return switch (s) {                              // no default
        case OnShelf shelf -> true;
        case OnLoan loan -> false;
        case OnHold hold -> false;
        case Missing missing -> false;
    };
}"""
K_SW = """fun canLendToday(s: CopyStatus): Boolean = when (s) {   // no else
    is CopyStatus.OnShelf -> true
    is CopyStatus.OnLoan -> false
    is CopyStatus.OnHold -> false
    is CopyStatus.Missing -> false
}"""

S3 = """Sealing pays off in a `switch`. Over a sealed type, javac knows every possible subtype, so a switch with one case per subtype is **exhaustive**: its cases cover every possible value, and it needs no `default`. javac checks that the cases really do cover every subtype. The `StatusSwitches` demo has three switches over `CopyStatus`, where one copy of a book is right now: on the shelf, on loan, on hold for a member, or missing. Here is one of them:

""" + pair(J_SW, K_SW) + """

Now the library starts sending damaged books away to be repaired, and someone adds `InRepair` to `CopyStatus`. Every switch over `CopyStatus` without a `default` stops compiling. On JDK 21 to 26 the error is the bare one, pointing at the `switch`:

```text
StatusSwitches.java:30: error: the switch expression does not cover all possible input values
        return switch (s) {
               ^
```

JDK 27's javac adds the cases you're missing, under a `missing patterns:` line, here `InRepair _`. kotlinc has always been specific: `'when' expression must be exhaustive. Add the 'is InRepair' branch or an 'else' branch.` Either way, the build hands you a to-do list: every switch that has to learn about repairs.

The third switch isn't on that list. `reminderDays` ends with `default -> 0`, which means "and anything else", and the compiler takes it at its word. `InRepair` drops into the default without a sound and gets 0 reminder days, though the repair has a due date too. A `default` on your own sealed type throws away the one check sealing gives you. The OpenJDK team's 2026 guide to switching over sealed types has a section called "By default, avoid `default`", because a default "sweeps errors, both present and future, under the rug".

**A default on a list that grows hides the next item. Leave it out.**

Keep `default` for switches where "everything else" really is one answer, such as the illegal (state, event) pairs of a state machine in *State and Chain of Responsibility*. The same guide asks authors to say in the Javadoc why a type is sealed. Maybe it models a closed set, like the statuses of a copy. Or maybe the author only wants to control who implements it. Say which, and whether you expect to add subtypes, so the people switching over it know what's coming.

Exhaustive has one limit, and it's about time. javac checks a switch against the list it can see when it compiles. A program compiled against the old list can still meet an `InRepair` from a newer library at run time, and lesson 3 of this track shows what happens then. Sealing also fits only lists you own: a plug-in point that other people extend should stay open."""

L = {
 "id": "dop-02",
 "title": "Sealed types: hierarchies the compiler can check",
 "minutes": 35,
 "goal": "By the end you can declare a sealed hierarchy with the right modifier on every subtype, say where its subtypes may live, and use it so that adding a subtype turns every switch you forgot into a compile error.",
 "opening": OPENING,
 "warmup": {
  "q": "`sealed class Extension permits FixedDays, SameAgain {}` is not abstract, and `FixedDays` and `SameAgain` are its final subclasses. A switch expression over an `Extension` has `case FixedDays f` and `case SameAgain s` and no `default`. Does it compile?",
  "options": ["Yes: the permits list is complete, so the switch is exhaustive",
              "No: `new Extension()` is also a possible value, so the switch misses a case",
              "No: only interfaces can be sealed",
              "Yes, but a plain `Extension` throws MatchException at run time"],
  "answer": 1,
  "why": "A sealed class that isn't abstract can be instantiated itself, so an `Extension` that is neither `FixedDays` nor `SameAgain` can exist, and javac reports `the switch expression does not cover all possible input values`. Make `Extension` abstract, or an interface, and the two cases cover it. Kotlin sidesteps the trap: a sealed class there is always abstract."
 },
 "sections": [
  {
   "h": "A sealed type closes the list of direct subtypes",
   "body": S0,
   "try": {
    "title": "Break the list on purpose",
    "minutes": 4,
    "steps": [
     "Run `SealedBasics` (or `SealedBasicsKt`) with the command below.",
     "In the Java demo, uncomment `static final class Donate implements Request {}` and run again. Read the error.",
     "Add `Donate` to the `permits` clause and delete `final` from it. Run again. Then put `final` back.",
     "Now delete the whole `permits ...` clause and run. What does `getPermittedSubclasses()` print?",
     "In the Kotlin twin, uncomment `class Donate : Request`. Does it compile? Why is that different from Java?"
    ],
    "code": demo("SealedBasics"),
    "expect": "The first run prints `Request.isSealed(): true`, the three records marked `(final)`, and `Renew.isSealed(): false`. The unlisted class fails with `class is not allowed to extend sealed class: Request (as it is not listed in its 'permits' clause)`. Listed but without a modifier, it fails with `sealed, non-sealed or final modifiers expected`. With no `permits` clause, javac infers all four from the file and prints `Donate (final)` too. In Kotlin, `class Donate : Request` compiles: the list is whatever sits in the same package and module."
   },
   "refs": [
    {"title": "JEP 409: Sealed Classes", "url": "https://openjdk.org/jeps/409", "kind": "read"}
   ]
  },
  {
   "h": "final, sealed or non-sealed: every branch has to choose",
   "body": S1,
   "figure": {"svg": FIG, "caption": "Each permitted subtype ends its branch: final has no subtypes, sealed keeps a closed list, non-sealed lets anyone in. A switch still needs only one case per branch."},
   "try": {
    "title": "Reopen one branch, close the trap",
    "minutes": 4,
    "steps": [
     "Run `NonSealedDemo`. `ArchiveBox` is a partner library's code: which modifier lets it exist?",
     "Delete `non-sealed` from `PartnerItem`, leaving a plain `interface`, and run. Read the error, then put it back.",
     "Delete `abstract` from `sealed abstract static class Extension` and run again."
    ],
    "code": demo("NonSealedDemo"),
    "expect": "The demo prints `book Dune`, `disc Dvd[title=Paddington]`, `partner city-archive`, `PartnerItem.isSealed(): false` and `renewal: 7 and 21 extra days`. Without a modifier, javac says `sealed or non-sealed modifiers expected` (an interface can't be final, so `final` isn't offered). Without `abstract`, the `extraDays` switch fails with `the switch expression does not cover all possible input values`: a plain `Extension` is now a possible value. The Kotlin twin can't show that trap, because its sealed class is always abstract."
   },
   "refs": [
    {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html", "kind": "docs"}
   ]
  },
  {
   "h": "Where the subtypes may live: one package, or one module",
   "body": S2,
   "aside": ASIDE2,
   "try": {
    "title": "Split a hierarchy across packages",
    "minutes": 4,
    "steps": [
     "The folder `labs/modernjava/javac/sealed-packages` holds a sealed `LibraryItem` in `library.api`, a `Book` record in `library.book`, and a `module-info.java`. Gradle doesn't compile it; you run `javac` yourself.",
     "Run the first command. Read the error and the line it points at.",
     "Run the second command, which adds the module descriptor.",
     "Predict, then check: move `Book.java` into `library/api/`, change its package line to `library.api`, change the permits clause to `permits Book`, and run the first command again (with `library/api/Book.java` in place of the old path)."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "cd labs/modernjava/javac/sealed-packages\n\n# 1. class path, unnamed module: two packages are not allowed\njavac -d ../../build/sealed-packages library/api/LibraryItem.java library/book/Book.java\n\n# 2. one named module: two packages are fine\njavac -d ../../build/sealed-packages module-info.java library/api/LibraryItem.java library/book/Book.java", "run": ""},
    "expect": "The first command fails with `class LibraryItem in unnamed module cannot extend a sealed class in a different package`, pointing at `library.book.Book` in the permits clause. The second compiles with no output, because both packages belong to the module `library`. After the move, the first command compiles too: on the class path, one package is enough."
   }
  },
  {
   "h": "Let the compiler find every switch, and keep default out",
   "body": S3,
   "try": {
    "title": "Send a copy away for repair",
    "minutes": 5,
    "steps": [
     "Run `StatusSwitches` once and look at the three functions: `label`, `canLendToday` and `reminderDays`. Which one has a `default`?",
     "Add `InRepair` to the `permits` clause and uncomment the `InRepair` record. Before you run, predict which functions javac will report.",
     "Run it, then make it compile again by handling `InRepair` where javac asked. What does `reminderDays` return for a copy in repair now? Is that right?",
     "Do the same in the Kotlin twin, `StatusSwitchesKt`."
    ],
    "code": demo("StatusSwitches"),
    "expect": "The first run prints four lines, from `on shelf  lend today: true   reminder in 0 days` to `missing   lend today: false  reminder in 0 days`. With `InRepair`, javac reports two errors, `the switch expression does not cover all possible input values`, one in `label` and one in `canLendToday`. On JDK 27 each also says `missing patterns:` with `InRepair _`. `reminderDays` compiles silently and returns 0 for a copy in repair, which is probably wrong (the repair has a due date too), and nothing told you. kotlinc reports the same two functions with `Add the 'is InRepair' branch or an 'else' branch.`"
   },
   "refs": [
    {"title": "Preparing for Change: Safe Switching over Sealed APIs (OpenJDK Amber, 2026)", "url": "https://github.com/openjdk/amber-docs/blob/master/site/guides/exhaustiveness-guide.md", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "The copy statuses in Java and Kotlin",
  "java": {"title": "CopyStatus.java", "src": """public sealed interface CopyStatus permits OnShelf, OnLoan, OnHold, Missing {}

record OnShelf(String shelfmark) implements CopyStatus {}
record OnLoan(String memberId, int daysLeft) implements CopyStatus {}
record OnHold(String memberId) implements CopyStatus {}
record Missing(int daysMissing) implements CopyStatus {}

static String label(CopyStatus s) {
    return switch (s) {                 // no default
        case OnShelf shelf -> "on shelf";
        case OnLoan loan -> "on loan";
        case OnHold hold -> "on hold";
        case Missing missing -> "missing";
    };
}"""},
  "kotlin": {"title": "CopyStatus.kt", "src": """sealed interface CopyStatus {
    data class OnShelf(val shelfmark: String) : CopyStatus
    data class OnLoan(val memberId: String, val daysLeft: Int) : CopyStatus
    data class OnHold(val memberId: String) : CopyStatus
    data class Missing(val daysMissing: Int) : CopyStatus
}

fun label(s: CopyStatus): String = when (s) {   // no else
    is CopyStatus.OnShelf -> "on shelf"
    is CopyStatus.OnLoan -> "on loan"
    is CopyStatus.OnHold -> "on hold"
    is CopyStatus.Missing -> "missing"
}"""},
  "note": "The idea is the same and so is the bytecode: both compilers write a `PermittedSubclasses` attribute, so each language sees the other's sealed types as sealed. Three things differ. Java names the subtypes in `permits` (or infers them from one source file) and makes every subtype choose `final`, `sealed` or `non-sealed`; Kotlin's list is whatever is declared in the same package and module, and subtypes are final unless you open them. Java's location rule is the module, or the package on the class path; Kotlin's is always the package and the module. And Kotlin has `data object` for a case with no fields, where Java uses a record with no components or an enum."
 },
 "worked": {
  "title": "Seal the events from the self-service machine",
  "steps": [
   {"say": "The self-service machine by the door sends the library's program an event each time someone uses it. Today there are two kinds, and a handler sorts them with an `instanceof` chain. Someone adds a third kind to the machine, `Renewed`. This compiles with no warning, and the handler starts throwing on every renewal.",
    "code": """public interface MachineEvent {}

void handle(MachineEvent e) {
    if (e instanceof CheckedOut c) lend(c);
    else if (e instanceof CheckedIn c) takeBack(c);
    else throw new IllegalArgumentException("unknown event " + e);   // Renewed lands here
}""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """interface MachineEvent

fun handle(e: MachineEvent) {
    if (e is CheckedOut) lend(e)
    else if (e is CheckedIn) takeBack(e)
    else throw IllegalArgumentException("unknown event $e")        // Renewed lands here
}"""},
   {"say": "Seal the event type and make each event a record in the same package. Records are final, so they need no modifier.",
    "code": """// 1. close the list
public sealed interface MachineEvent permits CheckedOut, CheckedIn, Renewed {}

public record CheckedOut(String memberId, String isbn) implements MachineEvent {}
public record CheckedIn(String isbn) implements MachineEvent {}
public record Renewed(String memberId, String isbn, int extraDays) implements MachineEvent {}""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """// 1. close the list
sealed interface MachineEvent {
    data class CheckedOut(val memberId: String, val isbn: String) : MachineEvent
    data class CheckedIn(val isbn: String) : MachineEvent
    data class Renewed(val memberId: String, val isbn: String, val extraDays: Int) : MachineEvent
}"""},
   {"say": "Replace the chain with a switch that has no `default`. The chain could never be checked; the switch is checked on every build, and the `else throw` disappears because there is no \"else\" left.",
    "code": """// 2. one case per event, no default
void handle(MachineEvent e) {
    switch (e) {
        case CheckedOut c -> lend(c);
        case CheckedIn c -> takeBack(c);
        case Renewed r -> extend(r);
    }
}""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """// 2. one branch per event, no else
fun handle(e: MachineEvent) = when (e) {
    is MachineEvent.CheckedOut -> lend(e)
    is MachineEvent.CheckedIn -> takeBack(e)
    is MachineEvent.Renewed -> extend(e)
}"""},
   {"say": "A switch *statement* with patterns must be exhaustive too, so the `void` version is checked just like an expression. Last, write down why the type is sealed, so the next person knows that new events will come and that handlers must be updated, not given a default.",
    "code": """/**
 * Every event the self-service machine sends. Sealed because handlers must deal with each one.
 * New events will be added: expect your switch to stop compiling, and handle the new case.
 */
public sealed interface MachineEvent permits CheckedOut, CheckedIn, Renewed {}   // 3. say why""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """/**
 * Every event the self-service machine sends. Sealed because handlers must deal with each one.
 * New events will be added: expect your when to stop compiling, and handle the new case.
 */
sealed interface MachineEvent   // 3. say why"""}
  ]
 },
 "lab": {
  "title": "Seal the library's items",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/LibraryItem.java", f"{lab}/main/{P}/Loans.java"],
  "run": "./gradlew :modernjava:test --tests 'workbench.modernjava.l02.*'",
  "steps": [
   "Run the tests. All seven fail. Two of them run `javac` inside the test, through `javax.tools`, the JDK's way of calling the compiler from Java code. Read the Java source they compile.",
   "In `LibraryItem`, seal the interface, seal `Disc`, and give `PartnerItem` the modifier that keeps it open to partner libraries (TODO 1 to 3). Run the tests: four should pass now.",
   "In `Loans`, write `loanDays` with one case per type and no `default` (TODO 4).",
   "Write `returnBin` with a single case for all discs (TODO 5). Run until all seven tests pass.",
   "Add `record BoardGame(String title) implements LibraryItem {}` to the hierarchy and to `permits`, then run `./gradlew :modernjava:compileJava`. Which lines does javac point at? Remove it again."
  ],
  "hints": [
   "Types nested in an interface are implicitly `public static`. Write `permits LibraryItem.Book, ...`, or leave `permits` out, since every subtype is in this one file.",
   "A sealed sub-interface looks like `sealed interface Disc extends LibraryItem permits Dvd, AudioCd {}`.",
   "`sealed or non-sealed modifiers expected` means a permitted interface has no modifier; an interface can't be final. Records are final already.",
   "The tests call `ToolProvider.getSystemJavaCompiler()`. If it returns null, Gradle is running on a JRE: point it at a full JDK."
  ],
  "done_when": "All seven tests in `SealedHierarchyTest` pass."
 },
 "drill": {
  "title": "Seal a hierarchy from memory",
  "minutes": 5,
  "prompt": "Close this page. Write a sealed `HoldOutcome` with three results: `Collected(String memberId)`, `Expired(int daysOnShelf)` and `Waiting`, where `Waiting` is itself sealed, with `InTransit` (no fields) and `OnHoldShelf(int shelf)` below it. Then write `label(HoldOutcome)` with no `default`, using one case for everything still waiting. Java first, then Kotlin.",
  "answer": {"lang": "java", "src": """sealed interface HoldOutcome permits Collected, Expired, Waiting {}
record Collected(String memberId) implements HoldOutcome {}
record Expired(int daysOnShelf) implements HoldOutcome {}
sealed interface Waiting extends HoldOutcome permits InTransit, OnHoldShelf {}
record InTransit() implements Waiting {}
record OnHoldShelf(int shelf) implements Waiting {}

static String label(HoldOutcome o) {
    return switch (o) {
        case Collected c -> "collected by " + c.memberId();
        case Expired e -> "expired after " + e.daysOnShelf() + " days";
        case Waiting w -> "waiting";          // one case covers the sealed branch
    };
}""",
             "alt": {"lang": "kotlin", "src": """sealed interface HoldOutcome {
    data class Collected(val memberId: String) : HoldOutcome
    data class Expired(val daysOnShelf: Int) : HoldOutcome
    sealed interface Waiting : HoldOutcome
    data object InTransit : Waiting
    data class OnHoldShelf(val shelf: Int) : Waiting
}

fun label(o: HoldOutcome): String = when (o) {
    is HoldOutcome.Collected -> "collected by ${o.memberId}"
    is HoldOutcome.Expired -> "expired after ${o.daysOnShelf} days"
    is HoldOutcome.Waiting -> "waiting"      // one branch covers the sealed branch
}"""}}
 },
 "recap": [
  "`sealed ... permits` fixes the list of direct subtypes. javac checks it, and the JVM refuses to load a subclass that isn't on it.",
  "Each permitted subtype is `final` (records already are), `sealed` (closed one level down) or `non-sealed` (open again, and still covered by one case).",
  "A sealed class that isn't abstract is itself a possible value, so its subtypes don't cover it. Make it abstract or an interface.",
  "Java subtypes must share the module, or the package on the class path. Kotlin subtypes must share the package and the module.",
  "A switch over a sealed type with no `default` is checked: add a subtype and every such switch fails to compile. JDK 27 also lists the missing patterns. A `default` hides the new subtype instead.",
  "The limit: sealing works only for a list you own and compile together. A plug-in point that others extend stays open, and an old program can still meet a subtype it never saw."
 ],
 "closing": "We started with a form that lists every box to tick, and a blank line that let a board game in. A sealed type is that printed list: javac and the JVM refuse a subtype that isn't on it, and each branch ends final, sealed or non-sealed. In return, every switch without a `default` is checked against it.\n\nNow look in your own code for an `if`/`else` chain of `instanceof` checks that ends in `else throw`. That `else` is a blank line on the form.\n\nNext, we'll meet the clerk who reads these forms. What can a switch do when it can see inside each record, and what does it do with a blank sheet?",
 "quiz": [
  {"q": "You seal `LibraryItem`. Partner libraries must be able to add their own kinds of item under `PartnerItem`, in their own packages. Which declaration fits?",
   "options": ["`final interface PartnerItem extends LibraryItem`", "`sealed interface PartnerItem extends LibraryItem`", "`non-sealed interface PartnerItem extends LibraryItem`", "`interface PartnerItem extends LibraryItem`, with no modifier"],
   "answer": 2, "why": "`non-sealed` reopens the branch, so any class in any package may implement it, and a switch still covers it with one case. An interface can't be final, `sealed` would close it again, and no modifier at all fails with `sealed or non-sealed modifiers expected`."},
  {"q": "`LibraryItem` is sealed with `Book`, `Disc` (sealed: `Dvd`, `AudioCd`), `Magazine` and `PartnerItem` (non-sealed). A switch has cases for `Book`, `Dvd`, `Magazine` and `PartnerItem`, and no default. What happens?",
   "options": ["It compiles, because PartnerItem is open anyway", "javac reports that the switch doesn't cover all possible input values: `AudioCd` is missing", "javac demands a default, because a non-sealed branch can never be covered", "It compiles, and an audio CD throws MatchException"],
   "answer": 1, "why": "`Dvd` alone doesn't cover the sealed `Disc` branch, so `AudioCd` is uncovered and the switch is rejected (JDK 27 prints `missing patterns:` with `AudioCd _`). The non-sealed branch is fine: `case PartnerItem p` matches every implementation, known or not."},
  {"q": "Your program runs on the class path, with no `module-info.java`. You put `sealed interface LibraryItem` in `org.townlibrary.items` and its records in `org.townlibrary.items.books`. What happens?",
   "options": ["It compiles, because the packages share a prefix", "It compiles, but the JVM refuses to load the records", "It compiles if the permits clause uses fully qualified names", "javac rejects it: in the unnamed module, permitted subtypes must be in the same package"],
   "answer": 3, "why": "Packages have no hierarchy in Java, so `org.townlibrary.items.books` is simply a different package. Without a named module, javac requires the same package and reports `cannot extend a sealed class in a different package`. Move the records into `org.townlibrary.items`, or put both packages in one named module."},
  {"q": "From *State and Chain of Responsibility*: a state machine switches over its states, and in each state an inner switch over the event ends in `default -> throw illegal(state, event)`, on purpose. Someone adds a new event to the sealed event type. What does the compiler tell you about those inner switches?",
   "options": ["Nothing: they have a default, so the new event is silently treated as illegal in every state", "Every inner switch fails to compile until it handles the new event", "Only the outer switch over states fails", "The build passes, but every transition throws MatchException"],
   "answer": 0, "why": "A default covers every event, including new ones, so the compiler has nothing to report. That was a deliberate choice there, because most (state, event) pairs are illegal, but it means a new event needs a manual review of each state. The outer switch is over states, which didn't change.",
   "from": "pat-09"},
  {"q": "A Kotlin module defines `sealed interface Outcome` with three data classes. Java code in the same project switches over an `Outcome` with three cases and no `default`. What happens?",
   "options": ["javac requires a default, because Java can't see Kotlin's sealing", "It compiles: kotlinc writes the PermittedSubclasses attribute, so javac treats `Outcome` as sealed", "It compiles only if the data classes are marked `@JvmRecord`", "It compiles, and Java code may still add a fourth implementation"],
   "answer": 1, "why": "With a JDK 17 or newer target, such as the labs' 21, kotlinc writes the same class-file attribute javac does. javac then checks the switch for exhaustiveness and rejects a Java class that tries to implement `Outcome`. `@JvmRecord` is about records, not sealing."}
 ],
 "flashcards": [
  {"front": "Which modifiers can a permitted subtype of a sealed type have?", "back": "Exactly one of `final`, `sealed` or `non-sealed`. Records and enums are implicitly final, so they need none."},
  {"front": "What does `non-sealed` do?", "back": "It reopens that branch: anyone may extend it. A switch still covers the whole branch with one case for the non-sealed type."},
  {"front": "Why don't `case FixedDays` and `case SameAgain` cover `sealed class Extension permits FixedDays, SameAgain` when `Extension` isn't abstract?", "back": "`new Extension()` is a possible value too. Make `Extension` abstract or an interface."},
  {"front": "Where may a Java sealed type's permitted subtypes live?", "back": "In the same module. On the class path (the unnamed module), in the same package."},
  {"front": "Where may a Kotlin sealed type's direct subtypes live?", "back": "In the same package and the same module."},
  {"front": "When can you leave out `permits`?", "back": "When every subtype is declared in the same source file as the sealed type. javac infers the list."},
  {"front": "Why avoid `default` in a switch over your own sealed type?", "back": "It stops the compiler from reporting the switch when a subtype is added. The new subtype silently takes the default branch."}
 ],
 "terms": [
  {"term": "Sealed type", "plain": "A class or interface that lists which classes may extend it directly, like a form with a fixed set of boxes to tick."},
  {"term": "Permitted subtype", "plain": "A class on a sealed type's list. It must be final, sealed or non-sealed."},
  {"term": "non-sealed", "plain": "The modifier that reopens one branch of a sealed hierarchy to any subclass."},
  {"term": "Exhaustive switch", "plain": "A switch whose cases cover every possible value of its selector, so it needs no default."},
  {"term": "PermittedSubclasses", "plain": "The class-file attribute that records a sealed type's list. The JVM checks it when a class loads."},
  {"term": "Unnamed module", "plain": "Where code on the class path lives when it has no `module-info.java`. Most applications run here."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to add `default -> throw new IllegalStateException(\"unknown item\")` to every switch over your sealed `LibraryItem`, \"to be safe\". Explain, in your own words, what that costs and when a default is the right call.",
  "answer": "Over a sealed type, a switch with no default is checked by the compiler: it knows every subtype, and the build fails if a case is missing. That's the main reason to seal the type. Adding a default tells the compiler \"anything else goes here\", so when someone adds a new kind of item, every switch still compiles and the new item throws at run time instead, probably at the desk with a member waiting. Without the default, the build gives you the list of switches to update. A default is right only when \"everything else\" really has one answer, such as rejecting most events in a given state. For a branch others must extend, use a `non-sealed` subtype and one case for it, not a default."
 },
 "deeper": {
  "minutes": 8,
  "body": """Sealing is enforced in three places, and it helps to know which one you're looking at.

javac enforces it at compile time, with the errors in this lesson. The JVM enforces it at load time, from the `PermittedSubclasses` attribute. Compile `final class B implements S` against an old, unsealed `S`, then run it next to a newer `S` that is sealed and doesn't list `B`, and class loading fails with `java.lang.IncompatibleClassChangeError: class B cannot implement sealed interface S`. That stops a stray jar from smuggling a subtype into your hierarchy. And reflection reports it: `Class.isSealed()` and `Class.getPermittedSubclasses()`, both added with sealed classes, are what the tests in this lesson's lab use.

None of the three stops you from adding a subtype yourself, and that's on purpose. The 2026 Amber guide calls adding a permitted subtype "a permissible and compatible evolution" of a sealed API. Programs compiled against the old list keep loading and running; only their switches change behavior. Recompiled, those switches fail to build. Not recompiled, they meet the new subtype at run time and throw `MatchException`. The guide describes this as how Java balances "safety with resilience": you find out either at build time or loudly at run time, never silently. Lesson 3 runs that experiment, and shows that the same thing happens for an enum constant added after the switch was compiled.

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
