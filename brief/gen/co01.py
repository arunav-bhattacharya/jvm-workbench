import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/coroutines/src"
P = "kotlin/workbench/coroutines/l01"
J = "java/workbench/coroutines/l01"
read = lambda p: (ROOT / p).read_text()
run = lambda cls, extra="": f"./gradlew :coroutines:demo -Pmain=workbench.coroutines.l01.{cls}{extra}"


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
    '<svg viewBox="0 0 680 300" role="img" aria-label="State machine for makeSauce: three states joined by resume arrows. '
    'A suspending call returns COROUTINE_SUSPENDED and frees the thread. One continuation object, the bookmark, keeps the label and the locals.">'
    '<text class="t-s t-m" x="227" y="34" text-anchor="middle">resume</text>'
    '<text class="t-s t-m" x="452" y="34" text-anchor="middle">resume</text>'
    '<rect class="box-a" x="20" y="44" width="190" height="64" rx="8"/>'
    '<text class="t" x="115" y="70" text-anchor="middle">label 0</text>'
    '<text class="t-s t-code" x="115" y="92" text-anchor="middle">fryOnions(onions)</text>'
    '<rect class="box-a" x="245" y="44" width="190" height="64" rx="8"/>'
    '<text class="t" x="340" y="70" text-anchor="middle">label 1</text>'
    '<text class="t-s t-code" x="340" y="92" text-anchor="middle">simmer(base)</text>'
    '<rect class="box-ok" x="470" y="44" width="190" height="64" rx="8"/>'
    '<text class="t" x="565" y="70" text-anchor="middle">label 2</text>'
    '<text class="t-s t-code" x="565" y="92" text-anchor="middle">return sauce</text>'
    '<line class="ln-a" x1="210" y1="76" x2="243" y2="76" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="435" y1="76" x2="468" y2="76" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="115" y1="108" x2="115" y2="156" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="340" y1="108" x2="340" y2="156" marker-end="url(#arr)"/>'
    '<rect class="box-dim" x="20" y="158" width="415" height="50" rx="8"/>'
    '<text class="t-s t-code" x="227" y="180" text-anchor="middle">return COROUTINE_SUSPENDED</text>'
    '<text class="t-s t-m" x="227" y="198" text-anchor="middle">the thread goes off to other work</text>'
    '<text class="t-s t-m" x="560" y="176" text-anchor="middle">later: resumeWith(value)</text>'
    '<text class="t-s t-m" x="560" y="194" text-anchor="middle">jumps to the saved label</text>'
    '<rect class="box" x="20" y="230" width="640" height="52" rx="8"/>'
    '<text class="t-s t-m" x="340" y="250" text-anchor="middle">the bookmark: one object per call, on the heap</text>'
    '<text class="t-s t-code" x="340" y="270" text-anchor="middle">StateMachineKt$makeSauce$1 { label, L$0, L$1, result }</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Picture a home cook making a big dinner alone. She puts the soup on to simmer for twenty minutes, and she doesn't stand and watch it. She puts a bookmark in the recipe at the simmer step, sets a kitchen timer and starts on the salad. When the timer rings, she opens the book at the bookmark and carries on. One cook, three dishes, and nobody stands still.

A program that waits for a slow answer usually cooks the other way. Its thread, the worker that runs the code, stands by the pot until the answer comes. The soup doesn't cook any faster for being watched.

The reactive track ended with a promise: Kotlin coroutines free the thread just as its Reactor library did, but the code still reads from top to bottom, like a recipe. The keyword is `suspend`, and the easy trap is to think the word does the work by itself. It doesn't.

In this lesson, we'll share one thread among five pots, catch a `suspend` that changes nothing, read the compiler's bookmark, and wrap a callback so a cancel can reach it. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
K_SOUP = """suspend fun makeSoup(): Soup {
    val stock = boilStock()        // may pause here
    return addVegetables(stock)    // and here
}"""
J_SOUP = """// Java equivalent: plain blocking calls on a virtual thread (JDK 21+); the JVM does the pausing
Soup makeSoup() {
    Stock stock = boilStock();     // the virtual thread unmounts while it waits
    return addVegetables(stock);   // and here
}"""

