import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/executors/src"
P = "java/workbench/executors/l07"
KP = "kotlin/workbench/executors/l07"
read = lambda p: (ROOT / p).read_text()

def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l07.{name}",
            "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{KP}/{name}.kt"),
                    "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l07.{name}Kt",
                    "file": f"{lab}/demo/{KP}/{name}.kt"}}

def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

def box(cls, x, y, w, h, title, sub=None, code=True):
    cx = x + w / 2
    tc = "t t-code" if code else "t"
    out = f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>'
    if sub:
        out += f'<text class="{tc}" x="{cx:.0f}" y="{y + 19}" text-anchor="middle">{title}</text>'
        out += f'<text class="t-s" x="{cx:.0f}" y="{y + 36}" text-anchor="middle">{sub}</text>'
    else:
        out += f'<text class="{tc}" x="{cx:.0f}" y="{y + h / 2 + 5:.0f}" text-anchor="middle">{title}</text>'
    return out

rows = [(25, "box-bad", "corner", "closed today", "box-dim", "empty, onSkip"),
        (105, "box-ok", "market", "21.50 at 100 ms", "box-ok", "Optional[21.50]"),
        (185, "box-bad", "mill", "silent past 200 ms", "box-dim", "empty, onSkip")]
SVG = ('<svg viewBox="0 0 700 260" role="img" aria-label="Fan-out: best asks three suppliers at once; each call has its own 200 ms deadline and a handle step that turns a failure into an empty result; allOf then waits for all three and the lowest price wins">'
       + box("box", 10, 105, 110, 44, "best(item)"))
for y, c1, name, sub, c2, out in rows:
    SVG += box(c1, 165, y, 160, 44, name, sub, code=False)
    SVG += box(c2, 370, y, 150, 44, out, None)
    SVG += f'<line class="ln" x1="120" y1="127" x2="163" y2="{y + 22}" marker-end="url(#arr)"/>'
    SVG += f'<line class="ln" x1="325" y1="{y + 22}" x2="368" y2="{y + 22}" marker-end="url(#arr)"/>'
    SVG += f'<line class="ln" x1="520" y1="{y + 22}" x2="563" y2="127" marker-end="url(#arr)"/>'
SVG += (box("box-a", 565, 100, 125, 54, "allOf", "then min()")
        + '<text class="t-s t-m" x="347" y="18" text-anchor="middle">orTimeout(200 ms) + handle, per call</text>'
        + '<text class="t-s t-ok" x="627" y="180" text-anchor="middle">market 21.50</text>'
        + '<text class="t-s t-m" x="627" y="196" text-anchor="middle">or NoQuoteException</text>'
        + '<text class="t-s t-m" x="627" y="212" text-anchor="middle">if all are empty</text>'
        + '</svg>')

# ---------------------------------------------------------------- opening
OPENING = """Last lesson, the ticket for table 4 carried its own instructions: when the steak and the sauce are ready, plate them. In code, that ticket was a `CompletableFuture`, a promise of a result that starts the next step by itself.

Now the steak burns. The sauce cook has no business pouring sauce on charcoal, so a note goes on the ticket instead: "burned at the grill". Every later station passes the ticket along untouched, until someone at the pass, the counter where dishes leave the kitchen, reads the note and decides what table 4 gets.

`CompletableFuture` handles failure the same way, with three surprises. The note sometimes arrives in an envelope. A timer that tells the manager to stop waiting doesn't stop the cook. And waiting for three dishes at once fails the whole table when one of them burns. All three pass a quick test, because tests rarely burn the steak.

In this lesson, we'll follow a failure down a pipeline, open the envelope and put deadlines on slow calls. Then we'll ask three suppliers for a price without letting one bad answer spoil the rest. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_PIPE = """CompletableFuture<String> result = CompletableFuture.supplyAsync(ErrorPathDemo::grill, kitchen)
        .thenApply(s -> step("1. pour the sauce on " + s, s + " with pepper sauce"))
        .thenApply(s -> step("2. plate " + s, "a plate of " + s))
        .thenApply(s -> step("3. carry it to table 4", "table 4 got " + s))
        .whenComplete((v, ex) -> System.out.println("whenComplete sees: " + (ex == null ? v : ex)))
        .exceptionally(ex -> {                              // the pass
            System.out.println("exceptionally sees: " + ex);
            return "table 4 got an apology and the menu";
        });"""
K_PIPE = """val result = CompletableFuture.supplyAsync(::grill, kitchen)
    .thenApply { s -> step("1. pour the sauce on $s", "$s with pepper sauce") }
    .thenApply { s -> step("2. plate $s", "a plate of $s") }
    .thenApply { s -> step("3. carry it to table 4", "table 4 got $s") }
    .whenComplete { v, ex -> println("whenComplete sees: ${ex ?: v}") }
    .exceptionally { ex ->                                  // the pass
        println("exceptionally sees: $ex")
        "table 4 got an apology and the menu"
    }"""
J_EC = """CompletableFuture<String> steak = grill.cookAsync(order)
        .exceptionallyCompose(ex -> spareGrill.cookAsync(order));   // JDK 12+: the fallback is a future too"""
K_EC = """val steak: CompletableFuture<String> = grill.cookAsync(order)
    .exceptionallyCompose { spareGrill.cookAsync(order) }          // JDK 12+: the fallback is a future too"""

