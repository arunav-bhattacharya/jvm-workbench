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
    'collect runs the flow block, the block calls emit, emit runs map\'s collector, and that runs your lambda. '
    'A timeline on the right shows the producer waiting inside emit while a 300 ms collector works: emit 1 is called at 100 ms '
    'and returns at 400 ms, emit 2 is called at 500 ms.">'
    '<text class="t-s t-m" x="215" y="24" text-anchor="middle">One thread, one stack. Each box is a call still running.</text>'
    '<rect class="box" x="10" y="38" width="410" height="284" rx="8"/>'
    '<text class="t-s" x="215" y="58" text-anchor="middle">main calls collect { }</text>'
    '<rect class="box" x="30" y="72" width="370" height="242" rx="8"/>'
    '<text class="t-s" x="215" y="92" text-anchor="middle">the flow { } block runs: the cook</text>'
    '<rect class="box-b" x="50" y="106" width="330" height="200" rx="8"/>'
    '<text class="t-s t-b" x="215" y="126" text-anchor="middle">emit(pay-1): the cook walks to the table</text>'
    '<rect class="box" x="70" y="140" width="290" height="158" rx="8"/>'
    '<text class="t-s" x="215" y="160" text-anchor="middle">map\'s collector: the waiter</text>'
    '<rect class="box-a" x="90" y="174" width="250" height="116" rx="8"/>'
    '<text class="t-s" x="215" y="198" text-anchor="middle">your collect { } lambda: the diner</text>'
    '<text class="t-s t-code" x="215" y="222" text-anchor="middle">ledger.post(pay-1)</text>'
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

S1 = """Here is a settlement-file reader feeding a ledger writer through a flow. Before you read on, write down the order of the lines it prints.

```kotlin
val records = flow {
    for (line in lines) {                    // "pay-1,4250,EUR", "pay-2,990,EUR", "pay-3,12000,GBP"
        val id = line.substringBefore(",")
        println("read    $id")
        emit(id)
        println("emit($id) returned")
    }
}
println("flow built")
records.collect { id -> println("posted  $id") }
println("collect returned")
```

```java
// Java equivalent: Java has no Flow, so this is a hand-written push "flow".
// The reader calls the ledger writer's Consumer once per line.
static void readSettlementFile(List<String> lines, Consumer<String> ledgerWriter) {
    for (String line : lines) {
        String id = line.substring(0, line.indexOf(','));
        System.out.println("read    " + id);
        ledgerWriter.accept(id);
        System.out.println("accept(" + id + ") returned");
    }
}

readSettlementFile(lines, id -> System.out.println("posted  " + id));
```

Two guesses are tempting. One says all three `read` lines come first and then the three `posted` lines, as if `emit` dropped the value into a queue for later. The other gets the pairs right but prints `emit(pay-1) returned` before `posted pay-1`, as if `emit` handed the value over and moved on. Here is the real output:

```text
flow built
read    pay-1
posted  pay-1
emit(pay-1) returned
read    pay-2
posted  pay-2
emit(pay-2) returned
read    pay-3
posted  pay-3
emit(pay-3) returned
collect returned
```

`flow built` comes first, so building the flow ran none of its body. And `posted pay-1` comes before `emit(pay-1) returned`: the ledger writer's code ran while `emit` was still running. There is no queue here and no second thread.

Lesson 7 of the coroutines track gave you three rules about flows. They are cold, they run one value at a time, and a slow collector slows the producer. All three come from a single fact: `emit` is a plain function call into the collector. About ten lines of code are enough to prove it. The Java version prints the same order for the same reason. `accept` is a method call, and the line after a call runs when the call returns."""

