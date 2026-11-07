import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/vthreads/src"
P = "java/workbench/vthreads/l05"
K = "kotlin/workbench/vthreads/l05"
PV = "labs/vthreads/preview"
read = lambda p: (ROOT / p).read_text()


def demo(name):
    """Try-it code for a Gradle demo in Java plus its Kotlin twin."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": f"./gradlew :vthreads:demo -Pmain=workbench.vthreads.l05.{name}",
            "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": f"./gradlew :vthreads:demo -Pmain=workbench.vthreads.l05.{name}Kt",
                    "file": f"{lab}/demo/{K}/{name}.kt"}}


def preview(name, java_run, kt_jar, kt_flags, label):
    """Try-it code for a single-file JDK 25 program that lives outside Gradle, plus its Kotlin twin."""
    return {"lang": "java", "title": f"{name}.java ({label})", "src": read(f"{PV}/{name}.java"),
            "run": java_run, "file": f"{PV}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt ({label})", "src": read(f"{PV}/{name}.kt"),
                    "run": f"kotlinc vthreads/preview/{name}.kt -include-runtime -d vthreads/build/{kt_jar} && java {kt_flags}-jar vthreads/build/{kt_jar}",
                    "file": f"{PV}/{name}.kt"}}


FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="Two timelines of the same quote request. With a shared executor, the request fails at 100 ms but its customer subtask keeps running until 2 seconds. With a scope, the failure cancels the customer subtask, and close waits for it, so nothing outlives the block.">'
    '<text class="t-s t-m" x="20" y="22">A shared executor: the request ends, its subtask does not</text>'
    '<rect class="box" x="60" y="34" width="150" height="26" rx="8"/>'
    '<text class="t-s" x="135" y="51" text-anchor="middle">request</text>'
    '<rect class="box-bad" x="60" y="66" width="150" height="26" rx="8"/>'
    '<text class="t-s" x="135" y="83" text-anchor="middle">limit: fails</text>'
    '<rect class="box" x="60" y="98" width="150" height="26" rx="8"/>'
    '<text class="t-s" x="135" y="115" text-anchor="middle">customer</text>'
    '<rect class="box-bad" x="214" y="98" width="446" height="26" rx="8"/>'
    '<text class="t-s t-bad" x="437" y="115" text-anchor="middle">customer keeps calling the CRM after the request failed</text>'
    '<line class="ln-d" x1="60" y1="138" x2="660" y2="138" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="60" y="154" text-anchor="middle">0</text>'
    '<text class="t-s t-m" x="210" y="154" text-anchor="middle">100 ms</text>'
    '<text class="t-s t-m" x="640" y="154" text-anchor="middle">2 s</text>'
    '<text class="t-s t-m" x="20" y="182">A scope: no subtask outlives the block</text>'
    '<rect class="box-a" x="48" y="192" width="182" height="102" rx="8"/>'
    '<rect class="box" x="60" y="200" width="150" height="26" rx="8"/>'
    '<text class="t-s" x="135" y="217" text-anchor="middle">request</text>'
    '<rect class="box-bad" x="60" y="232" width="150" height="26" rx="8"/>'
    '<text class="t-s" x="135" y="249" text-anchor="middle">limit: fails</text>'
    '<rect class="box-ok" x="60" y="264" width="150" height="26" rx="8"/>'
    '<text class="t-s" x="135" y="281" text-anchor="middle">customer: interrupted</text>'
    '<text class="t-s" x="250" y="217">limit fails at 100 ms, so the scope cancels customer</text>'
    '<text class="t-s" x="250" y="249">join() throws, and close() waits for customer to end</text>'
    '<text class="t-s t-ok" x="250" y="281">the request ends with nothing left running</text>'
    '</svg>'
)

S1 = """Here is the fan-out from lesson 3 of this track, inside a quote handler. It needs the customer record (a CRM call that takes 2 s on a bad day) and a credit limit check, which fails after 100 ms.

```java
try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
    Future<Customer> customer = perTask.submit(() -> crm.find(id));   // up to 2 s
    Future<Limit> limit = perTask.submit(() -> limits.check(id));     // fails at 100 ms
    return new Quote(customer.get(), limit.get());
}
```

```kotlin
Executors.newVirtualThreadPerTaskExecutor().use { perTask ->
    val customer = perTask.submit(Callable { crm.find(id) })    // up to 2 s
    val limit = perTask.submit(Callable { limits.check(id) })   // fails at 100 ms
    Quote(customer.get(), limit.get())
}
```

The request is doomed at 100 ms, and it fails at 2 s. `customer.get()` waits the full 2 s before `limit.get()` gets to throw. Swap the two `get()` calls and it still takes 2 s, because `close()` waits for the CRM call and nothing tells that call to stop.

Many services keep one executor in a field instead. Then the method fails at 100 ms, but the CRM call keeps running with nobody waiting for its answer. It holds an HTTP connection and maybe a semaphore permit. Under load these orphans pile up, and nothing in a thread dump says which request they belonged to.

Three things are missing here:

- Failure doesn't cancel anything. To stop the siblings you must call `cancel(true)` on each other future, in every fan-out, on every error path.
- Lifetimes aren't tied to the code. A `Future` is a value you can store anywhere, so nothing promises that the threads a method started have ended when it returns.
- Context doesn't follow the work. A `ThreadLocal` set by the handler, such as the request id in your logging MDC, is empty in the subtasks. `InheritableThreadLocal` copies it into every new thread, and the copy goes stale.

