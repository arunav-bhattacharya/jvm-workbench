import json, pathlib

ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/flows/src"
P = "kotlin/workbench/flows/l01"
J = "java/workbench/flows/l01"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{LAB}/demo/{P}/{name}"
jdemo = lambda name: f"{LAB}/demo/{J}/{name}"
run = lambda cls: f"./gradlew :flows:demo -Pmain=workbench.flows.l01.{cls}"


def tryit(kt, java):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(demo(kt)), "run": run(k + "Kt"), "file": demo(kt),
            "alt": {"lang": "java", "title": java, "src": read(jdemo(java)), "run": run(j), "file": jdemo(java)}}


FIG = (
    '<svg viewBox="0 0 700 330" role="img" aria-label="Nested boxes show the call stack for one value: main calls collect, '
    'collect runs the flow block, which is the cook; the block calls emit, emit runs map\'s collector, the helper, and that runs '
    'your lambda, the diner. A timeline on the right shows the cook waiting inside emit while the diner eats for 300 ms: '
    'emit 1 is called at 100 ms and returns at 400 ms, emit 2 is called at 500 ms.">'
    '<text class="t-s t-m" x="215" y="24" text-anchor="middle">One thread, one stack. Each box is a call still running.</text>'
    '<rect class="box" x="10" y="38" width="410" height="284" rx="8"/>'
    '<text class="t-s" x="215" y="58" text-anchor="middle">main calls collect { }</text>'
    '<rect class="box" x="30" y="72" width="370" height="242" rx="8"/>'
    '<text class="t-s" x="215" y="92" text-anchor="middle">the flow { } block runs: the cook</text>'
    '<rect class="box-b" x="50" y="106" width="330" height="200" rx="8"/>'
    '<text class="t-s t-b" x="215" y="126" text-anchor="middle">emit(soup): the cook walks to the table</text>'
    '<rect class="box" x="70" y="140" width="290" height="158" rx="8"/>'
    '<text class="t-s" x="215" y="160" text-anchor="middle">map\'s collector: the helper</text>'
    '<rect class="box-a" x="90" y="174" width="250" height="116" rx="8"/>'
    '<text class="t-s" x="215" y="198" text-anchor="middle">your collect { } lambda: the diner</text>'
    '<text class="t-s t-code" x="215" y="222" text-anchor="middle">eat(SOUP)</text>'
    '<text class="t-s t-a" x="215" y="252" text-anchor="middle">emit returns only when</text>'
    '<text class="t-s t-a" x="215" y="270" text-anchor="middle">this box closes</text>'
    '<text class="t-s t-b" x="565" y="24" text-anchor="middle">The cook\'s clock</text>'
    '<text class="t-s t-m" x="565" y="42" text-anchor="middle">100 ms to cook, 300 ms to eat</text>'
    '<line class="ln" x1="470" y1="56" x2="470" y2="306"/>'
    '<circle class="box-a" cx="470" cy="70" r="4"/>'
    '<text class="t-s" x="482" y="74">t=100  emit(1) called</text>'
    '<rect class="box-b" x="465" y="78" width="10" height="72" rx="4"/>'
    '<text class="t-s t-b" x="482" y="104">cook waits at the table</text>'
    '<text class="t-s t-m" x="482" y="122">300 ms inside emit</text>'
    '<circle class="box-a" cx="470" cy="156" r="4"/>'
    '<text class="t-s" x="482" y="160">t=400  emit(1) returns</text>'
    '<circle class="box-a" cx="470" cy="190" r="4"/>'
    '<text class="t-s" x="482" y="194">t=500  emit(2) called</text>'
    '<rect class="box-b" x="465" y="198" width="10" height="72" rx="4"/>'
    '<text class="t-s t-b" x="482" y="236">waits again</text>'
    '<circle class="box-a" cx="470" cy="276" r="4"/>'
    '<text class="t-s" x="482" y="280">t=800  emit(2) returns</text>'
    '<text class="t-s t-m" x="482" y="302">t=900  emit(3) called</text>'
    '</svg>'
)

OPENING = """Picture the home cook from the coroutines track at dinner time. Tonight's recipe card lists three dishes: soup, salad and roast. The card cooks nothing by itself. When a diner sits down and asks to be served, the cook starts at the top. She makes the soup, carries the bowl to the table and stays there while the diner eats. This kitchen has no counter and no shelf, so there is nowhere to put a plate down. Only when the bowl is empty does she walk back and start the salad. It's lovely service, and it makes for a long dinner.

A Kotlin flow serves its values the same way. The easy trap is to picture `emit` dropping a value into a queue while the cook carries on.

The coroutines track ended with Coroutines meet Java, where flows crossed into Java and Reactor and back like sealed boxes. In this lesson, we'll open the box: predict a dinner's print order, build a flow from two small interfaces, read the stack from inside the diner, and trace the rules from Flow basics back to one function call. Before we start, make a guess, and keep it in mind."""