S0 = """Let's put the kitchen into code. A future is a claim ticket for a result that isn't ready yet, and a `CompletableFuture` is one you can attach the next step to. A **stage** is one such step, such as a `thenApply`, that runs when the step before it has finished. Our grill runs on `kitchen`, a thread pool: a few threads, paths of work that run side by side, taking tasks from one queue. Three plain stages follow the grill, one per station. Then come two handlers, which we'll meet in a moment:

""" + pair(J_PIPE, K_PIPE) + """

`step` prints its text and returns the value, so we can see which stations did any work. And `grill` always throws an `IllegalStateException` that says `the steak burned`. Before you read on, decide which numbered lines will print.

`ErrorPathDemo`, in the Try it below, printed this:

```text
whenComplete sees: java.util.concurrent.CompletionException: java.lang.IllegalStateException: the steak burned
exceptionally sees: java.util.concurrent.CompletionException: java.lang.IllegalStateException: the steak burned
result: table 4 got an apology and the menu
```

Not one numbered line. When a stage throws, its future **completes exceptionally**: it finishes with an exception instead of a value. Every `thenApply`, `thenCompose` and `thenCombine` after it is then skipped. Its function never runs, and its own future fails with the same cause. That's the note on the ticket, passed from station to station.

The failure stops at the first **handler**, a stage that also runs when the step before it failed. There are four:

| Method | Runs on | Changes the outcome? |
|---|---|---|
| `exceptionally(ex -> value)` | failure only | yes, replaces the failure with a value |
| `handle((value, ex) -> result)` | success and failure | yes, returns any result |
| `whenComplete((value, ex) -> ...)` | success and failure | no, passes the outcome on |
| `exceptionallyCompose(ex -> future)` | failure only | yes, with another future (JDK 12) |

`whenComplete` is the manager who glances at every ticket on its way past and writes in the log. It sees both outcomes and hands the same one on, so it suits logs and counters. (One detail: if its own action throws after a success, the result becomes that new failure. After a failure, the original failure wins.) `exceptionally` is the pass. It replaces the failure with a value, and everything after it sees a success.

Where you put the handler decides what you can still save. At the end, after the sauce, the plate and the walk to table 4 were all skipped, the only honest thing left is an apology. Move the handler up, right after the grill, and it can swap in a spare steak. Then every station after it works as if nothing had gone wrong. Run the demo with `early`, and it prints:

```text
exceptionally sees: java.util.concurrent.CompletionException: java.lang.IllegalStateException: the steak burned
1. pour the sauce on the spare steak
2. plate the spare steak with pepper sauce
3. carry it to table 4
whenComplete sees: table 4 got a plate of the spare steak with pepper sauce
```

**Recover as close to the failure as you can. Every step after the handler then runs as usual.**

Sometimes the fallback takes time of its own. Cooking a new steak on the second grill returns a future, not a steak. For that case, use `exceptionallyCompose`, added in JDK 12 (version 12 of Java's development kit). It is to `exceptionally` what `thenCompose` is to `thenApply`:

""" + pair(J_EC, K_EC) + """

Look again at what our two handlers printed, though. They didn't get our `IllegalStateException`. They got a `CompletionException` with ours inside, like a note sealed in an envelope. Where did the envelope come from?"""

# ---------------------------------------------------------------- section 1
J_UNWRAP = """.exceptionally(ex -> {
    Throwable cause = (ex instanceof CompletionException && ex.getCause() != null) ? ex.getCause() : ex;
    if (cause instanceof TimeoutException) return lastWeeksPrice;
    throw new CompletionException(cause);       // not ours to handle: keep failing
})"""
K_UNWRAP = """.exceptionally { ex ->
    val cause = if (ex is CompletionException && ex.cause != null) ex.cause!! else ex
    if (cause is TimeoutException) lastWeeksPrice
    else throw CompletionException(cause)       // not ours to handle: keep failing
}"""

S1 = """Handlers don't always get your exception. They get one of two things, by a rule that surprises everyone once.

A **`CompletionException`** is an unchecked exception, one that Java doesn't make you catch, that `CompletableFuture` wraps around a failure, with your exception inside as its cause. It's the envelope.

If the exception was thrown inside a stage, by a `supplyAsync` task or a `thenApply` function, the future stores it in an envelope. A handler on that future, or on any later stage, gets the `CompletionException`, and `getCause()` returns your exception. That's what our burned steak did.

If somebody completed the future by hand, with `completeExceptionally(ex)`, the future stores `ex` just as it is. `orTimeout`, which the next section covers, works that way, and so do many libraries that hand you a future. A handler attached right to that future gets the bare exception. One stage later it's in an envelope again, because the failure crossed a stage boundary on its way.

`WrapDemo` prints every case. Cover the output below, and predict each line before you read it:

```text
1. handle() on the supplyAsync future      CompletionException <- IllegalStateException
2. handle() on completeExceptionally       IllegalStateException
3. handle() one stage later                CompletionException <- IllegalStateException
4. handle() after orTimeout                TimeoutException
5. get() throws                            ExecutionException <- IllegalStateException
6. join() throws                           CompletionException <- IllegalStateException
```

Lines 2 and 4 are bare, because someone completed those futures by hand. The last two lines are the blocking calls from the last lesson, the ones that make a thread wait for the result: `get()` throws `ExecutionException` and `join()` throws `CompletionException`, both with the original exception as the cause.

So a handler that checks `ex instanceof TimeoutException` can be right in one place and quietly wrong one stage further down. Open the envelope first, then decide:

""" + pair(J_UNWRAP, K_UNWRAP) + """

First we take the cause out, if there is an envelope. Then we handle the one case we know, a timeout, with last week's price. The last line reads as "I opened it, and this one isn't mine, so pass it on." Throwing inside a handler keeps the future failing, so a later handler, or the caller, can deal with it.

The lab's `unwrap` method does the same job in a loop. It also strips the `ExecutionException` that `get()` adds, in case one wrapper ends up inside another. And on a future you know has failed, `exceptionNow()` (JDK 19) hands you the exception with the envelope already removed.

**Open the envelope before you test the type. Rethrow what isn't yours.**

Line 4 of the demo came from a timeout. A timeout looks like the cure for a slow call. It is only half of one."""