**Structured concurrency** fixes the first two with one rule: subtasks can't outlive the block that started them, the same way a local variable can't outlive its method. Scoped values, at the end of this lesson, fix the third."""

S2 = """A structured scope has three operations, and the code always has the same shape:

```java
try (var scope = new FailFastScope()) {                  // this lesson's lab
    Supplier<Customer> customer = scope.fork(() -> crm.find(id));
    Supplier<Limit> limit = scope.fork(() -> limits.check(id));
    scope.join();                                        // waits, or throws the first failure
    return new Quote(customer.get(), limit.get());
}                                                        // close(): no subtask is still running
```

```kotlin
FailFastScope().use { scope ->                           // this lesson's lab
    val customer = scope.fork { crm.find(id) }
    val limit = scope.fork { limits.check(id) }
    scope.join()                                         // waits, or throws the first failure
    Quote(customer.get(), limit.get())
}                                                        // close(): no subtask is still running
```

`fork` starts a subtask on a new virtual thread. `join` waits for the subtasks. `close` is the guarantee: when the block ends, every thread the scope started has ended, whether the block returned, threw or was interrupted. The policy here is **fail fast**: the first subtask to fail cancels the others, and `join` throws that failure at once.

You build exactly this in the lab, on a plain `newVirtualThreadPerTaskExecutor()`. Each forked task runs inside a wrapper. If the task throws, the wrapper records the failure with `AtomicReference.compareAndSet(null, failure)`, so only the first one wins, and then cancels everything else. Cancel means interrupt. That stops code blocked in `sleep`, socket reads, locks and queues, which covers almost all blocking on virtual threads. A loop that computes and never checks the interrupt flag keeps running.

Two details are easy to get wrong, and the tests check both.

The siblings you interrupt fail too, with an `InterruptedException`. Those failures must not replace the real one. The compare-and-set already handles it, because the real failure got there first.

`close()` must wait for threads, not for futures. `Future.cancel(true)` interrupts the thread and marks the future done at once. On JDK 21, `newVirtualThreadPerTaskExecutor` counts a task as finished as soon as its future is done, so `close()` can return while a cancelled task is still in its `finally` block, writing an audit row or releasing a permit. `executor.shutdownNow()` interrupts every thread and leaves the futures alone, so `close()` keeps waiting until each thread has really finished.

That second bug looks right and passes most tests, which is the strongest argument for using the JDK's scope once you can. The figure shows the difference it makes."""

S3 = """`StructuredTaskScope` is the JDK's version. Its current shape arrived in JDK 25 (JEP 505, the fifth preview). It is still a preview API in JDK 26 (JEP 525) and JDK 27 (JEP 533). JEP 543 makes it final in JDK 28, due in March 2027, with the JDK 27 API unchanged. Until then you need `--enable-preview`, which is why this course keeps it out of the Gradle labs.

Here is the quote handler in the JDK 25 shape:

```java
Quote quote(String id) throws InterruptedException {
    try (var scope = StructuredTaskScope.open()) {           // fail on the first failure
        Subtask<Customer> customer = scope.fork(() -> crm.find(id));
        Subtask<Limit> limit = scope.fork(() -> limits.check(id));
        scope.join();               // JDK 25: throws StructuredTaskScope.FailedException
        return new Quote(customer.get(), limit.get());
    }                               // close(): cancels what is left and waits for it
}
```

```kotlin
fun quote(id: String): Quote =
    StructuredTaskScope.open<Any>().use { scope ->              // fail on the first failure
        val customer = scope.fork(Callable { crm.find(id) })
        val limit = scope.fork(Callable { limits.check(id) })
        scope.join()               // JDK 25: throws StructuredTaskScope.FailedException
        Quote(customer.get(), limit.get())
    }                              // close(): cancels what is left and waits for it
```

It is your `FailFastScope` with stricter rules. Subtasks run on virtual threads. `get()` before `join()` throws `IllegalStateException`. Scopes must nest like blocks, and the JDK checks that you close them in order. A JSON thread dump (`jcmd <pid> Thread.dump_to_file -format=json`) shows each scope's threads grouped under it, so you can see which request a thread belongs to.

The policy is a `Joiner` that you pass to `open`. JDK 25 has four:

- `Joiner.awaitAllSuccessfulOrThrow()`, the default: fail fast, and `join()` returns `null`.
- `Joiner.allSuccessfulOrThrow()`: fail fast, and `join()` returns the subtasks as a `Stream<Subtask<T>>`.
- `Joiner.anySuccessfulResultOrThrow()`: the first success wins, and the scope cancels the rest.
- `Joiner.awaitAll()`: wait for everything and never throw. You check each subtask's `state()`.

A second argument configures the scope, for example a timeout:

```java
try (var scope = StructuredTaskScope.open(Joiner.<Rate>anySuccessfulResultOrThrow(),
        cf -> cf.withTimeout(Duration.ofMillis(300)))) {
    scope.fork(() -> fxPrimary.rate(pair));
    scope.fork(() -> fxBackup.rate(pair));
    return scope.join();        // the first rate back; the slower call is cancelled
}
```

```kotlin
StructuredTaskScope.open(Joiner.anySuccessfulResultOrThrow<Rate>()) { cf ->
    cf.withTimeout(Duration.ofMillis(300))
}.use { scope ->
    scope.fork(Callable { fxPrimary.rate(pair) })
    scope.fork(Callable { fxBackup.rate(pair) })
    scope.join()               // the first rate back; the slower call is cancelled
}
```

If the timeout expires first, the scope cancels both calls and `join()` throws `StructuredTaskScope.TimeoutException`.

Expect small edits when you move JDKs. JDK 26 renamed `anySuccessfulResultOrThrow` to `anySuccessfulOrThrow`, and `allSuccessfulOrThrow` now returns a `List<T>` of results. In JDK 27 the built-in joiners make `join()` throw the ordinary checked `ExecutionException`, like `Future.get()`, instead of `FailedException`. Your lab scope already behaves that way. Articles from the JDK 21 era show `new StructuredTaskScope.ShutdownOnFailure()` and `throwIfFailed()`. That API is gone and doesn't compile on JDK 25."""