S1 = r"""Here is that dinner as a flow. A **flow** is a stream of values that a program hands over one at a time, and `flow { }` is the usual way to build one. Inside its block, `emit(dish)` hands one value to whoever is collecting. `collect { }` is the call that asks for the values: it runs the block and receives each one.

In this track the people in the kitchen get jobs in the code. The cook is the **producer**, the code inside `flow { }` that makes the values. The diner is the **collector**, the code inside `collect { }` that receives them.

The cook prints a line before and after each `emit`, and the diner prints a line for each dish. Before you read on, write down the order of the lines:

```kotlin
val dinner = flow {
    for (dish in card) {                     // "soup", "salad", "roast"
        println("cook    $dish")
        emit(dish)
        println("emit($dish) returned")
    }
}
println("flow built")
dinner.collect { dish -> println("eat     $dish") }
println("collect returned")
```

```java
// Java equivalent: Java has no Flow, so this is a hand-written push "flow".
// The cook calls the diner's Consumer once per dish.
static void cookDinner(List<String> card, Consumer<String> diner) {
    for (String dish : card) {
        System.out.println("cook    " + dish);
        diner.accept(dish);
        System.out.println("accept(" + dish + ") returned");
    }
}

cookDinner(card, dish -> System.out.println("eat     " + dish));
```

Two guesses are tempting. One says the three `cook` lines come first and then the three `eat` lines, as if `emit` put each dish on a shelf for later. The other gets the pairs right but prints `emit(soup) returned` before `eat soup`, as if `emit` handed the bowl over and walked off. Here is the real output:

```text
flow built
cook    soup
eat     soup
emit(soup) returned
cook    salad
eat     salad
emit(salad) returned
cook    roast
eat     roast
emit(roast) returned
collect returned
```

`flow built` comes first, so building the flow ran none of its block. And `eat soup` comes before `emit(soup) returned`: the diner's code ran while `emit` was still running. The cook never put a plate down anywhere, because this kitchen has nowhere to put one. There is no queue here and no second **thread**, the worker that runs the code.

Flow basics gave you three rules about flows. They are cold, they handle one value at a time, and a slow collector slows the producer. All three come from one fact: `emit` is a plain function call into the collector.

The Java version prints the same order for the same reason. `accept` is a method call, and the line after a call runs when the call returns. About a dozen lines of Kotlin are enough to build a flow that works the same way, so let's write them."""

S2 = r"""A flow needs a receiving end and a sending end, and each one is a single suspend function. A **suspend function** is one that can pause without holding its thread, as the coroutines track showed from its first lesson. The piece of work that runs it is a **coroutine**, which can pause and carry on later. Here are the two ends, written from scratch, with toy names so they don't clash with the library's:

```kotlin
fun interface ToyCollector<in T> {
    suspend fun emit(value: T)
}

interface ToyFlow<out T> {
    suspend fun collect(collector: ToyCollector<T>)
}

fun <T> toyFlow(block: suspend ToyCollector<T>.() -> Unit): ToyFlow<T> =
    object : ToyFlow<T> {
        override suspend fun collect(collector: ToyCollector<T>) = collector.block()
    }
```

```java
// Java equivalent: the same two interfaces, with plain blocking methods
interface ToyCollector<T> {
    void emit(T value);
}

interface ToyFlow<T> {
    void collect(ToyCollector<T> collector);    // one abstract method, so a lambda is a ToyFlow
}
```

The first interface is the diner. A `ToyCollector` has one function, `emit`, that takes one value. The second is the recipe card. A `ToyFlow` has one function, `collect`, that takes a collector and pushes values into it. The `in T` and `out T` say which way values travel: a collector only takes values in, and a flow only hands them out.

The builder is the whole trick. `toyFlow { ... }` stores your block in an object and returns it. Nothing runs. When someone calls `collect(collector)`, the object runs your block with that collector as its receiver, so `this` inside the block is the collector. Every `emit(x)` inside the block is really `collector.emit(x)`: a direct call into the diner's code.

Let's use it like the real thing:

```kotlin
val dishes = toyFlow {
    for (id in 1..3) {
        println("  [producer] before emit($id)")
        emit(id)
        println("  [producer] after emit($id)")
    }
}
println("built the flow, nothing ran yet")
dishes.collect { v -> println("  [collector] got $v") }
dishes.collect { v -> println("  [collector] got $v") }   // the block runs again
```

```java
ToyFlow<Integer> dishes = collector -> {
    for (int id = 1; id <= 3; id++) {
        System.out.println("  [producer] before emit(" + id + ")");
        collector.emit(id);
        System.out.println("  [producer] after emit(" + id + ")");
    }
};
System.out.println("built the flow, nothing ran yet");
dishes.collect(v -> System.out.println("  [collector] got " + v));
dishes.collect(v -> System.out.println("  [collector] got " + v));   // the block runs again
```

Building prints nothing. The first `collect` runs the block, and each `before emit(n)` is followed by `got n` and only then by `after emit(n)`. That's the pattern the dinner printed. The second `collect` runs the whole block again from the top. That is all **cold** means: a flow is a function you haven't called yet, and `collect` calls it. Two diners get two dinners, each cooked from the top.

The Java twin has the same shape and prints the same lines. What differs is the cost of waiting. Java's `emit` is an ordinary call, so while the diner eats, the cook's thread sits inside `emit` and can do nothing else. Kotlin's `emit` is a suspend call. If the diner calls `delay` or waits for a slow answer, the coroutine pauses and the thread goes off to run other coroutines. The order of events is the same in both.

The order matches. But "a direct call" is still my claim, and the call stack can settle it."""

