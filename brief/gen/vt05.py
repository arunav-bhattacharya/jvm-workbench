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


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="Two timelines of the same checkout. With a shared executor, the checkout fails at 100 ms but its bank subtask keeps running until 2 seconds. With a scope, the failure cancels the bank subtask, and close waits for it, so nothing outlives the block.">'
    '<text class="t-s t-m" x="20" y="22">A shared executor: the checkout ends, its subtask does not</text>'
    '<rect class="box" x="60" y="34" width="150" height="26" rx="8"/>'
    '<text class="t-s" x="135" y="51" text-anchor="middle">checkout</text>'
    '<rect class="box-bad" x="60" y="66" width="150" height="26" rx="8"/>'
    '<text class="t-s" x="135" y="83" text-anchor="middle">stock: fails</text>'
    '<rect class="box" x="60" y="98" width="150" height="26" rx="8"/>'
    '<text class="t-s" x="135" y="115" text-anchor="middle">bank</text>'
    '<rect class="box-bad" x="214" y="98" width="446" height="26" rx="8"/>'
    '<text class="t-s t-bad" x="437" y="115" text-anchor="middle">the bank call keeps going after the checkout failed</text>'
    '<line class="ln-d" x1="60" y1="138" x2="660" y2="138" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="60" y="154" text-anchor="middle">0</text>'
    '<text class="t-s t-m" x="210" y="154" text-anchor="middle">100 ms</text>'
    '<text class="t-s t-m" x="640" y="154" text-anchor="middle">2 s</text>'
    '<text class="t-s t-m" x="20" y="182">A scope: no subtask outlives the block</text>'
    '<rect class="box-a" x="48" y="192" width="182" height="102" rx="8"/>'
    '<rect class="box" x="60" y="200" width="150" height="26" rx="8"/>'
    '<text class="t-s" x="135" y="217" text-anchor="middle">checkout</text>'
    '<rect class="box-bad" x="60" y="232" width="150" height="26" rx="8"/>'
    '<text class="t-s" x="135" y="249" text-anchor="middle">stock: fails</text>'
    '<rect class="box-ok" x="60" y="264" width="150" height="26" rx="8"/>'
    '<text class="t-s" x="135" y="281" text-anchor="middle">bank: interrupted</text>'
    '<text class="t-s" x="250" y="217">stock fails at 100 ms, so the scope cancels the bank call</text>'
    '<text class="t-s" x="250" y="249">join() throws, and close() waits for the bank call to end</text>'
    '<text class="t-s t-ok" x="250" y="281">the checkout ends with nothing left running</text>'
    '</svg>'
)

OPENING = """Picture a big table at the restaurant, looked after by a head waiter. The table orders, and he sends three helpers at once: one to the kitchen for the soup, one to the bar for the drinks, one to the cellar for a bottle of wine. Then he stays at the table until all three are back, so nobody is forgotten.

Now the cellar is out of that wine, and its helper comes straight back. The table changes its order. A careful head waiter calls the other two helpers back at once. A careless one lets them carry on, and a soup arrives for an order that no longer exists.

Lesson 3's fan-out is the careless head waiter. It waits for every helper, which looks complete, so the trap is easy to miss. But when one helper fails, nothing calls the others back. Lesson 4 left a second gap: a `ThreadLocal` doesn't follow the work into the helpers.

In this lesson, we'll watch a failed checkout keep working, build a scope that calls the helpers back, meet the JDK's own scope and pin a note to the order. Before we start, make a guess, and keep it in mind."""

S0 = """Let's set up the example first. A **fan-out**, from lesson 3 of this track, starts several calls at once and then collects all their answers. Each call is a **subtask**: a piece of a bigger job that runs on a thread of its own, here a virtual thread, the cheap kind the JDK sets aside whenever it waits. To save time, the shop's checkout now asks two services at the same moment instead of one after the other. The stock service says whether the items are in the warehouse, and the bank says whether the payment is approved. If the items are sold out, the bank's answer is useless.

Here is that fan-out in the lesson 3 shape. An **executor** is an object that runs tasks for you, and `submit` hands back a `Future`, a handle on a result that arrives later:

""" + pair(
"""try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
    Future<Approval> bank = perTask.submit(() -> theBank.approve(order));    // 2 s on a bad day
    Future<Stock> stock = perTask.submit(() -> stockService.check(order));   // fails at 100 ms: sold out
    return new Receipt(stock.get(), bank.get());
}""",
"""Executors.newVirtualThreadPerTaskExecutor().use { perTask ->
    val bank = perTask.submit(Callable { theBank.approve(order) })     // 2 s on a bad day
    val stock = perTask.submit(Callable { stockService.check(order) }) // fails at 100 ms: sold out
    Receipt(stock.get(), bank.get())
}""") + """

Predict when the checkout fails. The stock service says "sold out" after 100 ms, so a careful program would give up at 100 ms. `LeakDemo`, in the Try it below, runs this exact shape as variant A:

```text
A: an executor per checkout, closed by try-with-resources
  2,027 ms  bank: answered, but nobody needs the answer
  2,069 ms  checkout failed: stock service: sold out
```

The checkout was doomed at 100 ms, and it failed at 2 seconds. `stock.get()` threw at 100 ms, as it should. But leaving the try block runs `close()`, which waits for every task, and nothing told the bank call to stop. The bank, true to form, took its full two seconds to answer a question nobody was asking any more.

Many programs keep one long-lived executor in a field instead. `LeakDemo` tries that too, as variant B:

```text
B: one shared executor
    102 ms  checkout failed: stock service: sold out
  2,001 ms  bank: answered, but nobody needs the answer
```

Now the checkout fails fast, at 102 ms. But the bank call runs on for another two seconds, for a checkout that is long gone. It's the helper still in the cellar, fetching wine for a table that has left. A call like that holds a connection, and maybe a permit from lesson 3's semaphore. Under load these orphans pile up, and nothing in a thread dump, the list of every thread a program has, says which checkout they belonged to.

Three things are missing, and they are the same three in every fan-out:

- A failure cancels nothing. To stop the others, you'd call `cancel(true)` on each future, in every fan-out, on every error path.
- The subtasks' lives aren't tied to the code. A `Future` is a value you can store anywhere, so nothing promises that the threads a method started have ended when it returns.
- The order's details don't follow the work. A `ThreadLocal` is a variable with a separate value for each thread, so one set by the checkout, such as the order id for the log, is empty in the subtasks.

**Structured concurrency** fixes the first two with one rule: a subtask can't outlive the block of code that started it, just as a local variable can't outlive its method. Scoped values, at the end of this lesson, fix the third.

**Waiting for every subtask is half the job. When one fails, the others must stop too.**

So we need a head waiter who calls the helpers back. Let's build one."""