S4 = """Request context (a correlation id, a tenant, the authenticated merchant) travels down the call chain without being a parameter of every method. The usual tool is a `ThreadLocal`, and it has three problems:

- It is mutable. Any code can call `set()`, so the code that reads it can't tell where the value came from.
- It lives as long as the thread unless someone calls `remove()`. On a pooled thread, a forgotten value leaks into the next request. That is how one tenant's log lines end up tagged with another tenant's id.
- Its inheritance is a copy. `InheritableThreadLocal` copies values into each new thread. With a virtual thread per subtask, that's one copy per subtask, and a change in the parent never reaches the children.

A **scoped value** is the replacement. It is final in JDK 25 (JEP 506), so it needs no flag. You bind it for the length of one call, everything inside that call can read it, and nobody can change it:

```java
static final ScopedValue<String> TENANT = ScopedValue.newInstance();

void handle(Request req) {
    ScopedValue.where(TENANT, req.tenant()).run(() -> process(req));   // bound only inside run()
}

static String ledgerKey(String account) {
    return TENANT.get() + ":" + account;     // NoSuchElementException if nobody bound it
}
```

```kotlin
val TENANT: ScopedValue<String> = ScopedValue.newInstance()

fun handle(req: Request) {
    ScopedValue.where(TENANT, req.tenant).run(Runnable { process(req) })   // bound only inside run()
}

fun ledgerKey(account: String): String =
    TENANT.get() + ":" + account              // NoSuchElementException if nobody bound it
```

There is no `set()`. To use another value for a nested call, bind again with `where(...).run(...)`. The outer value comes back when that call returns. `isBound()` and `orElse(...)` let library code handle the case where nothing is bound, and `call(...)` is the variant that returns a value and may throw.

Scoped values flow into subtasks forked in a `StructuredTaskScope`. The child doesn't get a copy. It reads the parent's binding, which is safe because the binding can't change and the scope ends before the binding does. They do not flow into threads you start yourself or into executor tasks, so pass the value as an argument there.

On JDK 25 that gives a clear split. Use scoped values for new request context today. Their flow into subtasks needs `StructuredTaskScope`, which is still preview. Keep `ThreadLocal` where a library requires it, like SLF4J's MDC, and clear it in a `finally`."""