S3 = r"""A **call stack** is the chain of method calls a thread is in the middle of, newest on top, and any thread can print its own. Let's print it from inside the diner:

```kotlin
fun printStack(label: String) {
    println("$label, thread=${Thread.currentThread().name}")
    Thread.currentThread().stackTrace.drop(2)
        .takeWhile { !it.className.startsWith("kotlinx.coroutines.DispatchedTask") }
        .forEach { println("    at ${it.className}.${it.methodName}") }
}

toyFlow { emit("soup") }.collect { printStack("collector got $it") }
```

```java
static void printStack(String label) {
    System.out.println(label + ", thread=" + Thread.currentThread().getName());
    StackTraceElement[] frames = Thread.currentThread().getStackTrace();
    for (int i = 2; i < frames.length; i++)
        System.out.println("    at " + frames[i].getClassName() + "." + frames[i].getMethodName());
}

ToyFlow<String> dinner = collector -> collector.emit("soup");
dinner.collect(value -> printStack("collector got " + value));
```

For the toy flow it prints this. I trimmed the package names and the coroutine machinery at the bottom:

```text
collector got soup, thread=main
    at StackDemoKt$main$1$2.emit             <- your collector lambda: the diner
    at StackDemoKt$main$1$2.emit
    at StackDemoKt$main$1$1.invokeSuspend    <- the toyFlow { } block, calling emit
    at StackDemoKt$main$1$1.invoke
    at StackDemoKt$main$1$1.invoke
    at ToyFlowKt$toyFlow$1.collect           <- ToyFlow.collect, running the block
    at StackDemoKt$main$1.invokeSuspend      <- main, calling collect
```

Read it from the bottom. `main` called `collect`. `collect` ran the block. The block called `emit`, and `emit` is your lambda. It's all one thread, `main`. (Names such as `$main$1$2` are classes the Kotlin compiler makes for lambdas, and `invokeSuspend` is where a suspend lambda's body runs.)

The real `flow { }.map { }` gives a taller stack with the same shape. Here I also dropped repeated frames and two helper frames:

```text
collector got SOUP, thread=main
    at StackDemoKt$main$1$5.emit                                   <- your lambda
    at StackDemoKt$main$1$invokeSuspend$$inlined$map$1$2.emit      <- map's collector
    at kotlinx.coroutines.flow.internal.SafeCollector.emit         <- a checker
    at StackDemoKt$main$1$3.invokeSuspend                          <- your flow { } block
    at kotlinx.coroutines.flow.SafeFlow.collectSafely
    at kotlinx.coroutines.flow.AbstractFlow.collect
    at StackDemoKt$main$1$invokeSuspend$$inlined$map$1.collect     <- map's collect
    at StackDemoKt$main$1.invokeSuspend                            <- main
```

`map` is an **operator**, a function that takes a flow and returns a new one, here a flow that changes each value. It's also an inline function: the compiler copies its body into the calling code, so its collector shows up as a class in your own file. `SafeCollector` is a checker that `flow { }` puts in front of your collector. Lesson 2 of this track opens it up.

Here is the picture to keep. In the coroutines track the cook stood for a thread. Here she stands for the producer, and `emit` is her walk to the table: she carries one plate over and stands there while the diner eats. Only when the diner is done does she walk back and plate the next one. A `map` is a helper who stands between them, adds the sauce, carries the plate on and waits at the table too. In the stack, each of them is a box inside the one before.

The picture breaks at the waiting. A real cook standing at the table is lost to the kitchen. A suspended coroutine holds no thread: while your diner is inside `delay` or waiting for a slow answer, the thread runs other coroutines, and only this one dinner is held up.

**A plain flow is one call stack. The collector runs inside `emit`.**

So the call shape is real. Next, the three rules from Flow basics fall straight out of it."""

S4 = r"""The rules you learned about flows all follow from that stack.

A flow is cold because the block is the body of `collect`. No `collect`, no run. Two `collect` calls, two runs.

A flow is **sequential**, one value at a time, because `emit` can't return before the collector's code returns. The cook can't start the salad while the soup is still being eaten, and within one collection the diner never holds two plates at once. That's also why the KDoc of `FlowCollector` (KDoc is the documentation written in Kotlin source, like Javadoc) says `emit` "is not thread-safe and should not be invoked concurrently". `FlowCollector` is the library's version of our toy collector, and a plain call has nothing that would protect it from two callers at once.

A flow also gets backpressure for free. **Backpressure** means a slow consumer slows the producer down, so values don't pile up in memory. Reactive Streams, the standard behind the Reactor library from the reactive track, needs a whole protocol of requests for that. A flow needs nothing, because the cook is stuck inside `emit` until the diner is done.

Let's put numbers on it. The cook needs 100 ms per dish and the diner 300 ms to eat it. The demo runs under `runTest`, which uses **virtual time**: a fake clock from the coroutines test library, where `delay` moves the clock forward at once. So the numbers are exact and the run takes no real time. Both the toy and the real `flow { }` print:

```text
t= 100 emit 1
t= 400 eaten  1     <- emit(1) returns only now
t= 500 emit 2       <- 100 + 300 + 100
t= 800 eaten  2
t= 900 emit 3
t=1200 eaten  3     <- (100 + 300) x 3
```

The second `emit` happens at t=500, and it can't happen earlier: from 100 to 400 the cook was inside `emit(1)`, standing at the table. That's the warm-up question.

Free backpressure isn't fast backpressure. Three dishes took 1,200 ms, where the slower side alone needs only 900. A shelf between the kitchen and the table would let the cook work while the diner eats. Lesson 4 of this track adds one, called a buffer, and pays for it in memory.

**In a plain flow the times add up: each value costs the producer's time plus the collector's.**

Stopping early goes through the same call. A collector that wants no more values, like the one behind `take(2)`, has no handle on the cook's loop. All it can do is throw an exception. The exception flies back up through `emit`, the cook's loop ends, and her `finally` blocks run on the way out. The real `take` does exactly this with a special exception, which the next lesson takes apart. You'll write the toy version in the lab.

So the toy and the real thing behave alike, down to the millisecond. How close is the toy to the library's own interfaces?"""