S0 = """Start with what a program does while it waits. Picture code that asks a slow web service, a program on another computer that answers over the network, for something. It waits 120 ms for the answer, then asks a second service and waits 30 ms more. Nearly all of its time is waiting.

That code runs on a **thread**, one path of work through the program, with its own stack of method calls. A thread that waits in the usual way is **blocked**: it holds its memory and does nothing else until the answer comes. That's the cook standing at the pot. The Kotlin docs put the cost plainly: a thread usually needs a few megabytes of memory, and a JVM, the program that runs compiled Kotlin and Java code, typically handles a few thousand of them at once.

Kotlin's answer is the **suspend function**, a function that can pause in the middle and carry on later, without holding its thread while it's paused:

""" + pair(K_SOUP, J_SOUP) + """

When `makeSoup` pauses inside `boilStock`, the thread leaves and does other work. When the stock is ready, `makeSoup` carries on at the next line. The code still reads from top to bottom, with normal `try`/`catch` and normal return values.

A **coroutine** is one running piece of such code: work that can be paused and resumed. It's one dish on the go. A **suspension point** is a call to another suspend function, a place where the coroutine may pause. You start a coroutine with a builder, a function such as `runBlocking` or `launch`, which lesson 2 of this track covers. Two rules follow.

You can call a suspend function only from another suspend function or from inside a coroutine. Plain code has no bookmark to hand over, so the compiler refuses. (We'll see the bookmark in the third section.)

The waiting itself must be a suspending call. `delay(200)` suspends: the coroutine sets a timer and steps aside, and the thread is free. `Thread.sleep(200)` blocks: the thread stops, and every other coroutine that needs that thread waits too. The compiler accepts both without a word.

Let's watch the difference. `SleepVsDelay`, in the Try it below, uses `runBlocking`, which runs coroutines on the one thread that called it, here `main`. That thread is our cook. It starts five coroutines, the pots, and each one waits 200 ms. Predict first: with `delay`, the five waits should overlap, so the run should take a little over 200 ms. On this machine, while other programs kept it busy, it printed:

```text
pot 0 starts simmering on main
pot 1 starts simmering on main
pot 2 starts simmering on main
pot 3 starts simmering on main
pot 4 starts simmering on main
5 pots of 200 ms with delay took 358 ms
```

All five lines appeared at once, and the run took 358 ms: the 200 ms of waiting, plus start-up on a busy machine. Now change one word, and pass `sleep`:

```text
5 pots of 200 ms with Thread.sleep took 1130 ms
```

Same code, one word changed, and the cook is back at the pot. Each sleep held the only thread, so the five waits ran one after another, and the lines appeared 200 ms apart.

**A coroutine frees its thread only while it's suspended. Wait with `delay`, never with `Thread.sleep`.**

So `suspend` lets a function step away from the stove. But who comes back to it, and on which thread?"""

# ---------------------------------------------------------------- section 1
K_SCALE = """suspend fun scaleRecipe(gramsForFour: List<Int>, guests: Int): Int {
    var total = 0
    for (g in gramsForFour) total += g * guests / 4
    return total   // no suspension point anywhere
}"""
J_SCALE = """// Java equivalent: the same plain method; in Kotlin the suspend modifier changed nothing
int scaleRecipe(List<Integer> gramsForFour, int guests) {
    int total = 0;
    for (int g : gramsForFour) total += g * guests / 4;
    return total;
}"""

S1 = """The most common wrong idea about coroutines is that `suspend` sends work to a background thread. It doesn't. The word adds the ability to pause, and nothing else. Which thread runs the code is decided by the coroutine's **dispatcher**, the part of the coroutine library that hands coroutines to threads (lesson 4 of this track).

Here's a suspend function with nothing to wait for. It scales a recipe written for four people to any number of guests:

""" + pair(K_SCALE, J_SCALE) + """

`scaleRecipe` never suspends, so it runs from start to finish on the caller's thread, exactly like a normal function. IntelliJ IDEA, the editor JetBrains makes for Kotlin, greys out the modifier as redundant. Put a two-second calculation in a suspend function, and the thread that calls it is busy for two seconds. In the kitchen, that's chopping: the cook can't put a bookmark in the middle of slicing an onion.

Now the other half of the story. After a real suspension, the coroutine may carry on on a different thread. Picture the kitchen on a busy night, with friends helping. When the soup's timer rings, whichever cook is free opens the book at the bookmark. `Dispatchers.Default`, the library's ready-made pool of threads, works like that. It has one thread per **core**, a part of the processor that runs one thread at a time. A coroutine can start on worker-1, pause in `delay`, and resume on worker-3.

`WhichThread`, in the Try it below, shows both halves. It prints where `scaleRecipe` ran. Then it starts four dishes on Default, and each one notes its thread, pauses 20 ms, and does that four times. One run printed:

```text
main coroutine runs on main
scaleRecipe says 2000 g, computed on main
dish 1 ran on worker-2 -> worker-4 -> worker-4 -> worker-4
dish 3 ran on worker-4 -> worker-4 -> worker-4 -> worker-4
dish 0 ran on worker-1 -> worker-4 -> worker-4 -> worker-4
dish 2 ran on worker-3 -> worker-4 -> worker-4 -> worker-4
```

`scaleRecipe` ran on `main`, the caller's thread. Three of the four dishes started on one worker and finished on another, and none of them noticed.

Two things follow for your code. A `ThreadLocal`, a variable with a separate value for each thread, isn't safe across a suspension point, because the thread that resumes you may hold someone else's value. It's a note pinned to the cook's apron: when another cook picks up the dish, the note stays with the first cook. Lesson 4 of this track shows the coroutine way to carry such a note.

Memory visibility, on the other hand, is taken care of. Values a coroutine wrote before it paused are visible after it resumes, even on another thread, so you don't need `@Volatile` on its locals. The reason is the hand-off. To resume you on another thread, the dispatcher submits your coroutine to its pool as a task. The JDK's rule for executors, the pools that run submitted tasks, then applies: whatever a thread wrote before it submitted a task is visible to the thread that runs it. The memory model track calls that a happens-before edge. It covers one coroutine's own state. Two coroutines that share a variable still need a lock or an atomic, the tools from the first track, as lesson 10 of this track shows.

**`suspend` gives a function the right to pause, not a thread of its own. Move work to another thread on purpose.**

How can a function stop in the middle on one thread and carry on, with all its local variables, on another? Somebody has to write the bookmark, and that somebody is the compiler."""

# ---------------------------------------------------------------- section 2
K_SAUCE = """suspend fun makeSauce(onions: String): String {
    val base = fryOnions(onions)   // suspension point 1
    val sauce = simmer(base)       // suspension point 2
    return sauce
}"""
J_SAUCE = """// Java equivalent: the same steps on a virtual thread (JDK 21+); the JVM saves the whole stack instead
String makeSauce(String onions) {
    String base = fryOnions(onions);   // blocks; the virtual thread unmounts
    String sauce = simmer(base);       // and here
    return sauce;
}"""