L = {
 "id": "vt-05",
 "title": "Structured concurrency and scoped values",
 "minutes": 35,
 "goal": "By the end you can say what structured concurrency guarantees, build fail-fast fork and join on a plain executor, read the JDK 25 `StructuredTaskScope` API and what changes after it, and use scoped values instead of request-context ThreadLocals.",
 "warmup": {
  "q": "A handler submits two tasks to `newVirtualThreadPerTaskExecutor()` inside try-with-resources. Task A takes 2 s. Task B throws after 100 ms. The handler calls `b.get()` first. When does the handler's exception reach its caller?",
  "options": [
   "After about 100 ms: `b.get()` throws, and the executor cancels A",
   "After about 2 s: `b.get()` throws at 100 ms, but `close()` waits for A to finish",
   "Never: the executor logs B's exception and returns `null`",
   "After about 100 ms, and A is still running when the caller sees the exception"
  ],
  "answer": 1,
  "why": "`get()` throws at 100 ms, but leaving the try block runs `close()`, which waits for every task. Nothing cancels A, so the failed request still takes 2 s. The last option is what happens with a long-lived executor in a field: the method fails fast, and A keeps running with nobody waiting for it."
 },
 "sections": [
  {
   "h": "A failed fan-out keeps working after nobody cares",
   "body": S1,
   "try": {
    "title": "Watch the orphaned call",
    "minutes": 5,
    "steps": [
     "Read `LeakDemo`. Variant A opens an executor per request in try-with-resources. Variant B uses one shared executor. For each, predict when the request fails and whether the CRM call finishes.",
     "Run it with the command below.",
     "Fix variant A by hand. Wrap `limit.get()` in a try, call `customer.cancel(true)` in the `catch (ExecutionException e)`, then rethrow. Run it again."
    ],
    "code": demo("LeakDemo"),
    "expect": "A: the CRM call finishes at about 2,000 ms, and only then does the request fail, although the error was known at 100 ms. B: the request fails at about 100 ms, and the CRM call still finishes at about 2,000 ms, for a request that is long gone. After your fix, A prints `customer: interrupted, stopped early` and fails at about 100 ms. That fixes one fan-out. Every other fan-out in the service needs the same code on every error path."
   },
   "refs": [
    {"title": "ExecutorService (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ExecutorService.html", "kind": "docs"}
   ]
  },
  {
   "h": "A scope ties every subtask to one block",
   "body": S2,
   "figure": {"svg": FIG, "caption": "With a shared executor the failed request leaves its customer call running. In a scope the failure cancels it, and close() waits until it has ended."}
  },
  {
   "h": "StructuredTaskScope: the JDK's scope, still preview",
   "body": S3,
   "try": {
    "title": "Run the scope on JDK 25",
    "minutes": 6,
    "steps": [
     "This one needs JDK 25 exactly, because `--enable-preview` only works for the JDK's own release. Check with `java -version`. It runs outside Gradle, as a single-file program, from `labs/`.",
     "Run `ScopeDemo` and compare its timeline with `LeakDemo`. Look at the `[req-42]` on the customer's line: the subtask can read the request's scoped value.",
     "Make `limit()` return `\"limit ok\"` after its sleep instead of throwing. Predict how long the request takes, then run it.",
     "Now open the scope with a timeout: `StructuredTaskScope.open(Joiner.awaitAllSuccessfulOrThrow(), cf -> cf.withTimeout(Duration.ofMillis(500)))` (in Kotlin, `open(Joiner.awaitAllSuccessfulOrThrow<Any>()) { cf -> cf.withTimeout(Duration.ofMillis(500)) }`). Predict, then run."
    ],
    "code": preview("ScopeDemo", "java --enable-preview --source 25 vthreads/preview/ScopeDemo.java", "scope-demo.jar", "--enable-preview ", "JDK 25 preview"),
    "expect": "First run: at about 100 ms the customer line says `interrupted, stopped early`, then `request failed: credit limit service: 503`, then the `done` line, with `[-]` because the binding has ended. When both succeed, the quote arrives after about 2,000 ms, since the default joiner waits for every subtask. With the 500 ms timeout, the customer is interrupted at about 500 ms and the request reports `request timed out`. In every case the `done` line comes last: the scope never leaves a subtask running."
   },
   "refs": [
    {"title": "JEP 505: Structured Concurrency (Fifth Preview)", "url": "https://openjdk.org/jeps/505", "kind": "read"},
    {"title": "JEP 533: Structured Concurrency (Seventh Preview)", "url": "https://openjdk.org/jeps/533", "kind": "read"}
   ]
  },
  {
   "h": "Scoped values: request context with a lifetime",
   "body": S4,
   "try": {
    "title": "ThreadLocal and ScopedValue side by side",
    "minutes": 4,
    "steps": [
     "You need JDK 25 or later. Scoped values are final there, so this runs without `--enable-preview`.",
     "Read `ScopedValueDemo` and predict its six lines of output before you run it.",
     "Run it. Then, in part 1, move the work into a `try` and add `TENANT_TL.remove()` in a `finally`. Run it again."
    ],
    "code": preview("ScopedValueDemo", "java vthreads/preview/ScopedValueDemo.java", "sv-demo.jar", "", "JDK 25"),
    "expect": "Line 1 shows `ThreadLocal=bank-a` in a task that never set it: the value leaked from the previous task on the same pool thread. After your fix it shows `ThreadLocal=null`. The scoped value is `bank-a` inside `run()` and `unbound` after it, `bank-b` in the nested call and `bank-a` again after it. The plain virtual thread prints `unbound`, because only `StructuredTaskScope` forks see the parent's binding."
   },
   "refs": [
    {"title": "JEP 506: Scoped Values", "url": "https://openjdk.org/jeps/506", "kind": "read"}
   ]
  }
 ],
 "analogy": "A structured scope works like a function call for concurrent work. A local variable can't outlive the method that declared it, and a subtask can't outlive the block that forked it. A `ThreadLocal` is a whiteboard on the thread's wall: anyone can write on it, nobody has to wipe it, and the next person to use the room reads whatever was left. A scoped value is a sealed envelope handed down the call chain and shredded when the call returns. The analogy breaks for subtasks: a scope's forks don't get their own envelopes, they all read the parent's. That is safe only because nobody can change the envelope and the scope ends before the call does.",
 "in_your_world": "A quote or authorization endpoint in a Quarkus service often fans out to a CRM, a limits service and an FX provider. Today those calls usually go through `CompletableFuture` or an injected executor, and a failure in one leaves the others running and holding connections. On JDK 25 you can get fail-fast behavior now with a small scope like the lab's, and move to `StructuredTaskScope` when JDK 28 makes it final. The same rule fits a Temporal activity that fans out: when Temporal cancels or times out the activity, a scope makes sure its HTTP calls stop with it instead of finishing in the background. For context, look at your MDC: SLF4J's MDC is a `ThreadLocal`, so log lines written inside forked subtasks lose the correlation id unless you copy it in, and a pooled thread that skips `MDC.clear()` tags the next request with the wrong id.",
 "mistake": "The most common mistake is copying `StructuredTaskScope` code written for a different JDK. `new StructuredTaskScope.ShutdownOnFailure()` with `join().throwIfFailed()` is the JDK 21 to 24 API and doesn't compile on JDK 25. JDK 25 code that catches `FailedException` stops compiling on JDK 27, where `join()` throws `ExecutionException`. And `--enable-preview` only works with the JDK's own release, so a preview API ties the whole build to one JDK version. Pin the JDK version in any code that uses the preview, and keep that code small and in one place. For production services on JDK 25, use a plain executor with explicit cancellation (or a small scope like the lab's), and switch to the JDK's scope when JDK 28 makes it final.",
 "compare": {
  "title": "Request context that follows the subtasks",
  "java": {"title": "Java: ScopedValue plus a scope (JDK 25, scope in preview)", "src": "static final ScopedValue<String> TENANT = ScopedValue.newInstance();   // final in JDK 25\n\nStatement statement(Request req) throws Exception {\n    return ScopedValue.where(TENANT, req.tenant()).call(() -> {          // bound for this call\n        try (var scope = StructuredTaskScope.open()) {                   // preview in JDK 25\n            Subtask<Customer> customer = scope.fork(() -> crm.find(req.customerId()));\n            Subtask<Balance> balance = scope.fork(() -> ledger.balance(ledgerKey(req.account())));\n            scope.join();\n            return new Statement(customer.get(), balance.get());\n        }\n    });\n}\n\nstatic String ledgerKey(String account) {\n    return TENANT.get() + \":\" + account;   // the fork reads the parent's binding\n}"},
  "kotlin": {"title": "Kotlin: a coroutine context element", "src": "// the coroutine carries the context, not the thread\nclass Tenant(val id: String) : AbstractCoroutineContextElement(Tenant) {\n    companion object Key : CoroutineContext.Key<Tenant>\n}\n\nsuspend fun statement(req: Request): Statement = withContext(Tenant(req.tenant)) {   // bound for this block\n    val customer = async { crm.find(req.customerId) }\n    val balance = async { ledger.balance(ledgerKey(req.account)) }      // children inherit the context\n    Statement(customer.await(), balance.await())\n}\n\nsuspend fun ledgerKey(account: String): String =\n    (currentCoroutineContext()[Tenant]?.id ?: error(\"no tenant\")) + \":\" + account"},
  "note": "Both are immutable context that children inherit and that ends with the block. The difference is what carries it. A scoped value is bound to a thread's call stack, and only `StructuredTaskScope` forks inherit it. A coroutine context element is bound to the coroutine, so it survives a coroutine moving to another thread at a suspension point, and every child started with `launch` or `async` inherits it. That is why scoped values and `ThreadLocal`s are the wrong tool inside suspending code: a coroutine can resume on a different thread, where the binding isn't there. In Kotlin coroutine code, put context in the coroutine context. Use `ScopedValue` from Kotlin only in plain blocking code on threads."
 },
 "worked": {
  "title": "Make an authorization fan-out fail fast",
  "steps": [
   {"say": "An authorization needs a fraud score and the card's open-to-buy amount. Both are blocking HTTP calls. The code runs on a shared executor field, and the request id lives in a `ThreadLocal` for logging. Read it and list what goes wrong when the fraud call fails.",
    "code": "Auth authorize(Payment p) throws Exception {\n    REQUEST_ID.set(p.requestId());                                   // a ThreadLocal\n    Future<Score> fraud = shared.submit(() -> fraudApi.score(p));    // 300 ms\n    Future<Money> open = shared.submit(() -> cards.openToBuy(p));    // 80 ms\n    return decide(fraud.get(), open.get());\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "fun authorize(p: Payment): Auth {\n    REQUEST_ID.set(p.requestId)                                       // a ThreadLocal\n    val fraud = shared.submit(Callable { fraudApi.score(p) })         // 300 ms\n    val open = shared.submit(Callable { cards.openToBuy(p) })         // 80 ms\n    return decide(fraud.get(), open.get())\n}"},
   {"say": "Three problems. If the card call fails, `fraud.get()` still waits up to 300 ms first. If the fraud call fails, the card call keeps running after `authorize` has thrown. And both subtasks log without the request id, because `REQUEST_ID` is set on the handler's thread only. On a pooled handler thread it is also never cleared."},
   {"say": "On JDK 25 without preview, use a scope that owns its threads, like the lab's `FailFastScope`, and pass the request id as an argument. Every subtask now ends before `authorize` returns, and the first failure cancels the other call.",
    "code": "Auth authorize(Payment p) throws Exception {\n    try (var scope = new FailFastScope()) {                 // 1. open: owns the subtasks\n        String rid = p.requestId();                         // 2. context as a plain argument\n        Supplier<Score> fraud = scope.fork(() -> fraudApi.score(p, rid));\n        Supplier<Money> open = scope.fork(() -> cards.openToBuy(p, rid));\n        scope.join();                                       // 3. first failure cancels the other\n        return decide(fraud.get(), open.get());\n    }                                                       // 4. close: nothing left running\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "fun authorize(p: Payment): Auth =\n    FailFastScope().use { scope ->                          // 1. open: owns the subtasks\n        val rid = p.requestId                               // 2. context as a plain argument\n        val fraud = scope.fork { fraudApi.score(p, rid) }\n        val open = scope.fork { cards.openToBuy(p, rid) }\n        scope.join()                                        // 3. first failure cancels the other\n        decide(fraud.get(), open.get())\n    }                                                       // 4. close: nothing left running"},
   {"say": "On JDK 25 with `--enable-preview`, the JDK's scope does the same job, and a scoped value carries the request id into both forks. No method signature has to change.",
    "code": "static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();\n\nAuth authorize(Payment p) throws Exception {\n    return ScopedValue.where(REQUEST_ID, p.requestId()).call(() -> {     // 1. bind the context\n        try (var scope = StructuredTaskScope.open()) {                   // 2. fail-fast scope\n            Subtask<Score> fraud = scope.fork(() -> fraudApi.score(p));  //    forks read REQUEST_ID\n            Subtask<Money> open = scope.fork(() -> cards.openToBuy(p));\n            scope.join();                                                // 3. FailedException on JDK 25\n            return decide(fraud.get(), open.get());\n        }                                                                // 4. close: nothing left running\n    });\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "val REQUEST_ID: ScopedValue<String> = ScopedValue.newInstance()\n\nfun authorize(p: Payment): Auth =\n    ScopedValue.where(REQUEST_ID, p.requestId).call<Auth, Exception> {   // 1. bind the context\n        StructuredTaskScope.open<Any>().use { scope ->                    // 2. fail-fast scope\n            val fraud = scope.fork(Callable { fraudApi.score(p) })        //    forks read REQUEST_ID\n            val open = scope.fork(Callable { cards.openToBuy(p) })\n            scope.join()                                                  // 3. FailedException on JDK 25\n            decide(fraud.get(), open.get())\n        }                                                                 // 4. close: nothing left running\n    }"},
   {"say": "When you move to JDK 27 or 28, change the error handling where you call `authorize`: catch `ExecutionException` from `join()` instead of `StructuredTaskScope.FailedException`. The fork, join and close lines stay the same."}
  ]
 },
 "lab": {
  "title": "Build a fail-fast scope on an executor",
  "minutes": 14,
  "files": [f"{lab}/main/{P}/FailFastScope.java"],
  "run": "./gradlew :vthreads:test --tests 'workbench.vthreads.l05.*'",
  "steps": [
   "Run the tests once. All seven fail with `UnsupportedOperationException`. Read the class comment in `FailFastScope`: it lists the rules the tests check.",
   "Add the state as fields: an `ExecutorService` from `Executors.newVirtualThreadPerTaskExecutor()`, a `CopyOnWriteArrayList<Future<?>>`, an `AtomicReference<Throwable>` for the first failure and a `volatile boolean joined`.",
   "Write `fork`. Submit a `Callable` that runs `task.call()` in a try. In the catch, record the failure with `compareAndSet(null, failure)`; if that wins, call `executor.shutdownNow()` to interrupt the siblings. Rethrow. Add the future to the list and return a `Supplier` that throws `IllegalStateException` until `join()` has run, then returns `future.resultNow()`.",
   "Handle a fork after cancellation: once the executor is shut down, `submit` throws `RejectedExecutionException`. Catch it and return a handle whose `get()` always throws `IllegalStateException`.",
   "Write `join`: call `get()` on each future in order, ignore `ExecutionException` and `CancellationException`, and stop as soon as a failure is recorded. Set `joined`, then throw `new ExecutionException(failure)` if there was one. Write `close`: `shutdownNow()`, then `close()` on the executor.",
   "Run the tests until all seven pass, then run them twice more."
  ],
  "hints": [
   "Why `compareAndSet`? The siblings you interrupt fail too, with `InterruptedException`. They fail after the real failure is recorded, so their `compareAndSet(null, ...)` returns `false` and they don't replace it.",
   "Don't cancel with `future.cancel(true)`. A cancelled future counts as done at once, and on JDK 21 the executor then stops waiting for that thread while its `finally` block still runs. The `close()` test catches exactly that. `shutdownNow()` interrupts the threads and leaves the futures alone.",
   "`catch (Throwable failure) { ...; throw failure; }` compiles inside the submitted lambda: Java's precise rethrow knows `task.call()` can only throw an `Exception`.",
   "`Future.resultNow()` (JDK 19 and later) returns the result of a task that succeeded and throws `IllegalStateException` for one that failed or was cancelled, which is what a handle needs after `join()`."
  ],
  "done_when": "All seven tests in `FailFastScopeTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Write the JDK 25 scope from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `Quote quote(String id)` that loads a customer and a credit limit at the same time with `StructuredTaskScope` (JDK 25 preview), fails fast, and closes cleanly. Then write the catch clause a caller needs on JDK 25, and the one it needs on JDK 27.",
  "answer": {"lang": "java", "src": "Quote quote(String id) throws InterruptedException {\n    try (var scope = StructuredTaskScope.open()) {                  // default: fail on the first failure\n        Subtask<Customer> customer = scope.fork(() -> crm.find(id));\n        Subtask<Limit> limit = scope.fork(() -> limits.check(id));\n        scope.join();                                               // throws if a subtask failed\n        return new Quote(customer.get(), limit.get());              // get() only after join()\n    }                                                               // close() waits for every subtask\n}\n\n// a caller on JDK 25\ntry {\n    return quote(id);\n} catch (StructuredTaskScope.FailedException e) {     // unchecked; the cause is the subtask's exception\n    throw new QuoteUnavailableException(e.getCause());\n}\n// on JDK 27 and later, join() throws the checked ExecutionException instead:\n// } catch (ExecutionException e) { throw new QuoteUnavailableException(e.getCause()); }",
             "alt": {"lang": "kotlin", "src": "fun quote(id: String): Quote =\n    StructuredTaskScope.open<Any>().use { scope ->                 // default: fail on the first failure\n        val customer = scope.fork(Callable { crm.find(id) })\n        val limit = scope.fork(Callable { limits.check(id) })\n        scope.join()                                               // throws if a subtask failed\n        Quote(customer.get(), limit.get())                         // get() only after join()\n    }                                                              // close() waits for every subtask\n\n// a caller on JDK 25\ntry {\n    return quote(id)\n} catch (e: StructuredTaskScope.FailedException) {    // the cause is the subtask's exception\n    throw QuoteUnavailableException(e.cause)\n}\n// on JDK 27 and later, catch ExecutionException instead:\n// } catch (e: ExecutionException) { throw QuoteUnavailableException(e.cause) }"}}
 },
 "recap": [
  "An executor fan-out doesn't cancel the other tasks when one fails, and with a shared executor they outlive the request.",
  "Structured concurrency ties subtasks to a block: fork, join, and a close that guarantees every subtask has ended.",
  "Fail fast means the first failure interrupts the siblings and `join()` throws it. Built by hand, `close()` must wait for the threads, not for the futures.",
  "`StructuredTaskScope` is preview in JDK 25 to 27: `open()`, a `Joiner` and `FailedException` in 25, `ExecutionException` from JDK 27. JDK 28 makes it final.",
  "Scoped values are final in JDK 25: bound for one call with `where(...).run(...)`, read-only, gone afterwards, and inherited only by `StructuredTaskScope` forks.",
  "A `ThreadLocal` used for context is mutable, leaks on pooled threads without `remove()`, and is copied by `InheritableThreadLocal`."
 ],
 "quiz": [
  {"q": "You compile on JDK 25 with `--enable-preview`. Which fan-out compiles and fails fast?",
   "options": [
    "`try (var scope = new StructuredTaskScope.ShutdownOnFailure()) { ...; scope.join().throwIfFailed(); }`",
    "`try (var scope = StructuredTaskScope.open()) { ...; scope.join(); }`, with callers catching `StructuredTaskScope.FailedException`",
    "`try (var scope = StructuredTaskScope.open()) { ...; scope.join(); } catch (ExecutionException e) { ... }`",
    "`try (var scope = Executors.newStructuredTaskScope()) { ...; scope.join(); }`"
   ], "answer": 1,
   "why": "JDK 25 (JEP 505) uses the static `open()` factory, and its default joiner makes `join()` throw the unchecked `FailedException`. `ShutdownOnFailure` is the JDK 21 to 24 API and no longer exists. Catching the checked `ExecutionException` is the JDK 27 shape; on JDK 25 nothing in the try block throws it, so javac rejects the catch. There is no `Executors.newStructuredTaskScope()`."},
  {"q": "What does this print on JDK 25?\n\n```java\nstatic final ScopedValue<String> ID = ScopedValue.newInstance();\n\nScopedValue.where(ID, \"a\").run(() -> {\n    ScopedValue.where(ID, \"b\").run(() -> System.out.print(ID.get()));\n    System.out.print(ID.get());\n});\nSystem.out.print(ID.orElse(\"-\"));\n```",
   "options": ["`bb-`", "`ab-`", "`ba-`", "`bab`"], "answer": 2,
   "why": "The inner `where` rebinds `ID` to `b` for the nested call only. When it returns, the outer binding `a` is back, and after the outer `run()` nothing is bound, so `orElse` gives `-`. There is no `set()` that could leave `b` behind, which is the difference from a `ThreadLocal`."},
  {"q": "Inside `ScopedValue.where(TENANT, \"bank-a\").run(...)`, a handler submits a task to `Executors.newVirtualThreadPerTaskExecutor()`. What does `TENANT.isBound()` return inside that task?",
   "options": [
    "`false`: only subtasks forked in a `StructuredTaskScope` see the parent's binding",
    "`true`: every virtual thread inherits its creator's scoped values",
    "`true`, but only if the task starts before `run()` returns",
    "It throws `IllegalStateException`, because scoped values can't be read on virtual threads"
   ], "answer": 0,
   "why": "Scoped value bindings flow only into threads forked by a `StructuredTaskScope`, whose lifetime is guaranteed to fit inside the binding. A thread started by an executor could outlive the `run()` call, so it gets nothing. Pass the value as an argument there. The second option describes `InheritableThreadLocal`, which copies values into every new thread."},
  {"q": "You want an FX rate from whichever of two providers answers first, and the slower call cancelled. Which tool fits?",
   "options": [
    "`CompletableFuture.anyOf(primary, backup)`",
    "`StructuredTaskScope.open()` with the default joiner",
    "`StructuredTaskScope.open(Joiner.allSuccessfulOrThrow())`",
    "`StructuredTaskScope.open(Joiner.anySuccessfulResultOrThrow())` (JDK 25 name)"
   ], "answer": 3,
   "why": "`anySuccessfulResultOrThrow` (renamed `anySuccessfulOrThrow` in JDK 26) returns the first successful result and cancels the rest. `CompletableFuture.anyOf` completes with the first result but cancels nothing, so the slower call runs to the end. The default joiner and `allSuccessfulOrThrow` both wait for every subtask to succeed."},
  {"q": "From the lesson \"Callable, Future, cancellation and interruption\": a fail-fast scope cancels a sibling that runs `while (true) { total = total.add(nextChunk(buffer)); }`, pure computation that never blocks and never checks the interrupt flag. What happens to that sibling?",
   "options": [
    "It stops at once, because cancelling a subtask kills its thread",
    "It keeps running: cancellation only interrupts, and this loop never looks",
    "It stops at its next loop iteration, because virtual threads check the flag automatically",
    "The JVM throws `InterruptedException` inside `add`"
   ], "answer": 1, "from": "exec-04",
   "why": "Cancellation in Java is cooperative. `cancel(true)`, `shutdownNow()` and a scope's cancel all just set the interrupt flag. Blocking calls react by throwing `InterruptedException`; a loop that never blocks must check `Thread.currentThread().isInterrupted()` itself. A scope's `close()` would wait for this loop forever."}
 ],
 "flashcards": [
  {"front": "What does structured concurrency guarantee when the block that opened a scope ends?", "back": "Every subtask forked in the scope has finished. None is still running, whether the block returned, threw or was interrupted."},
  {"front": "In a fail-fast scope, what happens to the other subtasks when one fails?", "back": "They are cancelled, which means interrupted. `join()` throws the first failure."},
  {"front": "What does `join()` throw on JDK 25 when a subtask fails in `StructuredTaskScope.open()`?", "back": "`StructuredTaskScope.FailedException` (unchecked), with the subtask's exception as its cause. From JDK 27 the built-in joiners throw `ExecutionException`."},
  {"front": "Is `StructuredTaskScope` final in JDK 25?", "back": "No. It is a preview API in JDK 25, 26 and 27 and needs `--enable-preview`. JEP 543 makes it final in JDK 28."},
  {"front": "Are scoped values final in JDK 25?", "back": "Yes, since JDK 25 (JEP 506). They need no flag."},
  {"front": "Which threads can read a scoped value's binding?", "back": "Code running inside `where(...).run(...)` or `call(...)`, and subtasks forked in a `StructuredTaskScope` opened there. Not threads you start yourself and not executor tasks."},
  {"front": "Why can't a hand-built scope cancel with `future.cancel(true)` and rely on `executor.close()` to wait?", "back": "A cancelled future is done at once, so on JDK 21 the executor stops waiting for that thread while it still runs its `finally`. Use `shutdownNow()`, which interrupts without completing the futures."}
 ],
 "terms": [
  {"term": "Structured concurrency", "plain": "Concurrent subtasks are tied to the block that started them and can't outlive it."},
  {"term": "Scope", "plain": "The object that forks subtasks, joins them, and on close guarantees they have all ended."},
  {"term": "Fail fast", "plain": "The first failure cancels the remaining subtasks and is reported at once."},
  {"term": "Joiner", "plain": "The policy you pass to `StructuredTaskScope.open`: when `join()` returns and what it returns or throws."},
  {"term": "Scoped value", "plain": "A read-only value bound for the length of one call and visible to all the code that call runs."},
  {"term": "Preview API", "plain": "A complete JDK API that is not final yet. It needs `--enable-preview` and can change in the next release."}
 ],
 "explain_back": {
  "prompt": "A colleague says that try-with-resources around `newVirtualThreadPerTaskExecutor()` already gives you structured concurrency. Explain what it gives you, what it is missing, and what `StructuredTaskScope` and scoped values add.",
  "answer": "It gives you half of it. When the block ends, `close()` waits for every task, so no task outlives the method. What it lacks is a failure policy: when one task fails, nothing cancels the others, so a failed request still waits for the slowest call, and you must write `cancel` calls on every error path yourself. Hand-built cancellation also has traps, such as `close()` not waiting for a task you cancelled with `cancel(true)`. `StructuredTaskScope` adds the policy (the first failure cancels the siblings, or another `Joiner` such as first success wins), timeouts, and checks that scopes nest properly, and its `close()` always waits for the threads. It is still preview until JDK 28. Scoped values, final in JDK 25, add context that flows into the scope's subtasks without copying, can't be changed by callees, and disappears when the call ends, unlike a `ThreadLocal`."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Custom joiners.** A `Joiner` has two hooks, `onFork` and `onComplete`, and a `result()` method that `join()` calls at the end. `onComplete` returns `true` to cancel the scope. That is enough for policies the built-in joiners don't cover, such as \"stop once three of five ledger replicas agree\" or \"collect successes and ignore failures\". `onComplete` runs on the thread of the subtask that just finished, so a joiner's state must be thread-safe. Check the Javadoc of the exact JDK you use, because JDK 26 changed the hook signatures slightly.\n\n**Why `CompletableFuture` doesn't solve this.** `allOf` waits for everything even after one future fails, and `cancel(true)` on a `CompletableFuture` doesn't interrupt the thread doing the work: it only completes the future. The lesson \"CompletableFuture: errors, timeouts and fan-out\" builds fan-out that way; notice how much code its error handling needs compared with a scope.\n\n**Kotlin already has this.** In coroutine code, `coroutineScope { async { } }` gives the same guarantees without a preview flag: children can't outlive the scope, the first failure cancels the siblings, and cancellation reaches each child at its next suspension point. The coroutines track covers it. `StructuredTaskScope` matters most for Java code and for Kotlin code that blocks on threads.\n\n**Scoped values and virtual threads.** A `ThreadLocal` costs a map entry per thread, and with a million virtual threads that adds up, as lesson 4 of this track showed. A scoped value binding is attached to the call, not copied per thread, and its forks share it. That makes it the natural fit for one virtual thread per request with many short subtasks.\n\n**Old articles.** Before JDK 25 the API was `StructuredTaskScope.ShutdownOnFailure` and `ShutdownOnSuccess`, subclasses you created with `new`. Scoped values had static helpers such as `ScopedValue.runWhere`, which were removed during the previews. If a snippet uses either, it was written for an older preview."
 },
 "sources": [
  {"title": "JEP 505: Structured Concurrency (Fifth Preview)", "url": "https://openjdk.org/jeps/505"},
  {"title": "JEP 506: Scoped Values", "url": "https://openjdk.org/jeps/506"},
  {"title": "JEP 533: Structured Concurrency (Seventh Preview)", "url": "https://openjdk.org/jeps/533"},
  {"title": "Structured Concurrency (Java SE 25 Core Libraries guide)", "url": "https://docs.oracle.com/en/java/javase/25/core/structured-concurrency.html"}
 ]
}
out = ROOT / "content/lessons/vt-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