S2 = """A flow needs a receiving end and a sending end. Each is a single suspend function.

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

The builder is the whole trick. `toyFlow { ... }` stores your block in an object and returns it. Nothing runs. When someone calls `collect(collector)`, the object runs your block with that collector as the receiver. So every `emit(x)` inside the block is really `collector.emit(x)`: a direct call into the collector's code.

Use it like the real thing:

```kotlin
val payments = toyFlow {
    for (id in 1..3) {
        println("  [producer] before emit($id)")
        emit(id)
        println("  [producer] after emit($id)")
    }
}
println("built the flow, nothing ran yet")
payments.collect { v -> println("  [collector] got $v") }
payments.collect { v -> println("  [collector] got $v") }   // the body runs again
```

```java
ToyFlow<Integer> payments = collector -> {
    for (int id = 1; id <= 3; id++) {
        System.out.println("  [producer] before emit(" + id + ")");
        collector.emit(id);
        System.out.println("  [producer] after emit(" + id + ")");
    }
};
System.out.println("built the flow, nothing ran yet");
payments.collect(v -> System.out.println("  [collector] got " + v));
payments.collect(v -> System.out.println("  [collector] got " + v));   // the body runs again
```

Building prints nothing. The first `collect` runs the body, and each `before emit(n)` is followed by `got n` and only then by `after emit(n)`. That's the same pattern the settlement reader printed. The second `collect` runs the whole body again from the top. That is all **cold** means: a flow is a function you haven't called yet, and `collect` calls it.

The Java twin has the same shape and prints the same lines. What differs is the cost of waiting. Java's `emit` is an ordinary call, so while the collector works, the producer's thread sits inside `emit` and can do nothing else. Kotlin's `emit` is a suspend call. If the collector calls `delay` or waits on a socket, the coroutine suspends and the thread goes off to run other coroutines. The order of events is the same in both."""

S3 = """You can see the call shape for yourself. Print the stack from inside the collector:

```kotlin
fun printStack(label: String) {
    println("$label, thread=${Thread.currentThread().name}")
    Thread.currentThread().stackTrace.drop(2)
        .takeWhile { !it.className.startsWith("kotlinx.coroutines.DispatchedTask") }
        .forEach { println("    at ${it.className}.${it.methodName}") }
}

toyFlow { emit("pay-1") }.collect { printStack("collector got $it") }
```

```java
static void printStack(String label) {
    System.out.println(label + ", thread=" + Thread.currentThread().getName());
    StackTraceElement[] frames = Thread.currentThread().getStackTrace();
    for (int i = 2; i < frames.length; i++)
        System.out.println("    at " + frames[i].getClassName() + "." + frames[i].getMethodName());
}

ToyFlow<String> payments = collector -> collector.emit("pay-1");
payments.collect(value -> printStack("collector got " + value));
```

For the toy flow it prints this, newest call on top (I trimmed the package names):

```text
collector got pay-1, thread=main
    at StackDemoKt$main$1$2.emit             <- your collector lambda
    at StackDemoKt$main$1$2.emit
    at StackDemoKt$main$1$1.invokeSuspend    <- the toyFlow { } block, calling emit
    at StackDemoKt$main$1$1.invoke
    at StackDemoKt$main$1$1.invoke
    at ToyFlowKt$toyFlow$1.collect           <- ToyFlow.collect, running the block
    at StackDemoKt$main$1.invokeSuspend      <- main, calling collect
```

Read it from the bottom. `main` called `collect`. `collect` ran the block. The block called `emit`, and `emit` is your lambda. It is all one thread. The real `flow { }.map { }` gives a taller stack with the same shape (here I also dropped repeated frames and two helper frames):

```text
collector got PAY-1, thread=main
    at StackDemoKt$main$1$5.emit                                   <- your lambda
    at StackDemoKt$main$1$invokeSuspend$$inlined$map$1$2.emit      <- map's collector
    at kotlinx.coroutines.flow.internal.SafeCollector.emit         <- a checker
    at StackDemoKt$main$1$3.invokeSuspend                          <- your flow { } block
    at kotlinx.coroutines.flow.SafeFlow.collectSafely
    at kotlinx.coroutines.flow.AbstractFlow.collect
    at StackDemoKt$main$1$invokeSuspend$$inlined$map$1.collect     <- map's collect
    at StackDemoKt$main$1.invokeSuspend                            <- main
```

`map` is an inline function, so its collector is compiled into your own file. `SafeCollector` is a checker that `flow { }` puts in front of your collector. Lesson 2 of this track opens it up.

Here is the picture to keep. A plain flow is a small restaurant with one cook and no counter. The cook plates a dish (`emit`), walks it to the table, and stands there while the diner eats (your collector). Only when the diner is done does the cook walk back and plate the next one. A `map` is a waiter between them, and the waiter stands at the table too. In the stack, each of them is a box inside the one before."""