S1 = """Here is the head waiter again, part by part. He is the **scope**: an object that starts subtasks and owns them. Sending a helper is **fork**, which starts a subtask on a new virtual thread. Waiting at the table is **join**, which waits for the subtasks. Calling the others back when one returns with bad news is **fail fast**: the first failure cancels the rest, and `join` reports it at once. And not leaving the table until every helper is back is **close**. When the block ends, every thread the scope started has ended, whether the block returned, threw or was interrupted.

In code the shape is always the same. Both versions use this lesson's lab class, `FailFastScope`, a small scope you build yourself on a plain executor:

""" + pair(
"""try (var scope = new FailFastScope()) {                                   // the head waiter
    Supplier<Approval> bank = scope.fork(() -> theBank.approve(order));
    Supplier<Stock> stock = scope.fork(() -> stockService.check(order));
    scope.join();                                                         // waits, or throws the first failure
    return new Receipt(stock.get(), bank.get());
}                                                                         // close(): no subtask is still running""",
"""FailFastScope().use { scope ->                                            // the head waiter
    val bank = scope.fork { theBank.approve(order) }
    val stock = scope.fork { stockService.check(order) }
    scope.join()                                                          // waits, or throws the first failure
    Receipt(stock.get(), bank.get())
}                                                                         // close(): no subtask is still running""") + """

Read it aloud: send two helpers, wait for both or for the first bad news, and don't leave until they're back. `fork` returns a handle, a `Supplier` whose `get()` gives the subtask's result after `join`.

Let's trace the smallest case, with the stock check failing and the bank slow:

- At 0 ms, the scope forks both subtasks, each on a new virtual thread.
- At 100 ms, the stock subtask throws. Its wrapper records the failure as the first one and cancels the scope.
- Cancel means interrupt: a signal that wakes a waiting thread with an `InterruptedException`. The bank subtask, blocked in a network read, wakes up that way.
- The bank subtask's failure arrives second, so it doesn't replace the first.
- `join()` sees the first failure and throws it, at about 100 ms.
- `close()` waits until the bank thread has really finished.
- A subtask forked after the cancel never runs, and its handle throws if you ask for a result.

How does the lab do this? Each forked task runs inside a small wrapper. If the task throws, the wrapper records the failure with `AtomicReference.compareAndSet(null, failure)`, read as "store it only if nobody stored one first", so exactly one failure wins. Then it calls `shutdownNow()` on the executor, which interrupts every running subtask and refuses new ones.

An interrupt stops code that waits in `sleep`, a network read, a lock or a queue, which covers almost all waiting on virtual threads. It doesn't stop a loop that computes and never checks the interrupt flag. In Java, cancelling is a request the code has to cooperate with. Here the head waiter picture breaks: a real helper hears his name called, but a subtask that never waits and never checks hears nothing.

One detail looks right and is wrong. You might cancel each sibling with `future.cancel(true)`. That interrupts the thread, but it also marks the future as done at once. On JDK 21, `newVirtualThreadPerTaskExecutor` counts a task as finished as soon as its future is done. So `close()` can return while the cancelled task still runs its `finally` block, giving back a permit, say. `shutdownNow()` interrupts without touching the futures, so `close()` keeps waiting until each thread has truly ended. The lab's `close()` test catches exactly this bug, which is a good reason to prefer the JDK's own scope once you can use it.

**A subtask must never outlive the block that forked it. Make the scope wait for threads, not for futures.**

Check yourself: in your `FailFastScope`, the stock check fails at 100 ms. The bank call is blocked in a network read, and a third subtask runs a 3-second loop that computes and never checks the interrupt flag. When does `join()` throw, and when does `close()` return? `join()` throws at about 100 ms with the stock failure. `close()` returns at about 3 seconds: the interrupt stops the network read but not the loop, and `close()` waits for every thread.

We built a head waiter by hand. The JDK has one of its own, still a preview in JDK 25. Let's see what that means."""