S5 = r"""Very close. In kotlinx.coroutines 1.11.0, the coroutines library this course uses, the two interfaces are:

```kotlin
public interface Flow<out T> {
    public suspend fun collect(collector: FlowCollector<T>)
}

public fun interface FlowCollector<in T> {
    public suspend fun emit(value: T)
}
```

```java
// Java equivalent: java.util.concurrent.Flow, the JDK's Reactive Streams interfaces (abridged)
interface Publisher<T>  { void subscribe(Subscriber<? super T> subscriber); }
interface Subscription  { void request(long n); void cancel(); }
interface Subscriber<T> {
    void onSubscribe(Subscription subscription);
    void onNext(T item);
    void onError(Throwable throwable);
    void onComplete();
}
```

Only `FlowCollector` is a `fun interface`, an interface with one abstract method that a lambda can be turned into. That's how `flow.collect { v -> ... }` takes your lambda: Kotlin converts the lambda into a `FlowCollector`. `Flow` is a plain interface, so `Flow { ... }` doesn't compile ("interface ... does not have constructors"). That's on purpose. Its KDoc says `Flow` "is not stable for inheritance in 3rd party libraries", because new methods may be added to it later. Build flows with `flow { }`, or extend `AbstractFlow`, which is marked `@ExperimentalCoroutinesApi`.

Java's own `java.util.concurrent.Flow`, in the JDK since Java 9, works the other way round. The subscriber pulls: it calls `request(n)`, and the publisher may send at most `n` more items. Kotlin's flow needs no such call, because the cook can't get ahead of a call that hasn't returned yet.

Operators are flows built on flows. Here is `map` on the toy:

```kotlin
fun <T, R> ToyFlow<T>.map(transform: suspend (T) -> R): ToyFlow<R> =
    toyFlow { this@map.collect { value -> emit(transform(value)) } }
```

```java
// a default method in the Java ToyFlow interface
default <R> ToyFlow<R> map(Function<T, R> transform) {
    return downstream -> this.collect(value -> downstream.emit(transform.apply(value)));
}
```

Read it from the inside out. `map` returns a new flow. When that flow is collected, it collects the flow above it with a collector of its own, and that collector calls the next `emit` with the new value. It's a collector wrapped in a collector: the helper who takes each plate from the cook, adds the sauce and carries it on. `filter` is the same thing with an `if` around the `emit`, a helper who only passes on the plates that pass a check. The library writes both in nearly the same way, as the next lesson shows.

So a chain of five operators is five nested calls for each value. That's why the stack grew by one `emit` frame per `map`, and why operators need no locks or queues between them. This shape also names the parts of a chain. Everything above an operator, towards the cook, is its **upstream**. Everything below it, towards the diner, is its **downstream**.

The toy is honest, but it's also trusting. Nothing stops a toy flow from calling `emit` from another thread, or from carrying on after the diner sent a plate back. The real `flow { }` checks for both, and that's where we go next."""

CLOSING = """We started with a cook who carries each plate to the table and waits while the diner eats. A flow is that kitchen: two interfaces, a builder that only stores the recipe, and an `emit` that calls straight into the collector. Cold, one value at a time and backpressure all come from that one call, and so does the wait.

Now look in your own code for a timer or a log line wrapped around `emit`. It measures everything downstream, not the producer's own work.

Next, we'll meet the inspector that `flow { }` puts at the kitchen door. What does it check on every `emit`, and why does a try/catch around `emit` lose the rest of dinner?"""