S4 = """The rules you learned about flows all follow from that stack.

A flow is **cold** because the block is the body of `collect`. No `collect`, no run. Two `collect` calls, two runs.

A flow is sequential because `emit` cannot return before the collector's code returns. The producer can't start on the second value while the first one is still being posted, and inside one collection the collector never runs twice at once. That is also why the KDoc of `FlowCollector` says `emit` "is not thread-safe and should not be invoked concurrently". A plain call has nothing that would protect the collector from two callers at the same time.

A flow also gets backpressure for free. Backpressure means a slow consumer slows the producer down, so values don't pile up in memory. Reactive Streams needs a protocol for that. A flow needs nothing, because the producer is stuck inside `emit` until the consumer is done. Take a reader that needs 100 ms per settlement line and a ledger writer that needs 300 ms per posting. In virtual time, which is exact, both the toy and the real `flow { }` print:

```text
t= 100 emit 1
t= 400 posted 1     <- emit(1) returns only now
t= 500 emit 2       <- 100 + 300 + 100
t= 800 posted 2
t= 900 emit 3
t=1200 posted 3     <- (100 + 300) x 3
```

The second `emit` happens at t=500, and it can't happen earlier: from 100 to 400 the producer was inside `emit(1)`. In the restaurant, that's the cook standing at the table. Free backpressure has a price, and this is it: 1200 ms for three items, where the slower side alone needs only 900. Lesson 4 of this track adds a buffer to win some of that back, and pays for it in memory.

Stopping early goes through the same call. A collector that wants no more values, like the one behind `take(2)`, has no handle on the producer's loop. All it can do is throw. The exception flies back up through `emit`, the producer's loop ends, and its `finally` blocks run on the way out. The real `take` does this with an internal exception, which the next lesson takes apart. You'll write the toy version in the lab."""

S5 = """The library's two interfaces have the toy's shape. In kotlinx.coroutines 1.11.0 they are:

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

Only `FlowCollector` is a `fun interface`. That is how `flow.collect { v -> ... }` takes your lambda: Kotlin converts the lambda into a `FlowCollector`. `Flow` is a plain interface, so `Flow { ... }` does not compile ("interface ... does not have constructors"). That's on purpose. Its KDoc says `Flow` "is not stable for inheritance in 3rd party libraries", because new methods may be added to it later. Build flows with `flow { }`, or extend `AbstractFlow`, which is marked `@ExperimentalCoroutinesApi`.

Java's own `java.util.concurrent.Flow` works the other way round. The subscriber pulls: it calls `request(n)`, and the publisher may send at most `n` more items. Kotlin's flow needs no such call, because the producer can't get ahead of a function call that hasn't returned yet.

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

Read it from the inside out. `map` returns a new flow. When that flow is collected, it collects the flow above it with a collector of its own, and that collector calls the next `emit` with the new value. It is a collector wrapped in a collector. `filter` is the same thing with an `if` around the `emit`. The library writes both in nearly the same way, as the next lesson shows. So a chain of five operators is five nested calls for each value. That's why the stack grew by one `emit` frame per `map`, and why operators need no locks or queues between them."""

