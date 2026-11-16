import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/executors/src"
P = "java/workbench/executors/l04"
KP = "kotlin/workbench/executors/l04"
read = lambda p: (ROOT / p).read_text()

def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l04.{name}",
            "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{KP}/{name}.kt"),
                    "run": f"./gradlew :executors:demo -Pmain=workbench.executors.l04.{name}Kt",
                    "file": f"{lab}/demo/{KP}/{name}.kt"}}

SVG = (
    '<svg viewBox="0 0 640 250" role="img" aria-label="Future states: RUNNING moves to SUCCESS, FAILED or CANCELLED, and get() behaves differently in each">'
    '<rect class="box-a" x="20" y="97" width="150" height="56" rx="8"/>'
    '<text class="t t-code" x="95" y="121" text-anchor="middle">RUNNING</text>'
    '<text class="t-s t-m" x="95" y="141" text-anchor="middle">get() blocks</text>'
    '<rect class="box-ok" x="380" y="15" width="240" height="56" rx="8"/>'
    '<text class="t t-code" x="500" y="39" text-anchor="middle">SUCCESS</text>'
    '<text class="t-s" x="500" y="59" text-anchor="middle">get(), resultNow(): the value</text>'
    '<rect class="box-bad" x="380" y="97" width="240" height="56" rx="8"/>'
    '<text class="t t-code" x="500" y="121" text-anchor="middle">FAILED</text>'
    '<text class="t-s" x="500" y="141" text-anchor="middle">get() throws, exceptionNow() works</text>'
    '<rect class="box-dim" x="380" y="179" width="240" height="56" rx="8"/>'
    '<text class="t t-code" x="500" y="203" text-anchor="middle">CANCELLED</text>'
    '<text class="t-s" x="500" y="223" text-anchor="middle">get() throws CancellationException</text>'
    '<line class="ln-a" x1="170" y1="110" x2="376" y2="45" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="262" y="66" text-anchor="middle">task returns</text>'
    '<line class="ln" x1="170" y1="125" x2="376" y2="125" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="272" y="116" text-anchor="middle">task throws</text>'
    '<line class="ln-d" x1="170" y1="140" x2="376" y2="205" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="236" y="196" text-anchor="middle">cancel()</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Picture a takeaway counter. You order a burger, pay, and the cashier hands you a ticket with the number 42 on it. The burger doesn't exist yet. The ticket promises that it will, and lets you collect it.

With the ticket, you can do three things. You can wait at the counter until 42 is called. You can wait only five minutes, because your bus is coming. Or you can glance at the screen to see whether it's ready.

Say you give up after five minutes and catch your bus. Nobody tells the kitchen. At minute seven your burger is ready, hot and paid for, with nobody to eat it.

Java's thread pools hand out the same kind of ticket, with the same gap. (A thread pool is a small team of threads, paths of work that run side by side, taking tasks from a queue.) Sizing a pool ended on a question: how do we stop a thread that waits too long? In this lesson, we'll wait for a result with a time limit, ask a task to stop, and keep that request from getting lost. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Start with a shop's website. When a customer pays, the program asks the bank to charge their card. The bank is another computer, so the program sends a request over the network and waits for the answer. On a normal day, that's about 200 ms. (It's the bank from Sizing a pool.)

We'd like to hand that call to a thread pool and get the answer back. In Why pools, every task was a `Runnable`, whose `run()` method returns nothing. A task that should hand back an answer is a **`Callable<V>`** instead. Its `call()` method returns a value of type `V`, and it may throw any exception, even a checked one.

You give a `Callable` to the pool with `submit`, and the pool gives you a `Future<V>` back at once. A **`Future`** is the ticket from the counter: a promise of a result that doesn't exist yet. Here's the smallest one, with a task that just multiplies:

```java
Future<Integer> answer = pool.submit(() -> 6 * 7);   // returns at once, with a ticket
int n = answer.get();                                // waits for the task: 42
```

```kotlin
val answer: Future<Int> = pool.submit<Int> { 6 * 7 }  // returns at once, with a ticket
val n = answer.get()                                  // waits for the task: 42
```

`get()` is the wait at the counter. It **blocks**: the calling thread stops and does nothing else until the task has finished. Then `get()` hands over the value.

If the task threw an exception, `get()` throws an `ExecutionException` with the task's own exception inside it, as its cause. If someone cancelled the task, it throws `CancellationException`. And if your own thread is asked to stop while it waits, it throws `InterruptedException`, which the next two sections are about. (A successful `get()` also makes everything the task wrote visible to the thread that got the result. The memory model track explains why that matters.)

Plain `get()` waits as long as the task takes. If the bank takes 30 seconds, your customer waits 30 seconds. So real code waits with a time limit, `get(200, TimeUnit.MILLISECONDS)`, which throws `TimeoutException` if the answer isn't there in time. That's the five minutes before the bus.

Now the trap from the counter. `TimeoutDemo`, in the Try it below, asks a bank that's having a slow day and takes 600 ms, and it waits only 200 ms. Each line shows the time, the thread and what happened. On a busy machine, it printed:

```text
  86 ms  pool-1-thread-1 asking the bank to charge the card
 285 ms  main         get timed out after 200 ms
 771 ms  pool-1-thread-1 bank answered: APPROVED (the card was charged)
 773 ms  main         pool closed
```

The `main` thread gave up at 285 ms. In a real shop, that's the moment the program tells the customer the payment failed. The task didn't know. It kept waiting for the bank, and at 771 ms the bank charged the card. The customer heard "failed" and paid anyway, which is the one combination nobody wants.

So the bank call is the burger at minute seven. A time limit on `get` ends your wait. It says nothing to the task, which keeps going until it's done.

**A time limit ends your wait, not the work. Decide what happens to the work.**

You have two choices. Stop the work, or make sure its result is written down somewhere you can find it later. Stopping it means asking the task, and Java's way of asking does less than its name suggests."""

ASIDE0 = {
    "title": "Why doesn't a time limit cancel the task for me?",
    "body": "One good reason: a ticket can have many people waiting on it. Several threads may call `get` on the same `Future`, each with its own time limit. If the first impatient one cancelled the task, the others would lose their result too. And sometimes you still want the result after you stop waiting, for example to record what the bank said. So `Future` leaves that choice to you: call `cancel` yourself, when you mean it."
}

# ---------------------------------------------------------------- section 1
S1 = """The `cancel` run of `TimeoutDemo` looked easy. We cancelled, and the task stopped within a few milliseconds. Here it is, from the same busy machine:

```text
  60 ms  pool-1-thread-1 asking the bank to charge the card
 257 ms  main         get timed out after 200 ms
 260 ms  pool-1-thread-1 interrupted: giving up on the bank
 275 ms  main         cancel(true) returned true
 280 ms  main         pool closed
```

To see why it worked, and when it won't, we need to know what `cancel` actually does.

`Future.cancel(boolean mayInterruptIfRunning)` has two modes. `cancel(false)` stops a task that hasn't started yet, so it never runs, and leaves a running task alone. `cancel(true)` does the same, and if the task is running, it also interrupts the thread that runs it.

An **interrupt** is a request to a thread to stop what it's doing. It sets a true-or-false value inside the thread, called the **interrupt flag**. If the thread is blocked at that moment, waiting in a method such as `Thread.sleep`, `BlockingQueue.take` or `Future.get`, that method wakes up and throws `InterruptedException`. If the thread is busy computing, nothing happens to it. The flag stays set until the thread looks at it.

Setting the flag is all `cancel(true)` does. Java has no safe way to kill a thread from outside. `Thread.stop()` was deprecated, marked as "don't use", for decades, has thrown `UnsupportedOperationException` since JDK 20, and was removed in JDK 26. So cancelling is **cooperative**: it works only if the task helps.

Picture the interrupt as a note that the manager puts on a cook's station: "please stop order 42". Our kitchen has three cooks. The first is waiting for the oven. The second is chopping onions, and looks up after each one. The third is chopping too, and never looks up.

The task in `TimeoutDemo` was the first cook. It was waiting in `Thread.sleep`, which stands in for the wait for the bank's answer, so the note woke it at once.

`CancelDemo` builds all three cooks in code. The sleeper sleeps. The checker does 400 slices of arithmetic, a few milliseconds each, and checks `Thread.currentThread().isInterrupted()` before each slice. The ignorer does the same work and never checks. After 100 ms, `main` calls `cancel(true)` on all three:

```text
after cancel: isCancelled=true/true/true isDone=true/true/true
sleeper: InterruptedException, stopping
checker: saw the flag after 51 slices, stopping
ignorer: finished all 400 slices anyway, 769 ms after the cancel
pool closed
```

Read the first line again. All three futures said cancelled and done straight away, before any task had reacted. A `Future` changes its state the moment you call `cancel`. It doesn't wait for the task to stop.

Then each cook did what that cook does. The sleeper, waiting for the oven, was woken by the note. The checker saw it the next time it looked up. The ignorer chopped on for another 769 ms, as if nobody had said a word. If its work had been charging a card, the card would be charged, under a ticket that says cancelled.

Here the kitchen picture breaks in two places. A real cook hears you shout across the room, but a thread hears nothing unless it's waiting or it looks. And a real kitchen can tell you whether the dish was made. A cancelled `Future` can't. It only knows that nobody will collect a result.

**Cancelling only asks. The task must listen, and the ticket can't tell you whether it did.**

So a long computing loop should look up now and then, as the checker does. In the Try it, you'll teach the ignorer that habit.

`cancel(false)` has its own use. When a program shuts down, you may want running tasks to finish but queued ones never to start. Cancel the queued ones with `false`. And `cancel` returns `false` if the task had already finished or was already cancelled, which tells you the request came too late.

The sleeper stopped because `sleep` threw `InterruptedException`. What a task does with that exception decides whether the stop request survives."""

# ---------------------------------------------------------------- section 2
S2 = """Here's a task that does almost everything right. `StatementPoller`, from this lesson's lab, asks the bank every so often for new lines on an account statement, the list of money in and out of an account. It runs as a task on a pool. It should stop when someone shuts the pool down with `shutdownNow()`, or cancels the task with `cancel(true)`. Both of those interrupt its thread. Here's its starting code:

```java
// Naive: the stop request is lost in pause()
public void run() {
    while (!Thread.currentThread().isInterrupted()) {
        pollOnce.run();
        polls.incrementAndGet();
        pause();
    }
}

private void pause() {
    try {
        Thread.sleep(interval.toMillis());
    } catch (InterruptedException e) {
        // nothing useful to do here; the loop will carry on
    }
}
```

```kotlin
// Naive: the stop request is lost in pause()
override fun run() {
    while (!Thread.currentThread().isInterrupted) {
        pollOnce.run()
        polls.incrementAndGet()
        pause()
    }
}

private fun pause() {
    try {
        Thread.sleep(interval.toMillis())
    } catch (e: InterruptedException) {
        // nothing useful to do here; the loop will carry on
    }
}
```

(The lab is in Java. The Kotlin version is a translation, so you can read it in either language.)

The loop checks the flag on every pass, so it looks right. Yet in the lab's tests, `shutdownNow()` returns, `awaitTermination` (which waits for the pool to finish) runs out its full five seconds, and the poller keeps polling. Let's follow one stop request through it, step by step:

1. The poller is asleep in `Thread.sleep`, where it spends nearly all its time.
2. The test calls `shutdownNow()` on the pool, which interrupts the poller's thread.
3. `sleep` wakes up. Before it throws `InterruptedException`, it clears the interrupt flag.
4. `pause()` catches the exception, does nothing, and returns.
5. The loop checks `isInterrupted()`. The flag is clear, so the check reads `false`, and the poller polls again.

Nobody interrupts it a second time, so it never stops.

Step 3 is the one people miss. In A thread's life, the interrupt was a note on a clerk's desk, and waking up tore the note off. Inside the catch block, you hold the only copy of the request. If you drop it, no code further up can ever see it.

So there are two correct moves. Let the exception travel up to your caller, or put the note back with `Thread.currentThread().interrupt()` before you go on. Here they are on a task that clips a ticket onto the kitchen's rail, a `BlockingQueue` whose `put` waits while the rail is full:

```java
// 1. propagate: declare it and let it go up
void clip(Ticket t) throws InterruptedException {
    rail.put(t);
}

// 2. you can't propagate (Runnable.run can't throw it): restore the flag
public void run() {
    try {
        rail.put(ticket);
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();   // put the request back
        return;                               // and stop
    }
}
```

```kotlin
// 1. propagate: Kotlin has no checked exceptions, so simply don't catch it
fun clip(t: Ticket) {
    rail.put(t)
}

// 2. if you do catch it: restore the flag
override fun run() {
    try {
        rail.put(ticket)
    } catch (e: InterruptedException) {
        Thread.currentThread().interrupt()    // put the request back
        return                                // and stop
    }
}
```

Wrapping it in an exception of your own is fine, as long as you restore the flag first. Logging it and moving on is not. From JDK 26, the `Thread` Javadoc has a section on interruption that states this same rule.

**A swallowed interrupt makes `shutdownNow()` and `cancel(true)` do nothing. Rethrow it, or restore it.**

A request can get lost in one more place: a thread waiting for another computer's answer. Whether that thread notices an interrupt depends on how it reads from the network. A read through a channel from `java.nio.channels`, Java's newer networking classes, does notice: the JDK closes the channel and the read fails. A read from a classic `java.net.Socket` on a platform thread, an ordinary operating-system thread, doesn't notice and waits on. So give every call to another computer its own time limit, and treat the interrupt as a second line of defense.

Check yourself before you go on. A task catches `InterruptedException` from `sleep`, logs it, and goes back to sleep. Does the second `sleep` throw at once? No. The flag was cleared, so it sleeps its full time. Add `Thread.currentThread().interrupt()` to the catch, and the second `sleep` throws straight away, because `sleep` checks the flag before it starts to wait.

The stop request survives now. One part of the ticket is still clumsy, though: to find out how a task ended, we call `get()` and catch every exception it can throw."""

# ---------------------------------------------------------------- section 3
S3 = """Before JDK 19, the only way to ask a `Future` how its task ended was to call `get()` inside a `try`, with a `catch` for each outcome. JDK 19 added `state()`, the glance at the screen. It never blocks, and it returns one of four values: `RUNNING`, `SUCCESS`, `FAILED` or `CANCELLED`. Two more methods read a finished ticket without any checked exceptions:

```java
switch (f.state()) {
    case RUNNING   -> log.info("still waiting for the bank");
    case SUCCESS   -> record(f.resultNow());                           // the value
    case FAILED    -> log.warn("bank call failed", f.exceptionNow());  // the task's own exception
    case CANCELLED -> log.info("cancelled");
}
```

```kotlin
when (f.state()) {
    Future.State.RUNNING -> log.info("still waiting for the bank")
    Future.State.SUCCESS -> record(f.resultNow())                          // the value
    Future.State.FAILED -> log.warn("bank call failed", f.exceptionNow())  // the task's own exception
    Future.State.CANCELLED -> log.info("cancelled")
}
```

`resultNow()` gives you the value, and `exceptionNow()` gives you the task's own exception, without the `ExecutionException` around it. Both are for tickets you know are finished.

`resultNow()` throws `IllegalStateException` if the task isn't done or didn't succeed. `exceptionNow()` throws it if the task didn't fail, and a cancelled task didn't fail. So check `state()` first, as the `switch` does. The lab's `Futures.describe` is this `switch`, turned into one line for a log.

A pool can also handle a whole list of tickets for you. Picture phoning three shops to ask whether they have an item in stock, and taking the first "yes". `ExecutorService`, the interface every pool in this track implements, has two methods for jobs like that:

- `invokeAll(tasks)` runs every task and returns all their futures once every one has finished. With a time limit, it cancels whatever isn't done by then, so every future it returns is finished.
- `invokeAny(tasks)` returns the result of the first task that succeeds. It cancels the rest, and it throws `ExecutionException` only if every task fails.

`InvokeAnyDemo` asks three exchange-rate services for today's rate from euros to US dollars, that is, how many dollars one euro buys. Alpha takes 300 ms. Beta takes 100 ms and then fails. Gamma takes 200 ms. Before reading on, guess what `invokeAny` returns:

```text
invokeAny -> gamma EUR/USD 1.0842
  alpha: interrupted, cancelled
invokeAll with a 250 ms deadline:
  alpha: interrupted, cancelled
  CANCELLED
  FAILED: beta is down
  SUCCESS: gamma EUR/USD 1.0842
```

Beta answered first, and its answer was that it was down. A failure doesn't count as an answer, so `invokeAny` waited for gamma, took its rate, and interrupted alpha, which was still on the phone. Then `invokeAll`, with a 250 ms deadline, returned one ticket of each kind: alpha cancelled at the deadline, beta failed, gamma succeeded.

Both methods block the thread that calls them until they return. So call them from a thread that is allowed to wait, never from a task running on the same small pool.

Here's why. Picture a pool of 3 threads, running 3 tasks that each call `invokeAll` with 3 subtasks on that same pool. All three threads now wait for subtasks, and no thread is free to run one. Nothing ever moves again. Lesson 9 of this track calls that pool-induced deadlock, and has you fix one.

**`state()` reads a ticket without waiting. Check it before you call `resultNow()`.**

We now have the whole ticket: collect it, wait with a limit, cancel it, read it at a glance. What a ticket can't do is come back on its own, every few seconds, all day."""

L = {
 "id": "exec-04",
 "title": "Callable, Future, cancellation and interruption",
 "minutes": 35,
 "goal": "By the end you can wait for a task with a time limit, cancel it in a way that really stops it, and handle InterruptedException so a stop request is never lost.",
 "opening": OPENING,
 "warmup": {
  "q": "A request thread calls `future.get(200, MILLISECONDS)` on a task that asks the bank to charge a card. The bank takes 600 ms to answer, so `get` throws `TimeoutException`. What happens to the charge?",
  "options": [
   "It is cancelled, because the time limit cancels the task",
   "It goes ahead, and the card is charged about 400 ms later",
   "It is undone when TimeoutException is thrown",
   "The task gets a TimeoutException too, and stops"
  ],
  "answer": 1,
  "why": "The time limit ends your wait, not the task. Nothing tells the task that you gave up, so it keeps going, and the bank charges the card. To stop it, you must call `cancel(true)`, and even that only sends a request, which the task may or may not notice in time. The first section shows it happening."
 },
 "sections": [
  {
   "h": "A claim ticket for a result: Callable, Future and a wait with a time limit",
   "body": S0,
   "aside": ASIDE0,
   "try": {
    "title": "Give up on a slow bank",
    "minutes": 3,
    "steps": [
     "Run `TimeoutDemo` in either language. Compare the time on the `bank answered` line with the time on the `get timed out` line.",
     "Run it again with `-Pargs=cancel`. That version calls `cancel(true)` right after the time limit. Before you run it, predict: does the bank still answer?"
    ],
    "code": demo("TimeoutDemo"),
    "expect": "Without `cancel`, the bank answers at about 600 to 800 ms, long after `get` gave up, and the pool closes only then, because `close()` waits for the task. With `cancel`, the task prints `interrupted: giving up on the bank` a few milliseconds after the time limit, `cancel(true)` returns `true`, and the pool closes at once. The next section explains why it worked here."
   },
   "refs": [
    {"title": "Future (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Future.html", "kind": "docs"}
   ]
  },
  {
   "h": "Asking the kitchen to stop: cancel(true) sends an interrupt, nothing more",
   "body": S1,
   "try": {
    "title": "Cancel three kinds of task",
    "minutes": 4,
    "steps": [
     "Run `CancelDemo` and match each line of the output to one of the three cooks.",
     "Teach the ignorer to look up: copy the checker's `isInterrupted()` check, with its `return`, into the ignorer's loop. Predict how long after the cancel it stops now, then run it."
    ],
    "code": demo("CancelDemo"),
    "expect": "First run: the sleeper and the checker stop within a few milliseconds of the cancel. The ignorer runs on for hundreds of milliseconds (769 ms in the run above, on a busy machine), and `close()` waits for it, so `pool closed` comes last. After your change, the ignorer stops after a few dozen slices too, and `pool closed` follows the cancel almost at once."
   }
  },
  {
   "h": "Keeping the stop request alive: rethrow InterruptedException or restore the flag",
   "body": S2
  },
  {
   "h": "Reading the ticket without waiting: Future.state(), invokeAll and invokeAny",
   "body": S3,
   "figure": {"svg": SVG, "caption": "A Future starts RUNNING and ends in one of three states. state() tells you which, without waiting."},
   "try": {
    "title": "First good answer wins",
    "minutes": 3,
    "steps": [
     "Read the three services in `InvokeAnyDemo`: alpha takes 300 ms, beta fails after 100 ms, gamma takes 200 ms. Predict what `invokeAny` returns and which service gets interrupted.",
     "Predict the three states that `invokeAll` reports with its 250 ms deadline. Then run the demo."
    ],
    "code": demo("InvokeAnyDemo"),
    "expect": "`invokeAny` returns gamma's rate. Beta finished first, but it failed, and a failure doesn't count. Alpha prints `interrupted, cancelled`. With the 250 ms deadline, `invokeAll` reports alpha `CANCELLED` (interrupted at the deadline), beta `FAILED` with `beta is down`, and gamma `SUCCESS`."
   },
   "refs": [
    {"title": "ExecutorService (Java SE 25 API): invokeAll and invokeAny", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ExecutorService.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "Cancelling work: a Future and an interrupt vs a coroutine",
  "java": {"title": "CancelOne.java", "src": "Future<String> f = pool.submit(() -> {\n    Thread.sleep(5_000);          // wakes with InterruptedException on cancel(true)\n    return \"done\";\n});\nThread.sleep(100);\nf.cancel(true);                   // sends an interrupt to the worker thread\n// f.isCancelled() is true at once, whatever the task does next"},
  "kotlin": {"title": "CancelOne.kt (kotlinx.coroutines)", "src": "val job = scope.launch(Dispatchers.IO) {\n    delay(5_000)                  // pauses; resumes with CancellationException on cancel\n    println(\"done\")\n}\ndelay(100)\njob.cancel()                      // no interrupt: delay() notices the cancellation itself\n\n// a blocking call ignores job.cancel() unless you wrap it:\n// runInterruptible { Thread.sleep(5_000) }"},
  "note": "Both versions ask, and neither can force. Java sends the request as an interrupt, which blocking methods and `isInterrupted()` checks pick up. Kotlin's coroutines, light tasks that can pause without holding a thread, get it as a `CancellationException` at the points where they pause, such as `delay`, `await` and `withContext`. No interrupt is involved, so a blocking Java call inside a coroutine doesn't notice the cancel unless you wrap it in `runInterruptible`. The interrupt rules from this lesson still apply to Kotlin code that runs blocking work on an executor. Watch `runCatching` there: it catches `InterruptedException` like any other exception, which makes it an easy way to swallow a stop request. The coroutines track covers cancellation in full."
 },
 "worked": {
  "title": "Give up on a slow bank without telling the customer something wrong",
  "steps": [
   {"say": "A payment handler hands the bank call to a pool and waits for the answer. On a normal day, this works. Before reading on, decide what happens when the bank starts taking 30 seconds to answer.",
    "code": "Future<String> charge = pool.submit(() -> bank.charge(payment));\nreturn charge.get();                     // waits as long as the bank does", "lang": "java",
    "alt_code": "val charge = pool.submit<String> { bank.charge(payment) }\nreturn charge.get()                      // waits as long as the bank does", "alt_lang": "kotlin"},
   {"say": "Every request thread ends up stuck in `get()`. Little's law, from Sizing a pool, does the rest: at 400 payments a second and 30 seconds each, 12,000 requests are inside at once, each holding a thread. The program stops answering anyone. So wait with a time limit, and cancel the work you stopped waiting for.",
    "code": "Future<String> charge = pool.submit(() -> bank.charge(payment));\ntry {\n    return charge.get(800, TimeUnit.MILLISECONDS);   // 1. wait, with a limit\n} catch (TimeoutException e) {\n    charge.cancel(true);                             // 2. ask the bank call to stop\n    return \"PENDING\";                                // 3. don't claim it failed\n}", "lang": "java",
    "alt_code": "val charge = pool.submit<String> { bank.charge(payment) }\nreturn try {\n    charge.get(800, TimeUnit.MILLISECONDS)           // 1. wait, with a limit\n} catch (e: TimeoutException) {\n    charge.cancel(true)                              // 2. ask the bank call to stop\n    \"PENDING\"                                        // 3. don't claim it failed\n}", "alt_lang": "kotlin"},
   {"say": "Why `PENDING` and not `DECLINED`? The request may have reached the bank before the interrupt arrived, and a classic socket read may not even notice the interrupt. So the card may still be charged. If we said \"declined\", the customer would pay again, and then they'd have paid twice.",
    "code": "", "lang": ""},
   {"say": "Make the outcome easy to find later. Give every payment a unique ID and send it with the request, so the bank charges each ID at most once, however many times it hears it. On a timeout, add the ID to a list that a small job works through later, asking the bank what happened to each one. (Engineers call an ID like this an idempotency key: sending it twice has the same effect as sending it once.)",
    "code": "String paymentId = payment.id();\nFuture<String> charge = pool.submit(() -> bank.charge(payment, paymentId));\ntry {\n    return charge.get(800, TimeUnit.MILLISECONDS);\n} catch (TimeoutException e) {\n    charge.cancel(true);\n    checkLater.add(paymentId);                       // 4. a later job asks the bank about it\n    return \"PENDING\";\n}", "lang": "java",
    "alt_code": "val paymentId = payment.id()\nval charge = pool.submit<String> { bank.charge(payment, paymentId) }\nreturn try {\n    charge.get(800, TimeUnit.MILLISECONDS)\n} catch (e: TimeoutException) {\n    charge.cancel(true)\n    checkLater.add(paymentId)                        // 4. a later job asks the bank about it\n    \"PENDING\"\n}", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Time limits, states and a poller that won't stop",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/Futures.java", f"{lab}/main/{P}/StatementPoller.java"],
  "run": "./gradlew :executors:test --tests 'workbench.executors.l04.*'",
  "steps": [
   "Run the tests. All seven fail.",
   "Write `Futures.getOrDefault`. Call `get` with the time limit, and write one `catch` for each outcome in the Javadoc. On a timeout, and when your own thread is interrupted, call `cancel(true)` first.",
   "Write `Futures.describe` as a `switch` on `future.state()`, using `resultNow()` and `exceptionNow()`.",
   "`StatementPoller` is the starting code from the third section. Run its two tests and read the failure: the pool never finishes. Fix the line that loses the stop request, with one statement.",
   "Run the tests until all seven pass."
  ],
  "hints": [
   "`get(long, TimeUnit)` can end in four ways here besides success: `TimeoutException`, `ExecutionException`, `CancellationException` and `InterruptedException`. One multi-catch handles the two that get the same answer.",
   "In `getOrDefault`, after you cancel on `InterruptedException`, throw the same exception again. Passing it up is one of the two correct moves, so you don't also need to restore the flag.",
   "The poller's `while` condition is fine. Ask what state the interrupt flag is in when that condition runs, right after `pause()` caught an `InterruptedException`."
  ],
  "done_when": "All seven tests in `CancellationTest` pass."
 },
 "drill": {
  "title": "A polling loop that stops when asked",
  "minutes": 4,
  "prompt": "Close this page. Write a `Runnable` that calls `poll()` once a second until its thread is interrupted, then returns. It must stop whether the interrupt arrives during `poll()` or during the sleep. Then compare with the answer. Did you restore the flag, or return straight from the catch? Both work.",
  "answer": {"lang": "java", "title": "Poller.java", "src": "Runnable poller = () -> {\n    while (!Thread.currentThread().isInterrupted()) {   // interrupt during poll(): seen here\n        poll();\n        try {\n            Thread.sleep(1_000);\n        } catch (InterruptedException e) {             // interrupt during sleep: flag now cleared\n            Thread.currentThread().interrupt();          // restore it (or simply return)\n        }\n    }\n};",
   "alt": {"lang": "kotlin", "title": "Poller.kt", "src": "val poller = Runnable {\n    while (!Thread.currentThread().isInterrupted) {    // interrupt during poll(): seen here\n        poll()\n        try {\n            Thread.sleep(1_000)\n        } catch (e: InterruptedException) {             // interrupt during sleep: flag now cleared\n            Thread.currentThread().interrupt()           // restore it (or simply return)\n        }\n    }\n}"}}
 },
 "recap": [
  "`submit(Callable)` hands back a `Future`, a claim ticket, at once. `get` returns the value, or throws `ExecutionException`, `CancellationException` or `InterruptedException`.",
  "`get` with a time limit ends your wait, not the task. Cancel the work, or make its outcome findable later, for example with a unique payment ID.",
  "`cancel(true)` only interrupts. The task stops if it's blocked in a method that listens for interrupts, or if it checks `isInterrupted()`. The `Future` says cancelled either way.",
  "Throwing `InterruptedException` clears the flag. Rethrow it, or restore it with `Thread.currentThread().interrupt()`. Never swallow it.",
  "JDK 19 added `state()`, `resultNow()` and `exceptionNow()`. `invokeAll` waits for every task, and `invokeAny` returns the first success and cancels the rest.",
  "The limit: a `Future` can only be waited on, read or cancelled. Nothing here runs a task again later, or on a timetable. That's the next lesson."
 ],
 "closing": "We started at a takeaway counter, with a ticket for a burger nobody came back for. A thread pool hands out the same ticket, a `Future`. We waited with a time limit and watched the bank charge the card anyway. Three tasks were asked to stop, and only the two that listened did. Then we kept the request alive in a catch block.\n\nNow search your own code for `.get(` on a `Future`. Each call should have a time limit, and each `TimeoutException` should lead to a `cancel` or a record of the unfinished work.\n\nNext, we'll give a pool a task that comes back on its own, again and again. What happens to it when one run throws?",
 "quiz": [
  {
   "q": "A task asks the bank to move money between two accounts. The caller's `get(500, MILLISECONDS)` throws `TimeoutException`, and the caller does nothing else. What happens to the transfer?",
   "options": [
    "It is cancelled automatically when get() times out",
    "It may well still happen, because the task keeps running",
    "The pool undoes it",
    "The task receives the TimeoutException and stops"
   ],
   "answer": 1,
   "why": "The time limit is only about the caller's wait. The task doesn't know that anyone gave up, so it carries on, and the transfer goes through. Only `cancel(true)` sends the task a signal, and even that is just a request."
  },
  {
   "q": "A worker runs `while (!Thread.currentThread().isInterrupted()) { work(); try { Thread.sleep(100); } catch (InterruptedException e) { log.warn(\"interrupted\"); } }`. The pool calls `shutdownNow()` while the worker sleeps. What happens?",
   "options": [
    "The worker stops at the next loop check",
    "The worker throws, and the pool replaces it",
    "The worker logs a warning and keeps looping, because the exception cleared the flag",
    "shutdownNow() waits until the worker finishes"
   ],
   "answer": 2,
   "why": "`sleep` clears the interrupt flag when it throws. The catch only logs, so the `while` check sees a clear flag and loops forever. Stopping at the next check is what the code seems to promise, but nothing set the flag again. Restore it in the catch, or `return` from there."
  },
  {
   "q": "You call `cancel(true)` on a task that is in a long computing loop and never checks the interrupt flag. What do you see?",
   "options": [
    "`isCancelled()` is true at once, and the loop runs to the end anyway",
    "`isCancelled()` stays false until the loop ends",
    "The thread is stopped immediately",
    "`cancel` returns false, because the task is running"
   ],
   "answer": 0,
   "why": "The `Future` moves to CANCELLED as soon as `cancel` succeeds, and `cancel` returns true for a running task. The interrupt sets a flag that the loop never reads, so the work goes on. Java can't stop a thread from outside."
  },
  {
   "q": "You ask three exchange-rate services for the euro to dollar rate. You want the first successful answer, you want to ignore services that fail, and you want the slower ones cancelled. Which tool fits?",
   "options": [
    "Submit each one and call `get()` on them in order",
    "`invokeAll`, then pick the first SUCCESS",
    "A pool with one thread, so they run one at a time",
    "`invokeAny`"
   ],
   "answer": 3,
   "why": "`invokeAny` returns the first task that completes successfully and cancels the rest. `invokeAll` waits for every service, so you pay for the slowest one. Calling `get()` in order waits for the first service, even if the third is faster."
  },
  {
   "q": "From \"A thread's life: start, join, sleep, interrupt\": thread `t` is in `Thread.sleep(10_000)`. Another thread calls `t.interrupt()`. Inside `t`'s catch block, what does `Thread.currentThread().isInterrupted()` return?",
   "options": [
    "true, because the thread was just interrupted",
    "false, because throwing InterruptedException cleared the flag",
    "It throws IllegalThreadStateException",
    "true until sleep's 10 seconds are up"
   ],
   "answer": 1,
   "why": "Blocking methods clear the interrupt flag when they throw `InterruptedException`. That's why a catch block that neither rethrows nor calls `Thread.currentThread().interrupt()` loses the stop request.",
   "from": "conc-02"
  }
 ],
 "flashcards": [
  {"front": "What does `cancel(true)` do to a task that is already running?", "back": "It calls `interrupt()` on the task's thread. The task stops only if it responds to the interrupt."},
  {"front": "You call `cancel(true)` and the task ignores the interrupt. What does `isCancelled()` return?", "back": "`true`, at once, even though the task keeps running to the end."},
  {"front": "Does `future.get(timeout)` stop the task when it throws `TimeoutException`?", "back": "No. It only ends your wait. Call `cancel(true)` if the work should stop."},
  {"front": "What happens to the interrupt flag when `sleep` throws `InterruptedException`?", "back": "It is cleared. Rethrow the exception, or restore the flag with `Thread.currentThread().interrupt()`."},
  {"front": "What does `invokeAny(tasks)` return?", "back": "The result of the first task that succeeds. It cancels the others, and throws `ExecutionException` only if all of them fail."},
  {"front": "What does `resultNow()` do on a future whose task failed?", "back": "It throws `IllegalStateException`. Check `state()` first, and use `exceptionNow()` for FAILED."}
 ],
 "terms": [
  {"term": "Callable", "plain": "A task that returns a value and may throw any exception, even a checked one."},
  {"term": "Future", "plain": "A claim ticket for a task's result: wait for it, read its state, or cancel the task."},
  {"term": "Interrupt", "plain": "A request to a thread to stop what it is doing. It sets a flag, and wakes the thread if it is waiting."},
  {"term": "Interrupt flag", "plain": "A true-or-false value in each thread. `interrupt()` sets it, and throwing `InterruptedException` clears it."},
  {"term": "Cooperative cancellation", "plain": "Cancelling that works only if the task checks for the request and stops itself."},
  {"term": "invokeAny", "plain": "Runs several tasks and returns the first successful result, cancelling the rest."}
 ],
 "explain_back": {
  "prompt": "A teammate's code has `catch (InterruptedException e) { log.warn(\"interrupted, retrying\"); }` inside a retry loop. Explain why this stops the program from shutting down cleanly, and what they should write instead.",
  "answer": "When a waiting method like sleep or take throws InterruptedException, it clears the thread's interrupt flag first. So once the catch logs and retries, nothing remembers that someone asked the loop to stop. When the pool calls shutdownNow, or someone calls cancel(true), this task just keeps retrying. awaitTermination runs out of time, and in the end the program gets killed in the middle of its work. They should either let the exception travel up, by declaring throws InterruptedException, or, if the method can't throw it, call Thread.currentThread().interrupt() in the catch and then stop the loop or throw a different exception. Then any code above them that checks the flag still sees the request."
 },
 "deeper": {
  "minutes": 8,
  "body": "Two methods read the interrupt flag, and they are easy to mix up. `Thread.currentThread().isInterrupted()` reads it and leaves it alone. The static `Thread.interrupted()` reads it and clears it. Use the second only when you are about to handle the interrupt yourself, for example to throw `InterruptedException` from a blocking method of your own:\n\n```java\nif (Thread.interrupted()) throw new InterruptedException();   // clear, then report by throwing\n```\n\n```kotlin\nif (Thread.interrupted()) throw InterruptedException()        // clear, then report by throwing\n```\n\nHow does `cancel(true)` find the thread? `submit` wraps your task in a `FutureTask`, and the `FutureTask` remembers the thread that is running it. `cancel(true)` moves the task to its cancelled state and then calls `interrupt()` on that thread.\n\nThe flag belongs to the thread, not to the task, so a pool has to make sure an interrupt meant for one task doesn't hit the next task on the same thread. `ThreadPoolExecutor` does that: before each task, its worker clears any leftover interrupt, unless the pool itself is stopping after `shutdownNow()`.\n\nVirtual threads, in the \"Virtual threads\" track, use the same interrupt mechanism. A virtual thread waiting in `sleep` or in a `BlockingQueue` responds exactly as described here, so everything in this lesson carries over."
 },
 "sources": [
  {"title": "Future (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Future.html"},
  {"title": "Thread (Java SE 25 API): interrupt()", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Thread.html"},
  {"title": "Interrupts (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/essential/concurrency/interrupt.html"},
  {"title": "Java Concurrency in Practice, Goetz et al., chapter 7 (cancellation and shutdown)", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/exec-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
