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


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="From one record header, javac generates private final fields, '
    'a canonical constructor and public accessors, plus equals, hashCode and toString that read the fields through ObjectMethods.bootstrap">'
    '<rect class="box-a" x="120" y="14" width="440" height="40" rx="8"/>'
    '<text class="t t-code" x="340" y="39" text-anchor="middle">record Shelfmark(String section, int shelf) {}</text>'
    '<line class="ln" x1="300" y1="54" x2="120" y2="96" marker-end="url(#arr)"/>'
    '<line class="ln" x1="340" y1="54" x2="340" y2="96" marker-end="url(#arr)"/>'
    '<line class="ln" x1="380" y1="54" x2="560" y2="96" marker-end="url(#arr)"/>'
    '<rect class="box" x="15" y="100" width="210" height="64" rx="8"/>'
    '<text class="t-s t-code" x="120" y="126" text-anchor="middle">final String section</text>'
    '<text class="t-s t-code" x="120" y="148" text-anchor="middle">final int shelf</text>'
    '<rect class="box" x="235" y="100" width="210" height="64" rx="8"/>'
    '<text class="t-s t-code" x="340" y="126" text-anchor="middle">Shelfmark(String, int)</text>'
    '<text class="t-s t-m" x="340" y="148" text-anchor="middle">canonical constructor</text>'
    '<rect class="box" x="455" y="100" width="210" height="64" rx="8"/>'
    '<text class="t-s t-code" x="560" y="126" text-anchor="middle">section()  shelf()</text>'
    '<text class="t-s t-m" x="560" y="148" text-anchor="middle">public accessors</text>'
    '<line class="ln-a" x1="120" y1="212" x2="120" y2="170" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="130" y="196">reads the fields</text>'
    '<rect class="box-b" x="15" y="214" width="650" height="72" rx="8"/>'
    '<text class="t t-code" x="340" y="238" text-anchor="middle">equals   hashCode   toString</text>'
    '<text class="t-s" x="340" y="258" text-anchor="middle">each one invokedynamic call to ObjectMethods.bootstrap,</text>'
    '<text class="t-s t-m" x="340" y="276" text-anchor="middle">passed "section;shelf" and a getter for each private field (not the accessors)</text>'
    '</svg>'
)

OPENING = """Picture the front desk of a small town library. To borrow books, you fill in a loan slip: your member number, the titles, and the date they're due back. It sits in a clear sleeve, so anyone can read every box, and nothing is written on the back. Two slips filled in the same way stand for the same loan. Before a slip is stamped, the clerk at the counter checks it.

Programs are full of slips like that: small classes that only carry data. For years Java made you write them by hand: fields, a constructor, getters, `equals`, `hashCode` and `toString`. That's five places that must agree on what the data is, and nothing makes them agree. Someone adds a box and updates three places out of five, and the program quietly treats two different slips as one.

The design patterns track was about objects that carry behavior. This track is about the data they carry. In this lesson, we'll let a record write those five places from one line, give it a counter where every instance is checked, and find where its promises stop. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_OLD = """public final class Shelfmark {
    private final String section;
    private final int shelf;                         // added later

    public Shelfmark(String section, int shelf) { this.section = section; this.shelf = shelf; }
    public String section() { return section; }
    public int shelf() { return shelf; }

    @Override public boolean equals(Object o) {
        return o instanceof Shelfmark s && s.section.equals(section);   // nobody updated this
    }
    @Override public int hashCode() { return section.hashCode(); }
    @Override public String toString() { return "Shelfmark[section=" + section + "]"; }
}"""
K_OLD = """class Shelfmark(val section: String, val shelf: Int) {               // shelf added later
    override fun equals(other: Any?) = other is Shelfmark && other.section == section   // nobody updated this
    override fun hashCode() = section.hashCode()
    override fun toString() = "Shelfmark(section=$section)"
}"""
J_REC = "public record Shelfmark(String section, int shelf) {}"
K_REC = "data class Shelfmark(val section: String, val shelf: Int)"

S0 = """Start with a shelfmark, the label on a book's spine that says where the book lives: a three-letter section and a shelf number, such as `FIC 12`. Here it is the way Java classes were written for years, by hand. The shelf number was added later:

""" + pair(J_OLD, K_OLD) + """

It compiles. The `RecordAnatomy` demo in the Try it keeps this class as `OldShelfmark` and runs it on two books on different shelves:

```text
by hand:    OldShelfmark[section=FIC] equals OldShelfmark[section=FIC]: true
```

Shelf 12 and shelf 40 now count as the same place, and the log line can't even say which shelf it meant. The class states "these fields are the data" in five places: the fields, the constructor, `equals`, `hashCode` and `toString`. Five copies of one list drifted apart, the way paperwork does when nobody owns it.

A record states it once. A **record** is a class whose header lists its components, the values that make up its data, and javac, the Java compiler, writes everything else from that list:

""" + pair(J_REC, K_REC) + """

Here is the picture we'll use for the whole track: library paperwork. A record is a filled-in form in a clear sleeve. Each component is one box on the form, and what you see through the sleeve is all there is: no notes on the back, no hidden boxes. Comparing two forms means comparing them box by box. Reading a form aloud means reading every box, in order.

