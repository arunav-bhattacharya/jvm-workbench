import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/kotlin/src"
P = "kotlin/workbench/kotlin/l05"
DK = "kotlin/workbench/kotlin/l05/demo"
DJ = "java/workbench/kotlin/l05/demo"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :kotlin:demo -Pmain=workbench.kotlin.l05.demo."


def demo(name):
    """Kotlin demo with its runnable Java twin."""
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{DK}/{name}.kt"),
            "run": RUN + name + "Kt", "file": f"{lab}/demo/{DK}/{name}.kt",
            "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(f"{lab}/demo/{DJ}/{name}Java.java"),
                    "run": RUN + name + "Java", "file": f"{lab}/demo/{DJ}/{name}Java.java"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 680 230" role="img" aria-label="A function with context parameters compiles to a static method whose first parameters are the context parameters, then the extension receiver, then the ordinary parameters">'
    '<text class="t-s t-m" x="340" y="20" text-anchor="middle">Kotlin declaration</text>'
    '<rect class="box-a" x="20" y="32" width="270" height="40" rx="8"/>'
    '<text class="t-s t-code" x="155" y="57" text-anchor="middle">context(logbook: Logbook, shift: Shift)</text>'
    '<rect class="box-b" x="305" y="32" width="110" height="40" rx="8"/>'
    '<text class="t-s t-code" x="360" y="57" text-anchor="middle">fun Job.</text>'
    '<rect class="box" x="430" y="32" width="230" height="40" rx="8"/>'
    '<text class="t-s t-code" x="545" y="57" text-anchor="middle">check(printer: String)</text>'
    '<line class="ln" x1="115" y1="72" x2="82" y2="138" marker-end="url(#arr)"/>'
    '<line class="ln" x1="195" y1="72" x2="227" y2="138" marker-end="url(#arr)"/>'
    '<line class="ln" x1="360" y1="72" x2="360" y2="138" marker-end="url(#arr)"/>'
    '<line class="ln" x1="545" y1="72" x2="545" y2="138" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="420" y="106" text-anchor="middle">order on the JVM</text>'
    '<rect class="box-a" x="20" y="142" width="125" height="40" rx="8"/>'
    '<text class="t t-code" x="82" y="167" text-anchor="middle">Logbook</text>'
    '<rect class="box-a" x="165" y="142" width="125" height="40" rx="8"/>'
    '<text class="t t-code" x="227" y="167" text-anchor="middle">Shift</text>'
    '<rect class="box-b" x="305" y="142" width="110" height="40" rx="8"/>'
    '<text class="t t-code" x="360" y="167" text-anchor="middle">Job</text>'
    '<rect class="box" x="430" y="142" width="230" height="40" rx="8"/>'
    '<text class="t t-code" x="545" y="167" text-anchor="middle">String</text>'
    '<text class="t-s t-code" x="340" y="212" text-anchor="middle">static boolean check(Logbook, Shift, Job, String)</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """At the print shop, jobs travel between desks in envelopes. A clerk who opens an envelope and sees a paper size written inside knows the job has one. The next clerk down the line doesn't know that, and she would have to open the envelope again. Unless the first clerk stamps the outside: "checked, paper size filled in". Then the next clerk trusts the stamp and gets on with the job.

The Kotlin compiler works the same way. It knows what it saw in the function it is reading, and it never opens a function you call, so your own check function, however careful, teaches it nothing. A contract is the stamp on the outside. The easy trap is the other half of the story: nobody checks a stamp. The compiler believes it, true or not.

In the last lesson we wrote a small language and saw context receivers retire. This time we stamp our own envelopes, watch a false stamp fail at run time, and meet context parameters, the values every clerk on a shift carries without being handed them on each job. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_PLAIN = """// Java's type system doesn't track null at all, so the question never comes up
static void requirePaper(String paper) {
    if (paper == null) throw new IllegalArgumentException("paper size missing");
}

requirePaper(paper);
System.out.println(paper.toUpperCase());      // compiles, as everything does"""
K_PLAIN = """fun requirePaperPlain(paper: String?) {
    if (paper == null) throw IllegalArgumentException("paper size missing")
}

requirePaperPlain(paper)
println(paper.uppercase())
// error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'."""
J_CONTRACT = """// Java can't assign a local inside a lambda at all:
// "local variables referenced from a lambda expression must be final or effectively final"
String[] label = new String[1];
ContractsDemoKt.once(() -> { label[0] = "job-17"; return Unit.INSTANCE; });"""
K_CONTRACT = """@OptIn(ExperimentalContracts::class)
fun requirePaper(paper: String?) {
    contract { returns() implies (paper != null) }
    if (paper == null) throw IllegalArgumentException("paper size missing")
}

@OptIn(ExperimentalContracts::class)
inline fun <T> once(block: () -> T): T {
    contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }
    return block()
}

val label: String
once { label = "job-17" }     // allowed: the block runs exactly once"""