S2 = """`StructuredTaskScope`, in `java.util.concurrent`, is the JDK's scope. It's a **preview API**. An API is the set of classes and methods a library offers, and a preview one is finished and fully specified, and still allowed to change its mind in the next release. The compiler and the JVM refuse it unless you pass `--enable-preview`. Its current shape arrived in JDK 25 (JEP 505, the fifth preview). It stayed a preview in JDK 26 (JEP 525) and JDK 27 (JEP 533). JEP 543 makes it final in JDK 28, due in March 2027, with the JDK 27 API unchanged. So the Gradle labs, which must run on JDK 21, leave it out, and this lesson's demo lives in `labs/vthreads/preview/` as a single-file program for JDK 25.

Here is the checkout in the JDK 25 shape:

""" + pair(
"""Receipt checkout(Order order) throws InterruptedException {
    try (var scope = StructuredTaskScope.open()) {          // fail on the first failure
        Subtask<Approval> bank = scope.fork(() -> theBank.approve(order));
        Subtask<Stock> stock = scope.fork(() -> stockService.check(order));
        scope.join();               // JDK 25: throws StructuredTaskScope.FailedException
        return new Receipt(stock.get(), bank.get());
    }                               // close(): cancels what is left and waits for it
}""",
"""fun checkout(order: Order): Receipt =
    StructuredTaskScope.open<Any>().use { scope ->            // fail on the first failure
        val bank = scope.fork(Callable { theBank.approve(order) })
        val stock = scope.fork(Callable { stockService.check(order) })
        scope.join()               // JDK 25: throws StructuredTaskScope.FailedException
        Receipt(stock.get(), bank.get())
    }                              // close(): cancels what is left and waits for it""") + """

It has the same shape as `FailFastScope`, with stricter rules. Subtasks run on virtual threads. Calling `get()` before `join()` throws `IllegalStateException`. Scopes must nest like blocks, and the JDK checks that you close them in that order. And a thread dump written as JSON, a structured text format (`jcmd <pid> Thread.dump_to_file -format=json threads.json`), groups each scope's threads under it, so you can see which checkout a thread belongs to.

`ScopeDemo`, in the Try it below, is `LeakDemo`'s checkout written this way. Predict the timeline first. On JDK 25, run from `labs/`, it printed:

```text
$ java --enable-preview --source 25 vthreads/preview/ScopeDemo.java
    135 ms  [order-42] bank: interrupted, stopped early
    165 ms  [order-42] checkout failed: stock service: sold out
    165 ms  [-] done: the binding has ended, and no subtask is still running
```

That's the careful head waiter. The stock failure cancelled the bank call, `join()` threw at once, and nothing was still running when the block ended. The times are a little over 100 ms because the first run also loads the classes it needs. The `[order-42]` on each line comes from a scoped value, the topic of the next section.

Leave out the flag, and javac, the Java compiler, stops at the first line that uses the API: `error: StructuredTaskScope is a preview API and is disabled by default`. Kotlin's compiler doesn't check for preview APIs, and on JDK 25 the Kotlin jar even ran without the flag here. Don't lean on that: the API can change in the next JDK, flag or no flag.

The scope's policy is a **joiner**, an object you pass to `open` that decides when `join()` returns and what it gives back. JDK 25 has four built in:

- `Joiner.awaitAllSuccessfulOrThrow()`, the default: fail fast, and `join()` returns `null`.
- `Joiner.allSuccessfulOrThrow()`: fail fast, and `join()` returns the subtasks as a `Stream<Subtask<T>>`.
- `Joiner.anySuccessfulResultOrThrow()`: the first success wins, and the scope cancels the rest.
- `Joiner.awaitAll()`: wait for everything and never throw. You check each subtask's `state()`.

A second argument changes the scope's settings, such as a timeout. Here the shop asks two delivery companies for a price and takes whichever answers first:

""" + pair(
"""try (var scope = StructuredTaskScope.open(Joiner.<Price>anySuccessfulResultOrThrow(),
        cf -> cf.withTimeout(Duration.ofMillis(300)))) {
    scope.fork(() -> fastPost.price(parcel));
    scope.fork(() -> cheapPost.price(parcel));
    return scope.join();        // the first price back; the slower call is cancelled
}""",
"""StructuredTaskScope.open(Joiner.anySuccessfulResultOrThrow<Price>()) { cf ->
    cf.withTimeout(Duration.ofMillis(300))
}.use { scope ->
    scope.fork(Callable { fastPost.price(parcel) })
    scope.fork(Callable { cheapPost.price(parcel) })
    scope.join()               // the first price back; the slower call is cancelled
}""") + """

If the 300 ms run out first, the scope cancels both calls, and `join()` throws `StructuredTaskScope.TimeoutException`.

Expect small edits whenever you change JDKs, because that is what preview means. JDK 26 renamed `anySuccessfulResultOrThrow` to `anySuccessfulOrThrow`, and `allSuccessfulOrThrow` now returns a `List` of results. In JDK 27 the built-in joiners make `join()` throw the ordinary checked `ExecutionException`, like `Future.get()`, instead of `FailedException`. Your lab scope already behaves that way. And articles from the JDK 21 days show `new StructuredTaskScope.ShutdownOnFailure()` with `throwIfFailed()`. That API is gone, and it doesn't compile on JDK 25.

**A preview API can change in the next release. Pin the JDK version, and keep preview code small and in one place.**

The scope calls the helpers back. One gap from the first section is left: the order's own details, which a `ThreadLocal` failed to carry into the subtasks."""