javac turns that one line into the parts we used to type. Each component gets a private final field and a public accessor, a method named after the component that returns it: `section()` and `shelf()`, with no `get`. The **canonical constructor** takes every component, in header order. `equals`, `hashCode` and `toString` use every component, so they can't drift. The class is final and extends `java.lang.Record`. Records have been a final feature, that is, finished and switched on, since JDK 16 (JEP 395, the JDK Enhancement Proposal that describes them). So all of this works on the JDK 21 the labs compile for.

**Five copies of one list drift apart. Write the list once, in the header.**

The `Record` Javadoc calls a record "a shallowly immutable, transparent carrier for a fixed set of values", and each word is a rule. Fixed: you can't add instance fields, and `private int cache;` in the body fails with `field declaration must be static`. Static fields, methods and nested types are fine. Transparent: the state is the API, so every component is public through its accessor. A record can implement interfaces, but it can't extend a class, because it already extends `Record`. Shallowly immutable gets its own section below.

The generated methods aren't what you would write by hand, and you can see that one level down. `javap`, the JDK's class-file reader, shows that `equals`, `hashCode` and `toString` are each one `invokedynamic` instruction. That is a call whose target the JVM, the program that runs your Java code, picks the first time the call runs, by asking a bootstrap method, here `ObjectMethods.bootstrap`. javac hands it the component names as one string, `section;shelf`, and a getter for each private field, and the JDK builds the method bodies from that list. That's why the Javadoc says the `toString` format may change: never parse it. kotlinc, the Kotlin compiler, does it the older way and writes the bodies into your class.

A record is still an ordinary object with its own identity: every `new` makes a separate one. Two forms with the same boxes are still two sheets of paper, so `new Shelfmark("FIC", 12) == new Shelfmark("FIC", 12)` is `false`, and `synchronized` on a record works. Objects without identity are what Project Valhalla adds, as a preview in JDK 28 (a preview feature is switched off unless you ask for it, and may still change). Lesson 4 of this track covers it.

javac now prints every box on the form. It doesn't yet check what anybody writes in them."""

ASIDE0 = {
    "title": "Can a component have any name?",
    "body": "Almost any. The Java Language Specification forbids eight: `clone`, `finalize`, `getClass`, `hashCode`, `notify`, `notifyAll`, `toString` and `wait`. Each one would give the record an accessor with the same name as a method of `Object`, so javac stops with `illegal record component name wait`. A plain Kotlin data class turns `val wait` into `getWait()`, so the clash doesn't come up there. In Java, a waiting time is `expectedWait`, which reads better anyway."
}

# ---------------------------------------------------------------- section 1
J_COMPACT = """record Shelfmark(String section, int shelf) {
    Shelfmark {                                          // the compact canonical constructor
        Objects.requireNonNull(section, "section");
        if (shelf < 1) throw new IllegalArgumentException("shelf must be 1 or more: " + shelf);
        section = section.toUpperCase(Locale.ROOT);      // reassign the parameter
    }                                                    // javac assigns the fields here

    Shelfmark(String section) { this(section, 1); }     // any other constructor calls it first
}"""
K_COMPACT = """data class Shelfmark(val section: String, val shelf: Int) {
    init {                                               // runs on every construction, and on copy()
        require(shelf >= 1) { "shelf must be 1 or more: $shelf" }
        require(section == section.uppercase()) { "section must be upper case: $section" }
    }

    constructor(section: String) : this(section, 1)     // any other constructor calls it first
}"""

S1 = """A form is only as good as the counter that checks it. Suppose the checks live in a static factory, `Shelfmark.of(...)`. It can check the section all it likes, and `new Shelfmark("fiction!", -3)` walks straight past it, through the side door.

A record gives you a counter with no side door. Every other constructor must call the canonical constructor first, with `this(...)`, and so does every factory and every wither. That makes the canonical constructor the one place to check and tidy every instance. You write it in the **compact** form, with no parameter list:

""" + pair(J_COMPACT, K_COMPACT) + """

Read the compact constructor as the clerk at the counter. First it rejects a missing section, then it checks the shelf, and finally it tidies the writing, so `"fic"` becomes `"FIC"`. In the compact form the parameters are ordinary local variables. You may reassign them, and javac copies their final values into the fields after your code runs. The clerk can't stamp the fields directly: `this.shelf = shelf;` fails with `cannot assign a value to final variable shelf`.

The second constructor shows the rule for side doors: it must start with `this(section, 1)`. On JDK 21, any statement before that line fails with `constructor is not canonical, so its first statement must invoke another constructor of class Shelfmark`. JDK 25 made flexible constructor bodies final (JEP 513), so there you may run plain statements first, such as splitting the label `"fic 12"` in two, as long as they don't touch the fields.

The Kotlin twin shows a real difference. `init` runs on every construction, including `copy()`. But a data class can't change a constructor parameter before it becomes a property. It can reject `"fic"`, but it can't turn it into `"FIC"`. Tidying moves into a factory function, and the public constructor still accepts the raw value.

The last door is deserialization, which rebuilds an object from bytes, for example bytes read back from a file. The `Record` Javadoc says the canonical constructor runs during deserialization, so a record gets its checks there for free. An ordinary class needs a hand-written `readObject` method to check itself again, and most classes don't have one. A Kotlin data class doesn't run its `init` there at all, unless it's marked `@JvmRecord`, which compiles it to a real record.

The demo in the Try it swaps two numbers inside the bytes of a `PageRange`, a request to photocopy pages 1 to 5, and reads it back. The Java record prints `tampered stream rejected: first > last: 5 > 1`. The Kotlin twin prints:

```text
tampered stream gave: PageRangeK(first=5, last=1)
tampered stream rejected: first > last: 5 > 1
```

The plain data class climbed in through a window: it came back as a range its own `init` forbids. The `@JvmRecord` version went past the clerk like everyone else.

**A check that some paths skip is only a suggestion. Put it in the canonical constructor.**

The clerk checks what's written in every box. The clerk can't see a sheet stapled to the form that somebody is still writing on."""