S2 = """Coroutines need no special support from the JVM. They're a compiler feature plus a library, kotlinx.coroutines. Here's the function we'll take apart. It makes a sauce in two steps, and each step waits:

""" + pair(K_SAUCE, J_SAUCE) + """

The Kotlin compiler rewrites every suspend function in **continuation-passing style**: it adds one hidden last parameter, a `Continuation`, and changes the return type to `Any?`. `javap`, the JDK tool that prints what's inside a compiled class, shows it:

```text
// you write
suspend fun makeSauce(onions: String): String

// javap shows
public static final java.lang.Object makeSauce(java.lang.String, kotlin.coroutines.Continuation<? super java.lang.String>);
```

A **continuation** is the bookmark: an object that knows how to carry on a paused coroutine. Its interface is short: `interface Continuation<in T> { val context: CoroutineContext; fun resumeWith(result: Result<T>) }`. The context holds the coroutine's settings, which lesson 4 of this track opens up. `resumeWith` is how someone says "the wait is over, here's the value". The `Object` return is either the real result or a marker, `COROUTINE_SUSPENDED`, which means "I paused; I'll call your continuation later".

The body becomes a **state machine**, a class with a counter that says which step comes next. Each suspension point ends a state. For `makeSauce`, the compiler generates one small class, `StateMachineKt$makeSauce$1`. It has an `int label` for the next state and two fields, `L$0` and `L$1`, where local variables wait while the function is paused. Let's follow it:

1. Label 0: save the locals in the object, set `label = 1`, and call `fryOnions(onions, this)`. If that returns `COROUTINE_SUSPENDED`, return the marker straight up the stack. The thread is now free.
2. When the onions are golden, someone calls `resumeWith(base)`. That calls `makeSauce` again, with the same object. A `tableswitch`, the JVM's instruction for a `switch` over a small range of `int`s, jumps on `label` to state 1, which picks up `base` and calls `simmer`.
3. Label 2: take the sauce and return it to whoever is waiting.

If `fryOnions` doesn't suspend (the onions were fried earlier, say), it returns its value at once and the function carries on. Nothing is scheduled, and no thread changes.

The bookmark from the opening is exactly that object. `label` is the page, and the `L$` fields are the sticky note of what's already measured. You met a bigger bookmark in How virtual threads work. There, the JVM copied a virtual thread's whole stack to the heap, the memory where objects live, every frame of it, like a full order slip clipped to the board. A coroutine's bookmark is smaller: one small object for each suspend function still running, holding only that function's own fields.

That explains both the cost and the rules. A suspended coroutine is a few small objects, not a thread's stack, so you can have hundreds of thousands. And plain code can't call a suspend function, because it has no continuation to pass in.

Here the picture breaks a little. A real cook hears the timer and walks back to the book herself. A paused coroutine does nothing at all until something calls `resumeWith`: the library's timer, for `delay`, or the code that got the answer. If nothing ever calls it, the coroutine stays paused for good.

**A suspended coroutine is a bookmark, not a thread. Something has to call `resumeWith` to wake it.**

So who calls `resumeWith` when the answer comes from someone else's code?"""

ASIDE = {
    "title": "Does every pause create a new object?",
    "body": "No. The state-machine object is created once, when the function is called, and reused at every suspension point of that call. `makeSauce` pauses twice and allocates one `StateMachineKt$makeSauce$1`. A suspend function whose only suspending call is its very last step needs no state machine at all: it passes its caller's continuation straight through. The KEEP, the design document for Kotlin coroutines (linked in the sources), describes both rules.",
}

# ---------------------------------------------------------------- section 3
K_WRAP = """suspend fun BakerySdk.orderAwait(bread: String): String =
    suspendCancellableCoroutine { cont ->
        val cancel = order(bread) { ticket -> cont.resume(ticket) }   // 1. order; resume on the callback
        cont.invokeOnCancellation { cancel() }                         // 2. we were cancelled: tell the bakery
    }"""
J_WRAP = """// Java equivalent: complete a CompletableFuture from the callback, and pass cancellation back
CompletableFuture<String> orderAsync(BakerySdk bakery, String bread) {
    CompletableFuture<String> result = new CompletableFuture<>();
    Runnable cancel = bakery.order(bread, result::complete);              // 1. order; complete on the callback
    result.whenComplete((v, e) -> { if (e != null) cancel.run(); });      // 2. timed out or cancelled: tell the bakery
    return result;
}"""