S0 = """Start with a check the print shop's app makes all the time. Some printers report their paper size and some don't, so `lookupPaper("laser-1")` returns a `String?`: a paper size such as `"a4"`, or `null`, Kotlin's word for no value at all. Before printing, the app must be sure there is one. The standard library's `require(paper != null)` does that, and on the next line `paper` can be used as a plain `String`. Write the same check as your own function, and the compiler forgets it:

""" + pair(J_PLAIN, K_PLAIN) + """

The feature that fails here is the **smart cast**: after a check such as `if (paper != null)`, the compiler treats `paper` as the narrower type, `String`, without a cast written by you. It does that only for checks it can see in the function it is reading. It never reads the body of a function you call.

In the print shop, the compiler is a clerk who trusts her own eyes. She saw the check? Then she knows. A colleague did it at another desk? Then, as far as she is concerned, it never happened.

A **contract** is the stamp on the outside of the envelope. It is a `contract { }` block, written as the first statement of a function, that states a fact about the function's behavior for callers to rely on. Two kinds matter in practice. `returns() implies (paper != null)` says: if this function returns normally, the condition holds. `callsInPlace(block, InvocationKind.EXACTLY_ONCE)` says: the lambda runs exactly once, during this call, and is never kept for later. The other counts are `AT_MOST_ONCE`, `AT_LEAST_ONCE` and `UNKNOWN`.

""" + pair(J_CONTRACT, K_CONTRACT) + """

With the contract, `requirePaper(paper)` can be followed by `paper.uppercase()`, and the demo prints `paper = A4`. With `once`, a `val` declared without a value can be assigned inside the lambda, because the compiler now knows the lambda runs exactly once, before the next line. Take the `callsInPlace` line out, and being inline (pasted into the caller, as lesson 1 showed) isn't enough. You get `'val' cannot be reassigned.` and `variable 'label' must be initialized.`, because an inline function may still call its lambda twice, or not at all.

This is how `require`, `check`, `requireNotNull`, `run`, `let` and `apply` work in the standard library. Contracts are still Experimental in Kotlin 2.4, which means the feature may still change and you must agree to use it in writing. The 2.4.0 release notes say so, and without `@OptIn(ExperimentalContracts::class)` every part of the block fails with `this declaration needs opt-in.` No compiler flag is needed, only that annotation.

**The compiler smart-casts only from checks it can see. A contract writes the check on the outside of the function.**

So the clerk trusts the stamp. The next question is whether she should."""

ASIDE0 = {
    "title": "Why doesn't the compiler just read the body of the function?",
    "body": "Because then a change inside one function could break code far away. Today a function's signature, its parameter and return types, is the promise callers rely on, and the body is free to change. If smart casts followed bodies, deleting the `throw` from `requirePaper` would silently change which callers compile, perhaps in a module built months ago. Often the body isn't there to read anyway: a library arrives as compiled class files, and the compiler reads their signatures, not their code. A contract keeps the promise next to the signature, written down on purpose, where a reviewer can see it.",
}

# ---------------------------------------------------------------- section 1
J_LIE = """// Java's version of the same lie: a check that always says yes, and a cast that believes it
static boolean lyingIsPrinted(JobEvent e) { return true; }

if (lyingIsPrinted(jammed)) {
    Printed p = (Printed) jammed;                  // ClassCastException
}"""
K_LIE = """@OptIn(ExperimentalContracts::class)
fun JobEvent.lyingIsPrinted(): Boolean {
    contract { returns(true) implies (this@lyingIsPrinted is Printed) }
    return true                                    // the lie
}

if (jammed.lyingIsPrinted()) println(jammed.pages)   // ClassCastException"""

S1 = """A contract is a promise, and nothing checks the body against it. The design document for contracts, KEEP-139, says the compiler "trusts contracts unconditionally" and that the programmer is "responsible for writing correct and sound contracts". Proving the body right is listed as a non-goal.

The demo's job events say what happened to a print job: `Printed(jobId, pages)` when it came out of the printer, and `Jammed(jobId, printer)` when it got stuck, which `laser-1` does now and then. `isPrinted()` answers whether an event is a `Printed`, and its contract lets the caller read `event.pages` right after a `true`. The lying version answers `true` to everything, like a clerk who stamps every envelope unopened. It's very fast work. It also compiles without a single warning:

""" + pair(J_LIE, K_LIE) + """

The smart cast to `Printed` lets `jammed.pages` compile. At run time the JVM still checks every cast it is given, and a `Jammed` is not a `Printed`: `class ...Jammed cannot be cast to class ...Printed`. A contract can't make a wrong value right. It only moves the cast out of your code, where a reviewer would see it, into a promise inside another function.

One level down, the reason is plain. `javap -c` on the honest `isPrinted` shows a null check on the receiver, then `instanceof Printed` and `ireturn`, with no trace of the contract. The smart cast lands in the caller instead: right after the call, `javap` shows a `checkcast Printed` that nobody wrote by hand. The contract itself lives in the Kotlin metadata of the class file, extra data that only the Kotlin compiler reads when it compiles a caller. Java never sees it, and nothing in the running program enforces it.

The K2 compiler (the current Kotlin compiler, the default since Kotlin 2.0) does catch some `callsInPlace` mistakes, as warnings. A block declared `EXACTLY_ONCE` but called twice gets `wrong invocation kind 'EXACTLY_ONCE' for 'block: () -> Unit' specified, the actual invocation kind is 'AT_LEAST_ONCE'.` A block declared in place but kept in a list gets `leaked in-place lambda 'block: () -> Unit'.` Nothing checks `returns ... implies`. The one firm rule is the position: any statement before the block is an error, `contract should be the first statement.`

**A contract is believed, never checked. Keep the body as simple as the promise.**

So write contracts the way the standard library does: tiny functions whose body is the condition itself, such as `if (!condition) throw ...`, so that a reader can check the promise at a glance. Kotlin 2.2.20 added more Experimental forms, such as contracts on property getters, `returnsNotNull()` and `holdsIn`. The last two need a second opt-in, `ExperimentalExtendedContracts`.

Contracts tell the compiler what a function does. The next feature is about what a function needs, and it changes how arguments get passed."""