# ---------------------------------------------------------------- section 2
J_TIMERS = """price.orTimeout(300, TimeUnit.MILLISECONDS);                       // fails with TimeoutException
price.completeOnTimeout(lastWeeksPrice, 300, TimeUnit.MILLISECONDS);  // completes with a default"""
K_TIMERS = """price.orTimeout(300, TimeUnit.MILLISECONDS)                        // fails with TimeoutException
price.completeOnTimeout(lastWeeksPrice, 300, TimeUnit.MILLISECONDS)   // completes with a default"""
J_HTTP = """HttpRequest request = HttpRequest.newBuilder(uri)
        .timeout(Duration.ofMillis(300))    // the call itself gives up after 300 ms
        .build();"""
K_HTTP = """val request = HttpRequest.newBuilder(uri)
    .timeout(Duration.ofMillis(300))        // the call itself gives up after 300 ms
    .build()"""

S2 = """Timeouts need a scene of their own. The restaurant buys flour from a few suppliers, and each supplier has a **web service**: a program on another computer that answers questions over the network. Ask it for today's price of a sack of flour, and it answers within a few hundred milliseconds. On a bad day, it doesn't answer at all.

In code, asking is a blocking call. It holds a thread until the answer comes, just like the slow web service from Sizing a pool. So picture the call as a cook on the phone to the supplier. The manager wants the price, so he starts a kitchen timer. When it rings, he stops waiting and decides without it. Nobody tells the cook, who stays on hold, listening to the supplier's music.

JDK 9 gave `CompletableFuture` two such kitchen timers:

""" + pair(J_TIMERS, K_TIMERS) + """

Both change the future you call them on, and return it. If the future hasn't completed when the time is up, a timer thread inside the JDK completes it: `orTimeout` with a `TimeoutException`, `completeOnTimeout` with the value you gave it. The thread's name depends on the JDK. On JDK 21 it's `CompletableFutureDelayScheduler`, and on JDK 25 it's `ForkJoinPool.commonPool-delayScheduler`. Plain stages attached to the future, the ones without `Async` in their name, then run on that thread, so keep them cheap.

Now the trap. Neither timer touches the call. `KeepsRunningDemo` gives a 600 ms call to a slow supplier a deadline of 200 ms. On JDK 21 it printed this:

```text
  36 ms  io-1                                   asking the slow supplier for a price
 236 ms  CompletableFutureDelayScheduler        the future completed with TimeoutException
 695 ms  io-1                                   the supplier answered, but nobody is listening
 702 ms  main                                   pool closed
```

The future failed right on time. The call finished anyway, about 600 ms after it started, holding `io-1` the whole way, and the pool's `close()` had to wait for it. The answer went nowhere.

Maybe `cancel(true)` can hang up the phone? Run the demo with `cancel`:

```text
 243 ms  main                                   cancel(true) returned true
 247 ms  main                                   the future completed with CancellationException
 773 ms  io-1                                   the supplier answered, but nobody is listening
```

As far as the future knows, the cancel worked. The line `interrupted: the call stops here` never printed, though, so the call never noticed. The `CompletableFuture` Javadoc, its official documentation, says the flag `mayInterruptIfRunning` "has no effect in this implementation because interrupts are not used to control processing."

The source code shows why. `supplyAsync` hands the pool a small task that points to the future. The future keeps no pointer back to that task, or to the thread that runs it. So `cancel` can only store a `CancellationException` as the result. There's no thread it could interrupt.

The `FutureTask` that `submit` returns is the opposite. Its `cancel(true)` sends an interrupt, the polite request to stop from Callable, Future, cancellation and interruption.

Here the kitchen picture breaks. A real manager could walk over and tell the cook to hang up. A `CompletableFuture` has no line back to its cook at all.

Under load, that is how a pool fills up with nothing. Take a pool of 20 threads and a supplier that hangs for 30 seconds. Every request gets its `TimeoutException` after 300 ms, right on time. But every call holds its thread for 30 seconds. After 20 requests, all 20 cooks are on hold. New calls, even to healthy suppliers, wait in the pool's queue behind them and time out too.

So every call to another computer needs two timeouts. The one on the future is the caller's deadline. The one inside the client makes the call itself give up, and that gives the thread back. Java's HTTP client, the JDK's own tool for calling web services, takes it on the request:

""" + pair(J_HTTP, K_HTTP) + """

Set the client's timeout no longer than the future's. And give each supplier a limit of its own, a bulkhead from Sizing a pool, so one hung supplier can't take every thread. (A bulkhead is a separate cap on calls to each slow service.)

**A timeout on the future frees the caller, not the thread. Give the call its own timeout too.**

One call with a deadline is under control now. But the manager doesn't want one price. He wants three, and he wants them at the same time."""

ASIDE2 = {
    "title": "Does a framework's timeout stop the work?",
    "body": "If you write web services, your framework or a fault-tolerance library may let you put a timeout on a method with an annotation, often called `@Timeout`. Ask it the same question as `orTimeout`: when the time is up, does only the wait end, or does the work stop too? Some tools run the method on another thread and simply stop waiting for it. Others also interrupt that thread, which stops the call only if the call responds to interrupts. Either way, the client's own timeout is what reliably gives the thread back."
}