L = {
 "id": "flow-01",
 "title": "A flow from scratch: two interfaces and a function call",
 "minutes": 35,
 "goal": "By the end you can build a working flow from two small interfaces, read a collector's call stack, and explain from that call shape why a flow is cold, runs one value at a time, and slows down to the speed of its collector.",
 "opening": OPENING,
 "warmup": {
  "q": "A flow cooks one dish every 100 ms and emits it. The collector, the diner, needs 300 ms to eat each dish. There is no buffer. When does the second `emit` happen?",
  "options": [
   "At t=200 ms: the cook keeps cooking while the diner eats",
   "At t=400 ms: right after the first dish is eaten",
   "At t=500 ms: the first dish is eaten at 400, then the cook needs 100 ms more",
   "At t=300 ms: the two sides overlap halfway"
  ],
  "answer": 2,
  "why": "`emit(1)` is called at 100 ms and doesn't return until the diner has finished, at 400 ms. Only then does the cook start the next dish, which takes another 100 ms. The answer t=200 assumes `emit` drops the value into a queue, which a plain flow never does. The section on the three rules works it out on a virtual clock."
 },
 "sections": [
  {
   "h": "Predict the order: a cook, a diner and three dishes",
   "body": S1,
   "try": {
    "title": "Predict, then serve dinner",
    "minutes": 3,
    "steps": [
     "Write your predicted order on paper. Then run `DinnerOrder.kt` with the command below.",
     "Move the `println(\"cook    $dish\")` line below `emit(dish)`. Predict the new order for one dish, then run it again.",
     "Run the Java twin, `DinnerOrderJava`, and compare the two outputs line by line."
    ],
    "code": tryit("DinnerOrder.kt", "DinnerOrderJava.java"),
    "expect": "Each dish prints `cook`, then `eat`, then `emit(...) returned`, and nothing from the flow's block prints before `flow built`. After your move, each dish prints `eat` before `cook`, because the whole diner ran inside `emit`. The Java twin prints the same pattern with `accept(...) returned`: a `Consumer` call behaves the same way."
   }
  },
  {
   "h": "A flow from scratch: two interfaces and a three-line builder",
   "body": S2,
   "try": {
    "title": "Build it and collect it twice",
    "minutes": 4,
    "steps": [
     "Open `ToyFlow.kt` in the demo folder. It holds the two interfaces, the builder, a toy `map` and a `main`. Predict how many `[producer] start` lines it prints.",
     "Run it. Check that `built the flow, nothing ran yet` comes before any producer line.",
     "Add a third collection at the end of `main`: `dishes.map { it + 1 }.map { it * 2 }.collect { println(it) }`. Predict the values and the number of `[producer] start` lines, then run it.",
     "Run the Java twin, `ToyFlowJava`."
    ],
    "code": tryit("ToyFlow.kt", "ToyFlowJava.java"),
    "expect": "Two `[producer] start` lines, one per `collect`, and none before the `built` line. The first collection prints `got 100`, `got 200` and `got 300` through the toy `map`. Your third collection starts the block a third time and prints 4, 6 and 8: each value goes through both maps inside one `emit` call before the producer makes the next. The Java twin prints the same lines as the original Kotlin program."
   }
  },
  {
   "h": "The diner runs inside emit: reading the stack",
   "body": S3,
   "figure": {"svg": FIG, "caption": "The collector's code runs inside emit, so the cook waits at the table until the diner is done, and only then plates the next dish."},
   "try": {
    "title": "Print the stack from inside collect",
    "minutes": 4,
    "steps": [
     "Run `StackDemo.kt`. In each stack, find the frame for your flow block and the frame where `main` called `collect`.",
     "In the second example, add `.map { it.lowercase() }` after the first `map`. Predict how many new `emit` frames appear between your lambda and `SafeCollector.emit`, then run it.",
     "Run `StackDemoJava`. Find the frame of the lambda that called `emit`."
    ],
    "code": tryit("StackDemo.kt", "StackDemoJava.java"),
    "expect": "Every frame is on thread `main`, and the diner's frames sit above the block that called `emit`. The second `map` adds exactly one `emit` frame (`$$inlined$map$2$2.emit`) above the first one, and one `collect` frame near the bottom: one more box in the nest, one more helper at the table. In the Java twin, the collector (`lambda$main$1`) sits right on top of the flow body (`lambda$main$0`), which sits on `main`."
   }
  },
  {
   "h": "Cold, one at a time, and slowed by the diner: three rules from one call",
   "body": S4,
   "try": {
    "title": "Time the cook in virtual time",
    "minutes": 3,
    "steps": [
     "Read `Backpressure.kt`. It runs the toy flow and the real `flow { }` under `runTest`, where `delay` moves a virtual clock. Predict the time of `emit 3`.",
     "Run it.",
     "Change the diner's `delay(300)` to `delay(50)` in both halves. Predict when `emit 2` happens and the total, then run it.",
     "Run `BackpressureJava`, the same model with `Thread.sleep` in real time."
    ],
    "code": tryit("Backpressure.kt", "BackpressureJava.java"),
    "expect": "`emit 3` at t=900 and a total of 1200 ms, the same for both flows. With a 50 ms diner, `emit 2` is at t=250 (100 + 50 + 100) and the total is 450 ms, three rounds of 150. The Java run shows the same pattern in real time, with every number a little late. On this busy machine the first `eaten` line came about 70 ms late and the total was 1277 ms, because real sleeps overshoot and a cold JVM is slow at its first prints."
   }
  },
  {
   "h": "The real Flow, and operators as collectors inside collectors",
   "body": S5
  }
 ],
 "compare": {
  "title": "The toy flow in Java and Kotlin",
  "java": {"title": "ToyFlowJava.java (abridged)", "src": """// Java equivalent: a hand-written push flow. emit blocks the thread while the collector works.
interface ToyCollector<T> {
    void emit(T value);
}

interface ToyFlow<T> {
    void collect(ToyCollector<T> collector);

    default <R> ToyFlow<R> map(Function<T, R> transform) {
        return downstream -> this.collect(value -> downstream.emit(transform.apply(value)));
    }
}

ToyFlow<Integer> dishes = collector -> {
    for (int id = 1; id <= 3; id++) collector.emit(id);
};
dishes.map(id -> id * 100).collect(v -> System.out.println("got " + v));"""},
  "kotlin": {"title": "ToyFlow.kt (abridged)", "src": """fun interface ToyCollector<in T> {
    suspend fun emit(value: T)
}

interface ToyFlow<out T> {
    suspend fun collect(collector: ToyCollector<T>)
}

fun <T> toyFlow(block: suspend ToyCollector<T>.() -> Unit): ToyFlow<T> =
    object : ToyFlow<T> {
        override suspend fun collect(collector: ToyCollector<T>) = collector.block()
    }

fun <T, R> ToyFlow<T>.map(transform: suspend (T) -> R): ToyFlow<R> =
    toyFlow { this@map.collect { value -> emit(transform(value)) } }

val dishes = toyFlow { for (id in 1..3) emit(id) }
dishes.map { it * 100 }.collect { v -> println("got $v") }"""},
  "note": "Both versions have the same two interfaces and the same `map`, and the calls happen in the same order. What differs is underneath. Java's `emit` blocks a thread while the collector works, so a thousand slow collections need a thousand threads. Kotlin's `emit` suspends a coroutine, and the thread is free during the wait. Java lets any interface with one abstract method take a lambda, so a lambda can be a `ToyFlow`. Kotlin asks for `fun interface`, and the real `Flow` leaves it out on purpose, which is why you build flows through `flow { }`. Kotlin also declares variance on the interfaces (`out T` on the flow, `in T` on the collector), where Java would write `? super T` at every use."
 },
 "worked": {
  "title": "Write a toy operator that times the downstream",
  "steps": [
   {
    "say": "The cook wants to know how long each dish takes, so she wraps a timer around `emit`. It says 300 ms per dish, and she starts looking for a faster stove. Before she buys one, write a toy operator that measures exactly what a timer around `emit` measures. It has the shape of `map`: collect the flow above, and wrap the call to the next `emit`.",
    "code": "fun <T> ToyFlow<T>.timeDownstream(record: (value: T, took: Duration) -> Unit): ToyFlow<T> =\n    toyFlow {\n        this@timeDownstream.collect { value ->\n            val mark = TimeSource.Monotonic.markNow()   // 1. start the clock\n            emit(value)                                 // 2. every operator below, and the collector\n            record(value, mark.elapsedNow())            // 3. stop it when the downstream returns\n        }\n    }",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// a default method in the Java ToyFlow interface\ndefault ToyFlow<T> timeDownstream(BiConsumer<T, Long> record) {\n    return downstream -> this.collect(value -> {\n        long start = System.nanoTime();                                 // 1. start the clock\n        downstream.emit(value);                                         // 2. everything below runs here\n        record.accept(value, (System.nanoTime() - start) / 1_000_000);  // 3. stop it, in ms\n    });\n}"
   },
   {
    "say": "Put it between a cook who needs 100 ms per dish and a diner who needs 300 ms to eat. In real time it prints about 300 ms for every dish. That's the diner's time. The cook's own 100 ms happens before `emit` and never shows up, so the stove was never the problem.",
    "code": "toyFlow { for (i in 1..3) { delay(100); emit(\"dish-$i\") } }      // the cook\n    .timeDownstream { dish, took -> println(\"$dish downstream took ${took.inWholeMilliseconds} ms\") }\n    .collect { delay(300) }                                       // the diner\n// dish-1 downstream took 300 ms (give or take a few, in real time)",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "ToyFlow<String> cook = collector -> {\n    for (int i = 1; i <= 3; i++) { sleep(100); collector.emit(\"dish-\" + i); }   // the cook\n};\ncook.timeDownstream((dish, ms) -> System.out.println(dish + \" downstream took \" + ms + \" ms\"))\n    .collect(dish -> sleep(300));                                              // the diner"
   },
   {
    "say": "Where you put it decides what it measures. Each operator in a plain flow sees, inside its `emit`, the time of everything below it. So moving the timer down the chain takes operators out of the number.",
    "code": "cook.map { plate(it) }.timeDownstream(log).collect { diner.eat(it) }   // the diner only\ncook.timeDownstream(log).map { plate(it) }.collect { diner.eat(it) }   // plating plus the diner",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "cook.map(d -> plate(d)).timeDownstream(log).collect(diner::eat);   // the diner only\ncook.timeDownstream(log).map(d -> plate(d)).collect(diner::eat);   // plating plus the diner"
   },
   {
    "say": "The library's `onEach` has the same shape with your action in front of `emit`. In its source it is `transform { value -> action(value); return@transform emit(value) }`. On the toy it is one line:",
    "code": "fun <T> ToyFlow<T>.onEach(action: suspend (T) -> Unit): ToyFlow<T> =\n    toyFlow { this@onEach.collect { value -> action(value); emit(value) } }",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "default ToyFlow<T> onEach(Consumer<T> action) {\n    return downstream -> this.collect(value -> { action.accept(value); downstream.emit(value); });\n}"
   }
  ]
 },
 "lab": {
  "title": "Build the toy flow and make take stop the producer",
  "minutes": 12,
  "files": ["labs/flows/src/main/kotlin/workbench/flows/l01/ToyFlow.kt"],
  "run": "./gradlew :flows:test --tests 'workbench.flows.l01.*'",
  "steps": [
   "Run the tests once. All eight fail with `NotImplementedError`. Read the test names in `ToyFlowTest`: they are the spec.",
   "Write `toyFlow` and `toList`. Three tests turn green: running the block again, the event order, and the slow collector in virtual time.",
   "Write `map` and `filter` as collectors wrapped in collectors. Don't collect into a list first. The event-order test checks that each value goes all the way down before the producer makes the next one.",
   "Write `take`. Check `count` with `require` before you build the flow. Inside, make a fresh `Any()` as your marker, emit each value, and after the `count`-th one throw `ToyAbortException(marker)`. Catch it around the upstream `collect`, and rethrow it if `e.owner !== marker`.",
   "Run the tests until all eight pass, then run them once more."
  ],
  "hints": [
   "`take` can't `return` from the producer's loop, because that loop is someone else's code. Throwing from the collector is the only way out. The exception travels back through the producer's `emit`, which is why the producer's `finally` runs.",
   "Compare markers with `!==`, which tests identity. Two `Any()` objects are never the same object, and that is the point of the marker: it's the name signed on the note.",
   "If the nested-take test fails and your result has an extra 99 in it, your `take` catches every `ToyAbortException`. The inner `take(3)` swallowed the outer `take(1)`'s abort, so the outer block carried on and emitted 99.",
   "Put `require(count > 0)` before `return toyFlow { ... }`, so a bad count fails when the flow is built, as it does for the library's `take`."
  ],
  "done_when": "All eight tests in `ToyFlowTest` pass."
 },
 "drill": {
  "title": "Write the two interfaces from memory",
  "minutes": 5,
  "prompt": "Close this page. In a blank file, write `ToyCollector`, `ToyFlow`, the `toyFlow` builder and `map`, with no imports from `kotlinx.coroutines.flow`. Then write two lines that prove the flow is cold. Check the variance: which interface gets `out T`, and which gets `in T`?",
  "answer": {
   "lang": "kotlin",
   "src": "fun interface ToyCollector<in T> {          // it only takes values in\n    suspend fun emit(value: T)\n}\n\ninterface ToyFlow<out T> {                  // it only hands values out\n    suspend fun collect(collector: ToyCollector<T>)\n}\n\nfun <T> toyFlow(block: suspend ToyCollector<T>.() -> Unit): ToyFlow<T> =\n    object : ToyFlow<T> {\n        override suspend fun collect(collector: ToyCollector<T>) = collector.block()\n    }\n\nfun <T, R> ToyFlow<T>.map(transform: suspend (T) -> R): ToyFlow<R> =\n    toyFlow { this@map.collect { value -> emit(transform(value)) } }\n\n// cold: building prints nothing, each collect prints \"run\" again\nval f = toyFlow { println(\"run\"); emit(1) }\nrunBlocking { f.collect { }; f.collect { } }   // run, run",
   "alt": {
    "lang": "java",
    "src": "// Java equivalent: the same shape with plain methods (no variance on the declarations)\ninterface ToyCollector<T> {\n    void emit(T value);\n}\n\ninterface ToyFlow<T> {\n    void collect(ToyCollector<T> collector);\n\n    default <R> ToyFlow<R> map(Function<T, R> transform) {\n        return downstream -> this.collect(value -> downstream.emit(transform.apply(value)));\n    }\n}\n\n// cold: building prints nothing, each collect prints \"run\" again\nToyFlow<Integer> f = c -> { System.out.println(\"run\"); c.emit(1); };\nf.collect(v -> { });\nf.collect(v -> { });   // run, run"
   }
  }
 },
 "recap": [
  "A flow is two interfaces with one suspend function each: `Flow.collect(collector)` and `FlowCollector.emit(value)`.",
  "`flow { }` only stores your block, like a recipe card. `collect` runs it, from the top, once per call. That is what cold means.",
  "`emit` is a direct call into the collector. The collector's code runs inside `emit`, on the same stack and the same thread: the cook stands at the table while the diner eats.",
  "So a plain flow handles one value at a time, and a slow collector slows the producer. With 100 ms and 300 ms per item, the second `emit` is at t=500.",
  "Operators like `map` and `filter` are collectors wrapped in collectors. A collector stops the producer by throwing back up through `emit`, so the producer's `finally` runs.",
  "The limit: the times add up (1,200 ms where the slower side alone needs 900), and the toy checks nothing at all. Lesson 2 shows the checks in `flow { }`; lesson 4 adds a shelf so the cook can work ahead."
 ],
 "closing": CLOSING,
 "quiz": [
  {
   "q": "`toyFlow { println(\"A\"); emit(1); println(\"B\") }.collect { println(\"C\") }` prints what?",
   "options": ["A B C", "A C B", "C A B", "Nothing, because the flow is never started"],
   "answer": 1,
   "why": "`emit(1)` is a call into the collector, so `C` prints inside it, before `emit` returns and `B` prints. A B C is the queue model, where `emit` leaves the value for later. `collect` does start the flow, so something prints."
  },
  {
   "q": "A flow cooks a dish in 50 ms and the diner needs 200 ms to eat each one. There is no buffer. How long do 4 dishes take?",
   "options": ["200 ms", "850 ms", "1,000 ms", "800 ms"],
   "answer": 2,
   "why": "Each dish costs 50 + 200 = 250 ms, because the cook waits inside `emit` while the diner eats, so 4 dishes take 1,000 ms. 850 ms (50 + 4 x 200) is what you'd get if the cook could work ahead onto a shelf, a buffer. A plain flow can't."
  },
  {
   "q": "Which line compiles with kotlinx.coroutines 1.11.0?",
   "options": [
    "`val f: Flow<Int> = Flow { it.emit(1) }`",
    "`val c: FlowCollector<Int> = FlowCollector { println(it) }`",
    "Both of them",
    "Neither of them"
   ],
   "answer": 1,
   "why": "Only `FlowCollector` is a `fun interface`, so a lambda converts to it. `Flow` is a plain interface and not stable for inheritance, and `Flow { }` fails with \"does not have constructors\". Build flows with `flow { }`."
  },
  {
   "q": "A cook wraps `emit(dish)` in a timer, and the timer says 300 ms per dish. Making a dish takes 2 ms. Where did the rest of the time go?",
   "options": [
    "The first dishes are always slow while the JVM warms up",
    "A hidden buffer that `flow { }` fills and drains",
    "Thread switches between the cook's thread and the diner's",
    "The downstream: every operator below and the collector run inside that `emit` call"
   ],
   "answer": 3,
   "why": "In a plain flow, `emit` returns only when everything below it has finished with the value, so the timer measures the downstream. There is no hidden buffer and no second thread to switch to: the stack shows one thread, `main`, all the way down."
  },
  {
   "q": "Lesson 7 of the coroutines track said that `emit` inside `withContext(Dispatchers.IO)` throws \"Flow invariant is violated\". With this lesson's model, what would go wrong if it were allowed?",
   "options": [
    "The collector's code would run on an IO thread it never asked for, because it runs inside `emit`",
    "The values would reach the collector out of order",
    "The flow body would run twice",
    "Nothing: the rule is only there for speed"
   ],
   "answer": 0,
   "why": "Wherever `emit` runs, the collector runs, because it is a nested call. A raw `Flow` written by hand skips the check, and its collector printed a `DefaultDispatcher-worker` thread name. Lesson 3 of this track shows how `flowOn` moves the producer without dragging the collector along.",
   "from": "co-07"
  }
 ],
 "flashcards": [
  {"front": "What are Kotlin Flow's two interfaces, and what does each declare?", "back": "`Flow<out T>` with `suspend fun collect(collector: FlowCollector<T>)`, and `FlowCollector<in T>` with `suspend fun emit(value: T)`."},
  {"front": "In kotlinx.coroutines 1.11.0, which one is a `fun interface`: `Flow` or `FlowCollector`?", "back": "Only `FlowCollector`. So `FlowCollector { }` compiles and `Flow { }` doesn't."},
  {"front": "In a plain flow, where does the collector's lambda run?", "back": "Inside `emit`, on the producer's stack and thread, as a nested call. `emit` returns when the lambda returns."},
  {"front": "Producer 100 ms per item, collector 300 ms, no buffer. When is the second `emit`?", "back": "At t=500 ms: 100 to make item 1, 300 inside `emit(1)`, then 100 to make item 2."},
  {"front": "What runs when you call `flow { ... }` (or the toy `toyFlow { ... }`)?", "back": "Nothing. It stores the block in an object. Each `collect` runs the block from the top."},
  {"front": "How does `take(2)` stop a producer that is looping in someone else's code?", "back": "It throws from its collector. The exception flies back up through the producer's `emit`, ends the loop, runs the producer's `finally`, and `take` catches it."},
  {"front": "What does a timer around `emit(x)` measure?", "back": "The downstream: every operator below and the collector, for that value."}
 ],
 "terms": [
  {"term": "Collector", "plain": "The receiving end of a flow: an object with one suspend function, `emit(value)`. In the kitchen, the diner."},
  {"term": "Emit", "plain": "Hand one value to the collector. In a plain flow it is a direct call that returns when the collector is done."},
  {"term": "Cold flow", "plain": "A flow whose block runs only when it is collected, from the top, once per `collect` call."},
  {"term": "Backpressure", "plain": "A slow consumer slowing the producer down, so values don't pile up in memory."},
  {"term": "Upstream and downstream", "plain": "The part of a chain above an operator (towards the producer) and the part below it (towards the collector)."},
  {"term": "fun interface", "plain": "A Kotlin interface with one abstract method, which a lambda can be converted to."},
  {"term": "Virtual time", "plain": "A fake clock in kotlinx-coroutines-test. `delay` moves it at once, so timings are exact and tests finish fast."}
 ],
 "explain_back": {
  "prompt": "A friend says: \"My flow cooks in the background and keeps the dishes on a shelf until the diner catches up.\" Explain, from the call shape, what really happens in a plain flow.",
  "answer": "A plain flow has no background work and no shelf. `flow { }` only stores the cook's code, and `collect` runs it in the collector's own coroutine. Each `emit(dish)` is a direct call into the collector's code, so the diner eats while the cook is still inside `emit`. Only when the collector returns does `emit` return, and only then does the cook make the next dish. So the cook is never more than one dish ahead, it all runs on the same thread, and a slow diner slows the cook down. If we want the cook to work ahead, we have to ask for it with an operator such as `buffer` or `flowOn`, and those add a second coroutine and a channel between the two sides."
 },
 "deeper": {
  "minutes": 10,
  "body": "A few details help when you read real stack traces and real code.\n\nLine numbers in inlined frames can mislead. `map` is `inline`, so its collector's code is copied into your file, and the frame's file and line point into the library source it came from. They can even point past the end of that file. In one run, map's frame pointed at `Emitters.kt:217`. Trust the class name (`$$inlined$map$1$2`) more than the line.\n\n`flow.collect { }` calls the member function `Flow.collect`, with your lambda converted into a `FlowCollector`. Older versions had an inline extension `collect(action)`. It is still in 1.11.0, but marked `@Deprecated(level = DeprecationLevel.HIDDEN)` for JS and Native compatibility, so your code never calls it. In a stack trace your lambda appears as a generated class's `emit` method.\n\nYou can implement `Flow` yourself with `object : Flow<T>`. It compiles, and it behaves like the toy, with no checks at all. That's the reason not to. A hand-written `Flow` can call `emit` from another thread, or keep emitting after the collector failed, and nothing stops it. The next lesson shows the checks `flow { }` runs on every `emit`, and what goes wrong without them.\n\n`java.util.concurrent.Flow` (JDK 9 and later) is the JDK's copy of the Reactive Streams interfaces. Its contract has rules a Kotlin flow gets from the call shape: a publisher must not send more items than were requested, and it must not call `onNext` from two threads at once. In a plain Kotlin flow the first rule is replaced by `emit` not returning, and the second holds because there is only one call at a time."
 },
 "sources": [
  {"title": "Flow (kotlinx.coroutines API, 1.11.0)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-flow/"},
  {"title": "FlowCollector (kotlinx.coroutines API, 1.11.0)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-flow-collector/"},
  {"title": "Flow.kt at tag 1.11.0 (kotlinx.coroutines source)", "url": "https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/Flow.kt"},
  {"title": "Asynchronous Flow (Kotlin docs)", "url": "https://kotlinlang.org/docs/coroutines-flow.html"},
  {"title": "java.util.concurrent.Flow (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Flow.html"}
 ]
}

out = ROOT / "content/lessons/flow-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