# ---------------------------------------------------------------- section 2
J_CRATE = """// a crate of books on its way to a branch library
record Crate(String branch, List<String> titles) {}

var titles = new ArrayList<>(List.of("Dune", "Emma"));
var crate = new Crate("NORTH", titles);
var sent = new HashSet<>(Set.of(crate));
titles.add("Ulysses");             // someone reuses their list
sent.contains(crate);              // false: the hashCode changed under the set"""
K_CRATE = """// a crate of books on its way to a branch library
data class Crate(val branch: String, val titles: List<String>)

val titles = mutableListOf("Dune", "Emma")
val crate = Crate("NORTH", titles)
val sent = hashSetOf(crate)
titles += "Ulysses"                // someone reuses their list
crate in sent                      // false: the hashCode changed under the set"""
J_SAFE = """record SafeCrate(String branch, List<String> titles) {
    SafeCrate { titles = List.copyOf(titles); }          // an unmodifiable copy of the caller's list
}"""
K_SAFE = """data class SafeCrate(val branch: String, val titles: List<String>) {
    companion object {                                    // Kotlin can't reassign the parameter
        fun of(branch: String, titles: List<String>) = SafeCrate(branch, java.util.List.copyOf(titles))
    }
}"""

S2 = """Start with what `equals` compares. Two records are equal when they're the same record class and every component is equal. For a reference component that means `Objects.equals`. For a primitive it means the wrapper's `compare` method returns 0, which holds two surprises for a `double`. A record holding `NaN`, the "not a number" value, equals another one holding `NaN`, though `NaN == NaN` is false. And records holding `0.0` and `-0.0` aren't equal, though `0.0 == -0.0` is true. Kotlin data classes behave the same way.

Arrays are worse. An `int[]` component compares by reference, so two records with equal arrays aren't equal, and `toString` prints something like `[I@1b6d3586`. Use a `List` instead.

A `List` component brings the real trap. Picture a form with a box that says "see attached list", and a list stapled behind it. The form is checked and stamped, but whoever kept a copy of the attached sheet can still write on it. A record holds a reference to whatever list the caller passed in. Here a crate of books is on its way to the North branch, and the program keeps the crates it sent in a set:

""" + pair(J_CRATE, K_CRATE) + """

The `ShallowDemo` in the Try it prints:

```text
crate now:          Crate[branch=NORTH, titles=[Dune, Emma, Ulysses]]
hashCode changed:   true
sent.contains:      false
```

The crate is still in the set. The set just looks for it in the wrong place: a `HashSet` files each element under its `hashCode`, and that number changed after the crate was filed. Nothing threw. The fix is one line in the compact constructor:

""" + pair(J_SAFE, K_SAFE) + """

`List.copyOf` makes an unmodifiable copy, and it throws `NullPointerException` for a null element, which is what you want for library data. Kotlin's `List<String>` is a read-only view, not an immutable list: the caller may still hold the same object as a `MutableList`. So a data class needs the same copy, made in a factory. *Don't share: immutability, confinement, ThreadLocal* in the concurrency track made this point about threads. Here the cost is a lost crate, even with one thread.

**A record is only as immutable as its components. Copy collections on the way in.**

The last trap looks like a fix. To keep a member's phone number out of the logs, someone overrides the accessor, so `phone()` returns `****0123`. The demo prints `accessor: ****0123` and then `toString: Masked[phone=01614960123]`. The generated `toString` reads the field directly (those were the getters in the bootstrap arguments), so the logs never ask the accessor. The override breaks a promise in the `Record` Javadoc too: a copy built from the accessors, `new Masked(m.phone())`, should equal `m`, and the demo prints `false`. To hide a component, override `toString` itself, as the lab does.

Every slip is now checked at the counter and safe from other people's pens. Which leaves a fair question: how do you change one?"""

# ---------------------------------------------------------------- section 3
J_WITHER = """record Loan(String memberId, int days, List<String> titles) {
    Loan {
        if (days <= 0) throw new IllegalArgumentException("days must be positive: " + days);
        titles = List.copyOf(titles);
    }

    Loan withDays(int newDays) {                         // a wither, written by hand
        return new Loan(memberId, newDays, titles);      // through the canonical constructor
    }
}

Loan renewed = first.withDays(35);"""
K_WITHER = """data class LoanRequest(val memberId: String, val days: Int, val titles: List<String>) {
    init {
        require(days > 0) { "days must be positive: $days" }
    }
}

val renewed = first.copy(days = 35)                      // generated, and it runs init"""