# ---------------------------------------------------------------- section 2
J_CTX = """static boolean check(Logbook logbook, Shift shift, Job job, String printer) {
    logbook.write("[" + shift.name() + "] checking " + job.copies() + " copies of " + job.file() + " for " + printer);
    return job.copies() <= 1_000;
}

static String takeIn(Logbook logbook, Shift shift, Job job, String printer) {
    boolean ok = check(logbook, shift, job, printer);     // pass both on, by hand
    remark(logbook, job.file() + (ok ? " accepted" : " refused") + " on the " + shift.name() + " shift");
    return ok ? "ACCEPTED" : "REFUSED";
}"""
K_CTX = """context(logbook: Logbook, shift: Shift)
fun Job.check(printer: String): Boolean {
    logbook.write("[${shift.name}] checking $copies copies of $file for $printer")
    return copies <= 1_000
}

context(logbook: Logbook, shift: Shift)
fun takeIn(job: Job, printer: String): String {
    val ok = job.check(printer)                           // logbook and shift flow on by themselves
    remark("${job.file} ${if (ok) "accepted" else "refused"} on the ${shift.name} shift")
    return if (ok) "ACCEPTED" else "REFUSED"
}"""

S2 = """Some values must reach almost every function that handles a job. In the print shop, every decision goes into the shift's logbook, and every line in it starts with the name of the shift on duty, such as `[early]`. Passed by hand, the logbook and the shift show up in every signature, whether the function uses them or only hands them on:

""" + pair(J_CTX, K_CTX) + """

The Kotlin version declares the two values once per function, in `context(...)` before `fun`, and stops passing them. A **context parameter** is a parameter the caller doesn't write. You declare it with a name and a type, and inside the function you use it by its name, as `check` does with `logbook` and `shift`. At each call, the compiler looks for a value of that type in the caller's surroundings and passes it for you. The value it finds is called the **context argument**.

In the print shop, the context parameters are what every clerk on a shift carries: the shift's logbook and the shift's name. Nobody hands them over with each job. The demo hands them out once, at the start of the shift, with `context(console, Shift("early")) { ... }`, and inside that block every function that needs them has them.

The compiler finds a context argument in one of three places. The first is an enclosing function's own context parameter, as `takeIn` passes its `logbook` and `shift` on to `check`. The second is a `context(a, b) { ... }` block from the standard library. The third is an implicit receiver, such as the `this` of a `with(console) { ... }` block. If you don't need a name, write `_` and read the value with `contextOf<Logbook>()`, as the demo's `remark` does. Forget the context altogether, and the call doesn't compile: `no context argument for 'logbook: Logbook' found.`

The docs describe context parameters as dependencies that are "implicitly available in the surrounding context". On the JVM nothing about them is implicit, as the figure shows. They become ordinary leading parameters: the context parameters first, then the extension receiver, then the value parameters. `javap` prints `check(Logbook, Shift, Job, String)`, and Java calls it by passing all four. That's where the shift picture breaks. On the JVM the clerk is handed the logbook with every single job, and a Java caller hands it over in person, every time.

The status changed fast, so here it is plainly. Context parameters **replaced context receivers**, the experiment from the last lesson. Context receivers arrived in Kotlin 1.6.20 as a prototype behind `-Xcontext-receivers`. Kotlin 2.2.0 brought context parameters as a preview, a feature you can try but which may still change, behind `-Xcontext-parameters`. Kotlin 2.3.20 removed context receivers. Kotlin 2.4.0 made context parameters Stable, "except for context arguments and callable references", two parts the next section covers. So in Kotlin 2.4 you need no flag, and an old build file that still passes one earns `warning: the argument '-Xcontext-parameters' is redundant for the current language version 2.4.`

The two designs differ in one way that matters when you read older code. A context receiver had no name and acted like an extra `this`, so you called its members bare, as in `write("hi")`. A context parameter has a name, and you write `logbook.write("hi")`.

**A context parameter is an argument the compiler finds by type and passes for you. On the JVM, it is a plain leading parameter.**

Finding a value by type works well while there is exactly one candidate. The next section is about the other cases."""

