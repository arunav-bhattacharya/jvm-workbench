import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/kotlin/src"
P = "kotlin/workbench/kotlin/l01"
DK = "kotlin/workbench/kotlin/l01/demo"
DJ = "java/workbench/kotlin/l01/demo"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :kotlin:demo -Pmain=workbench.kotlin.l01.demo."


def demo(name, title_kt=None):
    """Kotlin demo with its runnable Java twin."""
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{DK}/{name}.kt"),
            "run": RUN + name + "Kt", "file": f"{lab}/demo/{DK}/{name}.kt",
            "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(f"{lab}/demo/{DJ}/{name}Java.java"),
                    "run": RUN + name + "Java", "file": f"{lab}/demo/{DJ}/{name}Java.java"}}


FIG = (
    '<svg viewBox="0 0 680 320" role="img" aria-label="Without inline the caller allocates a Function0 and calls through it; '
    'with inline the function body and the lambda body are pasted into the caller, and the finally block appears twice">'
    '<text class="t t-a" x="170" y="28" text-anchor="middle">fun (not inline)</text>'
    '<text class="t t-a" x="520" y="28" text-anchor="middle">inline fun</text>'
    '<rect class="box" x="40" y="44" width="260" height="40" rx="8"/>'
    '<text class="t t-code" x="170" y="69" text-anchor="middle">feeNotInline(amount)</text>'
    '<line class="ln" x1="100" y1="84" x2="100" y2="124" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="205" y="108" text-anchor="middle">new Function0 (indy)</text>'
    '<rect class="box" x="40" y="128" width="260" height="40" rx="8"/>'
    '<text class="t t-code" x="170" y="153" text-anchor="middle">timedNotInline(label, f)</text>'
    '<line class="ln" x1="100" y1="168" x2="100" y2="208" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="205" y="192" text-anchor="middle">f.invoke()</text>'
    '<rect class="box-b" x="40" y="212" width="260" height="40" rx="8"/>'
    '<text class="t t-code" x="170" y="237" text-anchor="middle">amount * 3 / 100</text>'
    '<text class="t-s t-bad" x="170" y="278" text-anchor="middle">result comes back boxed: checkcast, longValue</text>'
    '<text class="t-s t-m" x="170" y="302" text-anchor="middle">one extra object and one call per use</text>'
    '<rect class="box-dim" x="380" y="44" width="280" height="226" rx="8"/>'
    '<text class="t t-code" x="520" y="69" text-anchor="middle">feeInline(amount)</text>'
    '<rect class="box" x="400" y="82" width="240" height="36" rx="8"/>'
    '<text class="t-s t-code" x="520" y="105" text-anchor="middle">start = nanoTime()</text>'
    '<rect class="box-b" x="400" y="126" width="240" height="36" rx="8"/>'
    '<text class="t-s t-code" x="520" y="149" text-anchor="middle">amount * 3 / 100</text>'
    '<rect class="box" x="400" y="170" width="240" height="36" rx="8"/>'
    '<text class="t-s t-code" x="520" y="193" text-anchor="middle">println(...)  normal path</text>'
    '<rect class="box" x="400" y="214" width="240" height="36" rx="8"/>'
    '<text class="t-s t-code" x="520" y="237" text-anchor="middle">println(...)  exception path</text>'
    '<text class="t-s t-ok" x="520" y="290" text-anchor="middle">no Function0, no call, no boxing</text>'
    '<text class="t-s t-bad" x="520" y="310" text-anchor="middle">but the finally block is copied twice</text>'
    '</svg>'
)

