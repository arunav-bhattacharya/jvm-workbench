import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/executors/src"
P = "java/workbench/executors/l06"
KP = "kotlin/workbench/executors/l06"
read = lambda p: (ROOT / p).read_text()

def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l06.{name}",
            "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{KP}/{name}.kt"),
                    "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l06.{name}Kt",
                    "file": f"{lab}/demo/{KP}/{name}.kt"}}

def box(cls, x, y, w, h, title, sub=None):
    cx = x + w / 2
    out = f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>'
    if sub:
        out += f'<text class="t t-code" x="{cx:.0f}" y="{y + 20}" text-anchor="middle">{title}</text>'
        out += f'<text class="t-s" x="{cx:.0f}" y="{y + 38}" text-anchor="middle">{sub}</text>'
    else:
        out += f'<text class="t t-code" x="{cx:.0f}" y="{y + h / 2 + 5:.0f}" text-anchor="middle">{title}</text>'
    return out

SVG = (
    '<svg viewBox="0 0 700 250" role="img" aria-label="Checkout pipeline: the price call and the exchange-rate call start together on the io pool, thenCombine multiplies them, thenCompose calls the payment service, thenApply builds the receipt">'
    + box("box-a", 20, 30, 160, 50, "priceEur(cart)", "io, 300 ms")
    + box("box-a", 20, 140, 160, 50, "rate(EUR, USD)", "io, 300 ms")
    + box("box", 235, 85, 150, 50, "thenCombine", "price x rate")
    + box("box", 420, 85, 140, 50, "thenCompose", "gateway.charge")
    + box("box-ok", 590, 85, 100, 50, "thenApply", "Receipt")
    + '<line class="ln" x1="180" y1="55" x2="233" y2="100" marker-end="url(#arr)"/>'
    + '<line class="ln" x1="180" y1="165" x2="233" y2="120" marker-end="url(#arr)"/>'
    + '<line class="ln" x1="385" y1="110" x2="418" y2="110" marker-end="url(#arr)"/>'
    + '<line class="ln" x1="560" y1="110" x2="588" y2="110" marker-end="url(#arr)"/>'
    + '<text class="t-s t-m" x="100" y="218" text-anchor="middle">both start at 0 ms</text>'
    + '<text class="t-s t-m" x="310" y="160" text-anchor="middle">runs when the</text>'
    + '<text class="t-s t-m" x="310" y="175" text-anchor="middle">second one ends</text>'
    + '<text class="t-s t-m" x="490" y="160" text-anchor="middle">flattens the</text>'
    + '<text class="t-s t-m" x="490" y="175" text-anchor="middle">charge\'s ticket</text>'
    + '<text class="t-s t-m" x="640" y="160" text-anchor="middle">completes the</text>'
    + '<text class="t-s t-m" x="640" y="175" text-anchor="middle">last ticket</text>'
    + '<line class="ln-d" x1="20" y1="238" x2="680" y2="238"/>'
    + '<text class="t-s t-m" x="350" y="232" text-anchor="middle">total: about 300 ms plus the charge, not 600</text>'
    + '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Picture a busy kitchen and an order for table 4: steak with pepper sauce. The steak goes on the grill and the sauce on the stove, at the same time. The order's ticket carries instructions: "When the steak and the sauce are both ready, plate them and send them to table 4."

Nobody stands at the grill watching the steak. (It cooks just as fast without an audience.) Whichever cook finishes the last part reads the ticket and does the next step.

The tickets from the last two lessons couldn't carry instructions. A `Future` could only be waited on or read, and every wait held a thread, a path of work, doing nothing. Java's `CompletableFuture` is a ticket that can.

The new ticket has two easy traps. A chain of steps can look side by side and still run one after another. Or it can run on a pool the whole program shares, where one slow call holds up strangers. Both pass every test.

In this lesson, we'll rebuild the shop's checkout with these tickets, see which thread runs each step, and decide where waiting is still allowed. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Back to the shop's checkout. The shop prices everything in euros, and an American customer pays in dollars.

So the checkout needs two answers from two slow services. The cart service knows the cart's price in euros. The rate service knows the exchange rate, how many dollars one euro buys. (The code calls it `fx`, short for foreign exchange.) Each takes 300 ms. Then the checkout multiplies the two and charges the card.

Here's the honest version, with the tickets from Callable, Future, cancellation and interruption. `io` is a thread pool, a small team of threads that take tasks from a queue:

```java
Future<BigDecimal> price = io.submit(() -> prices.priceEur(cart));
Future<BigDecimal> rate = io.submit(() -> fx.rate("EUR", "USD"));
BigDecimal usd = price.get().multiply(rate.get());   // this thread waits here, doing nothing
```

```kotlin
val price = io.submit<BigDecimal> { prices.priceEur(cart) }
val rate = io.submit<BigDecimal> { fx.rate("EUR", "USD") }
val usd = price.get() * rate.get()                    // this thread waits here, doing nothing
```

Credit where it's due: it's correct, and both calls run side by side, so the wait is 300 ms, not 600. The catch is the thread that calls `get()`. It sits there for the whole 300 ms, doing nothing. Little's law, from Sizing a pool, says the number inside equals the arrival rate times the time each one stays. At 400 checkouts a second, that's 400 x 0.3 = 120 threads, all just waiting.

A **`CompletableFuture<T>`** is a ticket you can clip instructions to. It's still a `Future`, so `get` and `cancel` still work. But it also lets you say "when this is done, do that next", and walk away.

Something has to complete the ticket, and usually that's `supplyAsync`. (Async is short for asynchronous: the work runs while your code moves on.) It takes a `Supplier`, a function that takes nothing and returns a value. It runs the supplier on the pool you name, and completes the ticket with the result:

```java
CompletableFuture<BigDecimal> price =
        CompletableFuture.supplyAsync(() -> prices.priceEur(cart), io);   // starts now, on io
CompletableFuture<Void> note =
        CompletableFuture.runAsync(() -> orderLog.write(cart), io);       // no result
```

```kotlin
val price: CompletableFuture<BigDecimal> =
    CompletableFuture.supplyAsync({ prices.priceEur(cart) }, io)      // starts now, on io
val note: CompletableFuture<Void> =
    CompletableFuture.runAsync({ orderLog.write(cart) }, io)          // no result
```

Both calls return at once, while the work runs on `io` or waits in its queue. `runAsync` is the same for a task with no result. A ticket can also be completed by hand: a library can hand you a `new CompletableFuture<>()` and call `complete(value)` on it when its answer arrives. The payment service in this lesson's lab, the service that charges the card, works that way. The lab calls its client `PaymentGateway`, and its `charge` method returns a ticket.

The second argument, the pool, matters more than it looks. Leave it out, and the task goes to the **default async executor**, `ForkJoinPool.commonPool()`. That's one pool per JVM, the program that runs your Java code. It has one thread fewer than the machine has cores, the parts of the processor that each run one thread at a time.

Every parallel stream (a stream that splits its work across threads) uses it, and so does every library that calls `supplyAsync` without a pool. It's the shared kitchen that everyone borrows and nobody owns. A few 300 ms calls fill it, and everyone else's work waits behind them.

`WhoRunsItDemo`, in the Try it below, prints the thread that runs each `supplyAsync`, first without a pool and then with a pool named `io`. On a 4-core machine with JDK 21:

```text
JDK 21, common pool parallelism 3
supplyAsync(task)      ran on ForkJoinPool.commonPool-worker-1
supplyAsync(task)      ran on ForkJoinPool.commonPool-worker-1
supplyAsync(task)      ran on ForkJoinPool.commonPool-worker-1
supplyAsync(task, io)  ran on io-1
supplyAsync(task, io)  ran on io-2
supplyAsync(task, io)  ran on io-2
```

The version of the JDK, Java's standard library and tools, changes the small-machine case. Many programs run in a container, a fenced-off space where the operating system limits how much CPU a program may use. In a container limited to 2 CPUs, the common pool gets just one thread. Up to JDK 24, `CompletableFuture` noticed that and skipped the pool: it started a brand-new thread for every task. JDK 25 removed that special case.

Run the demo with `1cpu`, which sizes the common pool as that container would, and the two versions disagree. JDK 21 runs the three calls on `Thread-0`, `Thread-1` and `Thread-2`, a new thread each time. JDK 25 runs all three on `ForkJoinPool.commonPool-worker-1`. For a call that waits, both are wrong: one has no limit, and the other has a limit of one.

**Without a pool, async work runs on threads the whole JVM shares. Pass a pool for anything that waits.**

The pool you pass can be a fixed pool sized the way Sizing a pool showed. On JDK 21 and later, it can also be `Executors.newVirtualThreadPerTaskExecutor()`, which gives each task a virtual thread, a much lighter kind of thread that a later track covers. Keep the default for short computing work.

The price and the rate are on their way. Now we clip on the instructions."""

# ---------------------------------------------------------------- section 1
S1 = """Each of these methods takes a ticket, clips on one instruction, and hands back a new ticket for that instruction's result. Here's the smallest one, on a ticket that is already complete:

```java
CompletableFuture<Integer> six = CompletableFuture.completedFuture(6);
CompletableFuture<Integer> answer = six.thenApply(n -> n * 7);   // a new ticket, for 42
```

```kotlin
val six = CompletableFuture.completedFuture(6)
val answer = six.thenApply { n -> n * 7 }                         // a new ticket, for 42
```

Each step is called a **stage**: a ticket, plus the instruction that completes it from earlier results. Which method you use depends on the shape of the instruction you have:

| You have | Method | You get |
|---|---|---|
| `T -> U`, plain code | `thenApply` | `CompletableFuture<U>` |
| `T -> CompletableFuture<U>`, another async call | `thenCompose` | `CompletableFuture<U>` |
| a second ticket, and `(T, U) -> V` | `thenCombine` | `CompletableFuture<V>` |
| `T -> void`, a side effect | `thenAccept` | `CompletableFuture<Void>` |

`thenCompose` needs a second look. Say a step calls the payment service, which already returns its own ticket. With `thenApply`, you'd get a `CompletableFuture<CompletableFuture<String>>`: a ticket for a ticket, and nobody collects the inner one. `thenCompose` flattens it into a single `CompletableFuture<String>`. (If you know `Optional` or streams: `thenApply` is `map`, and `thenCompose` is `flatMap`.)

Now the checkout. `CombineDemo` starts the price and the rate, joins them with `thenCombine`, and logs each event with its time and thread. Here's the heart of it:

```java
// both calls start now and run side by side
CompletableFuture<BigDecimal> price = CompletableFuture.supplyAsync(CombineDemo::priceEur, io);
CompletableFuture<BigDecimal> rate = CompletableFuture.supplyAsync(CombineDemo::eurToUsd, io);
usd = price.thenCombine(rate, BigDecimal::multiply);
```

```kotlin
// both calls start now and run side by side
val price = CompletableFuture.supplyAsync(::priceEur, io)
val rate = CompletableFuture.supplyAsync(::eurToUsd, io)
price.thenCombine(rate) { p, r -> p * r }
```

Read the last line as the ticket for table 4: when the price and the rate are both ready, multiply them. Each call takes 300 ms, so I expect the charge a little after 300 ms. On a busy machine:

```text
  36 ms  main   pipeline built, nothing has arrived yet
 330 ms  io-1   price is 100.00 EUR
 332 ms  io-2   rate is 1.0842
 347 ms  main   charge 108.42 USD
```

The run matched my guess. The `main` thread built the whole pipeline in 36 ms and walked away. The price and the rate arrived together, on two `io` threads, and the charge followed.

Now a setback. The `chain` version fetches the rate inside `thenCompose`, after the price arrives:

```java
// the rate call starts only when the price has arrived
usd = CompletableFuture.supplyAsync(CombineDemo::priceEur, io)
        .thenCompose(p -> CompletableFuture.supplyAsync(CombineDemo::eurToUsd, io)
                .thenApply(p::multiply));
```

```kotlin
// the rate call starts only when the price has arrived
CompletableFuture.supplyAsync(::priceEur, io)
    .thenCompose { p -> CompletableFuture.supplyAsync(::eurToUsd, io).thenApply { r -> p * r } }
```

The chain is just as asynchronous, and `main` still walks away at once. But look at the times:

```text
  36 ms  main   pipeline built, nothing has arrived yet
 340 ms  io-1   price is 100.00 EUR
 644 ms  io-2   rate is 1.0842
 661 ms  main   charge 108.42 USD
```

The rate arrived at 644 ms, not 332. Nothing warned us. Both versions are asynchronous; only one of them is also fast.

The difference is where `supplyAsync` is called. Work starts when you call `supplyAsync`, not when you call `thenCombine`. In the first version, both calls start on the first two lines, before any instruction is clipped on. In the second, the rate call sits inside an instruction, and an instruction runs only when the stage before it completes.

**Work starts when you call `supplyAsync`. Start everything independent first, then combine.**

The figure shows where the lab takes this checkout: the charge clipped on with `thenCompose`, and the receipt with `thenApply`. If any step fails, the steps after it are skipped, and the last ticket fails with that exception. That's the next lesson.

One question is still open from the first run. The `main` thread built the pipeline and walked away, so which thread did the multiply?"""

# ---------------------------------------------------------------- section 2
S2 = """`thenApply`, `thenCompose`, `thenCombine` and `thenAccept` take no pool. So who runs the instruction?

There are two cases. If the stage before it is still running when you clip the instruction on, the instruction runs on **the thread that completes that stage**. If that stage is already complete, the instruction runs right away, on the thread that called `thenApply`.

Both cases follow from one detail of the class. Each `CompletableFuture` keeps a stack of the instructions clipped onto it. The thread that completes the ticket, by returning from a `supplyAsync` task or by calling `complete`, then takes those instructions off one by one. It runs every one that has no pool of its own. An instruction clipped on after that finds a finished ticket, so `thenApply` runs it on the spot.

The kitchen from the opening works the same way: whichever cook finishes the last part reads the ticket and does the next step. So in `CombineDemo`, the multiply ran on whichever `io` thread finished second, not on `main`.

`WhichThreadDemo` shows both cases, plus the two `Async` variants you'll meet in a moment. Write down your guess for each line before you read on:

```text
1. thenApply on a finished future:    main
2. thenApply attached while running:  io-1
3. thenApplyAsync(fn):                ForkJoinPool.commonPool-worker-1
4. thenApplyAsync(fn, cpu):           cpu-1
```

Line 1 was clipped onto a finished ticket, so `main` ran it on the spot. Line 2 was clipped onto a ticket whose task was still sleeping on `io-1`, so `io-1` ran it when the task finished.

For cheap steps, that's exactly right, and it's what the plain methods are for. Multiplying a price by a rate takes microseconds. It doesn't matter which thread does it, and skipping a trip to another pool saves a queue and a thread switch.

Trouble starts when the step is slow and the completing thread isn't yours. Some client libraries, the code you use to call another service, complete their tickets on a thread of their own that serves many requests at once. (That thread is often called an event loop.) A plain `thenApply` that blocks there for 50 ms stalls every other request it serves. The same goes for a scheduler's thread, from the last lesson, that completes a ticket at a deadline.

Here the kitchen picture breaks. A real cook who finishes the sauce knows to pass a two-hour braise to someone else. A plain `thenApply` doesn't. The thread that completes the stage does the next step, however slow it is, unless you name a pool.

The `Async` variants fix that. Every method has two of them:

- `thenApplyAsync(fn)` always hands the step to the default async executor, the common pool, with the same problems as `supplyAsync` without a pool.
- `thenApplyAsync(fn, executor)` hands it to the pool you name. Use it to move slow or waiting work off a thread you don't own.

**A plain step runs on whatever thread finished the stage before. Name a pool for any step that is slow.**

So far, every step completes a ticket and hands on. Sooner or later, though, somebody needs the actual value."""

# ---------------------------------------------------------------- section 3
S3 = """Sooner or later, a thread needs the value itself. It might send a web page back to a browser, print a receipt, or check a result in a test. `CompletableFuture` gives you two ways to wait for it.

`get()` is the `Future` method from Callable, Future, cancellation and interruption. It throws the checked exceptions `InterruptedException` and `ExecutionException`, with the failure as the cause, and `get(timeout, unit)` adds `TimeoutException`.

`join()` throws only unchecked exceptions: `CompletionException`, with the failure as the cause, or `CancellationException`. That makes it easy to call inside lambdas and streams. But it has no time limit, and it ignores interrupts: a thread stuck in `join()` stays stuck until the ticket completes. `getNow(fallback)` and `resultNow()` (JDK 19) never wait at all.

So build the whole pipeline without waiting. Then wait at most once, at the edge, on a thread that is allowed to wait, with a time limit. The edge is where your code meets the outside world, such as a request handler, the `main` method or a test:

```java
// a request thread that may wait, but not forever
Receipt r = checkout.checkout(cart, "USD").get(2, TimeUnit.SECONDS);
```

```kotlin
// a request thread that may wait, but not forever
val r = checkout.checkout(cart, "USD").get(2, TimeUnit.SECONDS)
```

Never call `join()` or `get()` inside a stage, on a ticket that may still be running. (On a ticket you know is complete, `join()` returns at once.) The stage runs on a pool thread, and that thread now sits idle until another task finishes. Picture a cook who stops cooking and stands at the counter, waiting for a dish that nobody is free to cook.

A few of those, and a small pool runs out of threads. If the task being waited for is queued behind them on the same pool, nothing ever finishes. That's the pool-induced deadlock from Callable, Future, cancellation and interruption, and lesson 9 of this track has you fix one. When a stage needs another async result, that's what `thenCompose` and `thenCombine` are for.

**Wait once, at the edge, with a time limit. Never wait inside a stage.**

The Try it below has a checkout that breaks this rule twice. Find both before you do the lab, which asks you to write it properly.

Every pipeline in this lesson has one limit: it assumes that each step succeeds, and none of its steps has a time limit. A rate service that throws, or never answers at all, needs tools we haven't met yet."""

ASIDE3 = {
    "title": "If you write web services, do you need to wait at all?",
    "body": "Often not. Many web frameworks let a request handler return a `CompletionStage<T>`, the interface that holds `CompletableFuture`'s composing methods, instead of a finished value. The framework then sends the response when the stage completes, and no request thread waits in the meantime. Spring and Quarkus both work this way. If your framework offers it, return the pipeline and let the framework do the waiting."
}

L = {
 "id": "exec-06",
 "title": "CompletableFuture: composing async steps",
 "minutes": 35,
 "goal": "By the end you can build a pipeline that never waits with supplyAsync, thenApply, thenCompose and thenCombine, say which thread runs each step, and keep slow calls off the common pool.",
 "opening": OPENING,
 "warmup": {
  "q": "On an 8-core machine running JDK 21, a shop's program calls `CompletableFuture.supplyAsync(() -> bank.charge(card))` with no pool. Where does the 200 ms call to the bank run?",
  "options": [
   "On the thread that called `supplyAsync`, a little later",
   "On a virtual thread created for the call",
   "On a worker of `ForkJoinPool.commonPool()`, which the whole JVM shares",
   "On a new thread created for the call"
  ],
  "answer": 2,
  "why": "With no pool, the async methods use the common pool, one pool that every parallel stream in the JVM uses too. On 8 cores it has 7 threads. A new thread per task only happened on JDK 21 to 24 when the common pool had fewer than 2 threads, as in a container with 2 CPUs, and JDK 25 removed even that. You get a virtual thread only if you pass a virtual-thread executor. The first section shows the thread names."
 },
 "sections": [
  {
   "h": "A ticket that knows the next step: CompletableFuture, and the pool that runs it",
   "body": S0,
   "try": {
    "title": "Find out who runs your task",
    "minutes": 3,
    "steps": [
     "Run `WhoRunsItDemo`. Note the thread names with and without a pool.",
     "Run it again with `-Pargs=1cpu`, which sizes the common pool as a 2-CPU container would. Predict the names first. Does your JDK version change the answer?"
    ],
    "code": demo("WhoRunsItDemo"),
    "expect": "Without a pool, every call runs on `ForkJoinPool.commonPool-worker-N`; with `io`, on `io-1` and `io-2`. With `1cpu` on JDK 21 to 24, the calls without a pool run on `Thread-0`, `Thread-1` and `Thread-2`, a new thread for each task. On JDK 25 or later, they all run on `ForkJoinPool.commonPool-worker-1`."
   },
   "refs": [
    {"title": "CompletableFuture (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html", "kind": "docs"}
   ]
  },
  {
   "h": "Clipping on instructions: thenApply maps, thenCompose flattens, thenCombine waits for two",
   "body": S1,
   "figure": {"svg": SVG, "caption": "The checkout from the demo and the lab: two calls side by side, joined by thenCombine, then the charge's own ticket flattened by thenCompose."},
   "try": {
    "title": "Side by side, or one after the other",
    "minutes": 4,
    "steps": [
     "Run `CombineDemo`. The price and the rate each take 300 ms. Read the times.",
     "Run it with `-Pargs=chain`, which fetches the rate inside `thenCompose`, after the price. Predict the total time before you run it.",
     "In the `chain` branch, change `thenCompose` to `thenApply` and compile again. Read what the compiler says about the type, then undo the change."
    ],
    "code": demo("CombineDemo"),
    "expect": "The default run prints the price and the rate at about 300 ms, on `io-1` and `io-2`, and charges 108.42 USD right after. With `chain`, the rate arrives at about 600 ms. With `thenApply`, the code no longer compiles: the result is now a `CompletableFuture<CompletableFuture<BigDecimal>>`, a ticket for a ticket, and `usd` is declared as a `CompletableFuture<BigDecimal>`."
   }
  },
  {
   "h": "Who carries the order to the next station: the thread that runs each step",
   "body": S2,
   "try": {
    "title": "Predict four thread names",
    "minutes": 3,
    "steps": [
     "Read `WhichThreadDemo` and write down the thread you expect for each numbered line.",
     "Run it and compare. For line 2, explain why it isn't `main`, even though `main` called `thenApply`."
    ],
    "code": demo("WhichThreadDemo"),
    "expect": "`main`, `io-1`, `ForkJoinPool.commonPool-worker-1` and `cpu-1`. Line 2 runs on `io-1` because the step was clipped on while the task was still sleeping, so the thread that completed it ran the step. If your machine paused `main` for more than 200 ms between those two lines, you'd see `main` there instead, which is the whole point: timing decides."
   }
  },
  {
   "h": "Getting the value out: join, get, and the one place you may wait",
   "body": S3,
   "aside": ASIDE3,
   "try": {
    "title": "Spot the waiting calls",
    "minutes": 4,
    "steps": [
     "Read this method. Mark every line that makes a thread wait, and say which thread.\n\n```java\nCompletableFuture<Receipt> checkout(String cart) {\n    BigDecimal price = CompletableFuture.supplyAsync(() -> prices.priceEur(cart), io).join();   // A\n    CompletableFuture<BigDecimal> rate = CompletableFuture.supplyAsync(() -> fx.rate(\"EUR\", \"USD\"), io);\n    return rate.thenApply(r -> {\n        BigDecimal amount = price.multiply(r);\n        String id = gateway.charge(cart, amount, \"USD\").join();                                 // B\n        return new Receipt(cart, amount, \"USD\", id);\n    });\n}\n```\n\n```kotlin\nfun checkout(cart: String): CompletableFuture<Receipt> {\n    val price = CompletableFuture.supplyAsync({ prices.priceEur(cart) }, io).join()              // A\n    val rate = CompletableFuture.supplyAsync({ fx.rate(\"EUR\", \"USD\") }, io)\n    return rate.thenApply { r ->\n        val amount = price * r\n        val id = gateway.charge(cart, amount, \"USD\").join()                                     // B\n        Receipt(cart, amount, \"USD\", id)\n    }\n}\n```",
     "Sketch the fix with `thenCombine` and `thenCompose`. The lab asks you to write it for real."
    ],
    "expect": "A makes the caller wait for the whole price call, and because the rate call starts only after it, the two calls run one after the other. B makes whichever thread completes `rate` (an `io` thread) wait for as long as the payment service takes. The fix starts both `supplyAsync` calls first, combines them with `thenCombine`, and calls `gateway.charge` inside `thenCompose`, so no thread waits anywhere inside `checkout`."
   }
  }
 ],
 "compare": {
  "title": "Two lookups side by side, then an async call",
  "java": {"title": "Delivery.java (CompletableFuture)", "src": "CompletableFuture<String> confirm(String orderId) {\n    CompletableFuture<Address> address = CompletableFuture.supplyAsync(() -> customers.address(orderId), io);\n    CompletableFuture<Duration> cooking = CompletableFuture.supplyAsync(() -> kitchen.cookTime(orderId), io);\n\n    return address\n            .thenCombine(cooking, (a, t) -> new RideRequest(a, t))\n            .thenCompose(riders::book)\n            .thenApply(ride -> \"Your food arrives at \" + ride.eta());\n}"},
  "kotlin": {"title": "Delivery.kt (kotlinx.coroutines)", "src": "suspend fun confirm(orderId: String): String = coroutineScope {\n    val address = async(Dispatchers.IO) { customers.address(orderId) }   // both start now\n    val cooking = async(Dispatchers.IO) { kitchen.cookTime(orderId) }\n\n    val request = RideRequest(address.await(), cooking.await())\n    val ride = riders.book(request).await()      // pauses on the CompletableFuture, holds no thread\n    \"Your food arrives at ${ride.eta}\"\n}"},
  "note": "The Java version is a chain of instructions: each method clips on a step, and you think about which thread runs each one. The Kotlin version reads top to bottom. It runs in coroutines, Kotlin's light tasks that can pause without holding a thread. `async` starts the two lookups at once, `await()` pauses the coroutine until a result is ready, and the `await()` extension from `kotlinx.coroutines.future` turns the rider service's `CompletableFuture` into a pause point. The structure differs too. If the cooking-time lookup fails, `coroutineScope` cancels the address lookup and rethrows. `thenCombine` does nothing like that: the address lookup keeps running, and its result is thrown away. The coroutines track covers the details."
 },
 "worked": {
  "title": "Turn a waiting delivery order into a pipeline",
  "steps": [
   {"say": "A food-delivery shop confirms each order. It looks up the customer's address (40 ms) and the kitchen's cooking time (60 ms), books a delivery rider with a rider service whose client already returns a `CompletableFuture` (120 ms), and tells the customer when the food arrives. This version takes 40 + 60 + 120 = 220 ms per order, and holds a thread for all of it. Before reading on, mark which calls depend on which.",
    "code": "String confirm(String orderId) {\n    Address address = customers.address(orderId);           // 40 ms\n    Duration cooking = kitchen.cookTime(orderId);            // 60 ms\n    Ride ride = riders.book(new RideRequest(address, cooking)).join();   // 120 ms\n    return \"Your food arrives at \" + ride.eta();\n}", "lang": "java",
    "alt_code": "fun confirm(orderId: String): String {\n    val address = customers.address(orderId)                 // 40 ms\n    val cooking = kitchen.cookTime(orderId)                  // 60 ms\n    val ride = riders.book(RideRequest(address, cooking)).join()   // 120 ms\n    return \"Your food arrives at ${ride.eta}\"\n}", "alt_lang": "kotlin"},
   {"say": "The address and the cooking time don't depend on each other. The rider needs both, and the message needs the rider. So the best case is max(40, 60) + 120 = 180 ms, and only if the two lookups start together. Start both first, on the `io` pool, because they wait.",
    "code": "// 1. start the independent lookups together\nCompletableFuture<Address> address = CompletableFuture.supplyAsync(() -> customers.address(orderId), io);\nCompletableFuture<Duration> cooking = CompletableFuture.supplyAsync(() -> kitchen.cookTime(orderId), io);", "lang": "java",
    "alt_code": "// 1. start the independent lookups together\nval address = CompletableFuture.supplyAsync({ customers.address(orderId) }, io)\nval cooking = CompletableFuture.supplyAsync({ kitchen.cookTime(orderId) }, io)", "alt_lang": "kotlin"},
   {"say": "Join the two with `thenCombine`. Building the request is cheap, so the plain method is right. The rider service returns its own ticket, so flatten it with `thenCompose`, and finish with a cheap `thenApply`.",
    "code": "return address\n        .thenCombine(cooking, (a, t) -> new RideRequest(a, t))      // 2. wait for both\n        .thenCompose(riders::book)                                  // 3. async call, flattened\n        .thenApply(ride -> \"Your food arrives at \" + ride.eta());   // 4. cheap mapping", "lang": "java",
    "alt_code": "return address\n    .thenCombine(cooking) { a, t -> RideRequest(a, t) }         // 2. wait for both\n    .thenCompose(riders::book)                                  // 3. async call, flattened\n    .thenApply { ride -> \"Your food arrives at ${ride.eta}\" }   // 4. cheap mapping", "alt_lang": "kotlin"},
   {"say": "The method now returns `CompletableFuture<String>` and waits for nothing. The request handler that calls it waits once, with a time limit. A framework that accepts a `CompletionStage` gets the ticket itself instead.",
    "code": "String message = confirm(orderId).get(2, TimeUnit.SECONDS);   // 5. wait once, at the edge", "lang": "java",
    "alt_code": "val message = confirm(orderId).get(2, TimeUnit.SECONDS)       // 5. wait once, at the edge", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Build a checkout that never waits",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/Checkout.java", f"{lab}/main/{P}/PaymentGateway.java", f"{lab}/main/{P}/Receipt.java"],
  "run": "./gradlew :executors:test --tests 'workbench.executors.l06.*'",
  "steps": [
   "Run the tests. All six fail with `UnsupportedOperationException`. Read the Javadoc on `Checkout.checkout`: it is the spec.",
   "Start the two slow calls first: `supplyAsync` for `prices.priceEur(cartId)` and for `fx.rate(\"EUR\", currency)`, both on `io`.",
   "Combine them with `thenCombine` into the amount: `price.multiply(rate).setScale(2, RoundingMode.HALF_EVEN)`, which rounds to cents.",
   "Charge with `thenCompose`, because `gateway.charge` (the payment service) already returns a `CompletableFuture<String>`. Build the `Receipt` from the amount and the charge ID.",
   "Run the tests until all six pass, then run them once more."
  ],
  "hints": [
   "`fetchesInParallel` makes each call wait at a barrier until the other one arrives. If it times out, your rate call starts only after the price is back.",
   "`composesTheCharge` gives the checkout an `io` pool with a single thread. If it fails, a stage is calling `join()` or `get()` on the payment service's ticket, and holding that thread.",
   "The receipt needs the amount, which only exists inside the `thenCompose` lambda. Clip `.thenApply(chargeId -> new Receipt(...))` onto the payment service's ticket inside that lambda, so `amount` is still in scope."
  ],
  "done_when": "All six tests in `CheckoutTest` pass."
 },
 "drill": {
  "title": "Two lookups and a send, from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `CompletableFuture<Void> sendPointsReminder(String customerId)`. It fetches the customer's name (`customers.name(id)`, which waits) and their loyalty points (`loyalty.points(id)`, which waits) side by side on `io`. It formats a line such as `\"Ana: 1250 points\"`, and sends it with `mailer.send(line)`, which returns a `CompletableFuture<Void>`. Nothing may wait. Then compare: did you start both lookups before clipping anything on?",
  "answer": {"lang": "java", "title": "Reminder.java", "src": "CompletableFuture<Void> sendPointsReminder(String customerId) {\n    CompletableFuture<String> name = CompletableFuture.supplyAsync(() -> customers.name(customerId), io);\n    CompletableFuture<Integer> points = CompletableFuture.supplyAsync(() -> loyalty.points(customerId), io);\n    return name\n            .thenCombine(points, (n, p) -> n + \": \" + p + \" points\")   // cheap, plain method\n            .thenCompose(mailer::send);                                 // async call, flattened\n}",
   "alt": {"lang": "kotlin", "title": "Reminder.kt", "src": "fun sendPointsReminder(customerId: String): CompletableFuture<Void> {\n    val name = CompletableFuture.supplyAsync({ customers.name(customerId) }, io)\n    val points = CompletableFuture.supplyAsync({ loyalty.points(customerId) }, io)\n    return name\n        .thenCombine(points) { n, p -> \"$n: $p points\" }    // cheap, plain method\n        .thenCompose(mailer::send)                         // async call, flattened\n}"}}
 },
 "recap": [
  "`supplyAsync(task, pool)` starts work at once and returns a ticket. Without a pool, it uses `ForkJoinPool.commonPool()`, which the whole JVM shares.",
  "Up to JDK 24, a common pool with fewer than 2 threads (a container with 1 or 2 CPUs) meant a new thread per async task. From JDK 25, the common pool is always used. Pass a pool for anything that waits.",
  "`thenApply` maps with plain code, `thenCompose` flattens a step that returns a ticket, and `thenCombine` waits for two tickets.",
  "Work starts when you call `supplyAsync`. Start the independent calls first; a call started inside `thenCompose` waits for the stage before it.",
  "A plain step runs on the thread that completes the stage before it, or on the caller if that stage is already complete. `thenApplyAsync(fn, pool)` moves it to your pool.",
  "`get` throws the checked `ExecutionException`, and `join` the unchecked `CompletionException`. Wait once, at the edge, with a time limit. The limit: nothing here handles a step that fails or never finishes."
 ],
 "closing": "We started with a ticket for table 4 that carried its own instructions: when the steak and the sauce are ready, plate them. `CompletableFuture` is that ticket. We started the price and the rate side by side and joined them. Then we watched a chain that looked just as quick take twice as long, and found that whichever thread finishes a stage carries the next step.\n\nNow search your own code for `supplyAsync(` and `runAsync(` with a single argument. Each one should be short computing work, or get a pool.\n\nNext, we'll let a station fail. When the steak burns at the grill, or the rate service throws, which steps still run, and how do we put a time limit on the whole order?",
 "quiz": [
  {
   "q": "`menu.findAsync(name)` returns `CompletableFuture<Dish>`, and `kitchen.cookAsync(dish)` returns `CompletableFuture<Plate>`. What is the type of `menu.findAsync(name).thenApply(kitchen::cookAsync)`?",
   "options": [
    "`CompletableFuture<Plate>`",
    "`CompletableFuture<CompletableFuture<Plate>>`",
    "`Plate`",
    "It doesn't compile"
   ],
   "answer": 1,
   "why": "`thenApply` wraps whatever the function returns, and this function returns a ticket. You get a ticket for a ticket, and nothing waits for the inner one. `thenCompose` would flatten it to `CompletableFuture<Plate>`."
  },
  {
   "q": "`price()` and `rate()` each wait 200 ms for another service. Which version finishes in about 200 ms?",
   "options": [
    "`supplyAsync(() -> price(), io).thenCompose(p -> supplyAsync(() -> rate(), io).thenApply(p::multiply))`",
    "`supplyAsync(() -> price().multiply(rate()), io)`",
    "`supplyAsync(() -> price(), io).thenApply(p -> p.multiply(rate()))`",
    "`supplyAsync(() -> price(), io).thenCombine(supplyAsync(() -> rate(), io), BigDecimal::multiply)`"
   ],
   "answer": 3,
   "why": "Only the last one starts both calls before waiting for either. The other three are all asynchronous, but each runs `rate()` after `price()` has returned, so they take about 400 ms. Being asynchronous is not the same as running side by side."
  },
  {
   "q": "Ticket `f` has already completed. Request thread `http-7` calls `f.thenApply(this::render)`. Which thread runs `render`?",
   "options": [
    "`http-7`, right away",
    "A common pool worker",
    "The thread that completed `f`",
    "A new thread"
   ],
   "answer": 0,
   "why": "When the stage before it is already complete, a plain `thenApply` runs the function at once, on the calling thread. The thread that completed `f` finished its work earlier and plays no part. Only `thenApplyAsync` would hand it to a pool."
  },
  {
   "q": "A program on JDK 21 runs in a container with 2 CPUs. It calls `supplyAsync(() -> slowLookup())` with no pool, 300 times a second. What happens?",
   "options": [
    "The lookups queue up behind a single common pool thread",
    "They run on virtual threads",
    "They run on the calling threads",
    "Each lookup gets a new thread, with no upper limit"
   ],
   "answer": 3,
   "why": "With 2 CPUs, the common pool has one thread, and before JDK 25 `CompletableFuture` skipped the common pool when it had fewer than 2 threads. It created a thread per task instead. The first option is what JDK 25 does with the same code. Neither is acceptable for a call that waits: pass a pool."
  },
  {
   "q": "From \"Sizing a pool: CPU-bound, IO-bound and Little's law\": a checkout runs the price call (100 ms) and the rate call (100 ms) side by side on `io`, and you get 200 checkouts a second. How many `io` threads are busy on average?",
   "options": [
    "20",
    "40",
    "200",
    "400"
   ],
   "answer": 1,
   "why": "Little's law: L = λ x W. Each checkout holds two `io` threads for 0.1 s, so the pool sees 400 calls a second x 0.1 s = 40 busy threads. Running the calls side by side cuts the time each checkout takes; it doesn't cut the number of threads you need. Size the pool above 40, and check that the services you call accept that many calls at once.",
   "from": "exec-03"
  }
 ],
 "flashcards": [
  {"front": "`thenApply` vs `thenCompose`?", "back": "`thenApply` maps with a plain function (`T -> U`). `thenCompose` flattens a function that returns a ticket (`T -> CompletableFuture<U>`), like `flatMap`."},
  {"front": "What does `a.thenCombine(b, fn)` do?", "back": "It waits until both `a` and `b` complete, then applies `fn(aResult, bResult)`. It starts nothing: `a` and `b` must already be running to overlap."},
  {"front": "Which executor does `supplyAsync(task)` use on JDK 25?", "back": "`ForkJoinPool.commonPool()`, always. Up to JDK 24, it used a new thread per task when the common pool had fewer than 2 threads."},
  {"front": "Which thread runs a plain `thenApply` step?", "back": "The thread that completes the stage before it, or the calling thread if that stage is already complete."},
  {"front": "`join()` vs `get()` on a failed CompletableFuture?", "back": "`get()` throws the checked `ExecutionException`, `join()` the unchecked `CompletionException`. Both carry the failure as the cause."},
  {"front": "Why pass a pool to `supplyAsync` for calls that wait?", "back": "Without one, the calls hold common pool threads, which every parallel stream and every default async task in the JVM shares."}
 ],
 "terms": [
  {"term": "CompletableFuture", "plain": "A Future you can complete by hand and clip further steps onto."},
  {"term": "Stage", "plain": "One step in a pipeline: a ticket, plus the instruction that completes it from earlier results."},
  {"term": "thenCompose", "plain": "Clips on a step that returns another ticket, and gives you one flat ticket back."},
  {"term": "thenCombine", "plain": "Waits for two tickets and merges their results with a function."},
  {"term": "Default async executor", "plain": "Where async methods run when you pass no pool: the common ForkJoinPool."},
  {"term": "Common pool", "plain": "One ForkJoinPool per JVM, with one thread fewer than the cores, shared by parallel streams and default async tasks."}
 ],
 "explain_back": {
  "prompt": "A teammate wrote `supplyAsync(() -> prices.price(cart)).thenCompose(p -> supplyAsync(() -> fx.rate(cur)).thenApply(p::multiply))`. Explain what is slower than it needs to be, what is risky, and what you'd change.",
  "answer": "It's slow because the rate call only starts inside thenCompose, after the price has come back, so the time is the sum of both calls instead of the slower one. Starting both supplyAsync calls first and joining them with thenCombine makes them overlap. It's risky because neither supplyAsync has a pool, so two calls that wait for other services run on the common pool, which has one thread fewer than the cores for the whole JVM and is shared with parallel streams. Under load they hold up everyone else, and on a small container before JDK 25 each call even gets its own new thread. I'd pass a pool meant for waiting calls, sized for the traffic, to both supplyAsync calls."
 },
 "deeper": {
  "minutes": 8,
  "body": "The stack of instructions from the third section has one more consequence. One slow plain step delays every other plain step clipped onto the same ticket, because the completing thread runs them one after another.\n\n`CompletableFuture` implements two interfaces. `Future` gives you `get` and `cancel`. `CompletionStage` has the composing methods, and nothing that completes the ticket or waits for it. When you write an API, return `CompletionStage<T>`, or call `minimalCompletionStage()` (JDK 9). Then callers can't call `complete` or `obtrudeValue` on your ticket and change a result you already computed. A caller who needs to wait can still call `toCompletableFuture().join()`, which makes the waiting visible in their code.\n\nThere are a few other ways to get a ticket. `completedFuture(v)` and `failedFuture(ex)` (JDK 9) are handy in tests. `new CompletableFuture<>()` plus `complete(v)` connects any library that reports its answer through a callback, a method the library calls when the answer arrives. And `completeAsync(supplier, executor)` (JDK 9) completes an existing ticket from a task, which helps when you must hand out the ticket before you know which pool will do the work."
 },
 "sources": [
  {"title": "CompletableFuture (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html"},
  {"title": "CompletionStage (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletionStage.html"},
  {"title": "Composing suspending functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/composing-suspending-functions.html"},
  {"title": "CompletionStage.await (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.future/await.html"}
 ]
}
out = ROOT / "content/lessons/exec-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
