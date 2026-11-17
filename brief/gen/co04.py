import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l04"
J = "java/workbench/coroutines/l04"
read = lambda p: (ROOT / p).read_text()
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l04.{cls}{extra}"


def demo(kt, java):
    """A Kotlin demo and its runnable Java twin, read from disk so the lesson never drifts."""
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(f"{lab}/demo/{P}/{kt}"), "run": run(k + "Kt"),
            "file": f"{lab}/demo/{P}/{kt}",
            "alt": {"lang": "java", "title": java, "src": read(f"{lab}/demo/{J}/{java}"), "run": run(j),
                    "file": f"{lab}/demo/{J}/{java}"}}


def pair(kotlin, java):
    """A Kotlin fence and its Java twin, side by side, as the validator expects."""
    return f"```kotlin\n{kotlin}\n```\n\n```java\n{java}\n```"


FIG = (
    '<svg viewBox="0 0 700 300" role="img" aria-label="One shared pool of worker threads. Default, the counter, takes one thread per core for CPU work. '
    'IO, the bench by the door, allows 64 blocking tasks. Two views over IO, bakery with 20 and recipe-copy with 100, add their own budgets on top, so up to 184 blocking tasks can run at peak.">'
    '<rect class="box" x="15" y="16" width="670" height="46" rx="8"/>'
    '<text class="t" x="350" y="37" text-anchor="middle">one shared pool of worker threads</text>'
    '<text class="t-s t-m" x="350" y="54" text-anchor="middle">threads are created as the budgets below need them</text>'
    '<line class="ln" x1="95" y1="62" x2="95" y2="120"/>'
    '<line class="ln" x1="265" y1="62" x2="265" y2="120"/>'
    '<line class="ln-d" x1="435" y1="62" x2="435" y2="120"/>'
    '<line class="ln-d" x1="605" y1="62" x2="605" y2="120"/>'
    '<rect class="box-a" x="15" y="120" width="160" height="70" rx="8"/>'
    '<text class="t t-code" x="95" y="145" text-anchor="middle">Default</text>'
    '<text class="t-s" x="95" y="165" text-anchor="middle">the counter: CPU work</text>'
    '<text class="t-s" x="95" y="181" text-anchor="middle">one per core (min 2)</text>'
    '<rect class="box-b" x="185" y="120" width="160" height="70" rx="8"/>'
    '<text class="t t-code" x="265" y="145" text-anchor="middle">IO</text>'
    '<text class="t-s" x="265" y="165" text-anchor="middle">the bench: blocking</text>'
    '<text class="t-s" x="265" y="181" text-anchor="middle">up to 64 at once</text>'
    '<rect class="box-ok" x="355" y="120" width="160" height="70" rx="8"/>'
    '<text class="t t-code" x="435" y="145" text-anchor="middle">"bakery"</text>'
    '<text class="t-s t-code" x="435" y="165" text-anchor="middle">IO.limited(20)</text>'
    '<text class="t-s" x="435" y="181" text-anchor="middle">adds up to 20</text>'
    '<rect class="box-ok" x="525" y="120" width="160" height="70" rx="8"/>'
    '<text class="t t-code" x="605" y="145" text-anchor="middle">"recipe-copy"</text>'
    '<text class="t-s t-code" x="605" y="165" text-anchor="middle">IO.limited(100)</text>'
    '<text class="t-s" x="605" y="181" text-anchor="middle">adds up to 100</text>'
    '<text class="t-s t-a" x="95" y="214" text-anchor="middle">never blocked by IO</text>'
    '<text class="t-s t-ok" x="520" y="214" text-anchor="middle">views over IO are elastic: they add to the 64</text>'
    '<rect class="box-dim" x="185" y="232" width="500" height="44" rx="8"/>'
    '<text class="t" x="435" y="259" text-anchor="middle">peak blocking tasks: 64 + 20 + 100 = 184</text>'
    '<text class="t-s t-m" x="95" y="250" text-anchor="middle">a view over Default</text>'
    '<text class="t-s t-m" x="95" y="266" text-anchor="middle">stays within its cores</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """On a big night, friends come to help, and the kitchen has two kinds of places to work. There's the counter, with one cutting board for each pair of hands that can chop. And there's the bench by the front door, where a helper sits when a delivery needs someone to sign for it. Chopping is work. Waiting at the door is only waiting, but somebody has to be there.

Now a helper takes a cutting board and stands at it, watching the door. The board does nothing. Four helpers do that, and nobody in the house can chop.

A coroutine can do the same, and nothing warns you. It's tempting to think a call inside a coroutine can't hold a thread, the worker that runs the code. But Suspend functions from zero showed that only a suspending call lets go. In Structured concurrency, the context carried a coroutine's job. Today it also says where the work runs. In this lesson, we'll see which thread runs a coroutine, move blocking calls to the bench, give a slow shop its own budget, and read the note every coroutine carries. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
K_CARD = """suspend fun printCard(dish: String): ByteArray {
    val steps = withContext(Dispatchers.IO) { book.loadSteps(dish) }   // a blocking database call
    return withContext(Dispatchers.Default) { printer.render(steps) }  // CPU-heavy layout
}"""
J_CARD = """// Java equivalent: CompletableFuture stages, each with its own executor
CompletableFuture<byte[]> printCard(String dish) {
    return CompletableFuture.supplyAsync(() -> book.loadSteps(dish), ioPool)  // a blocking database call
        .thenApplyAsync(printer::render, cpuPool);                            // CPU-heavy layout
}"""

S0 = """`suspend` says nothing about threads, as lesson 1 of this track showed. The **dispatcher** in a coroutine's context does. It decides which thread runs the coroutine each time it starts or resumes. In the kitchen, it's the station a dish is worked at. kotlinx.coroutines ships four:

- `Dispatchers.Default` is a pool, a group of threads kept ready for work. It has one thread per **core**, a part of the processor that runs one thread at a time, and at least two threads. `launch` and `async` use it when the context names no dispatcher. It's the counter, one cutting board per core.
- `Dispatchers.IO` is for calls that block a thread. Think of a database driver, the library a program uses to talk to a database, or an old library that waits on the network. Up to 64 of them run at once. It's the bench by the door.
- `Dispatchers.Main` is the thread that draws the screen in a desktop or Android app. It needs a module for that kind of app on the classpath, the list of libraries the program runs with (for Android, JavaFX or Swing). A plain program has none, and using it throws `IllegalStateException`.
- `Dispatchers.Unconfined` has no thread of its own. The coroutine starts on the caller's thread, and after its first pause it carries on wherever it was resumed. The docs say it shouldn't be used in general code.

`runBlocking` is the odd one out: it runs its coroutine on the thread that called it.

To run one piece of work somewhere else, use `withContext`. Here a recipe card is printed in two steps, one of each kind. First the steps are read from a recipe book kept in a database, with a driver that blocks. Then they're laid out for printing, which is pure calculation:

""" + pair(K_CARD, J_CARD) + """

`withContext` suspends the caller, runs the block on the other dispatcher, and then resumes the caller on its own dispatcher with the block's result. Carry this step to the bench, then come back to the counter with the answer. The code still reads from top to bottom. In the Java version, every stage names its executor, the JDK's word for a pool that runs submitted tasks. Whatever you chain next runs where the last stage left off, not back where you started.

`withContext` is also a scope, like `coroutineScope` in Builders. It waits for any children launched inside the block, and a failure inside it comes out as an exception in the caller.

`WhereDoesItRun`, in the Try it below, prints the thread for each dispatcher. It turns on debug mode, which adds the coroutine's name to thread names:

```text
runBlocking           Thread[#1,main @dinner#1,5,main]
Default               Thread[#19,DefaultDispatcher-worker-1 @dinner#1,5,main]
IO                    Thread[#19,DefaultDispatcher-worker-1 @dinner#1,5,main]
Unconfined, before    Thread[#1,main @dinner#1,5,main]
Unconfined, after     Thread[#21,kotlinx.coroutines.DefaultExecutor @dinner#1,5,main]
```

Two lines deserve a second look. Default and IO printed the same thread, `worker-1`: the two share one pool, and the next section explains why that's on purpose. And Unconfined started on `main`, then woke up on `DefaultExecutor`, the library's timer thread, because that's the thread that ended the `delay`. Unconfined goes wherever it's carried, like a dish that ends up with whoever happened to hear the timer.

A switch is cheap but not free: the library queues a task on the other dispatcher, and the coroutine's state machine resumes there. Values you wrote before the switch are visible after it, even on another thread, so a coroutine's own locals don't need `@Volatile`.

**The dispatcher picks the thread. `withContext` sends one step elsewhere and brings the answer back.**

So we can send work to the counter or to the bench. Which one does a blocking call belong on, and what happens when it lands on the wrong one?"""

# ---------------------------------------------------------------- section 1
S1 = """`Dispatchers.Default` has as many threads as the machine has cores. On a 4-core machine, that's 4. Run a 200 ms blocking call there, and you hold one of those 4 threads for 200 ms while it does nothing: the helper at the cutting board, watching the door. Four coroutines doing that at once take every thread, and all the CPU work in the program waits in the queue.

`BlockingOnDefault`, in the Try it below, does it on purpose. It starts 32 blocking calls of 200 ms on Default, then asks Default to run a task that takes a microsecond. Predict how long the tiny task waits to start. On this 4-core machine:

```text
32 blocking calls on Dispatchers.Default (4 cores): 1626 ms
a tiny CPU task on Default waited 1570 ms to start
```

A microsecond of work waited a second and a half. The 32 calls ran four at a time, in eight rounds, and the tiny task queued behind all of them. With `-Pargs=io`, the same calls go to the bench:

```text
32 blocking calls on Dispatchers.IO (4 cores): 255 ms
a tiny CPU task on Default waited 4 ms to start
```

All 32 ran at once, and the counter stayed free.

A blocking call belongs on `Dispatchers.IO`. Its limit is 64, or the number of cores if that's larger, and the system property `kotlinx.coroutines.io.parallelism`, a setting you pass on the command line with `-D`, changes it. IO threads spend most of their time waiting for something outside the program, a disk or another computer, so 64 of them on 4 cores is fine.

IO and Default share one pool of worker threads. When code on Default calls `withContext(Dispatchers.IO)`, the docs say it "typically does not lead to an actual switching to another thread". The same worker keeps going, and the library counts it against IO's limit instead of Default's. That's why `WhereDoesItRun` printed one worker for both. In the kitchen, the helper stays the same person: she walks from the counter to the bench, and her cutting board is free for somebody else. What the split buys you is two separate budgets. Blocking work can fill the bench, and Default still has a thread for every core.

Here the kitchen picture breaks. A helper on the bench could get up and chop for a minute while the doorbell is quiet. A blocked thread can't: it's stuck until the call returns. That's why only blocking calls need the bench at all. A coroutine that suspends gives its thread back at once, wherever it is.

Three rules follow.

Never block on Default. Put `withContext(Dispatchers.IO)` around each blocking call at the lowest level, inside the class that makes the call, so callers don't need to know it blocks.

Put long CPU work on Default: laying out a whole recipe book for printing, or resizing a hundred photos. A few microseconds of work need no switch at all.

Don't wrap calls that already suspend. `delay`, a suspending network client or a coroutine-aware queue never holds a thread while it waits, so `withContext(Dispatchers.IO)` around them only adds a hop.

**Nothing marks a call as blocking. Put each blocking call on IO yourself.**

Java has the same split under other names. The common `ForkJoinPool` is sized for CPU work, and blocking in it starves `parallelStream()` and every `CompletableFuture.supplyAsync` that names no executor. Sizing a pool, in the executors track, built one pool for each kind of work. Here the library hands you both pools ready-made, and your job is to put each call in the right one.

But one bench for every blocking call in the program has a problem of its own, as soon as one shop is slow."""

# ---------------------------------------------------------------- section 2
K_VIEW = """val bakery = Dispatchers.IO.limitedParallelism(20, "bakery")        // at most 20 bakery calls at once
val copier = Dispatchers.IO.limitedParallelism(100, "recipe-copy")  // a nightly copy job with its own budget"""
J_VIEW = """// Java equivalent: a separate pool per resource, often called a bulkhead
ExecutorService bakery = Executors.newFixedThreadPool(20, Thread.ofPlatform().name("bakery-", 0).factory());
ExecutorService copier = Executors.newFixedThreadPool(100, Thread.ofPlatform().name("recipe-copy-", 0).factory());"""

S2 = """IO's 64 is one budget for every blocking call in the JVM, the program that runs your code. That hurts when one resource is slow. Say the bakery from lesson 1 still has an old ordering client that blocks, and the bakery has 20 phone lines. When the bakery slows down, 64 coroutines can pile into bakery calls. Twenty of them get a line, and 44 hold an IO thread while they wait for one. Every other blocking call in the program, such as the recipe book's, queues behind them.

`limitedParallelism` makes a **view** of a dispatcher, with a limit of its own:

""" + pair(K_VIEW, J_VIEW) + """

A view owns no threads and needs no closing. It's a sign over part of the bench that says "bakery calls: 20 seats". At most 20 coroutines from the bakery view run at the same moment, and the rest wait in the view's queue without holding a thread. The name is optional. It arrived in kotlinx.coroutines 1.9, when the API became stable, and it's what `toString()` returns, which helps in logs.

Views over IO are **elastic**: they don't take a share of IO's 64, they add to it. The library's own docs give an example with a view of 100 for one database and 60 for another. The program, they say, may then run up to 64 + 100 + 60 blocking tasks at peak. So the view protects the bakery both ways. Bakery calls can't take more than 20 threads, and a burst of other blocking work can't starve the bakery either.

`BlockingBudgets`, in the Try it below, runs 400 blocking calls of 200 ms three ways. Predict each before you read on:

```text
Dispatchers.IO                    1446 ms, peak  64 calls at once
IO.limitedParallelism(400)         576 ms, peak 265 calls at once
virtual-thread executor            228 ms, peak 400 calls at once
```

Plain IO capped the run at 64 calls at once, so 400 calls took seven rounds. The view of 400 went far past 64, as promised, though not all the way to 400. The shared pool had to create a few hundred new threads, and on this busy machine it couldn't create them fast enough; a second run peaked at 237. The virtual-thread executor, the one from the virtual threads track, ran all 400 at once, because a virtual thread costs almost nothing to start.

Views over Default are different. A view can never go beyond its parent's limit, so `Dispatchers.Default.limitedParallelism(400)` still runs one task per core. Swap it into the demo, and the 400 calls take 20 seconds, four at a time. And `limitedParallelism(1)` gives a view that runs one task at a time, which is not the same as a lock. Lesson 10 of this track shows why.

When you need a dispatcher that isn't one of these, wrap an executor: `executor.asCoroutineDispatcher()`. That includes `Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher()`, which the demo used. kotlinx.coroutines 1.11 has no built-in virtual-thread dispatcher, so this is the supported route. A wrapped executor is yours to close: the dispatcher is `AutoCloseable`, and `close()` shuts the executor down.

**A slow resource needs a budget of its own. Give it a view over IO.**

The dispatcher is only one of the things a coroutine carries with it."""

# ---------------------------------------------------------------- section 3
K_TL = """guest.set("ana")
withContext(Dispatchers.Default) { guest.get() }                            // null: another thread
withContext(Dispatchers.Default + guest.asContextElement()) { guest.get() } // ana"""
J_TL = """// Java equivalent: copy the ThreadLocal into the task by hand
String captured = GUEST.get();
pool.submit(() -> {
    GUEST.set(captured);
    try { work(); } finally { GUEST.remove(); }
});"""

S3 = """Picture a note clipped to every dish in the kitchen. It says which station the dish is worked at, what the dish is called and which course it belongs to. It can also hold anything else the cook wants to remember, such as which guest the dish is for. When a dish is split into parts, each part gets a copy of the note.

That note is the **coroutine context**: a small set of elements, with at most one for each **key**, the label an element is filed under. You've met most of the elements already: the `Job`, which is the coroutine's place in the tree from Structured concurrency; the dispatcher; `CoroutineName`; and `CoroutineExceptionHandler`, which lesson 6 of this track covers. `+` combines two contexts, and when both have an element with the same key, the right side wins:

```kotlin solo
val ctx = Dispatchers.IO + CoroutineName("soup")
val renamed = ctx + CoroutineName("salad")
renamed[CoroutineName]             // CoroutineName(salad): the right side won
renamed[ContinuationInterceptor]   // Dispatchers.IO: untouched
```

The picture breaks in one place. A paper note can be scribbled on. A context can't be changed in place: `+` always makes a new one, and the old one stays as it was.

A new coroutine's context is built in three steps: the scope's context, then the context you pass to the builder, which overrides it, then a fresh `Job` that is a child of the scope's job. So children inherit the dispatcher, the name and anything else you add, but every child gets its own job, its own place in the tree. `withContext(ctx)` builds the context of its block the same way.

Inside a suspend function, read an element with `currentCoroutineContext()[Key]`. The key is usually the element's companion object, which is why `ctx[CoroutineName]` reads so naturally. One change in kotlinx.coroutines 1.11: using `CoroutineDispatcher` as the key is deprecated, and later versions will reject it. Look the dispatcher up with `ContinuationInterceptor`, as the snippet does.

You can define your own element by extending `AbstractCoroutineContextElement` and giving it a companion `Key`. The lab does that with `ForGuest`, a note that says which guest a dish is for, so every coroutine working on that dish can read it.

What doesn't follow a coroutine is a plain `ThreadLocal`, a variable with a separate value for each thread. It's a note pinned to the cook's apron instead of clipped to the dish: when another cook picks up the dish, the note stays with the first cook. A coroutine that resumes on another thread sees that thread's value. `asContextElement()` turns a `ThreadLocal` into a context element. The library then sets the value on whichever thread runs the coroutine, and puts the old value back when the coroutine leaves:

""" + pair(K_TL, J_TL) + """

`ContextElements`, in the Try it below, prints all three: `ana` on the main thread, `null` on Default with the plain `ThreadLocal`, and `ana` again with `asContextElement`.

**A `ThreadLocal` stays with the thread, not with the coroutine. Carry it in the context.**

Real programs need this most for logging. Many logging libraries keep an id for the current piece of work in a `ThreadLocal`, so that every log line can show it. For the widely used SLF4J library, the `kotlinx-coroutines-slf4j` module has a ready-made element, `MDCContext`; it isn't on this lab's classpath. And `CoroutineName` shows up in thread names when the JVM runs with `-Dkotlinx.coroutines.debug` (running with `-ea`, which turns on assertions, does it too). That costs little, and it makes a thread dump, a snapshot of every thread and what it's doing, readable."""

# ---------------------------------------------------------------- closing
CLOSING = """We started in a kitchen with a counter for chopping and a bench for waiting. Coroutines have the same two places: Default for CPU work, one thread per core, and IO for blocking calls. `withContext` carries one step across and brings the answer back. A view gives a slow resource its own bench, and the context is the note clipped to every coroutine.

Now search your own code for blocking calls, such as database queries or `Thread.sleep`, in coroutines on Default. Each one is a cutting board nobody can use.

Next, we'll call a dinner off halfway. What does a coroutine do when it's cancelled in the middle of a long loop, or inside a blocking call that won't let go?"""

L = {
 "id": "co-04",
 "title": "Dispatchers and the coroutine context",
 "minutes": 35,
 "goal": "By the end you can say which thread a coroutine runs on and why, move blocking and CPU work to the right dispatcher with withContext, give a slow resource its own budget with limitedParallelism, and read and extend a coroutine context with +.",
 "opening": OPENING,
 "warmup": {
  "q": "A coroutine launched on `Dispatchers.Default` calls a database driver that blocks for 300 ms. The machine has 4 cores. What does that call cost the rest of the program while it runs?",
  "options": [
   "Nothing: a coroutine suspends while the query runs, so the thread is free",
   "One of the 4 Default threads is stuck for 300 ms, so other CPU work queues behind it",
   "Nothing: kotlinx.coroutines moves blocking calls to `Dispatchers.IO` by itself",
   "The call fails, because blocking calls aren't allowed in a coroutine"
  ],
  "answer": 1,
  "why": "A coroutine frees its thread only at a suspension point, and a blocking driver call isn't one: it holds the thread. Default has one thread per core, so on 4 cores, four such calls stop all CPU work, like four helpers standing at the cutting boards watching the door. Nothing detects or moves the call for you. You move it yourself, with `withContext(Dispatchers.IO)`."
 },
 "sections": [
  {
   "h": "A dispatcher picks the thread, and withContext moves one step",
   "body": S0,
   "try": {
    "title": "Print where each step runs",
    "minutes": 4,
    "steps": [
     "Read `WhereDoesItRun.kt`. It turns on debug mode, which adds the coroutine's name and number to thread names. Predict the thread for each line.",
     "Run it. Look closely at the two Unconfined lines.",
     "Run it two or three times. Do Default and IO always print different workers?",
     "Run the Java twin and match each line to its Kotlin counterpart."
    ],
    "code": demo("WhereDoesItRun.kt", "WhereDoesItRunJava.java"),
    "expect": "`runBlocking` prints `main @dinner#1`. Default and IO print `DefaultDispatcher-worker-N` threads, and on many runs IO prints the same worker as Default: the two share one pool. Unconfined starts on `main` and, after `delay`, resumes on `kotlinx.coroutines.DefaultExecutor`, the thread that fired the timer. The single-thread executor prints `oven @roast#1` (the new name replaced the old one), and the virtual-thread executor prints a `VirtualThread`. In the Java twin, the `thenAccept` stage runs on whichever thread completed the timer stage, which is Java's version of Unconfined."
   },
   "refs": [
    {"title": "Coroutine context and dispatchers (Kotlin docs)", "url": "https://kotlinlang.org/docs/coroutine-context-and-dispatchers.html", "kind": "read"}
   ]
  },
  {
   "h": "Default is for CPU work, IO is for blocking calls",
   "body": S1,
   "try": {
    "title": "Starve Default with blocking calls",
    "minutes": 4,
    "steps": [
     "Read `BlockingOnDefault.kt`. It starts 32 blocking calls of 200 ms, then asks Default to run a task that takes a microsecond. Predict how long that tiny task waits to start on your machine.",
     "Run it.",
     "Run it with `-Pargs=io`, which puts the blocking calls on IO. Predict first.",
     "Run the Java twin both ways."
    ],
    "code": demo("BlockingOnDefault.kt", "BlockingOnDefaultJava.java"),
    "expect": "On 4 cores, the 32 calls take about 1,600 ms on Default (8 rounds of 4), and the tiny task waits about 1,500 ms (1,626 and 1,570 ms here), because every Default thread is asleep in `Thread.sleep`. With `-Pargs=io` the calls take about 220 ms, all 32 at once (255 ms here), and the tiny task starts within a few milliseconds. Scale the numbers to your core count. The Java twin shows the same starvation with a `ForkJoinPool` sized like Default (1,628 and 1,588 ms here)."
   }
  },
  {
   "h": "A limitedParallelism view gives one slow resource its own budget",
   "body": S2,
   "figure": {"svg": FIG, "caption": "Default and IO share one pool of threads but keep separate budgets. Views over IO add their own budgets on top of IO's 64."},
   "try": {
    "title": "Three budgets for 400 blocking calls",
    "minutes": 4,
    "steps": [
     "Read `BlockingBudgets.kt`. It runs 400 blocking calls of 200 ms on plain IO, on a view of 400 over IO, and on a virtual-thread executor. Predict the time and the peak for each.",
     "Run it.",
     "Change the view to `Dispatchers.Default.limitedParallelism(400)` and run it again. Predict first.",
     "Run the Java twin."
    ],
    "code": demo("BlockingBudgets.kt", "BlockingBudgetsJava.java"),
    "expect": "Plain IO peaks at 64 calls at once, so 400 calls take 7 rounds, about 1,400 ms (1,446 ms here). The view of 400 goes far beyond 64 because it adds to IO's budget instead of sharing it. On an idle machine it gets close to 400 at once in about 300 ms; on this busy one it peaked at 265 and 237 calls in two runs, taking about 600 ms, because the shared pool couldn't create new threads fast enough. The virtual-thread executor peaks at 400 (228 ms here). The view over Default peaks at your core count (at least 2) and takes far longer: 20 seconds on 4 cores, because a view can't exceed its parent. The Java twin shows the same pattern with a fixed pool of 64, a cached pool that grows and a virtual thread per task (1,424, 647 and 225 ms here)."
   },
   "refs": [
    {"title": "limitedParallelism (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-coroutine-dispatcher/limited-parallelism.html", "kind": "docs"},
    {"title": "Dispatchers.IO (API reference: the 64 limit and elastic views)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-dispatchers/-i-o.html", "kind": "docs"}
   ]
  },
  {
   "h": "The context is a set of elements, and + merges them",
   "body": S3,
   "try": {
    "title": "Merge contexts and lose a ThreadLocal",
    "minutes": 3,
    "steps": [
     "Read `ContextElements.kt`. Predict the three lines about `guest`.",
     "Run it.",
     "Add `+ CoroutineName(\"late\")` to the end of the `renamed` line and run again. Which name wins now?",
     "Run the Java twin, which copies the value by hand, the way a logging library's executor wrapper does."
    ],
    "code": demo("ContextElements.kt", "ContextElementsJava.java"),
    "expect": "The name lookups print `CoroutineName(soup)`, then `CoroutineName(salad)`, and the dispatcher lookup prints `Dispatchers.IO`. The main thread sees `ana`, the plain `ThreadLocal` on Default prints `null`, and the `asContextElement` version prints `ana`. After your change, the rightmost name, `late`, wins. The Java twin prints the same three `guest` lines."
   },
   "refs": [
    {"title": "asContextElement (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/as-context-element.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "One job, two kinds of work: executors vs dispatchers",
  "java": {"title": "RecipeCardService.java", "src": "class RecipeCardService {\n    private final ExecutorService io;     // sized for blocking database calls\n    private final ExecutorService cpu;    // sized to the cores\n\n    RecipeCardService(ExecutorService io, ExecutorService cpu) { this.io = io; this.cpu = cpu; }\n\n    CompletableFuture<byte[]> printCard(String dish) {\n        return CompletableFuture\n            .supplyAsync(() -> book.loadSteps(dish), io)   // 1. block on an IO thread\n            .thenApplyAsync(printer::render, cpu);         // 2. lay out on a CPU thread\n        // the caller gets a future; whatever it chains next runs on a cpu thread\n    }\n}"},
  "kotlin": {"title": "RecipeCardService.kt", "src": "class RecipeCardService(\n    private val io: CoroutineDispatcher = Dispatchers.IO,\n    private val cpu: CoroutineDispatcher = Dispatchers.Default,\n) {\n    suspend fun printCard(dish: String): ByteArray {\n        val steps = withContext(io) { book.loadSteps(dish) }   // 1. block on an IO thread\n        return withContext(cpu) { printer.render(steps) }      // 2. lay out on a CPU thread\n    }   // the caller resumes on its own dispatcher with the bytes\n}"},
  "note": "Both versions keep the blocking call off the CPU threads, and both take the pools as constructor arguments, so a test can pass its own. The difference is where the caller ends up. With `CompletableFuture`, the result is delivered on the thread of the last stage, and the caller either blocks on `join()` or keeps chaining callbacks that run who knows where. With `withContext`, the caller suspends, and when the block finishes it resumes on its own dispatcher, as if the call had been an ordinary one. You also own less. `Dispatchers.IO` and `Dispatchers.Default` are shared pools that live as long as the program and that you never create or shut down, while the Java version needs two executors with a life of their own."
 },
 "worked": {
  "title": "Give the bakery's blocking client a budget of its own",
  "steps": [
   {"say": "An app orders bread through the bakery's old blocking client, inside `launch` on Default, on a 4-core machine. When the bakery slows to 2 seconds a call, orders pile up, and unrelated work in the app stalls.",
    "code": "class BreadOrders(private val bakery: BlockingBakeryClient, private val scope: CoroutineScope) {\n    fun onOrder(order: BreadOrder) {\n        scope.launch {                                  // scope uses Dispatchers.Default\n            val ticket = bakery.order(order)            // blocks a Default thread for up to 2 s\n            pantry.expect(ticket)\n        }\n    }\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent of the bug: blocking calls on the common pool, which is sized for CPU work\nclass BreadOrders {\n    void onOrder(BreadOrder order) {\n        CompletableFuture.supplyAsync(() -> bakery.order(order))   // no executor: ForkJoinPool.commonPool()\n            .thenAccept(pantry::expect);\n    }\n}", "alt_lang": "java"},
   {"say": "First, get the blocking call off Default. Put the switch inside a small suspend wrapper around the client, so that no caller can forget it.",
    "code": "class SuspendingBakery(private val client: BlockingBakeryClient) {\n    // 1. the only place that knows this client blocks\n    suspend fun order(order: BreadOrder): Ticket =\n        withContext(Dispatchers.IO) { client.order(order) }\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent: the wrapper picks the executor, so callers can't forget\nclass AsyncBakery {\n    private final ExecutorService io = Executors.newCachedThreadPool();\n    // 1. the only place that knows this client blocks\n    CompletableFuture<Ticket> order(BreadOrder order) {\n        return CompletableFuture.supplyAsync(() -> client.order(order), io);\n    }\n}", "alt_lang": "java"},
   {"say": "IO allows 64 calls, but the bakery has 20 phone lines. A slow bakery would let 64 coroutines take IO threads, and 44 of them would only be waiting for a line, while other blocking calls queue for IO threads. Give the bakery a view sized to its lines, and pass it in, so a test can pass a test dispatcher.",
    "code": "class SuspendingBakery(\n    private val client: BlockingBakeryClient,\n    // 2. a budget sized to the bakery's 20 lines, on top of IO's 64\n    private val dispatcher: CoroutineDispatcher = Dispatchers.IO.limitedParallelism(20, \"bakery\"),\n) {\n    suspend fun order(order: BreadOrder): Ticket =\n        withContext(dispatcher) { client.order(order) }\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent: a pool of exactly 20 threads for the bakery\nclass AsyncBakery implements AutoCloseable {\n    // 2. a budget sized to the bakery's 20 lines\n    private final ExecutorService bakeryPool =\n        Executors.newFixedThreadPool(20, Thread.ofPlatform().name(\"bakery-\", 0).factory());\n\n    CompletableFuture<Ticket> order(BreadOrder order) {\n        return CompletableFuture.supplyAsync(() -> client.order(order), bakeryPool);\n    }\n\n    @Override public void close() { bakeryPool.shutdown(); }\n}", "alt_lang": "java"},
   {"say": "The app's own code no longer cares where the bakery call runs. Its other work, such as a suspending pantry call, stays on Default.",
    "code": "fun onOrder(order: BreadOrder) {\n    scope.launch {\n        val ticket = bakery.order(order)   // 3. suspends; no Default thread is held\n        pantry.expect(ticket)              // back on Default\n    }\n}", "lang": "kotlin",
    "alt_code": "void onOrder(BreadOrder order) {\n    bakery.order(order)                 // 3. runs on the bakery pool\n        .thenAccept(pantry::expect);    //    and so does this stage, unless you pass an executor\n}", "alt_lang": "java"},
   {"say": "Self-check: why not `Executors.newFixedThreadPool(20).asCoroutineDispatcher()` instead of the view? (It works, but it's a pool you must close, with 20 threads that sit idle between rushes. The view has no life of its own to manage, borrows threads from the shared pool only while calls run, and still caps the bakery at 20.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Put each call on the right dispatcher",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/RecipeCardService.kt", f"{lab}/main/{P}/BakeryDispatcher.kt", f"{lab}/main/{P}/GuestContext.kt",
            f"{lab}/main/{P}/KitchenModel.kt"],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l04.*'",
  "steps": [
   "Read `KitchenModel.kt` first. `BlockingRecipeBook.loadSteps` reads a recipe from a database and blocks; `CardPrinter.render` lays out a printable recipe card, which is pure CPU work; and `ForGuest` is a context element, a note that says which guest a dish is for. Run the tests: all eight fail.",
   "In `RecipeCardService.printCard`, run `loadSteps` inside `withContext(io)` and `render` inside `withContext(cpu)`. The tests pass two single-thread dispatchers named `test-io` and `test-cpu`, so they can see where each call ran.",
   "Write `bakeryDispatcher()`: a view over `Dispatchers.IO` that allows exactly 20 calls at once and is named `bakery`. Don't create a thread pool.",
   "Write `withGuest`: run the block in `withContext` with a `ForGuest(guest)` and a `CoroutineName(\"for-$guest\")`, combined with `+`.",
   "Write `currentGuest()`: read the `ForGuest` element from the current context by its key.",
   "Run the tests until all eight pass."
  ],
  "hints": [
   "`withContext(io) { book.loadSteps(dish) }` returns the steps. You don't need `async`, because the two steps depend on each other.",
   "`limitedParallelism` takes an optional second argument, the view's name. The name is what `toString()` returns.",
   "`withContext(context, block)` accepts the block parameter as it is. `ForGuest(guest) + CoroutineName(\"for-$guest\")` is a `CoroutineContext`.",
   "`currentCoroutineContext()` (from `kotlinx.coroutines`) returns the context of the calling coroutine. The companion object `ForGuest` is the key, so `ctx[ForGuest]` gives you a `ForGuest?`."
  ],
  "done_when": "All eight tests in `DispatchersTest` pass."
 },
 "drill": {
  "title": "Two dispatchers and a budget, from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `suspend fun weeklyMenu(family: String): Menu` that loads recipes with a blocking `repo.load(family)` and plans the week with a CPU-heavy `planner.plan(recipes)`, each on the right dispatcher. Then declare a dispatcher for a butcher's blocking ordering client, where the butcher has 8 phone lines, without creating a thread pool.",
  "answer": {"lang": "kotlin", "src": "suspend fun weeklyMenu(family: String): Menu {\n    val recipes = withContext(Dispatchers.IO) { repo.load(family) }      // blocking: IO\n    return withContext(Dispatchers.Default) { planner.plan(recipes) }   // CPU: Default\n}\n\nval butcher: CoroutineDispatcher = Dispatchers.IO.limitedParallelism(8, \"butcher\")",
             "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: one executor per kind of work, plus a pool sized to the butcher\nCompletableFuture<Menu> weeklyMenu(String family) {\n    return CompletableFuture.supplyAsync(() -> repo.load(family), ioPool)  // blocking: IO pool\n        .thenApplyAsync(planner::plan, cpuPool);                          // CPU: CPU pool\n}\n\nExecutorService butcher = Executors.newFixedThreadPool(8, Thread.ofPlatform().name(\"butcher-\", 0).factory());"}}
 },
 "recap": [
  "The dispatcher in a coroutine's context picks its thread. `launch` and `async` use `Dispatchers.Default` when none is given: one thread per core, at least 2.",
  "Blocking calls go on `Dispatchers.IO` (64 at once by default), wrapped in `withContext` inside the function that blocks. CPU work goes on Default. Calls that already suspend need no switch.",
  "`withContext` runs a block on another dispatcher and resumes the caller on its own, with the result. IO and Default share threads, so the switch is cheap.",
  "`Dispatchers.IO.limitedParallelism(n, name)` is a budget for one resource. Views over IO add to the 64; views over Default never exceed the core count.",
  "A context is a set of elements filed by key. `+` merges them, the right side wins, and children inherit everything except the `Job`. A plain `ThreadLocal` doesn't follow; carry it with `asContextElement()`.",
  "The limit: a dispatcher only decides where a coroutine runs. A blocking call on IO still holds its thread until it returns, and nothing here can stop it early."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "A program handles 10 orders at once on a 4-core machine. Each one runs `launch { recipes.load(id) }`, a blocking 300 ms database call, in a scope whose dispatcher is Default. At that moment a coroutine on Default needs 1 ms of CPU to resize a photo. When does it run?",
   "options": ["At once, because Default and IO are separate thread pools", "Only once a Default thread finishes its blocking call, roughly 300 ms later", "At once, because kotlinx.coroutines moves blocking calls to IO for you", "Never: Default throws `IllegalStateException` when a thread blocks for too long"],
   "answer": 1,
   "why": "All 4 Default threads are blocked inside database calls, so the photo task waits in the queue until one returns. Nothing moves a blocking call for you, and nothing throws. Wrapping the query in `withContext(Dispatchers.IO)` keeps Default free."},
  {"q": "A nightly job makes 300 blocking calls to copy the recipe book into a backup database, whose pool has 100 connections. It must not slow down the program's other blocking calls. Which dispatcher fits?",
   "options": ["`Dispatchers.IO`", "`Dispatchers.Default.limitedParallelism(100)`", "`Dispatchers.IO.limitedParallelism(100, \"recipe-copy\")`", "`Dispatchers.Unconfined`"],
   "answer": 2,
   "why": "A view over IO caps the copy at 100, and because IO views are elastic, it adds to IO's 64 instead of using them up. Plain IO would let the copy take all 64 threads. A view over Default can't exceed the core count, and Default must never block anyway."},
  {"q": "What does this print?\n\n```kotlin\nval ctx = CoroutineName(\"a\") + Dispatchers.IO + CoroutineName(\"b\")\nprintln(ctx[CoroutineName]?.name)\n```",
   "options": ["`b`", "`a`", "`a, b`", "`null`, because the dispatcher replaced the name"],
   "answer": 0,
   "why": "A context holds at most one element per key, and `+` lets the right side win. `CoroutineName(\"b\")` replaces `a`. The dispatcher has a different key, so it sits beside the name without touching it."},
  {"q": "Inside `withContext(Dispatchers.IO + CoroutineName(\"soup\")) { ... }` you call `launch(CoroutineName(\"salad\")) { ... }`. What does the child coroutine's context contain?",
   "options": ["Default and `salad`, because `launch` uses Default unless told otherwise", "IO and `soup`, because the parent's context always wins", "IO and `salad`, and the same `Job` as the `withContext` block", "IO and `salad`, and a new `Job` that is a child of the block's job"],
   "answer": 3,
   "why": "A child starts from its scope's context (IO and `soup`), then the builder's argument overrides it (`salad`), then it gets a fresh `Job` that is a child of the scope's job. The \"Default unless told\" rule applies only when the context has no dispatcher at all."},
  {"q": "From the executors track: each bakery call holds one of the bakery's 20 phone lines. You give bakery calls their own pool of 64 threads. How many bakery calls can really make progress at once?",
   "options": ["64", "20", "84", "One per core"],
   "answer": 1,
   "why": "The smallest limit on the path is the real ceiling. The other 44 threads sit waiting for a line. That's why the bakery's dispatcher in this lesson is a view of exactly 20.",
   "from": "exec-03"}
 ],
 "flashcards": [
  {"front": "How many threads does `Dispatchers.Default` have?", "back": "One per CPU core, and at least two."},
  {"front": "What is `Dispatchers.IO`'s default limit?", "back": "64 blocking tasks at once, or the core count if that's larger. The `kotlinx.coroutines.io.parallelism` property changes it."},
  {"front": "Does `Dispatchers.IO.limitedParallelism(100)` take 100 of IO's 64 threads?", "back": "No. Views over IO are elastic and add to IO's budget: IO and the view together can run 64 + 100 blocking tasks."},
  {"front": "What does `withContext(Dispatchers.IO) { load() }` do to the calling coroutine?", "back": "It suspends the caller, runs `load()` on IO, then resumes the caller on its own dispatcher with the result."},
  {"front": "`ctx` holds `CoroutineName(\"a\")`. What name does `ctx + CoroutineName(\"b\")` hold?", "back": "`b`. One element per key, and the right side of `+` wins."},
  {"front": "Why does a `ThreadLocal` read `null` after `withContext(Dispatchers.Default)`?", "back": "The block runs on another thread, which has its own value. Pass `threadLocal.asContextElement()` in the context to carry the value along."},
  {"front": "In kotlinx.coroutines 1.11, which key looks up the dispatcher in a context?", "back": "`ContinuationInterceptor`. Using `CoroutineDispatcher` as the key is deprecated."}
 ],
 "terms": [
  {"term": "Dispatcher", "plain": "The context element that decides which thread runs a coroutine each time it starts or resumes. In the kitchen, the station a dish is worked at."},
  {"term": "Dispatchers.Default", "plain": "The shared pool for CPU work: one thread per core, at least two."},
  {"term": "Dispatchers.IO", "plain": "The shared pool for blocking calls: up to 64 at once by default, using the same threads as Default."},
  {"term": "limitedParallelism view", "plain": "A dispatcher in front of another one that lets at most n of its tasks run at the same time. It owns no threads."},
  {"term": "withContext", "plain": "Runs a block with a changed context, often another dispatcher, and returns its result to the caller."},
  {"term": "Coroutine context", "plain": "The set of elements a coroutine carries: job, dispatcher, name, exception handler and your own elements. The note clipped to the dish."},
  {"term": "Context element", "plain": "One entry in a context, found by its key, usually the element class's companion object."}
 ],
 "explain_back": {
  "prompt": "A friend's recipe app got slow when many people used it, and so did unrelated screens. You find `repo.findRecipe(id)`, a blocking database call, inside a coroutine on Default. Explain what was happening, and the two changes you would make.",
  "answer": "Default has one thread per core, so on a 4-core machine only 4 coroutines can run on it at once. The database call doesn't suspend, it blocks, so each slow query held a Default thread for its whole length. A few slow queries took every Default thread, and all the CPU work in the program, including other screens, waited in the queue. First, I'd wrap the call in `withContext` inside the repository, so it runs on IO and nobody calling `findRecipe` has to remember. Second, I'd give the database a budget of its own, such as `Dispatchers.IO.limitedParallelism(20, \"recipes\")` to match a pool of 20 connections, so a slow database can't use up IO threads that other blocking calls need. That view adds to IO's 64 instead of taking from them, and it needs no closing."
 },
 "deeper": {
  "minutes": 10,
  "body": "Default and IO are two faces of one scheduler. On the JVM, kotlinx.coroutines runs a single pool of worker threads, and each task is marked as CPU work or blocking work. A worker running a blocking task doesn't count against Default's limit, so the scheduler can start another worker for CPU work. That's how a switch from Default to IO can stay on the same thread: the worker just changes which budget it's counted against. IO itself is a view of 64 over an unlimited budget for blocking work, which is why further views over IO can add to it.\n\nThe docs say `Dispatchers.IO.limitedParallelism(n)` can safely replace the older `newFixedThreadPoolContext(n)`. The old function creates n threads of its own, which you must close and which sit idle between rushes. If you find it in a code base, a view is almost always the better choice.\n\n`Dispatchers.Unconfined` has one fair niche: code that must react at once, on whatever thread delivered an event, such as some of the library's own operators. To avoid overflowing the stack, nested unconfined coroutines form an event loop instead of calling each other directly, which makes the order of execution surprising. Treat it as a tool for library writers.\n\nA virtual-thread dispatcher (`Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher()`) is an interesting option for code that blocks a lot, because each task gets a cheap virtual thread instead of an IO worker. It isn't a free win. A virtual thread pinned by `synchronized` on JDK 21 to 23 still holds a carrier (JEP 491 removed most pinning in JDK 24). Each time the coroutine resumes, the executor starts a new virtual thread for it, so you lose the scheduler's habit of keeping a coroutine on the same worker. And cancelling a coroutine that's blocked inside it still needs `runInterruptible`, which lesson 5 of this track covers. Lesson 11 of this track compares the options for a whole program."
 },
 "sources": [
  {"title": "Coroutine context and dispatchers (Kotlin docs)", "url": "https://kotlinlang.org/docs/coroutine-context-and-dispatchers.html"},
  {"title": "Dispatchers.IO (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-dispatchers/-i-o.html"},
  {"title": "CoroutineDispatcher.limitedParallelism (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-coroutine-dispatcher/limited-parallelism.html"},
  {"title": "withContext (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/with-context.html"}
 ]
}
out = ROOT / "content/lessons/co-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