# ---------------------------------------------------------------- section 3
S3 = """The compiler finds context arguments by type, so two values of the same type in the same place are a problem. Take a smaller `note` that needs only a logbook, `context(logbook: Logbook) fun note(line: String)`. Put the front desk's logbook and the back room's logbook in one block, `context(front, back) { note("x") }`, and the compiler won't pick one: `multiple potential context arguments for 'logbook: Logbook' in scope.` The docs give the rule: if several compatible values exist at the same scope level, the compiler reports an ambiguity. A nearer scope still wins over an outer one. In `context(front) { context(back) { note("x") } }`, the inner `back` is used, and the line goes to the back room.

That's a reason to give context parameters specific types: a `Shift` class instead of a bare `String`, a `Logbook` interface instead of a `(String) -> Unit` function type. A bare `String` in a context would match any string in scope.

A few things are not allowed. Constructors can't have context parameters: `context parameters on primary constructors are unsupported.` A property can have them only if it has no backing field, the hidden field that stores a property's value, so it must be a computed getter: `property with context parameters cannot be initialized because it has no backing field.` And two parts are still not stable in Kotlin 2.4. One is passing a context argument by name, as in `note(logbook = front, line = "x")`, an Experimental feature behind `-Xexplicit-context-arguments`. Without the flag, 2.4.21 says it "is only available since language version 2.5". The other is a callable reference, `::note`, which fails with `callable reference to 'context(logbook: Logbook) fun note(line: String): Unit' is unsupported because it has context parameters.` Leave both alone for now.

One change in Kotlin 2.3.20 can surprise you if you bring older preview code forward. Overload resolution, the compiler's choice between functions with the same name, used to prefer a function with context parameters over one without. The 2.3.20 notes say that rule no longer applies, so two overloads that differ only by a context may now be ambiguous.

The JVM shape has two more consequences. Java can call these functions, as long as it passes every argument itself. And adding a context parameter to a public function changes its JVM signature exactly as adding any parameter does, so code compiled against the old version fails with `NoSuchMethodError`. Treat it as a change to the function's public API.

So where do context parameters fit? Not for the long-lived helpers an object is built with: a paper catalogue or a printer driver belongs in the constructor, passed once. Context parameters suit values that belong to the current piece of work and are needed by many small functions: the shift, its logbook, the id of the job in hand, a clock that tests can stop. They are visible in every signature, and the compiler checks them, which a hidden global value never does.

That's also the limit of both tools in this lesson. A contract is believed without checks, and a context argument is found by its type, never by its meaning. Keeping either honest is your job.

A check to finish, with the lab's `review`, which needs a `Logbook` and a `Shift`: `with(Logbook { println(it) }) { context(Shift("late")) { JobRequest(40, "a3", "poster.pdf").review(1_000) } }`. Will it compile, and where does each context argument come from? (It compiles. The `Logbook` comes from the implicit receiver of `with`, and the `Shift` from the `context(...)` block. Each type has exactly one candidate.)"""

# ---------------------------------------------------------------- closing
CLOSING = """We started with envelopes moving between desks. A contract is the stamp on the outside, `returns() implies` or `callsInPlace`, and the compiler believes it without opening the envelope, so a false stamp turns into a `ClassCastException` later. Context parameters are what every clerk carries for the whole shift: passed by the compiler, and on the JVM as plain leading parameters.

In your own code, look for a check function followed by `!!` on the next line. Each one is a missing contract, or a hint that the check should return the value instead.

Next, we'll let the compiler change our classes as they pass through it. What do compiler plugins write into a class file that your source never mentions?"""