# ---------------------------------------------------------------- section 3
J_SAFE = """CompletableFuture<Optional<BigDecimal>> safe = ask(supplier)
        .orTimeout(200, TimeUnit.MILLISECONDS)                       // this supplier's deadline
        .handle((price, ex) -> ex == null ? Optional.of(price) : Optional.empty());"""
K_SAFE = """val safe: CompletableFuture<Optional<BigDecimal>> = ask(supplier)
    .orTimeout(200, TimeUnit.MILLISECONDS)                          // this supplier's deadline
    .handle { price, ex -> if (ex == null) Optional.of(price) else Optional.empty() }"""

S3 = """Back to the flour. Three suppliers sell it: the corner shop, the market and the mill. The manager wants today's price from all three, and he'll buy from the cheapest. Phoning them one after another wastes time, so three cooks phone at once. Sending out several calls at the same time and collecting the answers is called a **fan-out**. In code, it's three futures, all started before we wait for any of them.

`FanOutDemo` sets up the three suppliers with delays chosen for teaching. The corner shop fails after 50 ms, because it's closed today. The market answers 21.50 after 100 ms, and the mill answers 19.80 after 300 ms. The JDK has two methods that combine many futures, and the demo tries both.

`allOf(f1, f2, f3)` returns a `CompletableFuture<Void>` that completes when all three have completed. It carries no results of its own. You read them from your own futures with `join()`, which no longer blocks, because they're all done. Predict what `-Pargs=all` prints, then compare:

```text
  84 ms  corner fails
 151 ms  market answers 21.50
 333 ms  mill answers 19.80
 336 ms  all: failed with java.lang.IllegalStateException: corner is closed today
```

Two good prices came back, and the errand failed anyway. If any of its futures fails, `allOf` fails too, and only after the slowest one has finished. (Every timestamp runs a little late, because the clock starts before the pool does, and the machine was busy with other work.)

`anyOf(f1, f2, f3)` returns a future that completes the same way as the first of them to finish. Here's `-Pargs=any`:

```text
  99 ms  corner fails
 161 ms  any: failed with java.lang.IllegalStateException: corner is closed today
 161 ms  market answers 21.50
 352 ms  mill answers 19.80
```

The corner shop answered first, with the worst possible news, and `anyOf` took it. The first to finish includes failures. If you want the first *successful* answer, `anyOf` can't give it to you. (Go deeper has a ten-line helper for that.)

So neither method does the errand on its own. The fix is to make each call unable to fail before we combine them. Give every call its own deadline, then turn any failure into "no answer":

""" + pair(J_SAFE, K_SAFE) + """

`handle` sees both outcomes and returns a new result either way: the price inside an `Optional`, or an empty `Optional`. Now `allOf` over the safe futures can only succeed, and the step after it picks the lowest price that came back. Here's `-Pargs=safe`:

```text
  91 ms  corner fails
 170 ms  market answers 21.50
 340 ms  mill answers 19.80
 353 ms  safe: result 19.80
```

That's the mill's price, the cheapest, from the slowest supplier. The closed corner shop turned into an empty `Optional`, and it spoiled nothing.

The deadline must sit on each call. Put one `orTimeout` on the `allOf` instead, and a single hung supplier throws away the two good answers.

**Make each call unable to fail before you combine them. Then pick from what came back.**

That's the lab. Its `QuoteAggregator` asks every supplier for a quote, a price offer, all at the same time. Each call gets its own deadline, every skipped supplier is reported with its real cause, and the lowest price wins.

Notice the limit of the tool before we leave the phones. A `CompletableFuture` is good at waiting for calls and combining their answers. It can't stop a call it gave up on, and when one call fails, it doesn't cancel the others. It was built for work that waits. For work that is all arithmetic, the JDK has a pool of its own."""