L = {
 "id": "flow-01",
 "title": "A flow from scratch: two interfaces and a function call",
 "minutes": 35,
 "goal": "By the end you can build a working flow from two small interfaces, read a collector's call stack, and explain from that call shape why a flow is cold, runs one value at a time, and slows down to the speed of its collector.",
 "warmup": {
  "q": "A flow reads a settlement line every 100 ms and emits it. The collector needs 300 ms to post each line to the ledger. There is no buffer. When does the second `emit` happen?",
  "options": [
   "At t=200 ms: the producer keeps reading while the collector works",
   "At t=400 ms: right after the first posting finishes",
   "At t=500 ms: the first posting finishes at 400, then the producer needs 100 ms more",
   "At t=300 ms: the two sides overlap halfway"
  ],
  "answer": 2,
  "why": "`emit(1)` is called at 100 ms and does not return until the collector has posted the line at 400 ms. Only then does the producer read the next line, which takes another 100 ms. The answer t=200 assumes `emit` drops the value into a queue, which a plain flow never does."
 },
 "sections": [
  {
   "h": "A reader and a ledger writer: predict the print order",
   "body": S1,
   "try": {
    "title": "Predict, then run the reader",
    "minutes": 3,
    "steps": [
     "Write your predicted order on paper. Then run `SettlementOrder.kt` with the command below.",
     "Move the `println(\"read    $id\")` line below `emit(id)`. Predict the new order for one record, then run it again.",
     "Run the Java twin, `SettlementOrderJava`, and compare the two outputs line by line."
    ],
    "code": tryit("SettlementOrder.kt", "SettlementOrderJava.java"),
    "expect": "Each record prints `read`, then `posted`, then `emit(...) returned`, and nothing from the flow's body prints before `flow built`. After your move, each record prints `posted` before `read`, because the whole collector ran inside `emit`. The Java twin prints the same pattern with `accept(...) returned`: a Consumer call behaves the same way."
   }
  },
  {
   "h": "Two interfaces and a three-line builder",
   "body": S2,
   "try": {
    "title": "Build it and collect it twice",
    "minutes": 4,
    "steps": [
     "Open `ToyFlow.kt` in the demo folder. It holds the two interfaces, the builder, a toy `map` and a `main`. Predict how many `[producer] start` lines it prints.",
     "Run it. Check that `built the flow, nothing ran yet` comes before any producer line.",
     "Add a third collection at the end of `main`: `payments.map { it + 1 }.map { it * 2 }.collect { println(it) }`. Predict the values and the number of `[producer] start` lines, then run it.",
     "Run the Java twin, `ToyFlowJava`."
    ],
    "code": tryit("ToyFlow.kt", "ToyFlowJava.java"),
    "expect": "Two `[producer] start` lines, one per `collect`, and none before the `built` line. The first collection prints `got 100`, `got 200` and `got 300` through the toy `map`. Your third collection starts the body a third time and prints 4, 6 and 8: each value goes through both maps inside one `emit` call before the producer reads the next. The Java twin prints the same lines as the original Kotlin program."
   },
   "refs": [
    {"title": "Flow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-flow/", "kind": "docs"}
   ]
  },
  {
   "h": "The collector runs inside emit: read the stack",
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
    "expect": "Every frame is on thread `main`, and the collector's frames sit above the block that called `emit`. The second `map` adds exactly one `emit` frame (`$$inlined$map$2$2.emit`) above the first one, and one `collect` frame near the bottom: one more box in the nest. In the Java twin, the collector (`lambda$main$1`) sits right on top of the flow body (`lambda$main$0`), which sits on `main`."
   }
  },
  {
   "h": "Cold, sequential and slowed by its collector, all from one call",
   "body": S4,
   "try": {
    "title": "Time the cook in virtual time",
    "minutes": 3,
    "steps": [
     "Read `Backpressure.kt`. It runs the toy flow and the real `flow { }` under `runTest`, where `delay` moves a virtual clock. Predict the time of `emit 3`.",
     "Run it.",
     "Change the collector's `delay(300)` to `delay(50)` in both halves. Predict when `emit 2` happens and the total, then run it.",
     "Run `BackpressureJava`, the same model with `Thread.sleep` in real time."
    ],
    "code": tryit("Backpressure.kt", "BackpressureJava.java"),
    "expect": "`emit 3` at t=900 and a total of 1200 ms, the same for both flows. With a 50 ms collector, `emit 2` is at t=250 (100 + 50 + 100) and the total is 450 ms, three rounds of 150. The Java run shows the same pattern in real time. Every number is a little later than the model, by a few milliseconds up to a few dozen on the first lines, because real sleeps overshoot and a cold JVM is slow at its first prints."
   },
   "refs": [
    {"title": "Asynchronous Flow (Kotlin docs)", "url": "https://kotlinlang.org/docs/coroutines-flow.html", "kind": "read"}
   ]
  },
  {
   "h": "The real Flow, and operators as collectors inside collectors",
   "body": S5,
   "refs": [
    {"title": "FlowCollector (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-flow-collector/", "kind": "docs"},
    {"title": "java.util.concurrent.Flow (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/Flow.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A plain flow is a restaurant with one cook and no counter. The recipe card (the flow) does nothing by itself. A meal is cooked only when a diner sits down and calls `collect`, and every new diner gets a fresh cooking session from the top. The cook plates a dish, walks it to the table and waits there while the diner eats, so the kitchen can never get ahead of the dining room. A waiter (an operator such as `map`) can stand between them, but he too walks each plate over and waits. The analogy breaks at the waiting. A real cook standing at a table is lost to the kitchen. A suspended coroutine holds no thread: while your collector is inside `delay` or a database call, the thread goes off and runs other coroutines, and only this one collection is stuck.",
 "in_your_world": "Picture a Kafka consumer wrapped in `flow { }`: it polls a batch, emits each payment event, and the collector writes ledger entries to Oracle. Each `emit` returns only after the ledger write, so the consumer never polls the next batch while the current one is half posted. If Oracle slows down, the whole flow slows with it, and you see that as growing consumer lag, not as memory filling up with events nobody has written. Two things follow. A long stall in the collector is also a long gap between polls, so keep the consumer's `max.poll.interval.ms` in mind. And a metric around `emit` in the consumer measures the ledger, not Kafka.",
 "mistake": "The most common mistake is reading a timer around `emit` as the producer's own time. A settlement reader records `read_ms` around `emit(record)`, the dashboard shows 300 ms per line, and someone spends a day tuning the CSV parser. The 300 ms belongs to the ledger writer: everything downstream runs inside that `emit`. People make this mistake because `emit` looks like `queue.put`. Time the work you own, and keep `emit` outside the timer:\n\n```kotlin\nval start = System.nanoTime()\nval record = parse(line)                             // only the reader's work\nmetrics.record(\"read_ns\", System.nanoTime() - start)\nemit(record)                                         // the downstream's time, not ours\n```\n\n```java\nlong start = System.nanoTime();\nRecord record = parse(line);                         // only the reader's work\nmetrics.record(\"read_ns\", System.nanoTime() - start);\ncollector.emit(record);                              // the downstream's time, not ours\n```",
 "compare": {
  "title": "The toy flow in Java and Kotlin",
  "java": {
   "title": "ToyFlowJava.java (abridged)",
   "src": "// Java equivalent: a hand-written push flow. emit blocks the thread while the collector works.\ninterface ToyCollector<T> {\n    void emit(T value);\n}\n\ninterface ToyFlow<T> {\n    void collect(ToyCollector<T> collector);\n\n    default <R> ToyFlow<R> map(Function<T, R> transform) {\n        return downstream -> this.collect(value -> downstream.emit(transform.apply(value)));\n    }\n}\n\nToyFlow<Integer> payments = collector -> {\n    for (int id = 1; id <= 3; id++) collector.emit(id);\n};\npayments.map(id -> id * 100).collect(v -> System.out.println(\"got \" + v));"
  },
  "kotlin": {
   "title": "ToyFlow.kt (abridged)",
   "src": "fun interface ToyCollector<in T> {\n    suspend fun emit(value: T)\n}\n\ninterface ToyFlow<out T> {\n    suspend fun collect(collector: ToyCollector<T>)\n}\n\nfun <T> toyFlow(block: suspend ToyCollector<T>.() -> Unit): ToyFlow<T> =\n    object : ToyFlow<T> {\n        override suspend fun collect(collector: ToyCollector<T>) = collector.block()\n    }\n\nfun <T, R> ToyFlow<T>.map(transform: suspend (T) -> R): ToyFlow<R> =\n    toyFlow { this@map.collect { value -> emit(transform(value)) } }\n\nval payments = toyFlow { for (id in 1..3) emit(id) }\npayments.map { it * 100 }.collect { v -> println(\"got $v\") }"
  },
  "note": "The shapes match line for line, and the calls happen in the same order. What differs is underneath. Java's `emit` blocks a thread while the collector works, so a thousand slow collections need a thousand threads. Kotlin's `emit` suspends a coroutine, and the thread is free during the wait. Java lets any interface with one abstract method take a lambda, so a lambda can be a `ToyFlow`. Kotlin asks for `fun interface`, and the real `Flow` leaves it out on purpose, which is why you build flows through `flow { }`. Kotlin also declares variance on the interfaces (`out T` on the flow, `in T` on the collector), where Java would write `? super T` at every use."
 },
 "worked": {
  "title": "Write a toy operator that times the downstream",
  "steps": [
   {
    "say": "The settlement dashboard says each line takes 300 ms to read. Before you tune the parser, write a toy operator that measures exactly what a timer around `emit` measures. It has the shape of `map`: collect the flow above, and wrap the call to the next `emit`.",
    "code": "fun <T> ToyFlow<T>.timeDownstream(record: (value: T, took: Duration) -> Unit): ToyFlow<T> =\n    toyFlow {\n        this@timeDownstream.collect { value ->\n            val mark = TimeSource.Monotonic.markNow()   // 1. start the clock\n            emit(value)                                 // 2. every operator below, and the collector\n            record(value, mark.elapsedNow())            // 3. stop it when the downstream returns\n        }\n    }",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// a default method in the Java ToyFlow interface\ndefault ToyFlow<T> timeDownstream(BiConsumer<T, Long> record) {\n    return downstream -> this.collect(value -> {\n        long start = System.nanoTime();                                 // 1. start the clock\n        downstream.emit(value);                                         // 2. everything below runs here\n        record.accept(value, (System.nanoTime() - start) / 1_000_000);  // 3. stop it, in ms\n    });\n}"
   },
   {
    "say": "Put it between a reader that needs 100 ms per line and a ledger writer that needs 300 ms per posting. In a real-time run it printed 300, 302 and 300 ms. That's the ledger's time. The reader's own 100 ms happens before `emit` and never shows up.",
    "code": "toyFlow { for (i in 1..3) { delay(100); emit(\"pay-$i\") } }       // the reader\n    .timeDownstream { id, took -> println(\"$id downstream took ${took.inWholeMilliseconds} ms\") }\n    .collect { delay(300) }                                      // the ledger writer\n// pay-1 downstream took 300 ms\n// pay-2 downstream took 302 ms\n// pay-3 downstream took 300 ms",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "ToyFlow<String> reader = collector -> {\n    for (int i = 1; i <= 3; i++) { sleep(100); collector.emit(\"pay-\" + i); }   // the reader\n};\nreader.timeDownstream((id, ms) -> System.out.println(id + \" downstream took \" + ms + \" ms\"))\n    .collect(id -> sleep(300));                                               // the ledger writer"
   },
   {
    "say": "Where you put it decides what it measures. Each operator in a plain flow sees, inside its `emit`, the time of everything below it. So moving the timer down the chain takes operators out of the number.",
    "code": "reader.map { parse(it) }.timeDownstream(log).collect { ledger.post(it) }   // the ledger only\nreader.timeDownstream(log).map { parse(it) }.collect { ledger.post(it) }   // parse plus the ledger",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "reader.map(r -> parse(r)).timeDownstream(log).collect(ledger::post);   // the ledger only\nreader.timeDownstream(log).map(r -> parse(r)).collect(ledger::post);   // parse plus the ledger"
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
  "files": [f"{LAB}/main/{P}/ToyFlow.kt"],
  "run": "./gradlew :flows:test --tests 'workbench.flows.l01.*'",
  "steps": [
   "Run the tests once. All eight fail with `NotImplementedError`. Read the test names in `ToyFlowTest`: they are the spec.",
   "Write `toyFlow` and `toList`. Three tests turn green: running the body again, the event order, and the slow collector in virtual time.",
   "Write `map` and `filter` as collectors wrapped in collectors. Don't collect into a list first. The event-order test checks that each value goes all the way down before the producer reads the next one.",
   "Write `take`. Check `count` with `require` before you build the flow. Inside, make a fresh `Any()` as your marker, emit each value, and after the `count`-th one throw `ToyAbortException(marker)`. Catch it around the upstream `collect`, and rethrow it if `e.owner !== marker`.",
   "Run the tests until all eight pass, then run them once more."
  ],
  "hints": [
   "`take` can't `return` from the producer's loop, because that loop is someone else's code. Throwing from the collector is the only way out. The exception travels back through the producer's `emit`, which is why the producer's `finally` runs.",
   "Compare markers with `!==`, which tests identity. Two `Any()` objects are never the same object, and that is the point of the marker.",
   "If the nested-take test fails and your result has an extra 99 in it, your `take` catches every `ToyAbortException`. The inner `take(3)` swallowed the outer `take(1)`'s abort, so the outer body carried on and emitted 99.",
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
  "`flow { }` only stores your block. `collect` runs it, from the top, once per call. That is what cold means.",
  "`emit` is a direct call into the collector. The collector's code runs inside `emit`, on the same stack and the same thread.",
  "So a plain flow handles one value at a time, and a slow collector slows the producer: with 100 ms and 300 ms per item, the second `emit` is at t=500.",
  "Operators like `map` and `filter` are collectors wrapped in collectors. A collector stops the producer by throwing back up through `emit`, so the producer's `finally` runs.",
  "Only `FlowCollector` is a `fun interface`. Build flows with `flow { }`, because `Flow` is not stable for inheritance."
 ],
 "quiz": [
  {
   "q": "`toyFlow { println(\"A\"); emit(1); println(\"B\") }.collect { println(\"C\") }` prints what?",
   "options": ["A B C", "A C B", "C A B", "Nothing, because the flow is never started"],
   "answer": 1,
   "why": "`emit(1)` is a call into the collector, so `C` prints inside it, before `emit` returns and `B` prints. A B C is the queue model, where `emit` leaves the value for later. `collect` does start the flow, so something prints."
  },
  {
   "q": "A flow fetches a ledger page in 50 ms and the collector needs 200 ms per page. There is no buffer. How long do 4 pages take?",
   "options": ["200 ms", "850 ms", "1,000 ms", "800 ms"],
   "answer": 2,
   "why": "Each page costs 50 + 200 = 250 ms, because the producer waits inside `emit` while the collector works, so 4 pages take 1,000 ms. 850 ms (50 + 4 x 200) is what you'd get if the producer could fetch ahead into a buffer. A plain flow can't."
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
   "q": "A settlement reader wraps `emit(record)` in a timer, and the metric says 300 ms per line. Parsing a line takes 2 ms. Where did the rest of the time go?",
   "options": [
    "The JIT hasn't warmed up the parser yet",
    "A hidden buffer that `flow { }` fills and drains",
    "Thread switches between the reader's thread and the collector's",
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
  {"term": "Collector", "plain": "The receiving end of a flow: an object with one suspend function, `emit(value)`."},
  {"term": "Emit", "plain": "Hand one value to the collector. In a plain flow it is a direct call that returns when the collector is done."},
  {"term": "Cold flow", "plain": "A flow whose block runs only when it is collected, from the top, once per `collect` call."},
  {"term": "Backpressure", "plain": "A slow consumer slowing the producer down, so values don't pile up in memory."},
  {"term": "Upstream and downstream", "plain": "The part of a chain above an operator (towards the source) and the part below it (towards the collector)."},
  {"term": "fun interface", "plain": "A Kotlin interface with one abstract method, which a lambda can be converted to."},
  {"term": "Virtual time", "plain": "A fake clock in kotlinx-coroutines-test. `delay` moves it at once, so timings are exact and tests finish fast."}
 ],
 "explain_back": {
  "prompt": "A colleague says: \"Our settlement reader is a flow, so it reads the file in the background and keeps lines in a buffer until the ledger writer catches up.\" Explain, from the call shape, what really happens.",
  "answer": "There's no background work and no buffer in a plain flow. `flow { }` only stores the reader's code, and `collect` runs it in the collector's own coroutine. Each `emit(line)` is a direct call into the ledger writer's code, so the writer posts the line while the reader is still inside `emit`. Only when the posting returns does `emit` return, and only then does the reader read the next line. So the reader is never more than one line ahead, it runs on the same thread, and a slow ledger slows the reader down. If we want the reader to run ahead, we have to ask for it with an operator such as `buffer` or `flowOn`, and those add a second coroutine and a channel."
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