L = {
 "id": "kt-05",
 "title": "Contracts and context parameters",
 "minutes": 35,
 "goal": "By the end you can write a contract that gives callers smart casts and in-place lambdas, explain why the compiler trusts it blindly, declare and call functions with context parameters in Kotlin 2.4, and predict their JVM signature.",
 "opening": OPENING,
 "warmup": {
  "q": "`fun requirePaper(paper: String?) { if (paper == null) throw IllegalArgumentException() }`. After `requirePaper(paper)`, where `paper` is a `String?`, you write `paper.uppercase()`. What happens?",
  "options": ["It compiles: the compiler sees the throw inside `requirePaper`", "Compile error: `paper` is still a `String?` to the compiler", "It compiles with a warning", "It compiles, and throws `NullPointerException` if `paper` is null"],
  "answer": 1,
  "why": "The compiler decides smart casts one function at a time. It doesn't look inside `requirePaper` to learn that a normal return means `paper != null`, so `paper` stays nullable and you get `only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.` The standard library's `require` gets the smart cast because it declares a contract, the subject of the first section."
 },
 "sections": [
  {
   "h": "Your own check functions teach the compiler nothing, until they carry a contract",
   "body": S0,
   "aside": ASIDE0,
   "try": {
    "title": "Take each contract away",
    "minutes": 4,
    "steps": [
     "Run `ContractsDemo` (or `ContractsDemoJava`, which calls the same Kotlin functions).",
     "Wrong move 1: call `requirePaperPlain(paper)` instead of `requirePaper(paper)`. Predict the error, run, undo.",
     "Wrong move 2: delete the `contract { callsInPlace(...) }` line in `once`. `once` is still inline. Predict whether that is enough, run, undo.",
     "Wrong move 3: delete the `@OptIn` above `isPrinted`, run, undo."
    ],
    "code": demo("ContractsDemo"),
    "expect": "The demo prints `paper = A4`, `printed 12 pages` and `label = job-17`. Move 1 fails on `paper.uppercase()` with the nullable-receiver error. Move 2 fails with `'val' cannot be reassigned.` and `variable 'label' must be initialized.`: being inline doesn't tell the compiler how many times the body calls `block`. Move 3 fails with `this declaration needs opt-in. Its usage must be marked with '@kotlin.contracts.ExperimentalContracts' or '@OptIn(kotlin.contracts.ExperimentalContracts::class)'`."
   },
   "refs": [{"title": "KEEP-0139: Kotlin contracts", "url": "https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0139-kotlin-contracts.md", "kind": "read"}]
  },
  {
   "h": "The compiler trusts a contract and never checks it",
   "body": S1,
   "try": {
    "title": "Make a contract lie",
    "minutes": 3,
    "steps": [
     "Run `LyingContractDemo`. Before you do, predict: compile error, a warning, or a run-time failure?",
     "Run `LyingContractDemoJava`, which tells the same lie in Java with a cast, then calls the Kotlin function.",
     "Run `javap -c -p -cp kotlin/build/classes/kotlin/demo workbench.kotlin.l05.demo.ContractsDemoKt` from `labs/`. Read `isPrinted`, then find the `checkcast` in `main` right after the call to it."
    ],
    "code": demo("LyingContractDemo"),
    "expect": "It compiles cleanly and fails at run time with `ClassCastException: class workbench.kotlin.l05.demo.Jammed cannot be cast to class workbench.kotlin.l05.demo.Printed`. The Java twin fails the same way, then prints `Kotlin lyingIsPrinted from Java: true`: to Java it's a boolean method. In `javap`, `isPrinted` is a null check on the receiver, then `instanceof` and `ireturn`, with no contract in sight. In `main`, the call to `isPrinted` is followed by `checkcast Printed` and `getPages`: that cast is the smart cast."
   }
  },
  {
   "h": "Context parameters: what every clerk carries for the whole shift",
   "body": S2,
   "figure": {"svg": FIG, "caption": "On the JVM, context parameters are plain leading parameters, followed by the extension receiver and then the ordinary parameters."},
   "try": {
    "title": "Follow a context through two calls",
    "minutes": 4,
    "steps": [
     "Run `ContextParamsDemo`. Predict the seven lines it prints for the two jobs and the last remark.",
     "Run `ContextParamsDemoJava`, which calls the same functions from Java with every argument spelled out.",
     "Run `javap -p -cp kotlin/build/classes/kotlin/demo workbench.kotlin.l05.demo.ContextParamsDemoKt` and match each parameter to the figure.",
     "Uncomment the wrong move at the end of `main` (a call outside any context). Predict the error, then run."
    ],
    "code": demo("ContextParamsDemo"),
    "expect": "Each job prints `[early] checking ...`, then a `NOTE` line saying it was accepted or refused (5,000 copies is over the limit of 1,000), then `ACCEPTED` or `REFUSED`, and the last line is `NOTE an implicit receiver works too`. `javap` lists `check(Logbook, Shift, Job, String)`, `takeIn(Logbook, Shift, Job, String)` and `remark(Logbook, String)`. The wrong move fails twice: `no context argument for 'logbook: Logbook' found.` and the same for `shift: Shift`."
   },
   "refs": [{"title": "Context parameters (Kotlin docs)", "url": "https://kotlinlang.org/docs/context-parameters.html", "kind": "docs"},
            {"title": "What's new in Kotlin 2.4.0", "url": "https://kotlinlang.org/docs/whatsnew24.html", "kind": "docs"}]
  },
  {
   "h": "Finding values by type: ambiguity, limits, and where context parameters fit",
   "body": S3
  }
 ],
 "compare": {
  "title": "A job review with a logbook: Java parameters vs Kotlin contracts and context parameters",
  "java": {"title": "Review.java", "src": "final class Review {\n    static void ensure(boolean condition, String code, Supplier<String> message) {\n        if (!condition) throw new JobRejected(code, message.get());\n    }\n\n    static Decision review(Logbook logbook, Shift shift, JobRequest job, int maxCopies) {\n        try {\n            ensure(job.copies() <= maxCopies, \"TOO_MANY\", () -> \"over the limit\");\n            ensure(job.paper() != null, \"PAPER_MISSING\", () -> \"a paper size is required\");\n            logbook.write(\"[\" + shift.name() + \"] accepted \" + job.paper().toUpperCase());\n            return Decision.ACCEPTED;\n        } catch (JobRejected e) {\n            logbook.write(\"[\" + shift.name() + \"] rejected \" + e.code());\n            return Decision.rejected(e.code());\n        }\n    }\n}"},
  "kotlin": {"title": "Review.kt", "src": "@OptIn(ExperimentalContracts::class)\ninline fun ensure(condition: Boolean, code: String, lazyMessage: () -> String) {\n    contract {\n        returns() implies condition\n        callsInPlace(lazyMessage, InvocationKind.AT_MOST_ONCE)\n    }\n    if (!condition) throw JobRejected(code, lazyMessage())\n}\n\ncontext(logbook: Logbook, shift: Shift)\nfun JobRequest.review(maxCopies: Int): Decision =\n    try {\n        ensure(copies <= maxCopies, \"TOO_MANY\") { \"over the limit\" }\n        ensure(paper != null, \"PAPER_MISSING\") { \"a paper size is required\" }\n        logbook.write(\"[${shift.name}] accepted ${paper.uppercase()}\")   // smart cast\n        Decision.Accepted\n    } catch (e: JobRejected) {\n        logbook.write(\"[${shift.name}] rejected ${e.code}\")\n        Decision.Rejected(e.code)\n    }"},
  "note": "The Java version compiles because Java doesn't track null, so `job.paper().toUpperCase()` is accepted whether or not the check ran. The Kotlin version compiles only because the contract tells the compiler that `ensure` returns only when its condition holds. Kotlin's `ensure` is inline, so the message lambda costs nothing when the check passes, while Java builds a `Supplier` on every call. The logbook and the shift appear in Java's signature as two extra parameters that every caller passes on. In Kotlin they are context parameters, filled in by the compiler, and they still compile to exactly those two leading parameters, so Java can call the Kotlin `review` as `review(logbook, shift, job, maxCopies)`."
 },
 "worked": {
  "title": "Replace a ThreadLocal shift name with a context parameter",
  "steps": [
   {"say": "The app keeps the current shift's name in a `ThreadLocal`, a variable that holds one value per thread, so that deep helpers can write it into the logbook. It works until a helper runs on another thread, or a test forgets to set it, and then the logbook says `[null]`. The compiler can't help, because nothing in any signature says the value is needed.",
    "code": "final class CurrentShift {\n    static final ThreadLocal<String> NAME = new ThreadLocal<>();\n}\n\nstatic void note(String line) {\n    System.out.println(\"[\" + CurrentShift.NAME.get() + \"] \" + line);   // null if nobody set it\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "object CurrentShift {\n    val name = ThreadLocal<String>()\n}\n\nfun note(line: String) {\n    println(\"[${CurrentShift.name.get()}] $line\")                     // null if nobody set it\n}"},
   {"say": "Make the need part of the signature. The helper declares a context parameter, and so does every function that calls it, up to the place that knows the shift.",
    "code": "class Shift(val name: String)\n\n// 1. the helper declares what it needs\ncontext(shift: Shift)\nfun note(line: String) = println(\"[${shift.name}] $line\")\n\n// 2. callers in between declare it too, and never pass it by hand\ncontext(shift: Shift)\nfun printJob(jobId: String) {\n    note(\"printing $jobId\")\n}", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// Java's honest equivalent: an explicit parameter on every function in the chain\nrecord Shift(String name) {}\n\nstatic void note(Shift shift, String line) { System.out.println(\"[\" + shift.name() + \"] \" + line); }\n\nstatic void printJob(Shift shift, String jobId) { note(shift, \"printing \" + jobId); }"},
   {"say": "Open the context once, where the job comes in: the function that takes jobs at the counter. Forgetting it is now a compile error, `no context argument for 'shift: Shift' found.`, instead of a `[null]` in the logbook.",
    "code": "// 3. open the context where the shift is known\nfun onJobArrived(jobId: String, shiftName: String) {\n    context(Shift(shiftName)) {\n        printJob(jobId)\n    }\n}\n\n// printJob(\"job-7\")   // error: no context argument for 'shift: Shift' found.", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "void onJobArrived(String jobId, String shiftName) {\n    printJob(new Shift(shiftName), jobId);\n}"},
   {"say": "Check the price: each function in the chain gets one more JVM parameter, and nothing else. There is no `ThreadLocal` to look up, and the value follows the call instead of the thread, so it survives a move to another thread or into a coroutine (a task that can pause and resume, from the coroutines track).", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A contract-backed ensure and a context-aware review",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/Ensure.kt", f"{lab}/main/{P}/Review.kt", f"{lab}/main/{P}/Callers.kt"],
  "run": "./gradlew :kotlin:test --tests 'workbench.kotlin.l05.*'",
  "steps": [
   "A `JobRequest` is a job as it arrives at the counter: the copies, the paper size and the file name, and the last two may be missing. Run the tests. All seven fail. `Callers.kt` exists for the same reason as in lesson 1: `ensure` is inline.",
   "Write the body of `ensure` (TODO 1): throw `JobRejected(code, lazyMessage())` when the condition is false. Leave the contract for later.",
   "Write `note` (TODO 3) with the two context parameters, used by name.",
   "Write `review` (TODO 4). Use `paper.uppercase()` with no `!!` and build: it fails on the nullable receiver.",
   "Add the contract to `ensure` (TODO 2), with `@OptIn(ExperimentalContracts::class)` and the imports. Build again: `review` compiles now.",
   "Run until all seven pass, including `ReviewFromJavaTest`, which calls `review(logbook, shift, request, 1_000)` from Java."
  ],
  "hints": [
   "`contract { returns() implies condition; callsInPlace(lazyMessage, InvocationKind.AT_MOST_ONCE) }` must be the first statement in `ensure`.",
   "Inside `review`, `copies`, `paper` and `file` are properties of the receiver, so the smart cast works on `paper` directly.",
   "Wrap the four `ensure` calls and the success `note` in `try`, and catch `JobRejected` to build `Decision.Rejected(e.code)`. `try` is an expression, so the function can be `= try { ... } catch (...) { ... }`.",
   "`note(...)` needs no arguments for the context: inside `review`, the `logbook` and `shift` context parameters are in scope, and the compiler passes them on."
  ],
  "done_when": "All seven tests in `ReviewTest` and `ReviewFromJavaTest` pass."
 },
 "drill": {
  "title": "Write ensureNotNull with a contract, from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `ensureNotNull(value, code, lazyMessage)` that returns the value as non-null, throws `JobRejected` when it's null, and gives callers a smart cast on the variable they passed. Include the opt-in. Then write the Java version. What does the Kotlin compiler check about your contract?",
  "answer": {"lang": "kotlin", "src": "@OptIn(ExperimentalContracts::class)\ninline fun <T : Any> ensureNotNull(value: T?, code: String, lazyMessage: () -> String): T {\n    contract {\n        returns() implies (value != null)                       // callers get a smart cast\n        callsInPlace(lazyMessage, InvocationKind.AT_MOST_ONCE)\n    }\n    if (value == null) throw JobRejected(code, lazyMessage())\n    return value\n}\n\n// it checks that contract { } comes first and warns on some callsInPlace mistakes;\n// it never checks that the body keeps the returns-implies promise",
             "alt": {"lang": "java", "title": "Ensure.java", "src": "static <T> T ensureNotNull(T value, String code, Supplier<String> message) {\n    if (value == null) throw new JobRejected(code, message.get());\n    return value;            // Java has no smart casts, so callers use the return value\n}"}}
 },
 "recap": [
  "The compiler never reads the body of a function you call, so your own check functions give no smart casts until they declare a contract.",
  "`returns() implies cond` gives callers a smart cast after a normal return. `callsInPlace(block, EXACTLY_ONCE)` lets them assign a `val` inside the lambda.",
  "Contracts are Experimental in Kotlin 2.4 and need `@OptIn(ExperimentalContracts::class)`. The compiler trusts them without checking; a false one becomes a `ClassCastException` at run time.",
  "Context parameters, `context(shift: Shift) fun ...`, replaced context receivers: a preview in Kotlin 2.2.0, Stable since 2.4.0. The compiler fills them by type from enclosing context parameters, `context(...) { }` blocks and implicit receivers.",
  "On the JVM they are leading parameters (context, then receiver, then the rest), so Java passes them by hand, and adding one breaks callers that were already compiled.",
  "The limit: a contract is believed, never checked, and a context argument is found by type, never by meaning. Explicit context arguments and callable references are not stable yet."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "What happens with this code?\n\n```kotlin\n@OptIn(ExperimentalContracts::class)\nfun JobEvent.isPrinted(): Boolean {\n    contract { returns(true) implies (this@isPrinted is Printed) }\n    return this is Printed || this is Reprinted\n}\n\nif (event.isPrinted()) println(event.pages)\n```",
   "options": ["A compile error: the body doesn't match the contract", "A compiler warning about an unsound contract", "It compiles; for a `Reprinted` event the smart cast fails at run time with `ClassCastException`", "It compiles, and the smart cast is skipped when the contract is wrong"],
   "answer": 2, "why": "The compiler trusts `returns ... implies` without checking it, so `event.pages` compiles as if `event` were a `Printed`. At run time the JVM checks the cast it was given, and a `Reprinted` is not a `Printed`. K2 warns only about some `callsInPlace` mistakes, never about `implies`."},
  {"q": "Which contract makes this compile?\n\n```kotlin\nval total: Int\nwithTrayLock { total = tray.count() }\nprintln(total)\n```",
   "options": ["`callsInPlace(block, InvocationKind.EXACTLY_ONCE)` in `withTrayLock`", "`callsInPlace(block, InvocationKind.AT_MOST_ONCE)`", "No contract: making `withTrayLock` inline is enough", "`returns() implies (block != null)`"],
   "answer": 0, "why": "A `val` must be assigned exactly once, and only `EXACTLY_ONCE` tells the compiler the assignment happens once, during the call. `AT_MOST_ONCE` allows zero runs, so `total` might stay unassigned. Inline alone says nothing about how many times the body calls `block`: without the contract you get `'val' cannot be reassigned.`"},
  {"q": "How does Java call `context(logbook: Logbook) fun note(line: String)`?",
   "options": ["`note(line)`, and the logbook comes from a ThreadLocal", "`note(logbook, line)`: the context parameter is the first JVM parameter", "`note(line, logbook)`", "It can't: context parameters are Kotlin-only"],
   "answer": 1, "why": "On the JVM, context parameters become ordinary parameters placed first, then the extension receiver, then the value parameters. Java has no context, so it passes the value itself."},
  {"q": "Inside `context(front, back) { note(\"x\") }`, both values are `Logbook`s. What does the compiler do?",
   "options": ["Uses `front`, the first one listed", "Uses `back`, the last one listed", "Passes both and lets `note` choose", "Reports `multiple potential context arguments for 'logbook: Logbook' in scope.`"],
   "answer": 3, "why": "Context arguments are found by type. Two compatible values at the same scope level are an ambiguity, and the compiler refuses to guess. Give the two roles different types, or open the contexts in nested blocks so that one is nearer."},
  {"q": "From lesson 1: a test class was compiled against the stub of the public inline function `ensure`. You fix `ensure` and recompile only `src/main`. What does the old test class run when it calls `ensure`?",
   "options": ["Your new body, because it's on the classpath", "The stub's body, copied into the test class when the test was compiled", "Nothing: it fails with `NoSuchMethodError`", "Whichever version the class loader finds first"],
   "answer": 1, "why": "An inline body is pasted into the caller at the caller's compile time, so the old test class holds its own copy of the stub. That's why the lab's tests call `Callers.ensuring`, an ordinary function compiled together with your code.",
   "from": "kt-01"}
 ],
 "flashcards": [
  {"front": "What is a Kotlin contract?", "back": "A `contract { }` block, the first statement of a function, that tells the compiler something it can't infer: how a lambda is called, or what a normal return implies."},
  {"front": "What does `returns() implies (x != null)` give the caller?", "back": "A smart cast: after the call returns normally, the compiler treats `x` as non-null."},
  {"front": "What does `callsInPlace(block, EXACTLY_ONCE)` allow in the caller?", "back": "Assigning a `val` inside the lambda, because the compiler now knows the block runs exactly once during the call."},
  {"front": "Does the compiler check a contract against the function body?", "back": "No. It trusts it. A false `returns(true) implies (this is Printed)` compiles and fails at run time with `ClassCastException`."},
  {"front": "What opt-in do contracts need in Kotlin 2.4?", "back": "`@OptIn(ExperimentalContracts::class)`. They are still Experimental. No compiler flag is needed."},
  {"front": "Where can a context argument come from?", "back": "From the caller's surroundings, matched by type: an enclosing function's context parameter, a `context(a, b) { }` block, or an implicit receiver such as `with(x) { }`."},
  {"front": "JVM signature of `context(logbook: Logbook, shift: Shift) fun Job.check(printer: String): Boolean`?", "back": "`static boolean check(Logbook, Shift, Job, String)`: context parameters, then the receiver, then the value parameters."}
 ],
 "terms": [
  {"term": "Smart cast", "plain": "The compiler treating a variable as a narrower type after a check proves it, such as `String?` to `String` after `!= null`."},
  {"term": "Contract", "plain": "A `contract { }` block that states a fact about a function's behavior for callers to rely on. The compiler trusts it."},
  {"term": "callsInPlace", "plain": "A contract effect: the lambda runs during the call (it is not kept for later), a given number of times."},
  {"term": "returns implies", "plain": "A contract effect: if the function returns (or returns a given value), a condition holds."},
  {"term": "Context parameter", "plain": "A parameter declared in `context(...)` that callers don't write; the compiler fills it by type from the surroundings."},
  {"term": "Context argument", "plain": "The value the compiler finds and passes for a context parameter at a call site."},
  {"term": "Opt-in", "plain": "`@OptIn(...)`: your written agreement to use an Experimental API that may still change."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why `ensure(paper != null, \"PAPER_MISSING\") { ... }` followed by `paper.uppercase()` compiles only with a contract, and what the compiler does and doesn't check about that contract.",
  "answer": "The compiler decides smart casts inside one function at a time. It doesn't read the body of `ensure` when it compiles the caller, so without help it has no idea that `ensure` only returns when the condition is true, and `paper` stays a `String?`. The contract `returns() implies condition`, written as the first statement of `ensure`, is a promise stored in the Kotlin metadata: if this function returns normally, the condition holds. When the caller is compiled, the compiler reads that promise and treats `paper` as non-null after the call. It doesn't check the promise. If the body of `ensure` returned without checking, the code would still compile and fail later at run time. The compiler checks only the form: the opt-in is there, the block is the first statement, and for `callsInPlace` it warns about some obvious misuse such as calling the lambda twice or keeping it. So the body should be as simple as the promise, here a single `if (!condition) throw`."
 },
 "deeper": {
  "minutes": 8,
  "body": "Kotlin 2.4.0 added one more Experimental contract effect, `returnsResultOf()`, to help the new checker for unused return values. It needs the flag `-Xallow-returns-result-of`, and the release notes warn that using it \"produces pre-release binaries that earlier Kotlin compiler versions can't read\". Keep it out of libraries that other people use.\n\nThe extended contracts from Kotlin 2.2.20 behave in an interesting way on the 2.4.21 compiler. Their old flags (`-Xallow-contracts-on-more-functions` and friends) now print `the argument '...' is redundant for the current language version 2.4.`, and a generic `returns(true) implies (this is Ok<T>)` or a `holdsIn` contract compiles without any flag. So they appear to be switched on by default from language version 2.3. They still need their opt-ins, though: `returnsNotNull()` without `@OptIn(ExperimentalExtendedContracts::class)` is an opt-in error.\n\nIf you're moving code from context receivers, three differences bite. Context parameters must be named (or `_`), and a context parameter is not a receiver in the body, so `write(\"x\")` becomes `logbook.write(\"x\")`. `this@Logbook` is gone; use the name or `contextOf<Logbook>()`. And classes can't declare a context any more, only functions and properties.\n\nFinally, a design note. The docs list \"simplified dependency injection\" as one use, dependency injection being a framework that builds your objects and hands each one the helpers it needs. Treat that with care. A context parameter is resolved when the code is compiled, at each call site, from what is in scope there. A dependency injection framework wires objects when the program starts, from the whole application. They answer different questions: context parameters suit values that belong to one piece of work, and constructors suit helpers that live as long as the object."
 },
 "sources": [
  {"title": "Context parameters (Kotlin docs)", "url": "https://kotlinlang.org/docs/context-parameters.html"},
  {"title": "What's new in Kotlin 2.4.0", "url": "https://kotlinlang.org/docs/whatsnew24.html"},
  {"title": "KEEP-0139: Kotlin contracts", "url": "https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0139-kotlin-contracts.md"},
  {"title": "KEEP-0367: context parameters", "url": "https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0367-context-parameters.md"},
  {"title": "What's new in Kotlin 2.3.20", "url": "https://kotlinlang.org/docs/whatsnew2320.html"}
 ]
}
out = ROOT / "content/lessons/kt-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