L = {
 "id": "exec-07",
 "title": "CompletableFuture: errors, timeouts and fan-out",
 "minutes": 35,
 "goal": "By the end you can recover from a failure at the right stage, unwrap CompletionException, give each call its own timeout, and ask several suppliers at once without one bad answer failing the whole request.",
 "opening": OPENING,
 "warmup": {
  "q": "A pipeline reads `supplyAsync(this::grill, kitchen).thenApply(this::addSauce).thenApply(this::plate).exceptionally(ex -> apology)`. `grill` throws an `IllegalStateException`. What happens?",
  "options": [
   "`addSauce` and `plate` run with a null steak",
   "`addSauce` and `plate` are skipped, and `exceptionally` gets the exception wrapped in a `CompletionException`",
   "`supplyAsync` throws the exception on the calling thread",
   "`addSauce` and `plate` are skipped, and `exceptionally` gets the `IllegalStateException` itself"
  ],
  "answer": 1,
  "why": "A failed stage skips every later `thenApply` until a handler. The handler gets a `CompletionException` with the `IllegalStateException` as its cause, because the exception was thrown inside a stage. The last option is the tempting one, and code that checks `ex instanceof IllegalStateException` there is quietly wrong. The first two sections show both halves."
 },
 "sections": [
  {
   "h": "A dish burns at the grill: how a failure skips every step until a handler",
   "body": S0,
   "try": {
    "title": "Move the handler",
    "minutes": 3,
    "steps": [
     "Run `ErrorPathDemo`. The grill throws. Before you run it, write down which of the numbered steps will print.",
     "Run it with `-Pargs=early`, which recovers right after the grill. Predict again, including what `whenComplete` sees."
    ],
    "code": demo("ErrorPathDemo"),
    "expect": "The default run prints no numbered steps. `whenComplete` and then `exceptionally` both see a `CompletionException` with the burned steak inside, and the result is the apology. With `early`, `exceptionally` runs first and returns the spare steak, then steps 1, 2 and 3 run, and `whenComplete` sees a success: `table 4 got a plate of the spare steak with pepper sauce`."
   },
   "refs": [
    {"title": "CompletionStage (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletionStage.html", "kind": "docs"}
   ]
  },
  {
   "h": "The note in an envelope: when a handler gets CompletionException, and when it doesn't",
   "body": S1,
   "try": {
    "title": "Predict the envelope",
    "minutes": 3,
    "steps": [
     "Cover the output in the section. Read `WrapDemo` and write down, for each numbered line, what you expect it to print.",
     "Run it and check. For each line you got wrong, find out whether the exception was thrown inside a stage or passed to `completeExceptionally`."
    ],
    "code": demo("WrapDemo"),
    "expect": "The six lines shown in the section. Lines 2 and 4 are bare exceptions, because `completeExceptionally` and `orTimeout` store them as they are. Every exception that was thrown inside a stage, or crossed one on its way, arrives as a `CompletionException`."
   }
  },
  {
   "h": "A kitchen timer for the manager: orTimeout ends the wait, not the work",
   "body": S2,
   "aside": ASIDE2,
   "try": {
    "title": "Time out a call, then watch it finish",
    "minutes": 3,
    "steps": [
     "Run `KeepsRunningDemo`. Read the thread names and the timestamps.",
     "Run it with `-Pargs=cancel`, which calls `cancel(true)` at 200 ms instead. Predict first: does the call see an interrupt?"
    ],
    "code": demo("KeepsRunningDemo"),
    "expect": "The future completes with `TimeoutException` at about 200 ms, on the timer thread (`CompletableFutureDelayScheduler` on JDK 21, `ForkJoinPool.commonPool-delayScheduler` on JDK 25). The supplier still answers at about 600 ms, and `pool closed` waits for it. With `cancel`, `cancel(true)` returns `true` and the future completes with `CancellationException` on `main`, but the line `interrupted` never prints: the call runs to the end."
   }
  },
  {
   "h": "Three suppliers at once: allOf, anyOf, and one bad answer that mustn't spoil the rest",
   "body": S3,
   "figure": {"svg": SVG, "caption": "Each supplier call gets its own deadline and a handle step, so allOf only ever sees prices or empty results."},
   "try": {
    "title": "Three ways to fan out",
    "minutes": 4,
    "steps": [
     "Read `FanOutDemo`: the corner shop fails at 50 ms, the market answers at 100 ms, the mill at 300 ms.",
     "Run it with `-Pargs=any`, then `-Pargs=all`, then `-Pargs=safe`. Before each run, predict the result and when it arrives."
    ],
    "code": demo("FanOutDemo"),
    "expect": "`any` fails at about 50 ms with the corner shop's `closed today`, and the market and the mill keep going after the result is printed. `all` fails with the same exception, but only at about 300 ms, after the mill answers. `safe` succeeds at about 300 ms with 19.80, the mill's price, because the failure became an empty `Optional`. On a busy machine, every timestamp runs a little late."
   }
  }
 ],
 "compare": {
  "title": "One supplier call with a deadline: CompletableFuture vs coroutines",
  "java": {"title": "Ask.java (CompletableFuture)", "src": "CompletableFuture<Optional<Quote>> ask(QuoteProvider p, String item) {\n    return CompletableFuture.supplyAsync(() -> new Quote(p.name(), p.quote(item)), io)\n            .orTimeout(300, TimeUnit.MILLISECONDS)          // the caller stops waiting...\n            .handle((q, ex) -> ex == null ? Optional.of(q) : Optional.empty());\n    // ...but p.quote keeps running on io until it returns\n}"},
  "kotlin": {"title": "Ask.kt (kotlinx.coroutines)", "src": "suspend fun ask(p: QuoteProvider, item: String): Quote? =\n    try {\n        withTimeoutOrNull(300.milliseconds) {               // null when time is up\n            runInterruptible(Dispatchers.IO) {              // interrupts the thread on cancel\n                Quote(p.name(), p.quote(item))\n            }\n        }\n    } catch (e: CancellationException) {\n        throw e                                             // never swallow cancellation\n    } catch (e: Exception) {\n        null                                                // a failure becomes \"no answer\"\n    }"},
  "note": "Both versions have the same shape: a deadline, then a failure turned into \"no answer\". The difference is what happens to the work. `orTimeout` only completes the future, and the supplier call runs to its end. Kotlin's coroutines, its own light tasks with a track of their own, can do more. `withTimeoutOrNull` cancels the block when time is up, and `runInterruptible` turns that cancellation into `Thread.interrupt()` on the IO thread. So a blocking call that responds to interrupts stops and gives its thread back. In both languages, a call that ignores interrupts keeps its thread, which is why the client's own timeout still matters. Kotlin has one trap of its own: when you catch `Exception`, you must rethrow `CancellationException` by hand, or the coroutine stops responding to cancellation. `CompletableFuture` has no such trap."
 },
 "worked": {
  "title": "Give the flour price a deadline and a fallback",
  "steps": [
   {"say": "The kitchen gets the flour price from its main supplier through an async client, a library whose methods return a `CompletableFuture`. When the supplier hangs, everything that needs the price hangs with it. Before reading on, decide what should happen after 300 ms.",
    "code": "CompletableFuture<BigDecimal> price(String item) {\n    return supplier.priceAsync(item);     // no deadline: a hung supplier hangs the kitchen\n}", "lang": "java",
    "alt_code": "fun price(item: String): CompletableFuture<BigDecimal> =\n    supplier.priceAsync(item)             // no deadline: a hung supplier hangs the kitchen", "alt_lang": "kotlin"},
   {"say": "Give the call a deadline, count failures without changing them, then fall back to a second supplier, which has an async client too. `metrics` is a small counter that a dashboard reads. The fallback gets a short deadline of its own, because `exceptionallyCompose` starts a new call that the first timeout doesn't cover.",
    "code": "CompletableFuture<BigDecimal> price(String item) {\n    return supplier.priceAsync(item)\n            .orTimeout(300, TimeUnit.MILLISECONDS)                    // 1. the main call gets 300 ms\n            .whenComplete((p, ex) -> {                                // 2. look, don't change\n                if (ex != null) metrics.count(\"price.failed\", unwrap(ex).getClass().getSimpleName());\n            })\n            .exceptionallyCompose(ex -> backup.priceAsync(item)      // 3. fall back, asynchronously\n                    .orTimeout(100, TimeUnit.MILLISECONDS));          // 4. the fallback's own deadline\n}", "lang": "java",
    "alt_code": "fun price(item: String): CompletableFuture<BigDecimal> =\n    supplier.priceAsync(item)\n        .orTimeout(300, TimeUnit.MILLISECONDS)                        // 1. the main call gets 300 ms\n        .whenComplete { _, ex ->                                      // 2. look, don't change\n            if (ex != null) metrics.count(\"price.failed\", unwrap(ex).javaClass.simpleName)\n        }\n        .exceptionallyCompose {                                       // 3. fall back, asynchronously\n            backup.priceAsync(item).orTimeout(100, TimeUnit.MILLISECONDS)   // 4. the fallback's own deadline\n        }", "alt_lang": "kotlin"},
   {"say": "Why `unwrap` in the counter? The supplier's client may complete its future with a bare exception, `orTimeout` stores a bare `TimeoutException`, and anything thrown inside a stage arrives in an envelope. Without unwrapping, half the failures would be counted as `CompletionException`, which tells the person reading the dashboard nothing.",
    "code": "", "lang": ""},
   {"say": "One gap is left. After 300 ms the kitchen moves on, but the main call still holds a thread and a network connection. Give the request a timeout of its own, so the client gives up too. With the JDK's HTTP client, it's one line on the request.",
    "code": "HttpRequest request = HttpRequest.newBuilder(uri)\n        .timeout(Duration.ofMillis(300))    // 5. the call stops waiting too\n        .build();", "lang": "java",
    "alt_code": "val request = HttpRequest.newBuilder(uri)\n    .timeout(Duration.ofMillis(300))        // 5. the call stops waiting too\n    .build()", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A price checker that survives bad suppliers",
  "minutes": 14,
  "files": [f"{lab}/main/{P}/QuoteAggregator.java", f"{lab}/main/{P}/QuoteProvider.java", f"{lab}/main/{P}/NoQuoteException.java"],
  "run": "./gradlew :executors:test --tests 'workbench.executors.l07.*'",
  "steps": [
   "Meet the classes. A `QuoteProvider` is one supplier's price service: `quote(item)` makes a blocking call and returns today's price, or throws. A `Quote` is one answer, the supplier's name and its price. `QuoteAggregator.best(item)` must ask every supplier at once and complete with the lowest `Quote`. Its Javadoc is the spec. Run the tests: all seven fail.",
   "Write `unwrap`: loop while the throwable is a `CompletionException` or an `ExecutionException` and has a cause, moving to the cause each time.",
   "Add a private method `ask(QuoteProvider p, String item)` that returns `CompletableFuture<Optional<Quote>>`: `supplyAsync` on `io`, then `orTimeout`, then `handle`. On failure, call `onSkip.accept(p.name(), unwrap(ex))` and return `Optional.empty()`.",
   "In `best`, map every supplier to `ask`, collect the futures in a list, and pass them to `allOf`. In the `thenApply` after it, `join` each future, keep the quotes that are present, and return the lowest price, or throw `NoQuoteException`.",
   "Run the tests until all seven pass, then once more."
  ],
  "hints": [
   "`orTimeout` takes a `long` and a unit: `orTimeout(timeout.toMillis(), TimeUnit.MILLISECONDS)`.",
   "`allOf` takes an array (`asks.toArray(CompletableFuture[]::new)`) and returns `CompletableFuture<Void>`. Read the quotes from your own list.",
   "If `skipsFailingProvider` reports a `CompletionException`, you passed `ex` to `onSkip` without unwrapping it. If `skipsSlowProvider` times out, the deadline is on the whole call, not on each supplier.",
   "Throwing `NoQuoteException` inside the `thenApply` is enough: the returned future fails with it as the cause."
  ],
  "done_when": "All seven tests in `QuoteAggregatorTest` pass."
 },
 "drill": {
  "title": "A price with a deadline and a fallback",
  "minutes": 5,
  "prompt": "Close this page. Write `CompletableFuture<BigDecimal> price(String item)`: call `main.priceAsync(item)` with a 300 ms deadline. If it fails for any reason, log the unwrapped cause and fall back to `backup.priceAsync(item)`, which returns a `CompletableFuture` too. Then compare. Which method did you use for the fallback, and did you unwrap before logging?",
  "answer": {"lang": "java", "title": "Prices.java", "src": "CompletableFuture<BigDecimal> price(String item) {\n    return main.priceAsync(item)\n            .orTimeout(300, TimeUnit.MILLISECONDS)\n            .exceptionallyCompose(ex -> {\n                Throwable cause = ex instanceof CompletionException && ex.getCause() != null ? ex.getCause() : ex;\n                log.warn(\"main supplier failed, asking the backup: {}\", cause.toString());\n                return backup.priceAsync(item);      // a future, so exceptionallyCompose, not exceptionally\n            });\n}",
   "alt": {"lang": "kotlin", "title": "Prices.kt", "src": "fun price(item: String): CompletableFuture<BigDecimal> =\n    main.priceAsync(item)\n        .orTimeout(300, TimeUnit.MILLISECONDS)\n        .exceptionallyCompose { ex ->\n            val cause = if (ex is CompletionException && ex.cause != null) ex.cause!! else ex\n            log.warn(\"main supplier failed, asking the backup: {}\", cause.toString())\n            backup.priceAsync(item)                  // a future, so exceptionallyCompose, not exceptionally\n        }"}}
 },
 "recap": [
  "A failure skips every later stage until a handler. `exceptionally` and `handle` can recover, `whenComplete` only looks, and `exceptionallyCompose` (JDK 12) recovers with another future.",
  "Recover as close to the failure as you can, so that every stage after the handler runs as usual.",
  "An exception thrown inside a stage reaches handlers wrapped in a `CompletionException`. `completeExceptionally` and `orTimeout` store it bare. Unwrap before you test the type.",
  "`orTimeout` and `completeOnTimeout` end the caller's wait, not the work, and `cancel(true)` on a `CompletableFuture` interrupts nothing. Give the call its own timeout in the client.",
  "`allOf` waits for every future and fails if any failed. `anyOf` takes the first to finish, failures included. For a fan-out, give each call its own deadline and turn its failure into \"no answer\" before `allOf`.",
  "The limit: a `CompletableFuture` can stop waiting but can't stop the work, and one failed call doesn't cancel the others. It suits work that waits, not one big pile of arithmetic."
 ],
 "closing": "We started with a steak that burned at the grill. Its note skipped every station on the way to the pass, sometimes in an envelope. The kitchen timer freed the manager while the cook stayed on hold. And three suppliers gave one price, once no call could spoil the errand.\n\nNow search your own code for `orTimeout(`, and check that the call underneath has a timeout of its own. Then search for `allOf(`, and make sure every future it waits for has its own deadline and handler.\n\nNext, we'll go back to the chopping board, where the work is all arithmetic. How does a `ForkJoinPool` keep every cook busy on one big job, with no manager handing out tickets?",
 "quiz": [
  {
   "q": "Each step prints its letter: `supplyAsync(fails, io).thenApply(A).whenComplete(B).exceptionally(C).thenAccept(D)`, and the supplier throws. What prints?",
   "options": [
    "A, B, C, D",
    "B, C, D",
    "C, D",
    "B and C, then the pipeline fails"
   ],
   "answer": 1,
   "why": "`A` is skipped, because its input failed. `whenComplete` runs on a failure too, but it passes the failure on, so `C` runs and recovers. Then `D` runs with the fallback value. After `exceptionally` recovers, every stage after it sees a success, which is why the last option is wrong."
  },
  {
   "q": "`supplyAsync(() -> { throw new IllegalStateException(\"closed today\"); }, io).exceptionally(ex -> ...)`. What is the class of `ex`?",
   "options": [
    "`ExecutionException`",
    "`IllegalStateException`",
    "`RuntimeException`",
    "`CompletionException`, with the `IllegalStateException` as its cause"
   ],
   "answer": 3,
   "why": "The exception was thrown inside a stage, so the future stores it wrapped in a `CompletionException`. `ExecutionException` is what `get()` throws at the blocking edge. You would get the bare `IllegalStateException` only if someone had called `completeExceptionally` with it."
  },
  {
   "q": "Supplier calls run on a fixed pool of 20 threads with `orTimeout(300, MILLISECONDS)`. One supplier hangs for 30 s, and 100 requests arrive in one second. What happens?",
   "options": [
    "The first 20 time out at 300 ms but keep their threads; later calls queue behind them, so they time out too, even to healthy suppliers",
    "Every request times out at 300 ms, and the pool stays free",
    "`orTimeout` interrupts the hung calls, so the threads come back at 300 ms",
    "The pool rejects the 21st request"
   ],
   "answer": 0,
   "why": "`orTimeout` completes the future but never touches the call, so each hung call holds its thread for 30 s. A fixed pool has a queue with no limit, so nothing is rejected: new calls just wait behind the hung ones until their own deadlines pass. A timeout in the client and a limit per supplier prevent it."
  },
  {
   "q": "You want to count every supplier call as a success or a failure, without changing what the caller receives. Which method fits?",
   "options": [
    "`exceptionally`",
    "`handle`",
    "`whenComplete`",
    "`thenAccept`"
   ],
   "answer": 2,
   "why": "`whenComplete` sees both outcomes and passes the original one on. `handle` sees both too, but you'd have to rebuild the outcome yourself, rethrowing the failure, which is easy to get wrong. `exceptionally` misses successes, and `thenAccept` misses failures."
  },
  {
   "q": "From \"Callable, Future, cancellation and interruption\": the same blocking call, asleep in `Thread.sleep`, runs twice: once through `executor.submit(task)` and once through `CompletableFuture.supplyAsync(task, executor)`. You call `cancel(true)` on both futures. What happens?",
   "options": [
    "Both calls are interrupted",
    "Only the `submit` call is interrupted; the `CompletableFuture` one keeps sleeping",
    "Only the `CompletableFuture` call is interrupted",
    "Neither, because `cancel` only affects tasks that haven't started"
   ],
   "answer": 1,
   "why": "`submit` returns a `FutureTask`, whose `cancel(true)` interrupts the worker thread. `CompletableFuture.cancel` ignores the flag: it completes the future with `CancellationException` and leaves the task alone. Both futures report `isCancelled() == true`.",
   "from": "exec-04"
  }
 ],
 "flashcards": [
  {"front": "Which CompletableFuture handler sees a failure but can't change the outcome?", "back": "`whenComplete`. It passes the original result or failure on. `exceptionally` and `handle` can replace it."},
  {"front": "A handler on a failed `supplyAsync` future: which exception does it get?", "back": "A `CompletionException`, with the exception the task threw as `getCause()`."},
  {"front": "Does `orTimeout` stop the task?", "back": "No. It completes the future with `TimeoutException`, and the task keeps running, holding its thread."},
  {"front": "Does `cancel(true)` interrupt a CompletableFuture's task?", "back": "No. The flag has no effect. The future completes with `CancellationException`, and the task runs on."},
  {"front": "One of three futures fails at 50 ms, and the slowest takes 300 ms. When does `allOf` complete?", "back": "At 300 ms, exceptionally. `allOf` waits for all of them; it doesn't fail fast."},
  {"front": "What does `anyOf` give you if the fastest future fails?", "back": "A failure. `anyOf` completes like the first future to complete, success or failure."},
  {"front": "When do you use `exceptionallyCompose` instead of `exceptionally`?", "back": "When the fallback is itself a future, such as a call to a backup supplier (JDK 12+)."}
 ],
 "terms": [
  {"term": "Stage", "plain": "One step attached to a future, such as a thenApply, that runs when the step before it finishes."},
  {"term": "CompletionException", "plain": "The unchecked wrapper CompletableFuture puts around an exception thrown inside a stage."},
  {"term": "exceptionally", "plain": "Runs only on failure and replaces it with a value."},
  {"term": "handle", "plain": "Runs on success or failure and returns a new result either way."},
  {"term": "whenComplete", "plain": "Runs on success or failure to look; passes the outcome on unchanged."},
  {"term": "orTimeout", "plain": "Fails the future with TimeoutException if it isn't done in time. The work keeps running."},
  {"term": "Fan-out", "plain": "Sending several calls at the same time and collecting their answers."},
  {"term": "allOf / anyOf", "plain": "Combine many futures: wait for all of them, or take the first to complete."}
 ],
 "explain_back": {
  "prompt": "A friend's price checker does `allOf(askCorner, askMarket, askMill).orTimeout(500, MILLISECONDS)` and then picks the lowest price. Explain why it fails whenever one supplier is closed or slow, and how you would change it.",
  "answer": "`allOf` fails if any of its futures fails, so one closed supplier fails the whole call, and only after the slowest supplier has finished. The single `orTimeout` on the `allOf` means one hung supplier makes the whole call time out and throws away the prices that did come back. I'd give each supplier call its own `orTimeout`, then a `handle` that turns a failure into an empty `Optional` and reports the unwrapped cause. Then `allOf` over those safe futures can't fail, and the step after it picks the lowest price among the ones that are present, or fails with a clear \"no quote\" error if all are empty. I'd also set a timeout in the HTTP client, because `orTimeout` doesn't stop the call itself."
 },
 "deeper": {
  "minutes": 8,
  "body": "`anyOf` gives you the first to finish, not the first to succeed. When you want the first success, complete a future of your own from each success, and fail it only when every call has failed. `complete` returns `false` for every caller after the first, so the first success wins without a lock:\n\n```java\nstatic <T> CompletableFuture<T> firstSuccess(List<CompletableFuture<T>> calls) {   // calls must not be empty\n    CompletableFuture<T> first = new CompletableFuture<>();\n    AtomicInteger failed = new AtomicInteger();\n    for (CompletableFuture<T> call : calls) {\n        call.whenComplete((value, ex) -> {\n            if (ex == null) first.complete(value);                                   // only the first one counts\n            else if (failed.incrementAndGet() == calls.size()) first.completeExceptionally(ex);\n        });\n    }\n    return first;\n}\n```\n\n```kotlin\nfun <T> firstSuccess(calls: List<CompletableFuture<T>>): CompletableFuture<T> {     // calls must not be empty\n    val first = CompletableFuture<T>()\n    val failed = AtomicInteger()\n    for (call in calls) {\n        call.whenComplete { value, ex ->\n            if (ex == null) first.complete(value)                                    // only the first one counts\n            else if (failed.incrementAndGet() == calls.size) first.completeExceptionally(ex)\n        }\n    }\n    return first\n}\n```\n\nTwo smaller things are worth knowing. `orTimeout` and `completeOnTimeout` change the very future you call them on. If a library hands the same cached future to several callers, one caller's timeout fails it for all of them. Call `copy()` (JDK 9) first, and put the timeout on your copy. And when you need a delay without a timeout, `CompletableFuture.delayedExecutor(500, MILLISECONDS, io)` (JDK 9) returns an `Executor` that runs each task 500 ms after you hand it over. It's handy for a retry that waits a little first: `supplyAsync(this::call, CompletableFuture.delayedExecutor(500, MILLISECONDS, io))`."
 },
 "sources": [
  {"title": "CompletableFuture (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html"},
  {"title": "CompletionException (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletionException.html"},
  {"title": "Cancellation and timeouts (Kotlin docs)", "url": "https://kotlinlang.org/docs/cancellation-and-timeouts.html"},
  {"title": "runInterruptible (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/run-interruptible.html"}
 ]
}
out = ROOT / "content/lessons/exec-07.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