S3 = """Many libraries don't offer suspend functions. They take a **callback**, a function you pass in that the library calls later with the answer. Picture a bakery with an ordering library. You place an order, the call returns at once, and the library calls you back when the bread is ready. (A library that a company hands out for talking to its service is often called an SDK, a software development kit.)

`suspendCancellableCoroutine` turns such a callback into a suspend function. It suspends the coroutine and hands you its continuation, and you resume it when the callback fires:

""" + pair(K_WRAP, J_WRAP) + """

Read the Kotlin version aloud: "Pause here and place the order. When the bakery calls back, carry on with its ticket. If we're cancelled first, cancel the order." The `order` call returns a small function that cancels the order, and that's the `cancel` we keep.

Why the long name? The standard library also has a plain `suspendCoroutine`, and it works fine until someone **cancels** the caller, that is, asks the coroutine to stop. Our caller uses `withTimeout(100)`, which cancels its block if it isn't done in 100 ms. `CallbackBridge`, in the Try it below, wraps the bakery with the plain version first. The bakery takes a full second, as bakeries do. Predict: when does `withTimeout(100)` return?

```text
  timed out
withTimeout(100) returned after 1021 ms
```

Not after 100 ms: after a whole second. The timeout did fire at 100 ms. But a coroutine paused in `suspendCoroutine` can't react to the cancel. It stays paused until the bakery calls back, and the bakery never hears that anyone gave up. With the cancellable version and `invokeOnCancellation`, the same run printed:

```text
  bakery: order for sourdough cancelled
  timed out
withTimeout(100) returned after 135 ms
```

The order was cancelled, and the caller was free after about 100 ms, plus a little for the busy machine.

Three rules make a wrapper like this correct.

Resume exactly once. Call `resume` with a value or `resumeWithException` with an error. A second resume on the same continuation throws `IllegalStateException`.

Use the cancellable version, and tell the library when you give up, in `invokeOnCancellation`.

Expect late replies. If the coroutine is cancelled first, a callback that arrives afterwards is ignored. kotlinx.coroutines calls this the **prompt cancellation guarantee**: a cancelled coroutine doesn't resume successfully, even if the value was already on its way. If that late value is something you must give back, such as a borrowed pot, pass a cleanup function: `cont.resume(pot) { _, late, _ -> late.close() }`. The library calls it with the value it couldn't deliver. The worked example below builds exactly that.

**A callback wrapper must resume once and pass the cancel on. Use `suspendCancellableCoroutine`.**

This tool is for callbacks that fire once. Listeners that fire many times need `callbackFlow` (lesson 9 of this track). A `CompletableFuture` needs none of this, because `future.await()` already does it (lesson 11 of this track)."""

# ---------------------------------------------------------------- closing
CLOSING = """We started with a cook who puts a bookmark in the recipe instead of watching the pot. A suspend function does the same: it pauses at a suspension point, a small state machine keeps its place, and the thread goes off to other work. `Thread.sleep` still makes the cook stand at the pot.

Now search your own Kotlin code for `Thread.sleep`, and for other blocking calls inside a `suspend fun`. Each one holds a thread that other coroutines are waiting for.

Next, we'll start several dishes at once. How do `launch` and `async` start coroutines, and why does one `await` in the wrong place make three waits take as long as all three added up?"""