S3 = """A checkout carries details that many methods need but few should have to pass along: the order id for the log, or the customer's name for the receipt. The usual tool has been a `ThreadLocal`, the apron pocket from lesson 4 of this track. For this job the pocket has three problems:

- Anyone can write in it. Any code can call `set()`, so the code that reads the value can't tell where it came from.
- Nobody empties it unless someone calls `remove()`. On a pooled thread, a value one task forgot is still there for the next.
- Its inheritance is a copy. An `InheritableThreadLocal` copies its values into every new thread, so that's one copy per subtask, and a later change in the parent never reaches the children.

`ScopedValueDemo`, in the Try it below, shows the second problem first. A task on a one-thread pool sets the customer to `ann` and forgets to remove it. Then the next task on the same thread asks who its customer is:

```text
1. next task, same pool thread: ThreadLocal=ann, ScopedValue=unbound
```

That task never set anything, and it believes it's serving Ann. On a receipt, that's a stranger's name.

A **scoped value** is the replacement. Picture a note pinned to the order: everyone who works on the order can read it, nobody can change it, and it comes off when the order closes. In code, you **bind** a value for the length of one call. Everything that call runs can read it, and nobody can change it. Scoped values are final in JDK 25 (JEP 506), so they need no flag:

""" + pair(
"""static final ScopedValue<String> CUSTOMER = ScopedValue.newInstance();

void handle(Order order) {
    ScopedValue.where(CUSTOMER, order.customer()).run(() -> checkout(order));   // bound only inside run()
}

static String receiptLine(String item) {
    return item + " for " + CUSTOMER.get();     // NoSuchElementException if nobody bound it
}""",
"""val CUSTOMER: ScopedValue<String> = ScopedValue.newInstance()

fun handle(order: Order) {
    ScopedValue.where(CUSTOMER, order.customer).run(Runnable { checkout(order) })   // bound only inside run()
}

fun receiptLine(item: String): String =
    item + " for " + CUSTOMER.get()              // NoSuchElementException if nobody bound it""") + """

Map it back to the note. Pinning the note is `where(...)`, the order being open is the call inside `run()`, reading the note is `get()`, and the note comes off when `run()` returns. There is no `set()`. To use another value for a nested call, bind again with `where(...).run(...)`, and the outer value comes back when that call returns. `isBound()` and `orElse(...)` let code handle the case where nothing is bound, and `call(...)` is the version that returns a value and may throw. The rest of the demo shows each rule:

```text
2. inside run():   ThreadLocal=null, ScopedValue=ann
   after run():    ThreadLocal=null, ScopedValue=unbound
3. nested:         ThreadLocal=null, ScopedValue=ben
   outer again:    ThreadLocal=null, ScopedValue=ann
4. plain thread:   ThreadLocal=null, ScopedValue=unbound
```

The fourth line is the rule to remember. A scoped value flows into subtasks forked in a `StructuredTaskScope`, as `[order-42]` did in `ScopeDemo`. The child doesn't get a copy: it reads the parent's binding, which is safe because nobody can change the binding, and the scope ends before the binding does. A thread you start yourself, or an executor task, could outlive the binding, so it gets nothing. Pass the value as an argument there.

Here the note picture breaks a little. A paper note stays on the order for anyone who picks it up, even a helper borrowed from another table. A scoped value is visible only to code inside the call that bound it, and to that call's own scope.

On JDK 25 that gives a clear split. Use scoped values for new request details today, with no flag. Their flow into subtasks needs `StructuredTaskScope`, which is still a preview. Keep `ThreadLocal` where a library requires it, and clear it in a `finally`.

**Details that belong to one call should live as long as that call. Bind them with a scoped value, and let nobody change them.**

In the lab you build the head waiter itself: `FailFastScope`, on a plain executor, with JDK 21 APIs only."""

CLOSING = """We started with a head waiter who sends helpers and stays at the table until they're back. The executor fan-out stayed too, but it never called anyone back, so a sold-out checkout still waited two seconds for the bank. A scope adds the missing rule: the first failure cancels the rest, and nothing outlives the block. A scoped value is the note pinned to the order.

Now search your own code for a list of `Future`s, and check what happens to the others when one `get()` throws.

Next, we'll move a whole service to virtual threads. Its old pool of 10 threads also kept a limit that nobody wrote down. Which limit, and how do we write it back?"""