S3 = """You don't change a stamped form. You fill in a new one, and it goes past the counter again. A renewal is exactly that: the same loan, with a new number of days. Kotlin generates `copy()` for this, with a named parameter for each property. Java generates nothing, so you write a **wither**, a method that returns a copy of the record with one component changed:

""" + pair(J_WITHER, K_WITHER) + """

Both go through the checks, and that's the point. The `WitherDemo` ends with `wither ran the checks: days must be positive: -1`, and its Kotlin twin with the same message from `copy()`, so there's no path to an invalid loan. Both also print `same titles list object: true`: a wither and `copy()` reuse the component references. That's safe here only because the record made its own unmodifiable copy at the counter.

The cost on the Java side is typing, and it grows with the record. In a 2020 design draft, Brian Goetz, Java's language architect, noted that a class has one getter per component but "could conceivably have O(2^n) withers". He asked that hand-written withers not become a best practice. Write withers only for the changes your domain really makes. A loan earns `withDays`; a shelfmark probably needs none.

A language fix exists on paper. JEP 468, derived record creation, proposes `loan with { days = 35; }`. It would take the record apart, run the block, and call the canonical constructor with the result. It's a Candidate JEP, no JDK has it, and in January 2026 Goetz wrote that it "has been 'on hold' for a while". Don't plan around it.

The other differences between the two languages matter more day to day. A data class may declare properties in its body, and Kotlin leaves those out of `equals`, `hashCode`, `toString` and `copy()`, so two objects that differ only there are equal. A record can't have body state at all. A data class can't be `open`, `abstract` or `sealed`, and a record is always final. Kotlin takes a data class apart with `val (section, shelf) = mark`, through generated `componentN()` functions. Java takes a record apart with record patterns, which lesson 3 of this track covers.

Where the two languages meet, Kotlin reads a Java record's accessors as properties, `mark.section`. `@JvmRecord` on a data class emits a real `java.lang.Record`, which Java code sees as one. The Kotlin docs warn that adding `@JvmRecord` to an existing class isn't a binary-compatible change, so decide when you create the class.

Records have one honest limit. A record can't hide its representation or keep any state beyond its components. A class that needs one private cache, or an inside different from its outside, falls back to writing all five places by hand. Goetz's design note on carrier classes, in Go deeper, sketches a way back."""