L = {
 "id": "co-01",
 "title": "Suspend functions from zero",
 "minutes": 35,
 "goal": "By the end you can say what `suspend` really does (and what it doesn't), read the state machine the compiler builds from a suspend function, and wrap a callback API in a cancellable suspend function.",
 "opening": OPENING,
 "warmup": {
  "q": "What does adding `suspend` to a function do?",
  "options": [
   "It runs the function on a background thread",
   "It lets the function pause at suspending calls and carry on later, without holding a thread while it waits",
   "It makes the function return a `CompletableFuture`",
   "It runs the function in parallel with its caller"
  ],
  "answer": 1,
  "why": "`suspend` only gives a function the ability to pause, like the cook's bookmark. It doesn't pick a thread, start anything in parallel or return a future. The coroutine's dispatcher chooses the thread, and a suspend function that never reaches a suspending call runs from start to finish on its caller's thread."
 },
 "sections": [
  {
   "h": "One cook, five pots: a suspend function waits without holding its thread",
   "body": S0,
   "try": {
    "title": "Five pots on one thread",
    "minutes": 4,
    "steps": [
     "Read `SleepVsDelay.kt`. All five coroutines, the pots, run on `main`, the one cook. Predict the total time with `delay`.",
     "Run it with the command below.",
     "Run it again with `-Pargs=sleep` added. Predict first, then watch how the five lines appear."
    ],
    "code": demo("SleepVsDelay.kt", "SleepVsDelayJava.java"),
    "expect": "With `delay` the five lines appear at once and the run takes a little over 200 ms on an idle machine (358 and 427 ms in two runs here, on a busy one): the waits overlap on one thread. With `Thread.sleep` it takes over a second (1,130 ms here), and the lines appear 200 ms apart, because each sleep holds the only thread. Same code, one word changed. The Java twin shows the same two pictures (234 ms and 1,032 ms here): a timer callback on a single-thread executor is the closest Java match for `delay`."
   }
  },
  {
   "h": "`suspend` doesn't choose a thread: the code runs wherever it's called",
   "body": S1,
   "try": {
    "title": "Watch dishes change threads",
    "minutes": 3,
    "steps": [
     "Read `WhichThread.kt`. Predict which thread runs `scaleRecipe`.",
     "Run it. Look at the `dish N ran on` lines.",
     "Run it twice more. Do the thread sequences repeat?"
    ],
    "code": demo("WhichThread.kt", "WhichThreadJava.java"),
    "expect": "`scaleRecipe` runs on `main`, the caller's thread. Each dish shows a sequence such as `worker-1 -> worker-4 -> worker-4 -> worker-4`: after each `delay`, any free Default thread may pick it up. The sequences change from run to run. The Java twin shows the same thing for virtual threads: after each `Thread.sleep`, a virtual thread may carry on on a different carrier, the platform thread that runs it."
   }
  },
  {
   "h": "The bookmark the compiler writes: a suspend function becomes a state machine",
   "body": S2,
   "aside": ASIDE,
   "figure": {"svg": FIG, "caption": "Each suspension point ends a state. Suspending returns a marker and frees the thread; resuming calls the same function again, and the saved label, the bookmark, says where to carry on."},
   "try": {
    "title": "Read the state machine with javap",
    "minutes": 5,
    "steps": [
     "Run the demo once, so Gradle compiles it: `" + run("StateMachineKt") + "`.",
     "From `labs/`, run the first `javap` command. Find the `Continuation` parameter and the `Object` return type on `makeSauce`.",
     "Run the second command. It prints the generated state class, the bookmark. Find `label` and the `L$` fields.",
     "Run the third command. It prints one `tableswitch` for each of the three suspend functions. Predict first: how many cases will the one for `makeSauce`, the last of the three, have?"
    ],
    "code": {"lang": "bash", "title": "terminal",
             "src": "javap -p coroutines/build/classes/kotlin/demo/workbench/coroutines/l01/StateMachineKt.class\n\njavap -p 'coroutines/build/classes/kotlin/demo/workbench/coroutines/l01/StateMachineKt$makeSauce$1.class'\n\njavap -c -p coroutines/build/classes/kotlin/demo/workbench/coroutines/l01/StateMachineKt.class | grep -A4 tableswitch",
             "run": ""},
    "expect": "`makeSauce(java.lang.String, kotlin.coroutines.Continuation<? super java.lang.String>)` returns `java.lang.Object`, and so do `fryOnions` and `simmer`. The state class extends `kotlin.coroutines.jvm.internal.ContinuationImpl` and has `L$0`, `L$1`, `result` and `int label`. The first two `tableswitch`es say `0 to 1`: they belong to `fryOnions` and `simmer`, which pause once each. The third, in `makeSauce`, says `0 to 2`: three states for two suspension points."
   },
   "refs": [
    {"title": "KEEP: Kotlin coroutines design (continuations and state machines)", "url": "https://github.com/Kotlin/KEEP/blob/master/proposals/coroutines.md", "kind": "read"}
   ]
  },
  {
   "h": "Wrapping a callback in a suspend function, so a cancel can reach it",
   "body": S3,
   "try": {
    "title": "Make a timeout reach the bakery",
    "minutes": 5,
    "steps": [
     "Read `CallbackBridge.kt`. The bakery answers after one second. The caller allows 100 ms. Predict how long `withTimeout(100)` takes to return.",
     "Run it.",
     "Change `orderAwait` to use `suspendCancellableCoroutine` (import `kotlinx.coroutines.suspendCancellableCoroutine`). Keep the function the library returns: `val cancel = order(bread) { ticket -> cont.resume(ticket) }`, then add `cont.invokeOnCancellation { cancel() }`.",
     "Run it again.",
     "In the Java twin, run it, then add `result.whenComplete((v, e) -> { if (e != null) cancel.run(); });` before `return result;` and run it again."
    ],
    "code": demo("CallbackBridge.kt", "CallbackBridgeJava.java"),
    "expect": "First run: `timed out` after about 1,000 ms (1,021 ms here). The timeout did fire at 100 ms, but `suspendCoroutine` couldn't wake up until the bakery answered, and the bakery was never told. After the change: `bakery: order for sourdough cancelled`, then `timed out` after about 100 ms (135 ms here). The Java twin returns at about 100 ms even before your change (114 ms here), because `orTimeout` completes the future by itself. But the bakery hears about it only once you add the `whenComplete` hook (123 ms here)."
   },
   "refs": [
    {"title": "suspendCancellableCoroutine (API reference)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/suspend-cancellable-coroutine.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "Two waits in a row: CompletableFuture vs suspend",
  "java": {"title": "Sauce.java", "src": "CompletableFuture<String> makeSauce(String onions) {\n    return kitchen.fryOnions(onions)                  // CompletableFuture<String>\n        .thenCompose(base -> kitchen.simmer(base))    // CompletableFuture<String>\n        .orTimeout(2, TimeUnit.SECONDS);\n}"},
  "kotlin": {"title": "Sauce.kt", "src": "suspend fun makeSauce(onions: String): String = withTimeout(2.seconds) {\n    val base = kitchen.fryOnions(onions)   // suspend fun\n    kitchen.simmer(base)                   // suspend fun\n}"},
  "note": "Both versions free the thread while they wait. The Java version says \"then\" with callbacks: each `thenCompose` registers a function to run later, errors arrive wrapped in `CompletionException`, and `orTimeout` only completes the outer future with an error. The two calls underneath keep running, because cancelling a `CompletableFuture` never interrupts the work behind it. The Kotlin version reads like plain blocking code: locals, `try`/`catch` and loops all work, and the compiler builds the callbacks for you. When `withTimeout` fires, it cancels the coroutine, and the cancel reaches both calls if they're written to cooperate, as in the last section. On JDK 21 and later you can also write the Java version as plain blocking calls on a virtual thread. Lesson 11 of this track helps you choose between the two."
 },
 "worked": {
  "title": "Wrap a pot-lending library without losing pots",
  "steps": [
   {"say": "A community kitchen lends out big stock pots. Its library's `borrow` returns a `Ticket` at once and calls you back later with a pot or an error. Every pot must be given back, which is what its `close()` does. You want `suspend fun PotLender.borrowAwait(): Pot`.",
    "code": "class Pot(val id: Int) : AutoCloseable { override fun close() { /* back to the shelf */ } }\nfun interface Ticket { fun cancel() }\ninterface PotLender {\n    fun borrow(onReady: (Pot?, Throwable?) -> Unit): Ticket\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent: the same library shape\nfinal class Pot implements AutoCloseable {\n    @Override public void close() { /* back to the shelf */ }\n}\ninterface Ticket { void cancel(); }\ninterface PotLender {\n    Ticket borrow(BiConsumer<Pot, Throwable> onReady);\n}", "alt_lang": "java"},
   {"say": "Ask for the pot inside `suspendCancellableCoroutine`, and resume exactly once from the callback: a value on success, an exception on error.",
    "code": "suspend fun PotLender.borrowAwait(): Pot = suspendCancellableCoroutine { cont ->\n    // 1. ask for a pot; the library calls back on its own thread\n    val ticket = borrow { pot, error ->\n        // 2. resume exactly once, with a value or an error\n        if (error != null) cont.resumeWithException(error)\n        else cont.resume(pot!!)\n    }\n}", "lang": "kotlin",
    "alt_code": "// Java equivalent: complete a CompletableFuture from the callback\nstatic CompletableFuture<Pot> borrowAsync(PotLender lender) {\n    CompletableFuture<Pot> result = new CompletableFuture<>();\n    // 1. ask for a pot; the library calls back on its own thread\n    Ticket ticket = lender.borrow((pot, error) -> {\n        // 2. complete exactly once, with a value or an error\n        if (error != null) result.completeExceptionally(error);\n        else result.complete(pot);\n    });\n    return result;\n}", "alt_lang": "java"},
   {"say": "If the caller gives up, stop waiting for a pot. `invokeOnCancellation` runs when the coroutine is cancelled while it's suspended here.",
    "code": "    // 3. our caller gave up: cancel the ticket\n    cont.invokeOnCancellation { ticket.cancel() }", "lang": "kotlin",
    "alt_code": "    // 3. our caller gave up (cancelled the future): cancel the ticket\n    result.whenComplete((p, e) -> { if (result.isCancelled()) ticket.cancel(); });", "alt_lang": "java"},
   {"say": "One gap is left. The kitchen may hand out a pot just after you were cancelled. The continuation ignores that late resume, and the pot never goes back on the shelf. Use the `resume` overload that takes a cleanup function: the library calls it with the value it couldn't deliver.",
    "code": "        else cont.resume(pot!!) { _, late, _ -> late.close() }   // 4. a late pot: give it back", "lang": "kotlin",
    "alt_code": "        // 4. a late pot: complete() returns false when the future is already done, so give it back\n        else if (!result.complete(pot)) pot.close();", "alt_lang": "java"},
   {"say": "Self-check: why is step 4 needed even though step 3 cancels the ticket? (Cancelling is a request. The kitchen may already be calling you back on another thread, so the pot can still arrive after you were cancelled.)",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Wrap the bakery's library, then fix a blocking pause",
  "minutes": 12,
  "files": [
   f"{lab}/main/{P}/Bakery.kt",
   f"{lab}/main/{P}/SuspendingBakery.kt",
   f"{lab}/main/{P}/Backoff.kt"
  ],
  "run": "./gradlew :coroutines:test --tests 'workbench.coroutines.l01.*'",
  "steps": [
   "Meet the classes. `Bakery.kt` is the bakery's ordering library, and you don't change it. `BakeryClient.order` takes a `BreadOrder` and an `OrderCallback`, and returns a `PendingOrder` at once. Later, on its own thread, it calls `onReady` with a `Pickup` (a ticket to collect the bread) or `onFailed` with an error such as `SoldOutException`.",
   "Run the tests once. All five fail: four hit the `TODO` in `orderAwait`, and the fifth shows three coroutines waiting one after another.",
   "Write `orderAwait` in `SuspendingBakery.kt` with `suspendCancellableCoroutine`. Place the order with an `OrderCallback` object whose two methods resume the continuation.",
   "Register `invokeOnCancellation`, so that a cancelled caller calls `cancel()` on the `PendingOrder`.",
   "Fix `pauseBeforeRetry` in `Backoff.kt`, which waits before phoning the bakery again, so that it waits without blocking the thread.",
   "Run the tests until all five pass."
  ],
  "hints": [
   "You need three imports: `kotlinx.coroutines.suspendCancellableCoroutine`, `kotlin.coroutines.resume` and `kotlin.coroutines.resumeWithException`.",
   "An anonymous object implements the callback: `object : OrderCallback { override fun onReady(pickup: Pickup) = cont.resume(pickup); ... }`.",
   "If the cancellation test hangs for 10 seconds, you used `suspendCoroutine`. It can't react to cancellation, so `cancelAndJoin` waits forever.",
   "The backoff test runs under `runTest`, which runs `delay` on virtual time, a pretend clock that jumps ahead instead of waiting. That's why it expects `currentTime` to be exactly 200."
  ],
  "done_when": "All five tests in `SuspendFunctionsTest` pass."
 },
 "drill": {
  "title": "Wrap a callback from memory",
  "minutes": 4,
  "prompt": "Close this page. A recipe website's library has `fun lookup(dish: String, cb: (Recipe?, Throwable?) -> Unit): Call`, and `Call` has a `cancel()` method. Write `suspend fun RecipeSite.lookupAwait(dish: String): Recipe` so that errors are thrown and a cancelled caller cancels the call. Then compare.",
  "answer": {"lang": "kotlin", "src": "suspend fun RecipeSite.lookupAwait(dish: String): Recipe =\n    suspendCancellableCoroutine { cont ->\n        val call = lookup(dish) { recipe, error ->\n            if (error != null) cont.resumeWithException(error)\n            else cont.resume(recipe!!)\n        }\n        cont.invokeOnCancellation { call.cancel() }\n    }",
             "alt": {"lang": "java", "title": "Java equivalent", "src": "// Java equivalent: a CompletableFuture that cancels the call when it is cancelled\nstatic CompletableFuture<Recipe> lookupAsync(RecipeSite site, String dish) {\n    CompletableFuture<Recipe> result = new CompletableFuture<>();\n    Call call = site.lookup(dish, (recipe, error) -> {\n        if (error != null) result.completeExceptionally(error);\n        else result.complete(recipe);\n    });\n    result.whenComplete((v, e) -> { if (result.isCancelled()) call.cancel(); });\n    return result;\n}"}}
 },
 "recap": [
  "`suspend` lets a function pause at suspension points without holding a thread. It doesn't choose a thread or run anything in the background.",
  "`delay` suspends and frees the thread; `Thread.sleep` blocks it, and every coroutine that needs that thread waits.",
  "The compiler adds a `Continuation` parameter, returns `Any?` (`COROUTINE_SUSPENDED` or the result), and turns the body into a state machine: a `label` for the next step and fields for the locals. That object is the bookmark.",
  "A coroutine may resume on another thread after a pause, so a `ThreadLocal` doesn't follow it, but its own writes stay visible.",
  "Wrap a one-shot callback with `suspendCancellableCoroutine`: resume exactly once, pass the cancel on in `invokeOnCancellation`, and expect late replies.",
  "The limit: a coroutine can pause only at a suspend call. Blocking calls and long calculations inside it hold the thread, `suspend` or not."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "This runs on one thread: `runBlocking { repeat(3) { launch { Thread.sleep(100) } } }`. About how long does it take?",
   "options": ["About 100 ms, because the three coroutines run concurrently", "About 300 ms, because each sleep blocks the only thread", "About 0 ms, because `launch` returns at once", "It doesn't compile: `Thread.sleep` isn't allowed in a coroutine"],
   "answer": 1,
   "why": "`Thread.sleep` blocks the thread, and `runBlocking` gives all three coroutines one thread, so they sleep one after another. With `delay(100)` they would overlap and finish in about 100 ms. The compiler happily accepts `Thread.sleep` here, which is why the bug survives code review."},
  {"q": "`suspend fun scaleRecipe(gramsForFour: List<Int>, guests: Int): Int` is pure arithmetic with no suspending calls. A coroutine on thread `worker-2` calls it. Which thread runs the arithmetic?",
   "options": ["`worker-2`, the caller's thread", "A thread from `Dispatchers.IO`", "A new background thread for each call", "A thread the JVM picks at random"],
   "answer": 0,
   "why": "A suspend function that never suspends is ordinary code on the caller's thread. `suspend` doesn't move work anywhere. To run CPU work elsewhere you switch dispatcher on purpose, with `withContext(Dispatchers.Default)`, which lesson 4 of this track covers."},
  {"q": "How does `suspend fun stockOf(item: String): Int` look to a Java caller?",
   "options": ["`int stockOf(String item)`", "`CompletableFuture<Integer> stockOf(String item)`", "`Object stockOf(String item, Continuation<? super Integer> continuation)`", "`void stockOf(String item, Consumer<Integer> callback)`"],
   "answer": 2,
   "why": "The compiler adds a `Continuation` as the last parameter and changes the return type to `Object`, which holds either the result (boxed) or `COROUTINE_SUSPENDED`. That's why Java code can't simply call suspend functions; lesson 11 of this track shows the bridges, such as `future {}`."},
  {"q": "A callback library is wrapped with `suspendCoroutine`, not the cancellable version. The caller runs `withTimeout(200) { library.callAwait() }`, and the library answers after 3 seconds. What happens?",
   "options": ["`TimeoutCancellationException` at 200 ms, and the library call is cancelled", "The call returns the library's value after 3 seconds; the timeout is ignored", "`IllegalStateException`, because the continuation was resumed twice", "The coroutine stays suspended until the library answers at 3 s, then throws `TimeoutCancellationException`; the library is never told"],
   "answer": 3,
   "why": "The timeout cancels the coroutine at 200 ms, but a continuation that can't be cancelled can't wake up until it's resumed. When the library answers at 3 s, the coroutine finds itself cancelled and throws. `suspendCancellableCoroutine` would resume at 200 ms and run `invokeOnCancellation`, where you cancel the library call."},
  {"q": "From the virtual threads track: a virtual thread calls `Thread.sleep(200)`. What happens to its carrier thread?",
   "options": ["The carrier is blocked for the full 200 ms", "The virtual thread unmounts, and the carrier is free to run other virtual threads", "The JVM creates a new carrier to replace it", "`sleep` throws, because virtual threads can't sleep"],
   "answer": 1,
   "why": "When a virtual thread blocks in `sleep`, the JVM saves its stack and unmounts it, so the carrier runs other virtual threads. It's the same idea as a coroutine suspending, done by the JVM for any blocking call instead of by the Kotlin compiler for `suspend` calls.",
   "from": "vt-02"}
 ],
 "flashcards": [
  {"front": "Does `suspend` run a function on a background thread?", "back": "No. It only lets the function pause without blocking. The dispatcher decides the thread, and a suspend function that never suspends runs on its caller's thread."},
  {"front": "Inside a coroutine, what's the difference between `delay(200)` and `Thread.sleep(200)`?", "back": "`delay` suspends the coroutine and frees the thread for others. `Thread.sleep` blocks the thread, so every coroutine waiting for that thread waits too."},
  {"front": "What does the compiler add to a suspend function's signature?", "back": "A `Continuation<T>` as the last parameter. The return type becomes `Any?` (`Object` in Java)."},
  {"front": "What does a compiled suspend function return when it pauses?", "back": "The marker `COROUTINE_SUSPENDED`. The real result arrives later through `continuation.resumeWith(...)`."},
  {"front": "Where does a suspended coroutine keep its local variables?", "back": "In fields (`L$0`, `L$1`, ...) of a small state-machine object on the heap, next to an `int label` that says which state runs next."},
  {"front": "Why wrap a callback with `suspendCancellableCoroutine` and not `suspendCoroutine`?", "back": "Only the cancellable one reacts to cancellation: it resumes the caller at once with `CancellationException` and runs `invokeOnCancellation`, where you cancel the underlying call."},
  {"front": "A callback fires after its coroutine was cancelled. What happens to `cont.resume(value)`?", "back": "It's ignored (the prompt cancellation guarantee). If the value must be given back, pass a cleanup function: `cont.resume(value) { _, v, _ -> v.close() }`."}
 ],
 "terms": [
  {"term": "Thread", "plain": "One path of work through a program, with its own stack of method calls. In the kitchen, a pair of hands."},
  {"term": "Coroutine", "plain": "One running piece of work that can pause and resume later, without holding a thread while it's paused."},
  {"term": "Suspend function", "plain": "A function marked `suspend`. It may pause at suspending calls, and it can only be called from a coroutine or another suspend function."},
  {"term": "Suspension point", "plain": "A call to a suspend function, where the caller may pause. It doesn't always pause, for example when the answer is already there."},
  {"term": "Continuation", "plain": "The object that knows how to resume a paused coroutine: its context plus `resumeWith(result)`. The bookmark in the recipe."},
  {"term": "COROUTINE_SUSPENDED", "plain": "The marker a compiled suspend function returns to say it paused and will resume through the continuation."},
  {"term": "Continuation-passing style", "plain": "Compiling a function so it receives \"what to do next\" as an extra parameter, instead of returning to a waiting caller."},
  {"term": "Dispatcher", "plain": "The part of the coroutine library that decides which thread runs a coroutine, and which thread it resumes on."}
 ],
 "explain_back": {
  "prompt": "A friend says: \"I marked our `loadRecipes` function `suspend`, so it no longer blocks the thread.\" Inside, it calls a database driver that blocks until the database answers. Explain what `suspend` really changed, and what you'd do instead.",
  "answer": "`suspend` only gives the function the right to pause at suspension points, and the compiler adds a continuation parameter so it can be resumed later. It doesn't move the code to another thread. The database call blocks; it doesn't suspend. So the function never pauses: it holds the caller's thread for the whole query, exactly as before, like a cook standing at the pot. To keep that thread free, the blocking call has to run somewhere else, for example inside `withContext(Dispatchers.IO) { ... }` (lesson 4 of this track), or the driver has to offer a suspending or callback API that we wrap with `suspendCancellableCoroutine` or `await()`."
 },
 "deeper": {
  "minutes": 10,
  "body": "Kotlin coroutines and Java virtual threads both rest on continuations, but they keep them in different places.\n\nKotlin's continuations are **stackless**. The compiler rewrites each suspend function into a state machine, and a suspended coroutine is a chain of those small state objects, one for each suspend function still in progress. That's why `suspend` is part of the function's type: every function between the coroutine and the suspending call must be compiled this way, or there's nowhere to save its state. People call this function coloring: suspend functions have a different color, and the color spreads to every caller. It's also why coroutines work on any JVM version, on Android, and on Kotlin/JS and Kotlin/Native, where there are no virtual threads.\n\nVirtual threads use **stackful** continuations inside the JVM. When a virtual thread blocks, the JVM copies its stack frames to the heap and unmounts it from the carrier. Any blocking call, in any library, can pause it, with no change to the code and no coloring. The price is that the JVM decides when to pause, and code that holds a monitor or calls native code could pin the carrier on older JDKs (JDK 24 removed most pinning on `synchronized`, JEP 491).\n\nNeither is free of surprises. A coroutine pauses only where you wrote a suspend call, which makes every pause visible in the code but forces the color on every caller. A virtual thread pauses anywhere the JDK blocks, which keeps old code unchanged but hides where the pauses are.\n\nRead the \"Implementation details\" part of the KEEP (linked in the sources) if you want the pseudo-Java the compiler generates, including how the generated `invokeSuspend` method re-enters the function."
 },
 "sources": [
  {"title": "Coroutines basics (Kotlin docs)", "url": "https://kotlinlang.org/docs/coroutines-basics.html"},
  {"title": "KEEP: Kotlin coroutines design document (Breslav, Elizarov)", "url": "https://github.com/Kotlin/KEEP/blob/master/proposals/coroutines.md"},
  {"title": "suspendCancellableCoroutine (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/suspend-cancellable-coroutine.html"},
  {"title": "Intro to coroutines and channels (Kotlin hands-on tutorial)", "url": "https://kotlinlang.org/docs/coroutines-and-channels.html"}
 ]
}
out = ROOT / "content/lessons/co-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