L = {
 "id": "vt-05",
 "title": "Structured concurrency and scoped values",
 "minutes": 35,
 "goal": "By the end you can say what structured concurrency guarantees, build fail-fast fork and join on a plain executor, read the JDK 25 `StructuredTaskScope` API and what changes after it, and use scoped values instead of ThreadLocals for a request's details.",
 "opening": OPENING,
 "warmup": {
  "q": "A checkout submits two tasks to `newVirtualThreadPerTaskExecutor()` inside try-with-resources. The bank task takes 2 s. The stock task throws after 100 ms. The checkout calls `stock.get()` first. When does its exception reach the caller?",
  "options": [
   "After about 100 ms: `stock.get()` throws, and the executor cancels the bank task",
   "After about 2 s: `stock.get()` throws at 100 ms, but `close()` waits for the bank task to finish",
   "Never: the executor logs the stock task's exception and returns `null`",
   "After about 100 ms, and the bank task is still running when the caller sees the exception"
  ],
  "answer": 1,
  "why": "`get()` throws at 100 ms, but leaving the try block runs `close()`, which waits for every task. Nothing cancels the bank task, so the failed checkout still takes 2 s. The last option is what happens with a long-lived executor kept in a field: the method fails fast, and the bank task keeps running with nobody waiting for it. The first section runs both."
 },
 "sections": [
  {
   "h": "A failed checkout keeps working: what an executor fan-out leaves out",
   "body": S0,
   "try": {
    "title": "Watch the orphaned call",
    "minutes": 5,
    "steps": [
     "Read `LeakDemo`. Variant A opens an executor per checkout in try-with-resources. Variant B uses one shared executor. For each, predict when the checkout fails and whether the bank call finishes.",
     "Run it with the command below.",
     "Fix variant A by hand. Wrap `stock.get()` in a `try`, call `bank.cancel(true)` in the `catch (ExecutionException e)`, then rethrow `e`. Run it again."
    ],
    "code": demo("LeakDemo"),
    "expect": "A: the bank call finishes at about 2,000 ms, and only then does the checkout fail, although the answer was known at 100 ms (2,027 and 2,069 ms in a run here). B: the checkout fails at about 100 ms (102 ms here), and the bank call still finishes at about 2,000 ms, for a checkout that is long gone. After your fix, A prints `bank: interrupted, stopped early` and fails at about 100 ms (128 ms here). That fixes one fan-out. Every other fan-out in the program needs the same code on every error path."
   },
   "refs": [
    {"title": "ExecutorService (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ExecutorService.html", "kind": "docs"}
   ]
  },
  {
   "h": "The head waiter: a scope that owns its subtasks",
   "body": S1,
   "figure": {"svg": FIG, "caption": "With a shared executor, the failed checkout leaves its bank call running, like a helper still in the cellar. In a scope, the failure cancels it, and close() waits until it has ended."}
  },
  {
   "h": "StructuredTaskScope: the JDK's own scope, still a preview in JDK 25",
   "body": S2,
   "try": {
    "title": "Run the scope on JDK 25",
    "minutes": 6,
    "steps": [
     "This one needs JDK 25 exactly, because `--enable-preview` works only for the JDK's own release. Check with `java -version`. It runs outside Gradle, as a single-file program, from `labs/`.",
     "Run `ScopeDemo` and compare its timeline with `LeakDemo`'s. Look at the `[order-42]` on the bank's line: the subtask can read the checkout's scoped value.",
     "Make `stock()` return `\"in stock\"` after its sleep instead of throwing. Predict how long the checkout takes, then run it.",
     "Now open the scope with a timeout: `StructuredTaskScope.open(Joiner.awaitAllSuccessfulOrThrow(), cf -> cf.withTimeout(Duration.ofMillis(500)))` (in Kotlin, `open(Joiner.awaitAllSuccessfulOrThrow<Any>()) { cf -> cf.withTimeout(Duration.ofMillis(500)) }`). Predict, then run."
    ],
    "code": preview("ScopeDemo", "java --enable-preview --source 25 vthreads/preview/ScopeDemo.java", "scope-demo.jar", "--enable-preview ", "JDK 25 preview"),
    "expect": "First run: a little after 100 ms the bank's line says `interrupted, stopped early`, then `checkout failed: stock service: sold out`, then the `done` line with `[-]`, because the binding has ended (135, 165 and 165 ms in a run here; the Kotlin jar printed 144, 172 and 173 ms). When both succeed, the checkout arrives after about 2,000 ms (2,078 ms here), since the default joiner waits for every subtask. With the 500 ms timeout, the bank is interrupted at about 500 ms and the checkout reports `checkout timed out` (551 ms here). In every case the `done` line comes last: the scope never leaves a subtask running."
   },
   "refs": [
    {"title": "JEP 505: Structured Concurrency (Fifth Preview)", "url": "https://openjdk.org/jeps/505", "kind": "read"},
    {"title": "JEP 533: Structured Concurrency (Seventh Preview)", "url": "https://openjdk.org/jeps/533", "kind": "read"}
   ]
  },
  {
   "h": "A note pinned to the order: scoped values replace request ThreadLocals",
   "body": S3,
   "try": {
    "title": "ThreadLocal and ScopedValue side by side",
    "minutes": 4,
    "steps": [
     "You need JDK 25 or later. Scoped values are final there, so this runs without `--enable-preview`.",
     "Read `ScopedValueDemo` and predict its six lines of output before you run it.",
     "Run it. Then, in part 1, move the first task's work into a `try` and add `CUSTOMER_TL.remove()` in a `finally`. Run it again."
    ],
    "code": preview("ScopedValueDemo", "java vthreads/preview/ScopedValueDemo.java", "sv-demo.jar", "", "JDK 25"),
    "expect": "Line 1 shows `ThreadLocal=ann` in a task that never set it: the value leaked from the previous task on the same pool thread. After your fix it shows `ThreadLocal=null`. The scoped value is `ann` inside `run()` and `unbound` after it, `ben` in the nested call and `ann` again after it. The plain virtual thread prints `unbound`, because only `StructuredTaskScope` forks see the parent's binding. The Java and Kotlin versions print the same six lines."
   },
   "refs": [
    {"title": "JEP 506: Scoped Values", "url": "https://openjdk.org/jeps/506", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "Request details that follow the subtasks",
  "java": {"title": "Java: ScopedValue plus a scope (JDK 25, scope in preview)", "src": "static final ScopedValue<String> CUSTOMER = ScopedValue.newInstance();   // final in JDK 25\n\nReceipt checkout(Order order) throws Exception {\n    return ScopedValue.where(CUSTOMER, order.customer()).call(() -> {     // bound for this call\n        try (var scope = StructuredTaskScope.open()) {                   // preview in JDK 25\n            Subtask<Approval> bank = scope.fork(() -> theBank.approve(order));\n            Subtask<String> line = scope.fork(() -> receiptLine(order.item()));\n            scope.join();\n            return new Receipt(line.get(), bank.get());\n        }\n    });\n}\n\nstatic String receiptLine(String item) {\n    return item + \" for \" + CUSTOMER.get();   // the fork reads the parent's binding\n}"},
  "kotlin": {"title": "Kotlin: a coroutine context element", "src": "// the coroutine carries the details, not the thread\nclass Customer(val name: String) : AbstractCoroutineContextElement(Customer) {\n    companion object Key : CoroutineContext.Key<Customer>\n}\n\nsuspend fun checkout(order: Order): Receipt = withContext(Customer(order.customer)) {   // bound for this block\n    val bank = async { theBank.approve(order) }\n    val line = async { receiptLine(order.item) }        // children inherit the context\n    Receipt(line.await(), bank.await())\n}\n\nsuspend fun receiptLine(item: String): String =\n    item + \" for \" + (currentCoroutineContext()[Customer]?.name ?: error(\"no customer\"))"},
  "note": "Both are read-only details that children inherit and that end with the block. The difference is what carries them. A scoped value is bound to a thread's call stack, and only `StructuredTaskScope` forks inherit it. A coroutine context element is bound to the coroutine, so it survives when the coroutine moves to another thread at a suspension point, and every child started with `launch` or `async` inherits it. That's why scoped values and `ThreadLocal`s are the wrong tool inside suspending code: a coroutine can resume on a different thread, where the binding isn't there. In Kotlin coroutine code, put the details in the coroutine context. Use `ScopedValue` from Kotlin only in plain blocking code on threads, as `ScopedValueDemo.kt` does."
 },
 "worked": {
  "title": "Make the order page fail fast",
  "steps": [
   {"say": "The shop's order page needs two answers: the delivery date from the delivery company's web service (300 ms) and the customer's loyalty points (80 ms). Both are blocking calls. The code runs on a shared executor kept in a field, and the order id lives in a `ThreadLocal` for the log. Read it, and list what goes wrong when one call fails.", "code": "OrderPage show(Order o) throws Exception {\n    ORDER_ID.set(o.id());                                                 // a ThreadLocal\n    Future<LocalDate> date = shared.submit(() -> delivery.estimate(o));   // 300 ms\n    Future<Integer> points = shared.submit(() -> loyalty.points(o));      // 80 ms\n    return new OrderPage(date.get(), points.get());\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "fun show(o: Order): OrderPage {\n    ORDER_ID.set(o.id)                                                    // a ThreadLocal\n    val date = shared.submit(Callable { delivery.estimate(o) })           // 300 ms\n    val points = shared.submit(Callable { loyalty.points(o) })            // 80 ms\n    return OrderPage(date.get(), points.get())\n}"},
   {"say": "Three problems. If the points call fails, `date.get()` still waits up to 300 ms first. If the delivery call fails, the points call keeps running after `show` has thrown. And both subtasks log without the order id, because `ORDER_ID` is set on the handler's thread only. On a pooled handler thread it is also never cleared."},
   {"say": "On JDK 25 without preview, use a scope that owns its threads, like the lab's `FailFastScope`, and pass the order id as an argument. Every subtask now ends before `show` returns, and the first failure cancels the other call.", "code": "OrderPage show(Order o) throws Exception {\n    try (var scope = new FailFastScope()) {                  // 1. open: owns the subtasks\n        String id = o.id();                                  // 2. details as a plain argument\n        Supplier<LocalDate> date = scope.fork(() -> delivery.estimate(o, id));\n        Supplier<Integer> points = scope.fork(() -> loyalty.points(o, id));\n        scope.join();                                        // 3. first failure cancels the other\n        return new OrderPage(date.get(), points.get());\n    }                                                        // 4. close: nothing left running\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "fun show(o: Order): OrderPage =\n    FailFastScope().use { scope ->                           // 1. open: owns the subtasks\n        val id = o.id                                        // 2. details as a plain argument\n        val date = scope.fork { delivery.estimate(o, id) }\n        val points = scope.fork { loyalty.points(o, id) }\n        scope.join()                                         // 3. first failure cancels the other\n        OrderPage(date.get(), points.get())\n    }                                                        // 4. close: nothing left running"},
   {"say": "On JDK 25 with `--enable-preview`, the JDK's scope does the same job, and a scoped value carries the order id into both forks. No method signature has to change.", "code": "static final ScopedValue<String> ORDER_ID = ScopedValue.newInstance();\n\nOrderPage show(Order o) throws Exception {\n    return ScopedValue.where(ORDER_ID, o.id()).call(() -> {               // 1. bind the details\n        try (var scope = StructuredTaskScope.open()) {                   // 2. fail-fast scope\n            Subtask<LocalDate> date = scope.fork(() -> delivery.estimate(o));   // forks read ORDER_ID\n            Subtask<Integer> points = scope.fork(() -> loyalty.points(o));\n            scope.join();                                                // 3. FailedException on JDK 25\n            return new OrderPage(date.get(), points.get());\n        }                                                                // 4. close: nothing left running\n    });\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "val ORDER_ID: ScopedValue<String> = ScopedValue.newInstance()\n\nfun show(o: Order): OrderPage =\n    ScopedValue.where(ORDER_ID, o.id).call<OrderPage, Exception> {      // 1. bind the details\n        StructuredTaskScope.open<Any>().use { scope ->                   // 2. fail-fast scope\n            val date = scope.fork(Callable { delivery.estimate(o) })     //    forks read ORDER_ID\n            val points = scope.fork(Callable { loyalty.points(o) })\n            scope.join()                                                 // 3. FailedException on JDK 25\n            OrderPage(date.get(), points.get())\n        }                                                                // 4. close: nothing left running\n    }"},
   {"say": "When you move to JDK 27 or 28, change the error handling where you call `show`: catch `ExecutionException` from `join()` instead of `StructuredTaskScope.FailedException`. The fork, join and close lines stay the same."}
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
   "Write `fork`. Submit a `Callable` that runs `task.call()` in a `try`. In the `catch`, record the failure with `compareAndSet(null, failure)`, and if that wins, call `executor.shutdownNow()` to interrupt the siblings. Rethrow. Add the future to the list and return a `Supplier` that throws `IllegalStateException` until `join()` has run, then returns `future.resultNow()`.",
   "Handle a fork after a cancel: once the executor is shut down, `submit` throws `RejectedExecutionException`. Catch it and return a handle whose `get()` always throws `IllegalStateException`.",
   "Write `join`: call `get()` on each future in order, ignore `ExecutionException` and `CancellationException`, and stop as soon as a failure is recorded. Set `joined`, then throw `new ExecutionException(failure)` if there was one. Write `close`: `shutdownNow()`, then `close()` on the executor.",
   "Run the tests until all seven pass, then run them twice more."
  ],
  "hints": [
   "Why `compareAndSet`? The siblings you interrupt fail too, with `InterruptedException`. They fail after the real failure is recorded, so their `compareAndSet(null, ...)` returns `false`, and they don't replace it.",
   "Don't cancel with `future.cancel(true)`. A cancelled future counts as done at once, and on JDK 21 the executor then stops waiting for that thread while its `finally` block still runs. The `close()` test catches exactly that. `shutdownNow()` interrupts the threads and leaves the futures alone.",
   "`catch (Throwable failure) { ...; throw failure; }` compiles inside the submitted lambda: Java's precise rethrow knows that `task.call()` can only throw an `Exception`.",
   "`Future.resultNow()` (JDK 19 and later) returns the result of a task that succeeded, and throws `IllegalStateException` for one that failed or was cancelled, which is what a handle needs after `join()`."
  ],
  "done_when": "All seven tests in `FailFastScopeTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Write the JDK 25 scope from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `Receipt checkout(Order order)` that asks the bank and the stock service at the same time with `StructuredTaskScope` (JDK 25 preview), fails fast and closes cleanly. Then write the catch clause a caller needs on JDK 25, and the one it needs on JDK 27.",
  "answer": {"lang": "java", "src": "Receipt checkout(Order order) throws InterruptedException {\n    try (var scope = StructuredTaskScope.open()) {                  // default: fail on the first failure\n        Subtask<Approval> bank = scope.fork(() -> theBank.approve(order));\n        Subtask<Stock> stock = scope.fork(() -> stockService.check(order));\n        scope.join();                                               // throws if a subtask failed\n        return new Receipt(stock.get(), bank.get());                // get() only after join()\n    }                                                               // close() waits for every subtask\n}\n\n// a caller on JDK 25\ntry {\n    return checkout(order);\n} catch (StructuredTaskScope.FailedException e) {     // unchecked; the cause is the subtask's exception\n    throw new CheckoutFailedException(e.getCause());\n}\n// on JDK 27 and later, join() throws the checked ExecutionException instead:\n// } catch (ExecutionException e) { throw new CheckoutFailedException(e.getCause()); }",
             "alt": {"lang": "kotlin", "src": "fun checkout(order: Order): Receipt =\n    StructuredTaskScope.open<Any>().use { scope ->                 // default: fail on the first failure\n        val bank = scope.fork(Callable { theBank.approve(order) })\n        val stock = scope.fork(Callable { stockService.check(order) })\n        scope.join()                                               // throws if a subtask failed\n        Receipt(stock.get(), bank.get())                           // get() only after join()\n    }                                                              // close() waits for every subtask\n\n// a caller on JDK 25\ntry {\n    return checkout(order)\n} catch (e: StructuredTaskScope.FailedException) {    // the cause is the subtask's exception\n    throw CheckoutFailedException(e.cause)\n}\n// on JDK 27 and later, catch ExecutionException instead:\n// } catch (e: ExecutionException) { throw CheckoutFailedException(e.cause) }"}}
 },
 "recap": [
  "An executor fan-out doesn't cancel the other tasks when one fails, and with a shared executor they outlive the request.",
  "Structured concurrency ties subtasks to a block: fork, join, and a close that guarantees every subtask has ended.",
  "Fail fast means the first failure interrupts the siblings and `join()` throws it. Built by hand, `close()` must wait for the threads, not for the futures.",
  "The limit: `StructuredTaskScope` is a preview in JDK 25 to 27 and needs `--enable-preview` (`open()`, a `Joiner` and `FailedException` in 25, `ExecutionException` from 27). JDK 28 makes it final.",
  "Scoped values are final in JDK 25: bound for one call with `where(...).run(...)`, read-only, gone afterwards, and inherited only by `StructuredTaskScope` forks.",
  "A `ThreadLocal` used for a request's details can be changed by anyone, leaks on pooled threads without `remove()`, and is copied by `InheritableThreadLocal`."
 ],
 "quiz": [
  {"q": "You compile on JDK 25 with `--enable-preview`. Which fan-out compiles and fails fast?",
   "options": [
    "`try (var scope = new StructuredTaskScope.ShutdownOnFailure()) { ...; scope.join().throwIfFailed(); }`",
    "`try (var scope = StructuredTaskScope.open()) { ...; scope.join(); }`, with callers catching `StructuredTaskScope.FailedException`",
    "`try (var scope = StructuredTaskScope.open()) { ...; scope.join(); } catch (ExecutionException e) { ... }`",
    "`try (var scope = Executors.newStructuredTaskScope()) { ...; scope.join(); }`"
   ], "answer": 1,
   "why": "JDK 25 (JEP 505) uses the static `open()` factory, and its default joiner makes `join()` throw the unchecked `FailedException`. `ShutdownOnFailure` is the JDK 21 to 24 API and no longer exists, which is why old articles mislead. Catching the checked `ExecutionException` is the JDK 27 shape: on JDK 25 nothing in the try block throws it, so javac rejects the catch. There is no `Executors.newStructuredTaskScope()`."},
  {"q": "What does this print on JDK 25?\n\n```java\nstatic final ScopedValue<String> ID = ScopedValue.newInstance();\n\nScopedValue.where(ID, \"a\").run(() -> {\n    ScopedValue.where(ID, \"b\").run(() -> System.out.print(ID.get()));\n    System.out.print(ID.get());\n});\nSystem.out.print(ID.orElse(\"-\"));\n```",
   "options": ["`bb-`", "`ab-`", "`ba-`", "`bab`"], "answer": 2,
   "why": "The inner `where` binds `ID` to `b` for the nested call only. When it returns, the outer binding `a` is back, and after the outer `run()` nothing is bound, so `orElse` gives `-`. There is no `set()` that could leave `b` behind, which is the difference from a `ThreadLocal`."},
  {"q": "Inside `ScopedValue.where(CUSTOMER, \"ann\").run(...)`, a handler submits a task to `Executors.newVirtualThreadPerTaskExecutor()`. What does `CUSTOMER.isBound()` return inside that task?",
   "options": [
    "`false`: only subtasks forked in a `StructuredTaskScope` see the parent's binding",
    "`true`: every virtual thread inherits its creator's scoped values",
    "`true`, but only if the task starts before `run()` returns",
    "It throws `IllegalStateException`, because scoped values can't be read on virtual threads"
   ], "answer": 0,
   "why": "Bindings flow only into threads forked by a `StructuredTaskScope`, whose lives are sure to end inside the binding. A thread started by an executor could outlive the `run()` call, so it gets nothing. Pass the value as an argument there. The second option describes `InheritableThreadLocal`, which copies values into every new thread."},
  {"q": "The shop asks two delivery companies for a price, wants whichever answers first, and wants the slower call cancelled. On JDK 25, which tool fits?",
   "options": [
    "`CompletableFuture.anyOf(fast, cheap)`",
    "`StructuredTaskScope.open()` with the default joiner",
    "`StructuredTaskScope.open(Joiner.allSuccessfulOrThrow())`",
    "`StructuredTaskScope.open(Joiner.anySuccessfulResultOrThrow())`"
   ], "answer": 3,
   "why": "`anySuccessfulResultOrThrow` (renamed `anySuccessfulOrThrow` in JDK 26) returns the first successful result and cancels the rest. `CompletableFuture.anyOf` completes with the first result but cancels nothing, so the slower call runs to the end. The default joiner and `allSuccessfulOrThrow` both wait for every subtask to succeed."},
  {"q": "From the lesson \"Callable, Future, cancellation and interruption\": a fail-fast scope cancels a sibling that runs `while (true) { total = total.add(nextChunk(buffer)); }`, pure computing that never blocks and never checks the interrupt flag. What happens to that sibling?",
   "options": [
    "It stops at once, because cancelling a subtask kills its thread",
    "It keeps running: cancelling only interrupts, and this loop never looks",
    "It stops at its next loop iteration, because virtual threads check the flag automatically",
    "The JVM throws `InterruptedException` inside `add`"
   ], "answer": 1, "from": "exec-04",
   "why": "Cancelling in Java is cooperative. `cancel(true)`, `shutdownNow()` and a scope's cancel all just set the interrupt flag. Blocking calls react by throwing `InterruptedException`, and a loop that never blocks must check `Thread.currentThread().isInterrupted()` itself. A scope's `close()` would wait for this loop forever."}
 ],
 "flashcards": [
  {"front": "What does structured concurrency guarantee when the block that opened a scope ends?", "back": "Every subtask forked in the scope has finished. None is still running, whether the block returned, threw or was interrupted."},
  {"front": "In a fail-fast scope, what happens to the other subtasks when one fails?", "back": "They are cancelled, which means interrupted. `join()` throws the first failure."},
  {"front": "What does `join()` throw on JDK 25 when a subtask fails in `StructuredTaskScope.open()`?", "back": "`StructuredTaskScope.FailedException` (unchecked), with the subtask's exception as its cause. From JDK 27 the built-in joiners throw `ExecutionException`."},
  {"front": "Is `StructuredTaskScope` final in JDK 25?", "back": "No. It's a preview API in JDK 25, 26 and 27 and needs `--enable-preview`. JEP 543 makes it final in JDK 28."},
  {"front": "Are scoped values final in JDK 25?", "back": "Yes, since JDK 25 (JEP 506). They need no flag."},
  {"front": "Which threads can read a scoped value's binding?", "back": "Code running inside `where(...).run(...)` or `call(...)`, and subtasks forked in a `StructuredTaskScope` opened there. Not threads you start yourself, and not executor tasks."},
  {"front": "Why can't a hand-built scope cancel with `future.cancel(true)` and rely on `executor.close()` to wait?", "back": "A cancelled future is done at once, so on JDK 21 the executor stops waiting for that thread while it still runs its `finally`. Use `shutdownNow()`, which interrupts without completing the futures."}
 ],
 "terms": [
  {"term": "Structured concurrency", "plain": "Subtasks are tied to the block that started them and can't outlive it."},
  {"term": "Subtask", "plain": "One piece of a bigger job, running on a thread of its own."},
  {"term": "Scope", "plain": "The object that forks subtasks, joins them, and on close guarantees they have all ended."},
  {"term": "Fail fast", "plain": "The first failure cancels the remaining subtasks and is reported at once."},
  {"term": "Joiner", "plain": "The policy you pass to `StructuredTaskScope.open`: when `join()` returns, and what it returns or throws."},
  {"term": "Scoped value", "plain": "A read-only value bound for the length of one call and visible to all the code that call runs."},
  {"term": "Preview API", "plain": "A complete JDK API that isn't final yet. It needs `--enable-preview` and can change in the next release."}
 ],
 "explain_back": {
  "prompt": "A colleague says that try-with-resources around `newVirtualThreadPerTaskExecutor()` already gives you structured concurrency. Explain what it gives you, what it is missing, and what `StructuredTaskScope` and scoped values add.",
  "answer": "It gives you half of it. When the block ends, `close()` waits for every task, so no task outlives the method. What it lacks is a failure policy: when one task fails, nothing cancels the others, so a failed checkout still waits for the slowest call, and you must write `cancel` calls on every error path yourself. Hand-made cancelling also has traps, such as `close()` not waiting for a task you cancelled with `cancel(true)`. `StructuredTaskScope` adds the policy (the first failure cancels the siblings, or another `Joiner`, such as first success wins), timeouts and checks that scopes nest properly, and its `close()` always waits for the threads. It's still a preview until JDK 28. Scoped values, final in JDK 25, add request details that flow into the scope's subtasks without copying, that called code can't change, and that disappear when the call ends, unlike a `ThreadLocal`."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Joiners of your own.** A `Joiner` has two hooks, `onFork` and `onComplete`, and a `result()` method that `join()` calls at the end. `onComplete` returns `true` to cancel the scope. That's enough for policies the built-in joiners don't cover, such as \"stop once three of five price services agree\" or \"collect the successes and ignore the failures\". `onComplete` runs on the thread of the subtask that just finished, so a joiner's state must be thread-safe. Check the Javadoc of the exact JDK you use, because JDK 26 changed the hook signatures slightly.\n\n**Why `CompletableFuture` doesn't solve this.** `allOf` waits for everything even after one future fails, and `cancel(true)` on a `CompletableFuture` doesn't interrupt the thread doing the work: it only completes the future. The lesson \"CompletableFuture: errors, timeouts and fan-out\" builds a fan-out that way. Notice how much code its error handling needs compared with a scope.\n\n**Kotlin already has this.** In coroutine code, `coroutineScope { async { } }` gives the same guarantees without a preview flag: children can't outlive the scope, the first failure cancels the siblings, and cancelling reaches each child at its next suspension point. The coroutines track covers it. `StructuredTaskScope` matters most for Java code, and for Kotlin code that blocks on threads.\n\n**Scoped values and virtual threads.** A `ThreadLocal` costs a map entry per thread, and with a million virtual threads that adds up, as lesson 4 of this track showed. A scoped value's binding belongs to the call, not to each thread, and the scope's forks share it. That makes it a natural fit for one virtual thread per request with many short subtasks.\n\n**Old articles.** Before JDK 25 the API was `StructuredTaskScope.ShutdownOnFailure` and `ShutdownOnSuccess`, subclasses you created with `new`. Scoped values had static helpers such as `ScopedValue.runWhere`, which were removed during the previews. If a snippet uses either, it was written for an older preview."
 },
 "closing": CLOSING,
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