L = {
 "id": "kt-01",
 "title": "Inline functions: noinline, crossinline and non-local returns",
 "minutes": 35,
 "goal": "By the end you can say what `inline` does to the bytecode, use a non-local return on purpose, add `noinline` or `crossinline` when the compiler asks and know why it asks, and decide when a function should not be inline at all.",
 "warmup": {
  "q": "What does `firstDeclined(listOf(\"APPROVED p1\", \"DECLINED p2\", \"APPROVED p3\"))` return?\n\n```kotlin\nfun firstDeclined(results: List<String>): String? {\n    results.forEach { if (it.startsWith(\"DECLINED\")) return it }\n    return null\n}\n```",
  "options": ["`null`, because `return` only leaves the lambda and `forEach` carries on", "`\"DECLINED p2\"`, because `return` leaves `firstDeclined`", "It doesn't compile: `return` is not allowed inside a lambda", "It throws, because `forEach` can't be stopped early"],
  "answer": 1,
  "why": "`forEach` is an inline function, so its lambda is pasted into `firstDeclined`, and a bare `return` there returns from `firstDeclined` itself. That's a non-local return. In Java, `return` inside a `forEach` lambda would only leave the lambda, which is why the first option is tempting. Inside a lambda passed to an ordinary function, the third option would be right."
 },
 "sections": [
  {
   "h": "inline pastes the function and its lambda into the caller",
   "body": "Start with a helper that every service has: run a block of code and log how long it took.\n\n```java\nstatic <T> T timed(String label, Supplier<T> block) {\n    long start = System.nanoTime();\n    try {\n        return block.get();\n    } finally {\n        System.out.println(label + \" took \" + (System.nanoTime() - start) / 1_000 + \" us\");\n    }\n}\n\nlong fee = timed(\"fee\", () -> amountMinor * 3 / 100);\n```\n\n```kotlin\nfun <T> timedNotInline(label: String, block: () -> T): T {\n    val start = System.nanoTime()\n    try {\n        return block()\n    } finally {\n        println(\"$label took ${(System.nanoTime() - start) / 1_000} us\")\n    }\n}\n\nval fee = timedNotInline(\"fee\") { amountMinor * 3 / 100 }\n```\n\nCount what one call costs. The lambda `{ amountMinor * 3 / 100 }` uses a local variable from outside its braces, so it is a **closure**: the JVM builds a small object that holds a copy of `amountMinor`, and `timedNotInline` calls that object's `invoke` method. Kotlin creates the object with `invokedynamic`, the same instruction Java uses for its lambdas (the lesson \"invokedynamic: how lambdas and string concatenation compile\" goes into it). And because the helper is generic, the `Long` result travels back as an `Object` and has to be unboxed. That's one object, one call through an interface and one unboxing, on every call. The Kotlin docs name exactly these costs: function objects, captured closures and virtual calls.\n\nYou could avoid all of it by hand, by pasting the helper's body into the caller:\n\n```java\nlong start = System.nanoTime();\nlong fee;\ntry {\n    fee = amountMinor * 3 / 100;          // the lambda's body, pasted in\n} finally {\n    System.out.println(\"fee took \" + (System.nanoTime() - start) / 1_000 + \" us\");\n}\n```\n\n```kotlin\nval start = System.nanoTime()\nval fee = try {\n    amountMinor * 3 / 100                 // the lambda's body, pasted in\n} finally {\n    println(\"fee took ${(System.nanoTime() - start) / 1_000} us\")\n}\n```\n\nNobody writes that fifty times. **`inline` asks the compiler to do the pasting for you.** Write `inline fun <T> timed(...)` with the same body, and at every call site (every place in the code that calls it) the compiler copies the function's body, and the body of the lambda you passed, instead of making a call.\n\n`javap`, the JDK tool that prints a class file's bytecode, shows the difference in the demo below. The ordinary call site is seven instructions long: `invokedynamic` builds a `Function0`, `invokestatic` calls `timedNotInline` with it, and `checkcast java/lang/Number` plus `longValue` unbox the result. The inline call site has none of that. The multiply (`lmul`, `ldiv`) sits right inside `feeInline`, between two calls to `System.nanoTime`, just like the hand-pasted version.\n\nRead a bit further and you see the price. The `finally` block appears twice in `feeInline`, once for the normal exit and once for the exit by exception. That's real code growth, repeated in every caller, and the docs say it pays off only if you avoid inlining large functions. So **inline is for small functions that take lambdas**. The standard library is full of them: `forEach`, `map`, `filter`, `let`, `apply`, `use`, `repeat`, `synchronized`, `require`. Because they are inline, `payments.map { it.amountMinor }` costs about what a hand-written loop costs. The generics track used `inline` for one more reason: a `reified` type parameter exists only because the body is copied to a call site where the type is known.\n\nJava gets none of this. `javac` can't inline Kotlin code, so for Java `InlineDemoKt.timed(...)` is an ordinary static method that takes a `Function0`, and the Java lambda becomes an object like any other.",
   "figure": {"svg": FIG, "caption": "The same helper with and without inline. The inline caller has no lambda object and no call, but it carries its own copy of the whole body."},
   "try": {
    "title": "Read the bytecode of an inline call",
    "minutes": 4,
    "steps": [
     "Run `InlineDemo` (or `InlineDemoJava`) with the command below. Both print `fee = 360`.",
     "From `labs/`, run `javap -c -p kotlin/build/classes/kotlin/demo/workbench/kotlin/l01/demo/InlineDemoKt.class`.",
     "Find `feeNotInline` and `feeInline`. Before you look, predict which one contains `invokedynamic` and which one contains `lmul`. Then count the `println` calls inside `feeInline`."
    ],
    "code": demo("InlineDemo"),
    "expect": "`feeNotInline` is short: `invokedynamic` (a new `Function0`), `invokestatic timedNotInline`, then `checkcast java/lang/Number` and `longValue` to unbox the result. `feeInline` holds the arithmetic (`lmul`, `ldiv`) and two `PrintStream.println` calls, because the `finally` block was copied for both exits. Ignore the microsecond timings: one cold call measures class loading and lambda setup, not inlining. The bytecode is the evidence."
   },
   "refs": [{"title": "Inline functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-functions.html", "kind": "docs"}]
  },
  {
   "h": "A bare return in an inlined lambda leaves the caller",
   "body": "Inside an ordinary lambda, a bare `return` doesn't compile. The error is `'return' is prohibited here.` A lambda is an object with its own method, and that method can't make some other function return. An inlined lambda is different. Its body becomes part of the caller, so `return` can mean exactly what it says.\n\n```java\nstatic String firstDeclined(List<String> results) {\n    for (String r : results) {\n        if (r.startsWith(\"DECLINED\")) return r;     // Java needs a real loop to return early\n    }\n    return null;\n}\n\nstatic int countApproved(List<String> results) {\n    int approved = 0;\n    for (String r : results) {\n        if (!r.startsWith(\"APPROVED\")) continue;\n        approved++;\n    }\n    return approved;\n}\n```\n\n```kotlin\nfun firstDeclined(results: List<String>): String? {\n    results.forEach { if (it.startsWith(\"DECLINED\")) return it }   // leaves firstDeclined\n    return null\n}\n\nfun countApproved(results: List<String>): Int {\n    var approved = 0\n    results.forEach {\n        if (!it.startsWith(\"APPROVED\")) return@forEach              // leaves this lambda call only\n        approved++\n    }\n    return approved\n}\n```\n\nThe first `return` is a **non-local return**: it leaves the function that contains the lambda. It compiles only because `forEach` is inline. In the bytecode, `firstDeclined` is an `Iterator` loop with an `areturn` in the middle, and no lambda object exists at all.\n\nTo leave only the current call of the lambda, add a label. `return@forEach` behaves like `continue` in a loop.\n\nSince Kotlin 2.2.0, `break` and `continue` also work inside a lambda passed to an inline function. The feature is stable, so you need no compiler flag. In the demo, `break` inside `batch.forEach { }` leaves the outer `for` loop, the way Java's labeled `break outer` does.\n\nJava has no non-local return. A Java lambda always compiles to a separate method, so `return` inside `forEach(r -> { ... })` only ends that one call and the loop goes on. The demo's `firstDeclinedBroken` shows it: it always returns `null`. People who move from Java to Kotlin make the opposite mistake. They write `return` inside `forEach` to skip one element, and the whole function exits instead.",
   "try": {
    "title": "Return, label, break",
    "minutes": 4,
    "steps": [
     "Run `NonLocalReturnDemo` and then `NonLocalReturnDemoJava`. Before you run the Java one, predict what `firstDeclinedBroken` prints.",
     "Work out `totalUntilVoid` by hand from the three batches in `main`, then check your number against the output.",
     "Uncomment the wrong move at the bottom of `main` (a lambda stored in a `val`). Predict the error, run, then comment it out again."
    ],
    "code": demo("NonLocalReturnDemo"),
    "expect": "Kotlin prints `firstDeclined = DECLINED pay_2 insufficient funds`, `countApproved = 2` and `totalUntilVoid = 1650` (1,000 + 250 + 400, then the `-1` breaks out of the outer loop, so 900 and 75 are never added). Java's `firstDeclinedBroken` prints `null`. The wrong move fails with `'return' is prohibited here.` (Gradle adds `RETURN_NOT_ALLOWED`): a lambda stored in a `val` is an object, so it can't return from `main`."
   },
   "refs": [{"title": "What's new in Kotlin 2.2.0: non-local break and continue", "url": "https://kotlinlang.org/docs/whatsnew22.html", "kind": "docs"}]
  },
  {
   "h": "When a lambda can't be pasted: noinline and crossinline",
   "body": "Inlining works only if the compiler can paste the lambda's body where you call it. Two things get in the way, and each one has its own modifier.\n\nThe first is using the lambda as a value. An inlined lambda has no object behind it, so you can't store it in a field, add it to a list or pass it to an ordinary function. Try it and the compiler says `illegal usage of inline parameter 'listener: (String) -> Unit'. Add 'noinline' modifier to the parameter declaration.` **`noinline`** turns that one parameter back into a normal lambda object. The other parameters are still inlined.\n\nThe second is calling the lambda from somewhere else: inside an object, a `Runnable` or another lambda. The docs call this \"another execution context\". That code runs later, maybe on another thread, when the caller may have returned long ago. A non-local `return` from there can't work, so the compiler stops you: `cannot inline 'task: () -> Unit' here: it might contain non-local returns. Add 'crossinline' modifier to parameter declaration 'task: () -> Unit'.`\n\n`crossinline` is a rule for the caller's lambda: no bare `return` inside it. With that rule in place, the compiler still pastes the lambda's body, now into a `Runnable` class it generates for that call site. In the demo, `javap` finds a class called `ModifiersDemoKt$main$$inlined$runInBackground$1` with no `Function0` field: the body of the caller's lambda is inside its `run()`.\n\n```java\n// Java lambdas already behave like crossinline ones: return leaves only the lambda\nstatic void runInBackground(Executor executor, Runnable task) {\n    executor.execute(task);\n}\n\nrunInBackground(pool, () -> System.out.println(\"settling batch 17\"));\n```\n\n```kotlin\ninline fun runInBackground(executor: Executor, crossinline task: () -> Unit) {\n    executor.execute { task() }          // task runs later, on a pool thread\n}\n\nrunInBackground(pool) { println(\"settling batch 17\") }\n// runInBackground(pool) { return }     // error: 'return' is prohibited here.\n```\n\nBoth modifiers would make that function compile, so pick by what you do with the lambda. Use `crossinline` when you call it inside another lambda or object, because its body is still inlined into the new class. Use `noinline` when the lambda has to exist as a value you keep or hand on. Neither modifier changes the JVM signature: Java sees a `Function0` either way.\n\nYou'll need `crossinline` all the time at work. Plenty of Java APIs take a callback: `Executor.execute(Runnable)`, `CompletableFuture.supplyAsync(Supplier)`, a transaction template's `execute(callback)`, Temporal's `Async.function(...)`. Every inline Kotlin wrapper around one of them needs it.",
   "try": {
    "title": "Make the compiler ask for each modifier",
    "minutes": 5,
    "steps": [
     "Run `ModifiersDemo` (or `ModifiersDemoJava`, which calls the same Kotlin functions with plain Java lambdas).",
     "In `ModifiersDemo.kt`, delete `noinline` in `subscribe`. Predict the error, run, read it, then put it back.",
     "Delete `crossinline` in `runInBackground`, run, and put it back.",
     "Uncomment the last line of `main` and run. Why does the compiler refuse a `return` that it allowed in `forEach`?",
     "Predict without running: does `inline fun once(block: () -> Unit) = run { block() }` need `crossinline`? (`run` is itself inline.) Then add it to the file and check."
    ],
    "code": demo("ModifiersDemo"),
    "expect": "The first run prints `subscribing listener #1`, `listener got payment-captured` and `running on settlement-worker`. Without `noinline` the build fails with `illegal usage of inline parameter 'listener: (String) -> Unit'`. Without `crossinline` it fails with `cannot inline 'task: () -> Unit' here: it might contain non-local returns`. The last line fails with `'return' is prohibited here.`: by the time the `Runnable` runs on the pool thread, `main` may be somewhere else entirely. `once` compiles without `crossinline`: `run` is inline too, so `block` is still pasted into the caller's own code, and a `return` in it still has a function to leave. Swap `run` for an ordinary function that takes a lambda and the error comes back."
   }
  },
  {
   "h": "When not to inline",
   "body": "`inline` has costs, and three of them show up in real code.\n\nThe first is size. The body is copied into every caller, so a 40-line function called from 200 places becomes 200 copies. The compiler even warns when you inline a function that takes no lambdas: `expected performance impact from inlining is insignificant. Inlining works best for functions with parameters of function types.` The JIT already inlines small, hot methods at run time (the performance track covers how), so a lambda-free `inline fun` buys you nothing.\n\nThe second is frozen bodies. A caller gets its copy of the body when the caller is compiled. In one test run, a client was compiled against version 1 of a small library, and then version 2 replaced the library jar without recompiling the client. The client printed `inline=v1 plain=v2`: the ordinary function ran the new code, and the inline one still ran the old copy. So if you publish a shared library, such as an internal payments SDK, treat a public inline body like a public signature. Changing it takes effect only when every client is rebuilt.\n\nThe third is visibility, and it follows from the second. The body lands in other modules, so it may only use what those modules could use. Call a private function from a public inline one and you get `public-API inline function cannot access non-public-API function.` The fix is `@PublishedApi internal`: still hidden from Kotlin callers, but public in the bytecode, so the pasted copies can reach it. The helper's own body is not copied anywhere, so it can use private state freely.\n\n```java\n// Java has no internal or inline. The nearest shape: one public helper that callers reach\npublic final class Tracing {\n    private static final AtomicInteger COUNTER = new AtomicInteger();\n    public static String nextTraceId() { return \"trace-\" + COUNTER.incrementAndGet(); }\n}\n```\n\n```kotlin\ninline fun <T> traced(operation: String, block: () -> T): T {\n    val id = nextTraceId()                  // must be reachable from every caller's module\n    println(\"[$id] start $operation\")\n    val result = block()\n    println(\"[$id] end $operation\")\n    return result\n}\n\n@PublishedApi\ninternal fun nextTraceId(): String = \"trace-\" + counter.incrementAndGet()\n\nprivate val counter = AtomicInteger()       // fine: nextTraceId is not inline\n```\n\nThe compiler adds two hard limits. An inline function can't call itself (`inline function 'fun recI(n: Int): Int' cannot be recursive.`), and it can't contain a local function (`local functions are not yet supported in inline functions.`).\n\nProperties can be inline too, as long as the accessor has no backing field: `val Long.asEuros: String inline get() = ...`. You'll mostly see that for a property with a `reified` type parameter.\n\nHere's my rule. Inline small functions that take lambdas, or that need `reified` or a non-local return. Leave everything else ordinary. If the inline body starts to grow, keep the inline part to a few lines and move the real work into a `@PublishedApi internal` function, which is compiled once.",
   "try": {
    "title": "Break the visibility rule",
    "minutes": 3,
    "steps": [
     "Run `PublishedApiDemo`, then `PublishedApiDemoJava`.",
     "In `PublishedApiDemo.kt`, change `@PublishedApi internal fun nextTraceId()` to `private fun nextTraceId()`. Predict the error and run the Kotlin demo.",
     "Put it back. Why can the Java twin call `nextTraceId()` directly, when Kotlin code in another module could not?"
    ],
    "code": demo("PublishedApiDemo"),
    "expect": "Both print `[trace-1] start refund pay_7`, `[trace-1] end refund pay_7` and `refunded EUR 19.99`, and the Java twin also prints `trace-2` from a direct call. With `private`, the build fails with `public-API inline function cannot access non-public-API function.` `internal` is a Kotlin rule; in the bytecode the function is public, and javac doesn't know the rule exists."
   }
  }
 ],
 "analogy": "Inlining is a cook copying the recipe onto every order ticket instead of pinning one copy on the wall. Nobody walks to the wall, so each order moves faster, but every ticket gets longer. If the head chef fixes the recipe on the wall, tickets that were already printed still carry the old version: that's the frozen-body problem. The analogy breaks at `crossinline`. A cook can't accidentally walk out of the restaurant, but a lambda copied into a `Runnable` could try to `return` from a function that finished minutes ago, so the compiler has to forbid it.",
 "in_your_world": "Your Quarkus services are full of small wrappers: `timed(\"issuer.authorize\") { client.authorize(req) }` around a metrics timer, `withMdc(\"paymentId\", id) { ... }` around logging, a retry around a card-issuer call that takes 120 ms and sometimes times out. Each one is a good inline candidate: a few lines, a lambda parameter, called on every request. The moment a wrapper hands the lambda to a Java API (`executor.execute`, `CompletableFuture.supplyAsync`, a transaction callback, Temporal's `Async.function`), its parameter needs `crossinline`. And if those wrappers live in a shared library that ten services use, a fix to an inline body reaches each service only when that service is rebuilt against the new version.",
 "mistake": "Writing `return` inside `forEach` to skip one element. In Java, `return` in a `forEach` lambda skips to the next element, and many people carry that habit into Kotlin:\n\n```java\nbatch.forEach(p -> {\n    if (p.amountMinor() == 0) return;     // Java: skips this payment, carries on\n    ledger.post(p);\n});\n```\n\n```kotlin\nbatch.forEach { p ->\n    if (p.amountMinor == 0L) return       // Kotlin: leaves the whole function\n    ledger.post(p)\n}\n```\n\nIn Kotlin `forEach` is inline, so the bare `return` leaves the enclosing function, and every payment after the first zero-amount one is silently skipped. It compiles without a warning. Write `return@forEach` to skip one element, or use a plain `for` loop with `continue`, which reads better anyway.",
 "compare": {
  "title": "Wrapping a callback API: Java Supplier vs Kotlin inline with crossinline",
  "java": {"title": "Timing.java", "src": "import java.util.concurrent.CompletableFuture;\nimport java.util.concurrent.Executor;\nimport java.util.function.Supplier;\n\nfinal class Timing {\n    static <T> T timed(String label, Supplier<T> block) {\n        long start = System.nanoTime();\n        try {\n            return block.get();\n        } finally {\n            System.out.println(label + \" took \" + (System.nanoTime() - start) / 1_000 + \" us\");\n        }\n    }\n\n    // the caller's lambda is an object; supplyAsync gets a second lambda that calls it\n    static <T> CompletableFuture<T> timedAsync(String label, Executor executor, Supplier<T> block) {\n        return CompletableFuture.supplyAsync(() -> timed(label, block), executor);\n    }\n}\n\n// call site: Timing.timedAsync(\"capture\", pool, () -> gateway.capture(authId));"},
  "kotlin": {"title": "Timing.kt", "src": "import java.util.concurrent.CompletableFuture\nimport java.util.concurrent.Executor\n\ninline fun <T> timed(label: String, block: () -> T): T {\n    val start = System.nanoTime()\n    try {\n        return block()\n    } finally {\n        println(\"$label took ${(System.nanoTime() - start) / 1_000} us\")\n    }\n}\n\n// block runs inside the Supplier, another execution context: crossinline\ninline fun <T> timedAsync(label: String, executor: Executor, crossinline block: () -> T): CompletableFuture<T> =\n    CompletableFuture.supplyAsync({ timed(label) { block() } }, executor)\n\n// call site: timedAsync(\"capture\", pool) { gateway.capture(authId) }"},
  "note": "In Java the caller's lambda is always an object, and `timedAsync` wraps it in a second one for `supplyAsync`. In Kotlin the compiler pastes both `timed` and the caller's lambda into one `Supplier` class that it generates for that call site, so there is one object instead of two and no call through `Supplier.get` on the caller's code. The bigger difference is the rule on the caller: inside the Kotlin block a bare `return` is a compile error, while a Java lambda simply can't express one. Java code that calls the Kotlin `timedAsync` gets the ordinary compiled body and passes a `Function0`."
 },
 "worked": {
  "title": "Write an inline transaction helper over a Java callback API",
  "steps": [
   {"say": "A Java library (invented for this example) runs work inside a database transaction through a callback. You want Kotlin callers to write `tx.transaction { ledger.post(entry) }`. Start with the API and an ordinary Kotlin wrapper.",
    "code": "public interface TxRunner {\n    <T> T inTransaction(Callable<T> work);\n}\n\n// Java callers write the Callable themselves\nlong balance = tx.inTransaction(() -> ledger.balanceOf(\"merchant-981\"));", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "interface TxRunner {\n    fun <T> inTransaction(work: Callable<T>): T\n}\n\n// 1. an ordinary wrapper: it works, but each call builds a Function0 and a Callable\nfun <T> TxRunner.transaction(block: () -> T): T = inTransaction(Callable { block() })"},
   {"say": "The wrapper is one line and runs on every request, so make it inline. The compiler refuses, because `block()` is now called inside the `Callable`, which the library may run later or on another thread.",
    "code": "// 2. add inline: the compiler stops here\ninline fun <T> TxRunner.transaction(block: () -> T): T = inTransaction(Callable { block() })\n// error: cannot inline 'block: () -> T' here: it might contain non-local returns.\n// Add 'crossinline' modifier to parameter declaration 'block: () -> T'.", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// Java has no inline and no non-local return, so the question never comes up:\n// a return inside the Callable lambda only ends the Callable\nlong posted = tx.inTransaction(() -> { ledger.post(entry); return 1L; });"},
   {"say": "Add `crossinline`. The caller's lambda is now pasted into a `Callable` class the compiler generates for each call site. In exchange, callers lose the non-local `return`: that's the rule `crossinline` enforces.",
    "code": "// 3. crossinline: inlined into the generated Callable, no bare return allowed\ninline fun <T> TxRunner.transaction(crossinline block: () -> T): T =\n    inTransaction(Callable { block() })\n\nfun post(entry: JournalEntry) {\n    tx.transaction { ledger.post(entry) }\n    // tx.transaction { if (entry.isEmpty) return }   // error: 'return' is prohibited here.\n}", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "void post(JournalEntry entry) {\n    tx.inTransaction(() -> {\n        ledger.post(entry);\n        return null;                 // Callable must return something\n    });\n}"},
   {"say": "Check that it earns its place. It does: one line, a lambda parameter, called constantly. If it later grows logging, metrics and error mapping, keep the inline part to this one line and move the rest into a `@PublishedApi internal` function, so 300 call sites don't each carry a copy.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "An inline retry helper, sync and async",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/Retry.kt", f"{lab}/main/{P}/Callers.kt"],
  "run": "./gradlew :kotlin:test --tests 'workbench.kotlin.l01.*'",
  "steps": [
   "Run the tests. All eight fail with `NotImplementedError`. Read `Callers.kt` but don't edit it: the tests go through it, and its comment says why.",
   "Write `retry` (TODO 1). Start at attempt 1, `return block(attempt)` inside a `try`, catch `Exception`, and decide whether to go round again. Keep the earlier failures in a list.",
   "When you stop, `throw giveUp(attempt, e, earlier)`. The build now fails. Read the error, and fix the declaration of `giveUp` (TODO 2), not `retry`.",
   "Write `retryAsync` (TODO 3) as `CompletableFuture.supplyAsync({ retry(maxAttempts) { block(it) } }, executor)`. Add the modifier the compiler asks for.",
   "Run the tests until all eight pass, including `RetryFromJavaTest`, which calls your `retry` from Java with no inlining at all.",
   "Optional: add `crossinline` to `retry`'s `block` and run again. `Callers.firstApproved` stops compiling, because its `return card` is a non-local return. Undo it."
  ],
  "hints": [
   "`require(maxAttempts >= 1) { \"maxAttempts must be at least 1\" }` throws `IllegalArgumentException` before the loop starts, so the block is never called.",
   "A `while (true)` loop whose body ends only with `return` or `throw` needs no `return` after it. The compiler knows the loop never falls through.",
   "The fix for TODO 2 is two words on the declaration: `@PublishedApi internal fun giveUp(...)`. `internal` keeps it out of the Kotlin API, and `@PublishedApi` lets public inline bodies call it.",
   "`supplyAsync` stores a thrown exception in the future, and `get()` reports it as an `ExecutionException` whose cause is your `RetryExhaustedException`. You don't have to write anything for that."
  ],
  "done_when": "All eight tests in `RetryTest` and `RetryFromJavaTest` pass."
 },
 "drill": {
  "title": "Write timed and timedAsync from memory",
  "minutes": 5,
  "prompt": "Close this page. Write an inline `timed(label, block)` that returns the block's result and prints the elapsed time even when the block throws. Then write `timedAsync(label, executor, block)` that runs `timed` on an executor and returns a `CompletableFuture`. Which parameter needs a modifier, and which one?",
  "answer": {"lang": "kotlin", "src": "inline fun <T> timed(label: String, block: () -> T): T {\n    val start = System.nanoTime()\n    try {\n        return block()\n    } finally {\n        println(\"$label took ${(System.nanoTime() - start) / 1_000} us\")\n    }\n}\n\n// block is called inside the Supplier: another execution context, so crossinline\ninline fun <T> timedAsync(label: String, executor: Executor, crossinline block: () -> T): CompletableFuture<T> =\n    CompletableFuture.supplyAsync({ timed(label) { block() } }, executor)",
             "alt": {"lang": "java", "title": "Timing.java", "src": "static <T> T timed(String label, Supplier<T> block) {\n    long start = System.nanoTime();\n    try {\n        return block.get();\n    } finally {\n        System.out.println(label + \" took \" + (System.nanoTime() - start) / 1_000 + \" us\");\n    }\n}\n\n// no modifier exists in Java: the Supplier is always an object\nstatic <T> CompletableFuture<T> timedAsync(String label, Executor executor, Supplier<T> block) {\n    return CompletableFuture.supplyAsync(() -> timed(label, block), executor);\n}"}}
 },
 "recap": [
  "`inline` copies the function body and the bodies of its lambda arguments into each caller: no `Function` object, no call through an interface, no boxing of a generic result.",
  "A bare `return` in a lambda passed to an inline function is a non-local return and leaves the enclosing function. `return@forEach` leaves only the lambda. Since Kotlin 2.2, `break` and `continue` work there too.",
  "`noinline` keeps one lambda as a real object you can store or pass on. `crossinline` lets you call a lambda from another execution context (a `Runnable`, a `Supplier`, an object) by forbidding non-local returns in it.",
  "Inline only small functions that take lambdas. Every caller carries a copy, and a public inline body stays frozen in a client until that client is recompiled.",
  "A public inline function may only use public API. Reach a helper through `@PublishedApi internal`.",
  "Java never inlines Kotlin code. It calls the compiled body and passes `Function0` or `Function1` objects."
 ],
 "quiz": [
  {"q": "What does the compiler say about this function?\n\n```kotlin\ninline fun onIoThread(pool: Executor, task: () -> Unit) {\n    pool.execute { task() }\n}\n```",
   "options": ["Nothing: it compiles as written", "`cannot inline 'task' here: it might contain non-local returns`, and it suggests `crossinline`", "`illegal usage of inline parameter`, and it suggests `noinline`", "Inline functions can't call Java APIs such as `Executor`"],
   "answer": 1, "why": "`task` is called inside the `Runnable` lambda, which is another execution context. The compiler asks for `crossinline`, which forbids a `return` in the caller's lambda and still inlines its body into the generated `Runnable`. `noinline` would also make it compile, but the compiler suggests that one when you store or pass the lambda itself, and it gives up inlining the body."},
  {"q": "What does `process(listOf(1, 0, 2))` print?\n\n```kotlin\nfun process(xs: List<Int>) {\n    xs.forEach {\n        if (it == 0) return\n        print(it)\n    }\n    print(\" done\")\n}\n```",
   "options": ["`1`", "`12 done`", "`1 done`", "`12`"],
   "answer": 0, "why": "`forEach` is inline, so the bare `return` leaves `process` the first time it sees 0. Nothing after that runs, not even `print(\" done\")`. `12 done` is what the Java habit expects, where `return` only skips one element; that would be `return@forEach` in Kotlin."},
  {"q": "`ledger-client` 2.0 was compiled against `payments-common` 1.4.0 and calls its public `inline fun <T> withRetry(block: () -> T)`. Your service upgrades `payments-common` to 1.4.1, which fixes a bug inside `withRetry`, and keeps `ledger-client` 2.0. Which `withRetry` code runs when `ledger-client` calls it?",
   "options": ["The fixed 1.4.1 code, because the newest jar is on the classpath", "Neither: the JVM throws `NoSuchMethodError`", "The old 1.4.0 code, copied into `ledger-client`'s bytecode when it was compiled", "Whichever version the class loader happens to load first"],
   "answer": 2, "why": "An inline body is copied into the caller at the caller's compile time. `ledger-client` never calls the `withRetry` method in the jar; it runs its own pasted copy of the 1.4.0 body. The classpath only decides which method exists, and nobody in `ledger-client` calls it. Only rebuilding `ledger-client` against 1.4.1 picks up the fix."},
  {"q": "Which declaration makes the compiler warn `expected performance impact from inlining is insignificant`?",
   "options": ["`inline fun <T> timed(label: String, block: () -> T): T`", "`inline fun <reified T> Any?.isA(): Boolean = this is T`", "`inline fun <T> List<T>.sumMinorBy(selector: (T) -> Long): Long`", "`inline fun toMinor(amount: BigDecimal): Long = amount.movePointRight(2).longValueExact()`"],
   "answer": 3, "why": "`toMinor` has no function-typed parameter and no reified type parameter, so there is nothing for inlining to remove. The JIT would inline a hot small method like that by itself. `isA` has no lambda, but it needs `inline` for its reified `T`, so the compiler doesn't warn."},
  {"q": "From the generics track: why does `inline fun <reified T> Any?.isA() = this is T` need `inline`?",
   "options": ["Because reflection is slow, and inlining makes it fast", "Because the reified type is stored in a hidden field of the lambda object", "Because the JVM erases `T`, and only a copy of the body at each call site knows the real class", "It doesn't: since Kotlin 2.0 `reified` works on ordinary functions too"],
   "answer": 2, "why": "Type arguments are erased at run time, so an ordinary function can't know what `T` was. An inline function's body is compiled again at each call site, where the type argument is written in plain sight, and the compiler can put a real `instanceof` there. Ordinary functions still can't have reified type parameters.",
   "from": "gen-08"}
 ],
 "flashcards": [
  {"front": "What does `inline` do to a function and the lambdas passed to it?", "back": "The compiler copies the function body and each lambda body into the call site. No `Function` object is created and nothing is called through an interface."},
  {"front": "Inside `fun f()`, what does the `return` in `list.forEach { if (it == 0) return }` leave?", "back": "The whole function `f`. It's a non-local return, allowed because `forEach` is inline. `return@forEach` would leave only that lambda call."},
  {"front": "When does the compiler ask for `noinline`?", "back": "When you use an inline lambda parameter as a value: store it in a field, add it to a collection, or pass it to a non-inline function."},
  {"front": "When does the compiler ask for `crossinline`?", "back": "When you call the lambda from another execution context, such as an object, a `Runnable` or another lambda. `crossinline` forbids non-local returns in the caller's lambda."},
  {"front": "Why is a public inline function's body part of your library's binary interface?", "back": "Callers get a copy of the body when they are compiled. Change the body, and an old caller keeps running its old copy until it is recompiled."},
  {"front": "A public inline function calls a `private` helper. What happens, and what is the fix?", "back": "Compile error: `public-API inline function cannot access non-public-API function.` Mark the helper `@PublishedApi internal`."},
  {"front": "What does Java see when it calls a Kotlin inline function?", "back": "An ordinary static method that takes `Function0`/`Function1` objects. javac inlines nothing. A reified inline function is synthetic, so javac can't see it at all."}
 ],
 "terms": [
  {"term": "Inline function", "plain": "A function whose body the compiler copies into each call site, together with the bodies of the lambdas passed to it."},
  {"term": "Call site", "plain": "A place in the code that calls a function. With inline, this is where the copy of the body ends up."},
  {"term": "Non-local return", "plain": "A bare `return` inside an inlined lambda. It leaves the function that contains the lambda, not just the lambda."},
  {"term": "Labeled return", "plain": "`return@forEach`: leaves only the current call of the lambda, like `continue` in a loop."},
  {"term": "noinline", "plain": "Marks one lambda parameter of an inline function as an ordinary object, so you can store it or pass it on."},
  {"term": "crossinline", "plain": "Marks a lambda parameter that is called from another execution context. Non-local returns are forbidden in it."},
  {"term": "@PublishedApi", "plain": "Lets public inline functions use an internal declaration. The declaration is public in the bytecode."}
 ],
 "explain_back": {
  "prompt": "A teammate asks why the compiler made them write `crossinline` in `inline fun <T> TxRunner.transaction(block: () -> T) = inTransaction(Callable { block() })`. Explain, in your own words, what could go wrong without it and what they give up by adding it.",
  "answer": "Because the function is inline, the caller's lambda is pasted into the caller, and normally a bare `return` in it would return from the caller. Here the lambda isn't called directly: it's called inside a `Callable` that the transaction library runs, maybe later and maybe on another thread. By then the caller's function may already have returned, so a `return` from inside the `Callable` can't mean \"return from the caller\". The compiler can't allow that, so it asks for `crossinline`. With `crossinline`, the compiler still pastes the lambda's body, now into a `Callable` class it generates for that call site, and in exchange callers may not write a bare `return` in the block. They can still use a labeled return like `return@transaction`. `noinline` would also compile, but it keeps the lambda as a separate object, which is the fix for storing a lambda, not for calling it somewhere else."
 },
 "deeper": {
  "minutes": 10,
  "body": "Kotlin's inlining and the JIT's inlining are different tools. Kotlin inlines at compile time, across modules, before the JVM ever sees the code. That is the only kind that can make a non-local `return` or a `reified` type work, because both change what the code means. The JIT inlines at run time, only on hot paths, and can undo its choice (deoptimization) when its assumptions break. The lesson \"Inlining, deoptimization and intrinsics\" in the performance track covers that side.\n\nThe Kotlin docs say inlining pays off \"especially at 'megamorphic' call-sites inside loops\". Here's why. An ordinary `forEach` taking a `Function1` has one `invoke` call site inside it. If 30 different lambdas flow through that one call site, the JIT sees 30 receiver classes there and can't inline any of them. With an inline `forEach`, each caller has its own copy of the loop, with exactly one lambda body pasted in. Nothing is left for the JIT to guess.\n\nA `crossinline` lambda leaves two classes behind. Run `javap -p` on the `ModifiersDemoKt$...` classes in `kotlin/build/classes/kotlin/demo/workbench/kotlin/l01/demo/`:\n\n```text\nModifiersDemoKt$runInBackground$1 implements java.lang.Runnable {\n  final kotlin.jvm.functions.Function0<kotlin.Unit> $task;   // used when Java calls the compiled body\n  public final void run();\n}\nModifiersDemoKt$main$$inlined$runInBackground$1 implements java.lang.Runnable {\n  public final void run();                                   // main's lambda body is pasted in here\n}\n```\n\nThe first is the template that the compiled `runInBackground` method uses when Java (or reflection) calls it: it holds the `Function0`. The second was generated for the one call site in `main`, with the lambda's body inside `run()`. Each inlined call site of a `crossinline` function gets a class like that, which is one more reason to keep these functions few and small.\n\nFinally, a reified inline function has no callable form at all, because its body makes no sense without a concrete type. Kotlin still writes a method into the class file, but marks it `ACC_SYNTHETIC`, and `javac` ignores synthetic methods. That's why Java code can't call `filterIsInstance<T>()`-style functions."
 },
 "sources": [
  {"title": "Inline functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-functions.html"},
  {"title": "What's new in Kotlin 2.2.0 (non-local break and continue)", "url": "https://kotlinlang.org/docs/whatsnew22.html"},
  {"title": "Calling Kotlin from Java (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html"},
  {"title": "Kotlin language features and proposals", "url": "https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html"}
 ]
}
out = ROOT / "content/lessons/kt-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