L = {
 "id": "dop-01",
 "title": "Records: transparent carriers for data",
 "minutes": 35,
 "goal": "By the end you can write a record whose compact constructor checks and tidies every instance, explain what javac generates for it, and say exactly where its equality and immutability stop.",
 "opening": OPENING,
 "warmup": {
  "q": "`record Masked(String phone)` overrides its accessor so that `phone()` returns `\"****0123\"` for the number 01614960123. What does `toString()` return?",
  "options": ["`Masked[phone=****0123]`, because toString calls the accessor",
              "`Masked[phone=01614960123]`",
              "Nothing: it doesn't compile, because record accessors can't be overridden",
              "`Masked@1b6d3586`, because overriding an accessor turns off the generated toString"],
  "answer": 1,
  "why": "The generated `toString`, `equals` and `hashCode` read the private field directly, not the accessor, so the full number reaches the log. Overriding an accessor is legal as long as the return type matches. To hide a component, override `toString` itself, as the lab does. The section on equality and immutability shows it with real output."
 },
 "sections": [
  {
   "h": "A record is its components, and javac writes the rest",
   "body": S0,
   "aside": ASIDE0,
   "figure": {"svg": FIG, "caption": "One header line becomes fields, a constructor and accessors. The three Object methods are built at run time and read the fields, not the accessors."},
   "try": {
    "title": "Look inside a record",
    "minutes": 4,
    "steps": [
     "Run `RecordAnatomy` (or its Kotlin twin) with the command below. Predict the `==` line before you look.",
     "From `labs/`, print the bytecode of the nested record: `javap -p -c 'modernjava/build/classes/java/demo/workbench/modernjava/l01/demo/RecordAnatomy$Shelfmark.class'`. Find the three `invokedynamic` lines.",
     "Run `javap -v` on the same file and look for `BootstrapMethods`. Then run `javap -p modernjava/build/classes/kotlin/demo/workbench/modernjava/l01/demo/Shelfmark.class` and compare what kotlinc generated."
    ],
    "code": demo("RecordAnatomy"),
    "expect": "The first line shows the hand-written class calling two different shelves equal: `OldShelfmark[section=FIC] equals OldShelfmark[section=FIC]: true`. Then the record prints `Shelfmark[section=FIC, shelf=12]`, `equals: true`, `==: false`, `isRecord: true` and the components `[java.lang.String section, int shelf]`. The Kotlin twin prints `isRecord: false` for the plain data class and `true` for the `@JvmRecord` one. In the `javap -v` output, the bootstrap method is `ObjectMethods.bootstrap`, and its arguments include the string `section;shelf` and two `REF_getField` handles on the private fields. The Kotlin class has `getSection()`, `component1()`, `copy(java.lang.String, int)` and `copy$default(...)` instead."
   },
   "refs": [
    {"title": "Record (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Record.html", "kind": "docs"},
    {"title": "JEP 395: Records", "url": "https://openjdk.org/jeps/395", "kind": "read"}
   ]
  },
  {
   "h": "The compact constructor: one counter every instance passes",
   "body": S1,
   "try": {
    "title": "Go through every door",
    "minutes": 5,
    "steps": [
     "Run `CompactConstructorDemo`. Read the last line of output before you read the code that produced it.",
     "Run the Kotlin twin, `CompactConstructorDemoKt`. Which tampered page range got through?",
     "In the Java demo, add `this.shelf = shelf;` inside the compact constructor of `Shelfmark` and run again. Read the compiler error, then undo the change.",
     "If you have JDK 25, run `java preview/FlexibleConstructor.java` from `labs/modernjava`. Then run the same file with JDK 21 and read the two errors."
    ],
    "code": demo("CompactConstructorDemo"),
    "expect": "The Java demo prints `Shelfmark[section=FIC, shelf=12]`, `Shelfmark[section=BIO, shelf=1]`, `Shelfmark[section=REF, shelf=7]`, `IAE: shelf must be 1 or more: 0`, `NPE: section` and finally `tampered stream rejected: first > last: 5 > 1`. Deserialization called the compact constructor, it threw, and `ObjectInputStream` wrapped that in an `InvalidObjectException`. The Kotlin twin prints `tampered stream gave: PageRangeK(first=5, last=1)` for the plain data class, an object its own `init` forbids, and rejects the `@JvmRecord` one. The field assignment fails with `cannot assign a value to final variable shelf`. On JDK 25 the preview file reads `fic 12` into `Shelfmark[section=FIC, shelf=12]`. JDK 21 rejects it with `constructor is not canonical, so its first statement must invoke another constructor of class Shelfmark` and `call to this must be first statement in constructor`."
   },
   "refs": [
    {"title": "Records in Kotlin: @JvmRecord", "url": "https://kotlinlang.org/docs/jvm-records.html", "kind": "docs"}
   ]
  },
  {
   "h": "Equality and immutability go one level deep",
   "body": S2,
   "try": {
    "title": "Lose a crate, leak a phone number",
    "minutes": 4,
    "steps": [
     "Predict the `sent.contains` line, then run `ShallowDemo`.",
     "Give `Crate` a compact constructor that copies its list, as `SafeCrate` does. Run it again.",
     "Run the Kotlin twin and look at the `copy shares list` line. Did `copy()` copy the list?"
    ],
    "code": demo("ShallowDemo"),
    "expect": "`hashCode changed: true` and `sent.contains: false`. After your fix the crate keeps its two titles, the hash code stays the same, and the set finds it. The masked record prints `accessor: ****0123` but `toString: Masked[phone=01614960123]`, and `copy equals orig: false`. The `NaN` records are equal and the `0.0` and `-0.0` ones are not. In Kotlin, the copy shows `Persuasion`, which was added after the copy was made: `copy()` copies references, not the objects behind them."
   }
  },
  {
   "h": "Changing a record: withers in Java, copy() in Kotlin",
   "body": S3,
   "try": {
    "title": "Wither versus copy()",
    "minutes": 4,
    "steps": [
     "Run `WitherDemo` and its twin `WitherDemoKt`. Compare the four lines each prints.",
     "Add a `withMemberId(String id)` wither to the Java record and call it with `\" \"`. Should that be rejected? Add the check where every wither will get it.",
     "In `WitherDemo.kt`, add `var note = \"\"` to the body of `LoanRequest`, set `first.note = \"renewed by phone\"`, and print `first == first.copy()` and `first.copy().note`."
    ],
    "code": demo("WitherDemo"),
    "expect": "Both versions print the original loan, the renewed one with 35 days and two titles, `same titles list object: true`, and a rejected `days must be positive: -1`. Withers and `copy()` both reuse the component references, which is safe here only because the list can't change. The blank-id check belongs in the compact constructor, so every wither gets it for free. In Kotlin, `first == first.copy()` is `true` and the copy's `note` is empty: body properties are ignored by `equals` and not copied."
   },
   "refs": [
    {"title": "Data classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/data-classes.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "A checked shelfmark in Java and Kotlin",
  "java": {"title": "Shelfmark.java", "src": """public record Shelfmark(String section, int shelf) {
    private static final Pattern SECTION = Pattern.compile("[A-Z]{3}");

    public Shelfmark {
        Objects.requireNonNull(section, "section");
        section = section.trim().toUpperCase(Locale.ROOT);    // tidy in place
        if (!SECTION.matcher(section).matches()) throw new IllegalArgumentException("bad section: " + section);
        if (shelf < 1 || shelf > 999) throw new IllegalArgumentException("bad shelf: " + shelf);
    }

    public Shelfmark next() {
        return new Shelfmark(section, shelf + 1);              // past the counter again
    }
}"""},
  "kotlin": {"title": "Shelfmark.kt", "src": """data class Shelfmark(val section: String, val shelf: Int) {
    init {
        require(SECTION.matches(section)) { "bad section: $section" }   // can reject, can't tidy
        require(shelf in 1..999) { "bad shelf: $shelf" }
    }

    fun next() = Shelfmark(section, shelf + 1)                 // past init again

    companion object {
        private val SECTION = Regex("[A-Z]{3}")
        fun of(section: String, shelf: Int) = Shelfmark(section.trim().uppercase(), shelf)
    }
}"""},
  "note": "Both give you `equals`, `hashCode` and `toString` over all components, final fields, and a check that every construction goes through, including Kotlin's `copy()`. Three things differ. Java's compact constructor can tidy a parameter before it becomes a field; a data class can only reject it, so tidying lives in a factory and the public constructor stays open to raw input. Java deserialization rebuilds a record through its canonical constructor but skips a data class's `init` (`@JvmRecord` closes that gap). And Kotlin has `copy()` with named arguments, while Java has hand-written withers until JEP 468 ships, which it hasn't."
 },
 "worked": {
  "title": "Turn a hand-written membership form into a record",
  "steps": [
   {"say": "When someone joins the library, the program fills in a membership form. Here it is as a JavaBean, a class with a getter and a setter for every field. It hands out its live list of branches, and its hand-written `equals` and `toString` weren't updated when the phone number was added. Any code can change a form after it was checked.",
    "code": """public class MembershipForm {
    private String name;
    private String phone;
    private List<String> branches = new ArrayList<>();

    public void setPhone(String phone) { this.phone = phone; }
    public List<String> getBranches() { return branches; }    // hands out the live list
    // ... more setters and getters, and equals, hashCode, toString by hand
}""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """class MembershipForm {
    var name: String? = null
    var phone: String? = null
    val branches: MutableList<String> = mutableListOf()       // hands out the live list
}"""},
   {"say": "Write the header. The components are the whole state, and every setter is gone. Recompile: each place that called a setter is now a compile error, which is your list of code that changed a form after it was filled in.",
    "code": """// 1. the components are the state
public record MembershipForm(String name, PhoneNumber phone, List<String> branches) {}""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """// 1. the properties are the state
data class MembershipForm(val name: String, val phone: PhoneNumber, val branches: List<String>)"""},
   {"say": "Add the compact constructor. Reject what can't be valid, then copy the list so the caller can't change it later. `phone` is a `PhoneNumber`, the lab's record that checks itself, so the form doesn't repeat those checks.",
    "code": """public record MembershipForm(String name, PhoneNumber phone, List<String> branches) {
    public MembershipForm {
        Objects.requireNonNull(name, "name");                               // 2. reject
        Objects.requireNonNull(phone, "phone");
        if (name.isBlank()) throw new IllegalArgumentException("blank name");
        branches = List.copyOf(branches);                                    // 3. copy
        if (branches.isEmpty()) throw new IllegalArgumentException("no home branch");
    }
}""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """data class MembershipForm(val name: String, val phone: PhoneNumber, val branches: List<String>) {
    init {
        require(name.isNotBlank()) { "blank name" }                         // 2. reject
        require(branches.isNotEmpty()) { "no home branch" }
    }

    companion object {
        fun of(name: String, phone: PhoneNumber, branches: List<String>) =
            MembershipForm(name, phone, java.util.List.copyOf(branches))    // 3. copy
    }
}"""},
   {"say": "Add only the wither the library needs. Members do change their phone numbers, so `withPhone` earns its place. It calls the canonical constructor, so a changed form can't skip the checks. In Kotlin, `copy(phone = ...)` already exists and runs `init`.",
    "code": """    // 4. one wither, through the canonical constructor
    public MembershipForm withPhone(PhoneNumber newPhone) {
        return new MembershipForm(name, newPhone, branches);
    }""", "lang": "java",
    "alt_lang": "kotlin", "alt_code": """    // 4. no wither to write: copy() is generated and runs init
    val updated = form.copy(phone = PhoneNumber("0161 496 0999"))"""}
  ]
 },
 "lab": {
  "title": "The library's forms as records",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/Shelfmark.java", f"{lab}/main/{P}/LoanSlip.java", f"{lab}/main/{P}/PhoneNumber.java"],
  "run": "./gradlew :modernjava:test --tests 'workbench.modernjava.l01.*'",
  "steps": [
   "Run the tests once from `labs/`. All eight fail. Read the test names in `LibraryFormsTest`: they are the spec.",
   "In `Shelfmark`, write the compact constructor (TODO 1) and `next` (TODO 2).",
   "In `LoanSlip`, write the compact constructor with a copy of the titles (TODO 3), then `withDue`, the wither for renewals (TODO 4).",
   "In `PhoneNumber`, check the number and strip its spaces (TODO 5), override `toString` (TODO 6) and write `last4` (TODO 7).",
   "Run the tests until all eight pass. Then compare your code with the reference answers in `src/solution`."
  ],
  "hints": [
   "In a compact constructor you assign the parameter: `section = section.trim().toUpperCase(Locale.ROOT);`. Writing `this.section = ...` doesn't compile.",
   "Order matters in `Shelfmark`: tidy first, then check for three letters, or `\" fic \"` fails the check.",
   "`next` is one line. Call the canonical constructor with `shelf + 1`, and it rejects shelf 1000 by itself.",
   "`List.copyOf(titles)` throws `NullPointerException` for a null list, so it does that null check for you.",
   "Don't touch the `digits()` accessor. The test checks that `new PhoneNumber(p.digits())` still equals `p`."
  ],
  "done_when": "All eight tests in `LibraryFormsTest` pass."
 },
 "drill": {
  "title": "A checked member number from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `record MemberId(String value)` that rejects null, trims and upper-cases the value, and then rejects anything that isn't `M-` followed by four to six digits. Then write the Kotlin version. Which of the two can store the tidied value without a factory?",
  "answer": {"lang": "java", "src": """public record MemberId(String value) {
    private static final Pattern SHAPE = Pattern.compile("M-[0-9]{4,6}");

    public MemberId {
        Objects.requireNonNull(value, "value");
        value = value.trim().toUpperCase(Locale.ROOT);          // tidy first
        if (!SHAPE.matcher(value).matches()) {
            throw new IllegalArgumentException("bad member id: " + value);
        }
    }
}""",
             "alt": {"lang": "kotlin", "src": """data class MemberId(val value: String) {
    init {
        require(SHAPE.matches(value)) { "bad member id: $value" }   // can reject, can't tidy
    }

    companion object {
        private val SHAPE = Regex("M-[0-9]{4,6}")
        fun of(raw: String) = MemberId(raw.trim().uppercase())     // so tidying lives here
    }
}"""}}
 },
 "recap": [
  "A record is a final class whose header lists its components. javac writes private final fields, accessors, one canonical constructor, and `equals`, `hashCode` and `toString` from that list, so they can't drift apart.",
  "Check and tidy in the compact constructor. Every path goes through it: `new`, factories, other constructors, withers and Java deserialization. Kotlin's `init` is the twin, but it can't tidy a parameter, and Java deserialization skips it unless the class is `@JvmRecord`.",
  "Equality compares every component: `Objects.equals` for references and `compare` for primitives, so `NaN` equals `NaN` and `0.0` doesn't equal `-0.0`. Arrays compare by reference.",
  "Records are only shallowly immutable. Copy collection components with `List.copyOf`, or a changed list loses its record in a `HashSet`. The generated methods read fields, not accessors, so hide a secret in `toString`.",
  "Kotlin generates `copy()`; Java has hand-written withers, because JEP 468 is on hold and in no JDK.",
  "The limit: a record can't keep state beyond its components or hide its representation, and it's still an identity object. A class that needs a private cache goes back to writing everything by hand."
 ],
 "closing": "We started at the front desk, with a loan slip in a clear sleeve. A record is that slip, and its components are the boxes. javac writes what we used to keep in five places, and the compact constructor is the counter every instance passes, whichever door it came through. Its promises stop one level down, at the attached list and the masked accessor.\n\nNow look in your own code for a class with `equals`, `hashCode` and `toString` written by hand. Compare the fields each one uses. If the three lists differ, you've found a drifting form.\n\nNext, we'll fix which kinds of form exist at all. How can the compiler know it has seen every kind of library item?",
 "quiz": [
  {"q": "`record Crate(String branch, List<String> titles)` is a key in a `HashMap<Crate, String>` that records where each crate is. The code that built the crate later calls `titles.add(\"Persuasion\")` on its own list. What does `map.get(crate)` most likely return now?",
   "options": ["The location, because records are immutable", "`null`, because the key's hashCode changed and the map looks in the wrong bucket", "It throws ConcurrentModificationException", "The location, because HashMap compares record keys with =="],
   "answer": 1, "why": "The record's fields are final, but the list they point to is the caller's list. `hashCode` includes the list, so it changes, and the map searches a bucket where the entry isn't. Nothing throws. Copying the list in the compact constructor prevents it."},
  {"q": "Which of these makes `new Shelfmark(\"fic\", 12)` equal to `new Shelfmark(\"FIC\", 12)`?",
   "options": ["`public Shelfmark { this.section = section.toUpperCase(); }`", "`public String section() { return section.toUpperCase(); }`", "`public Shelfmark { section = section.toUpperCase(); }`", "`public Shelfmark(String section, int shelf) { section = section.toUpperCase(); }`"],
   "answer": 2, "why": "In the compact form you reassign the parameter and javac assigns the field afterwards. Assigning `this.section` there doesn't compile. The accessor override leaves the fields different, and `equals` compares fields. The full canonical constructor in the last option never assigns the fields, so it doesn't compile either."},
  {"q": "A Kotlin `data class PageRange(val first: Int, val last: Int) : Serializable` checks `first <= last` in `init`. A program deserializes a tampered stream that says first = 5, last = 1. What happens?",
   "options": ["You get `PageRange(first=5, last=1)`: Java deserialization doesn't run `init`", "`InvalidObjectException`, because `init` runs during deserialization", "`IllegalArgumentException` from `require`", "`ClassCastException`, because the stream no longer matches the class"],
   "answer": 0, "why": "Java deserialization builds a plain serializable class without calling its constructor, so `init` never runs and the invalid object comes back. A Java record, or the same data class marked `@JvmRecord`, is rebuilt through its canonical constructor, and the stream is rejected with `InvalidObjectException`."},
  {"q": "From the memory model track: `record OpeningHours(Map<String, String> days)` copies the map with `Map.copyOf` in its compact constructor. A new `OpeningHours` is published through a plain, non-volatile field. What is guaranteed for a thread that reads the new reference?",
   "options": ["Nothing: without volatile it may see a null map", "It may see a half-built map", "Nothing, because records have no final fields", "It sees the map as the constructor left it, because record fields are final, though it may keep reading the old reference for a while"],
   "answer": 3, "why": "Record fields are private final, so final-field rules apply: a thread that sees the reference sees the fields, and the map built in the constructor, as the constructor left them. A plain field doesn't promise when the new reference becomes visible. Publish it through a volatile field if readers must see updates promptly.",
   "from": "jmm-04"},
  {"q": "`data class Copy(val isbn: String) { var shelf = \"FIC 12\" }`. Copy `a` sits on shelf FIC 12. Copy `b` has the same ISBN and sits on REF 3. What is `a == b`?",
   "options": ["`false`, because the shelves differ", "`true`", "It doesn't compile: data classes can't have body properties", "It depends on which object was created first"],
   "answer": 1, "why": "Only primary-constructor properties take part in a data class's `equals`, `hashCode`, `toString` and `copy()`. `shelf` lives in the body, so Kotlin ignores it. A Java record can't have body state at all, so the question can't arise there."}
 ],
 "flashcards": [
  {"front": "What does javac generate for `record Shelfmark(String section, int shelf)`?", "back": "Private final fields, accessors `section()` and `shelf()`, a canonical constructor `Shelfmark(String, int)`, and `equals`, `hashCode` and `toString`. The class is final and extends `java.lang.Record`."},
  {"front": "In a compact constructor, how do you tidy a component?", "back": "Reassign the parameter: `section = section.trim();`. javac assigns the fields after the body. `this.section = ...` doesn't compile."},
  {"front": "A record overrides its accessor to mask a phone number. What does `toString` print?", "back": "The full number. The generated `toString`, `equals` and `hashCode` read the fields, not the accessors. Override `toString` instead."},
  {"front": "`record R(double d)`: is `new R(Double.NaN).equals(new R(Double.NaN))` true?", "back": "Yes. Primitive components compare with `Double.compare`, which treats NaN as equal to itself. And `0.0` doesn't equal `-0.0`."},
  {"front": "How do you make a record with a `List` component safe as a map key?", "back": "Copy it in the compact constructor: `titles = List.copyOf(titles);`. The copy is unmodifiable and rejects null elements."},
  {"front": "Does Java deserialization run a Kotlin data class's `init` block?", "back": "No, so a tampered stream can build an invalid object. A Java record, or a data class marked `@JvmRecord`, is rebuilt through its canonical constructor."},
  {"front": "Can you write `loan with { days = 35; }` in Java today?", "back": "No. Derived record creation (JEP 468) is a Candidate JEP, on hold since at least January 2026, and in no JDK. Write withers by hand."}
 ],
 "terms": [
  {"term": "Record component", "plain": "One of the values in a record's header, like one box on a form. Each one gets a private final field and a public accessor."},
  {"term": "Canonical constructor", "plain": "The constructor whose parameters match the components in order. Every other way of making the record goes through it."},
  {"term": "Compact constructor", "plain": "The canonical constructor written without a parameter list. Its parameters are locals you can check and reassign; javac assigns the fields at the end."},
  {"term": "Accessor", "plain": "The generated public method that returns a component. It's named after the component: `section()`, not `getSection()`."},
  {"term": "Shallow immutability", "plain": "The fields can't be reassigned, but the objects they point to may still change."},
  {"term": "Wither", "plain": "A method that returns a copy of a record with one component changed. Java has no generated ones."},
  {"term": "@JvmRecord", "plain": "A Kotlin annotation that compiles a data class to a real `java.lang.Record`."}
 ],
 "explain_back": {
  "prompt": "A teammate says: \"Our `MemberCard(String phone, List<String> branches)` record is immutable, so it's safe to keep in a `HashSet` and to log as it is.\" Explain, in your own words, the two ways that can go wrong and what you would change.",
  "answer": "A record is only shallowly immutable. Its fields can't be reassigned, but `branches` points to whatever list the caller passed in, and if the caller keeps changing that list, the record's `hashCode` changes and the set can't find it any more. I'd copy the list in the compact constructor with `List.copyOf`. Logging is the second problem: the generated `toString` prints every component, so the member's full phone number goes into the logs. Overriding the `phone()` accessor doesn't help, because `toString` reads the field directly. I'd override `toString` and print only the last four digits there, or better, make the phone a `PhoneNumber` record that masks itself."
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

So in Java, the checks must live inside the constructor, where nobody can bypass them. Kotlin lets you make a data class constructor private and send callers through a factory that tidies, but `copy()` still exposes it. Kotlin 2.4.21 warns about this, says the warning becomes an error in language version 2.5, and offers `@ConsistentCopyVisibility` to make `copy()` as private as the constructor.

The second detail is about what comes after records. In a January 2026 design note, "Data-Oriented Programming for Java: Beyond Records", Brian Goetz describes the cliff you fall off when a class is almost a record: one derived field or one private cache, and you're back to writing everything by hand. The note sketches *carrier classes*, written like `class Point(int x, int y) { ... }`: a normal class with a record-style state description. The language would require the canonical constructor and the accessors and give the class a deconstruction pattern, while the class declares its own fields and need not be final. It's a design note, and no JEP exists yet, so treat it as a direction for now."""
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
