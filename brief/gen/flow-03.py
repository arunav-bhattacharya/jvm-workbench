import json, pathlib

ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/flows/src"
P = "kotlin/workbench/flows/l03"
J = "java/workbench/flows/l03"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{LAB}/demo/{P}/{name}"
jdemo = lambda name: f"{LAB}/demo/{J}/{name}"
run = lambda cls: f"./gradlew :flows:demo -Pmain=workbench.flows.l03.{cls}"


def tryit(kt, java):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(demo(kt)), "run": run(k + "Kt"), "file": demo(kt),
            "alt": {"lang": "java", "title": java, "src": read(jdemo(java)), "run": run(j), "file": jdemo(java)}}


FIG = (
    '<svg viewBox="0 0 700 320" role="img" aria-label="Two rooms with a wall between them and a mailbox set in the wall. '
    'Behind the wall, on the io thread, a second coroutine runs the flow block and map and drops values into a 64-slot mailbox. '
    'In front, on the collector\'s thread, a drain loop takes values out and hands them to the collector, which posts them. '
    'Notes below: two flowOn calls make two walls and three rooms, adjacent flowOn calls fuse, flowOn with only a CoroutineName '
    'builds no wall, and withContext around emit sets off the alarm.">'
    '<text class="t-s t-m" x="350" y="22" text-anchor="middle">flowOn(io) builds a wall with a mailbox slot</text>'
    '<rect class="box-b" x="10" y="36" width="320" height="200" rx="8"/>'
    '<text class="t-s t-b" x="170" y="58" text-anchor="middle">behind the wall: io-thread</text>'
    '<rect class="box" x="40" y="76" width="140" height="40" rx="8"/>'
    '<text class="t t-code" x="110" y="101" text-anchor="middle">flow { }</text>'
    '<line class="ln" x1="110" y1="116" x2="110" y2="134" marker-end="url(#arr)"/>'
    '<rect class="box" x="40" y="136" width="140" height="40" rx="8"/>'
    '<text class="t t-code" x="110" y="161" text-anchor="middle">map { parse }</text>'
    '<text class="t-s t-m" x="170" y="212" text-anchor="middle">a second coroutine: the second cook</text>'
    '<line class="ln" x1="180" y1="156" x2="314" y2="146" marker-end="url(#arr)"/>'
    '<text class="t-s" x="246" y="138" text-anchor="middle">send</text>'
    '<rect class="box" x="370" y="36" width="320" height="200" rx="8"/>'
    '<text class="t-s t-b" x="530" y="58" text-anchor="middle">in front: the collector\'s thread</text>'
    '<line class="ln" x1="350" y1="36" x2="350" y2="110"/>'
    '<line class="ln" x1="350" y1="190" x2="350" y2="236"/>'
    '<rect class="box-a" x="318" y="110" width="64" height="80" rx="8"/>'
    '<text class="t" x="350" y="146" text-anchor="middle">64</text>'
    '<text class="t-s" x="350" y="166" text-anchor="middle">slots</text>'
    '<line class="ln" x1="382" y1="146" x2="426" y2="110" marker-end="url(#arr)"/>'
    '<rect class="box" x="430" y="76" width="200" height="40" rx="8"/>'
    '<text class="t-s t-code" x="530" y="101" text-anchor="middle">emitAll: the drain loop</text>'
    '<line class="ln" x1="530" y1="116" x2="530" y2="134" marker-end="url(#arr)"/>'
    '<rect class="box-a" x="430" y="136" width="200" height="40" rx="8"/>'
    '<text class="t-s t-code" x="530" y="161" text-anchor="middle">onEach { post } + collect</text>'
    '<text class="t-s t-m" x="530" y="212" text-anchor="middle">the collector never moves</text>'
    '<text class="t-s" x="350" y="262" text-anchor="middle">Two flowOn calls: two walls, three rooms. Adjacent ones fuse into one wall.</text>'
    '<text class="t-s" x="350" y="284" text-anchor="middle">flowOn(CoroutineName) only repaints the sign: same dispatcher, no wall.</text>'
    '<text class="t-s t-bad" x="350" y="306" text-anchor="middle">withContext around emit pushes a plate through the wall by hand: alarm.</text>'
    '</svg>'
)

S1 = """Take lesson 1's settlement reader and its ledger writer, and add one line: `.flowOn(io)`, where `io` is a dispatcher with one thread named `io-thread`. The ledger write takes 30 ms. Predict the order of the six lines.

```kotlin
settlementIds()                      // prints "read <id> on <thread>", then emits the id
    .flowOn(io)
    .collect { id ->
        delay(30)                    // the ledger write
        println("posted  $id   on ${Thread.currentThread().name}")
    }
```

```java
// Java equivalent: a reader thread puts lines into a 64-slot BlockingQueue,
// and the main thread takes them out and posts them
BlockingQueue<String> mailbox = new ArrayBlockingQueue<>(64);
new Thread(() -> { for (String id : ids) put(mailbox, id); put(mailbox, END); }, "io-thread").start();
for (String id = mailbox.take(); !id.equals(END); id = mailbox.take()) {
    Thread.sleep(30);                // the ledger write
    System.out.println("posted  " + id + "   on " + Thread.currentThread().getName());
}
```

Without `flowOn` you get lesson 1's pattern: read, posted, read, posted, all on `main`. With it:

```text
read    pay-1   on io-thread
read    pay-2   on io-thread
read    pay-3   on io-thread
posted  pay-1   on main
posted  pay-2   on main
posted  pay-3   on main
```

The reader ran ahead. It read all three lines before the first posting finished, so its `emit` calls returned without waiting for the ledger. In lesson 1, `emit` couldn't return before the collector did. Something now sits between the two sides and holds values, and the two sides run on different threads. The Java twin prints the same six lines, and it shows what that something is: a queue.

Why not just wrap the read and the `emit` in `withContext(io)`? Lesson 2 showed what `flow { }` says to that: "Flow invariant is violated". It also showed why. A hand-written raw `Flow` without the check ran its collector on `DefaultDispatcher-worker-1`. The collector runs inside `emit`, so an `emit` on an IO thread drags the collector onto that thread too. If your ledger client isn't thread-safe, or holds a connection checked out for this request, that's a real bug. To move the reader and leave the collector alone, you have to break the call chain between them. That takes a second coroutine and a place to keep values in between."""

S2 = """You can build `flowOn` yourself from two coroutine tools you met in lesson 9 of the coroutines track: `produce` and a channel.

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)                     // produce is experimental in 1.11.0
fun <T> Flow<T>.myFlowOn(dispatcher: CoroutineDispatcher): Flow<T> = flow {
    coroutineScope {
        val mailbox = produce(dispatcher, capacity = 64) {    // the second cook, behind the wall
            this@myFlowOn.collect { send(it) }                 // the upstream's emit now means send
        }
        for (value in mailbox) emit(value)                     // we stay in the collector's coroutine
    }
}
```

```java
// Java equivalent: an executor for the upstream and a 64-slot queue in between
static <T> void flowOn(ExecutorService executor, Consumer<Consumer<T>> upstream, Consumer<T> downstream)
        throws InterruptedException {
    BlockingQueue<Object> mailbox = new ArrayBlockingQueue<>(64);
    executor.execute(() -> {
        upstream.accept(value -> put(mailbox, value));   // the upstream's emit now means put
        put(mailbox, END);
    });
    for (Object v = mailbox.take(); v != END; v = mailbox.take()) downstream.accept((T) v);
}
```

Read it as a picture: a wall across the kitchen with a mailbox slot in it. Behind the wall, a second cook (the `produce` coroutine) runs on `io` and drops each plate into the mailbox. In front, the original diner takes plates out. Your `emit` calls now happen in the collector's own coroutine, so the inspector from lesson 2 has nothing to complain about. Nothing ever pushes a plate through the wall by hand.

The real `flowOn` does the same, with one shortcut. `flowOn(ctx)` returns a `ChannelFlowOperatorImpl`. When it is collected, it compares contexts. If the dispatcher is the same as the collector's, it runs the upstream inline with the new context and builds no channel. If the dispatcher differs, it runs `coroutineScope { collector.emitAll(produceImpl(this)) }`. That `produce` collects the upstream into a `SendingCollector`, whose `emit` is `channel.send(value)`. The channel's default capacity is `Channel.BUFFERED`, which is 64.

Two measurements show it. First, a probe that holds the first value in the collector and counts how many `emit` calls return meanwhile. A plain flow gives 0. Both `myFlowOn(io)` and `flowOn(io)` give 65: 64 in the mailbox and one in the diner's hands. Then the 66th `send` suspends, because the mailbox is full. So `flowOn` doesn't remove backpressure. It moves it from "wait for the collector" to "wait for a free slot", and a slow ledger still slows the reader down, 64 lines later. Second, the collector's stack after `flowOn(io)`:

```text
    at HandMadeFlowOnKt$main$1$9.emit                                     <- your collector
    at kotlinx.coroutines.flow.FlowKt__ChannelsKt.emitAllImpl$FlowKt__ChannelsKt   <- the drain loop
    at kotlinx.coroutines.flow.FlowKt__ChannelsKt$emitAllImpl$1.invokeSuspend
    at kotlin.coroutines.jvm.internal.BaseContinuationImpl.resumeWith
```

Your `flow { }` block is gone from it. It runs on another thread, in another coroutine, and only the drain loop, `emitAllImpl`, calls your collector."""

S3 = """`flowOn` changes the context of the operators above it, up to the previous `flowOn`, and nothing below it. With two of them you get two walls and three rooms:

```kotlin
flow { for (i in 1..2) { log("emit", i); emit(i) } }
    .map { log("map1", it); it }
    .flowOn(io)                                // wall 1: everything above runs on io
    .map { log("map2", it); it }
    .flowOn(cpu)                               // wall 2: map2 runs on cpu
    .collect { log("collect", it) }            // the collector's room: main
```

```java
// Java equivalent with Reactor: subscribeOn moves the source, publishOn moves what follows,
// and toStream() hands values back to the calling thread through a queue
Flux.range(1, 2)
    .doOnNext(i -> log("emit", i))
    .map(i -> { log("map1", i); return i; })
    .subscribeOn(io)
    .publishOn(cpu)
    .map(i -> { log("map2", i); return i; })
    .toStream()
    .forEach(i -> log("collect", i));
```

With coroutine debug mode on, the thread names count the coroutines for you:

```text
  emit     1   thread=io-thread @coroutine#3
  map1     1   thread=io-thread @coroutine#3
  emit     2   thread=io-thread @coroutine#3
  map1     2   thread=io-thread @coroutine#3
  map2     1   thread=cpu-thread @coroutine#2
  collect  1   thread=main @coroutine#1
  map2     2   thread=cpu-thread @coroutine#2
  collect  2   thread=main @coroutine#1
```

Three coroutines, so two channels. The order of lines across threads can change from run to run, but each stage always stays in its room. Notice the direction. Reactor's `publishOn` moves what comes after it. Kotlin's `flowOn` moves what comes before it. If you think in Reactor, read `flowOn` from the bottom up.

Three variants are worth knowing, because they surprise people. Two `flowOn` calls with nothing between them fuse into one wall, and the first one, nearest the source, wins: The `toString()` of `flowOf(1, 2, 3).flowOn(Dispatchers.IO).flowOn(Dispatchers.Default)` ends with `ChannelFlowOperatorImpl[context=Dispatchers.IO]`. (That string is a debug aid, not an API.) A `map` between them stops the fusion. Next, `flowOn(CoroutineName("renamed"))` keeps the dispatcher, so it builds no wall. The lines interleave on `main` like a plain flow, and the upstream's lines show `main @renamed#1`: the collector's coroutine number with a new name on it. Last, a `Job` in `flowOn` is refused as soon as you build the operator, with "Flow context cannot contain job in it."

`flowOn` never moves the collector. If the collecting side blocks, wrap the terminal call in `withContext(io) { flow.collect { ... } }`, as lesson 7 of the coroutines track showed."""

S4 = """Now fan in two acquirer feeds, north and east, into one flow. The obvious code is `flow { }` with a child coroutine per feed:

```kotlin
flow {
    coroutineScope {
        launch { north.collect { emit(it) } }
        launch { east.collect { emit(it) } }
    }
}
```

```java
// Java equivalent: two threads calling one consumer. Nothing stops them calling it at the same time.
Thread.ofVirtual().start(() -> north.forEach(collector::accept));
Thread.ofVirtual().start(() -> east.forEach(collector::accept));
```

It fails on the first value with an exact, helpful message:

```text
Flow invariant is violated:
		Emission from another coroutine is detected.
		Child of StandaloneCoroutine{Active}@5a8e6209, expected child of BlockingCoroutine{Active}@4b4523f8.
		FlowCollector is not thread-safe and concurrent emissions are prohibited.
		To mitigate this restriction please use 'channelFlow' builder instead of 'flow'
```

This is the second half of the context check from lesson 2. Two launched children could call `emit` at the same moment, and the collector would run twice at once. So the inspector refuses any `emit` from a `launch`ed child.

`channelFlow { }` is the builder for this. It is a channel flow like the one `flowOn` builds, with a 64-slot mailbox (`Channel.BUFFERED`). Its block runs with a `ProducerScope`, which is both a `CoroutineScope` you can `launch` in and a `SendChannel` you can `send` to. Its KDoc says the scope "can be used concurrently from different contexts". Several cooks, one mailbox:

```kotlin
fun bothAcquirers(north: Flow<Auth>, east: Flow<Auth>): Flow<Auth> = channelFlow {
    launch { north.collect { send(it) } }
    launch { east.collect { send(it) } }
}
```

```java
// Java equivalent: Flux.create gives a sink that several threads may call; you complete it yourself
Flux<Auth> both = Flux.create(sink -> {
    Thread n = Thread.ofVirtual().start(() -> north.forEach(sink::next));
    Thread e = Thread.ofVirtual().start(() -> east.forEach(sink::next));
    Thread.ofVirtual().start(() -> { join(n); join(e); sink.complete(); });
});
```

In a run with real threads, the builder block returned at t=17 ms, the four sends arrived from `DefaultDispatcher-worker-1`, every `collect` line printed on `main`, and the flow completed only at t=113 ms, after both children. The block may return early, and the flow still waits for every child. That is structured concurrency at work: the children belong to the producer coroutine's scope, and its channel closes only when that scope is done, so the collector's loop ends after the last `send`.

`produceIn(scope)` is the mailbox without the flow around it. It launches a coroutine in your scope that collects the flow, and returns the `ReceiveChannel` at once. The collecting starts at the caller's next suspension, whether or not anyone receives. It is hot: in the demo the upstream started and emitted 1 before anyone called `receive`. Consume it fully or `cancel()` it, because the scope waits for that producer coroutine like any other child."""

L = {
 "id": "flow-03",
 "title": "Context and threads: flowOn, the invariant, and channelFlow",
 "minutes": 35,
 "goal": "By the end you can explain why emit may not change context, say exactly what flowOn builds and which part of a chain it moves, predict the threads of a chain with several flowOn calls, and fan in several producers with channelFlow.",
 "warmup": {
  "q": "A settlement reader emits three ids instantly, and the collector needs 30 ms to post each one. You add `.flowOn(io)` before `collect`. What is the order of the read and posted lines now?",
  "options": [
   "read 1, posted 1, read 2, posted 2, read 3, posted 3, the same as without flowOn",
   "read 1, read 2, read 3, then posted 1, posted 2, posted 3",
   "posted 1, posted 2, posted 3, then the reads",
   "The flow throws \"Flow invariant is violated\""
  ],
  "answer": 1,
  "why": "With a different dispatcher, `flowOn` runs the reader in a second coroutine and puts a 64-slot channel between the two sides. The reader's `emit` now only drops the id into the channel, so it reads all three lines before the first 30 ms posting is done. The invariant error is for `withContext` around `emit`, not for `flowOn`."
 },
 "sections": [
  {
   "h": "Add flowOn and the print order changes",
   "body": S1,
   "try": {
    "title": "Watch the reader run ahead",
    "minutes": 3,
    "steps": [
     "Read `FlowOnOrder.kt`. It runs the reader twice, without and with `.flowOn(io)`. Write down both orders before you run it.",
     "Run it.",
     "Replace `.flowOn(io)` with `.flowOn(CoroutineName(\"reader\"))` (import `kotlinx.coroutines.CoroutineName`). Predict the order and the threads, then run it.",
     "Run the Java twin, `FlowOnOrderJava`."
    ],
    "code": tryit("FlowOnOrder.kt", "FlowOnOrderJava.java"),
    "expect": "Without `flowOn`, read and posted alternate on `main`. With it, the three reads come first on `io-thread`, then the three postings on `main`. With `flowOn(CoroutineName(\"reader\"))` the order goes back to read, posted, read, posted, all on `main`: the dispatcher didn't change, so there is no second coroutine and no channel. Section 3 comes back to this. The Java twin with a BlockingQueue prints the same six lines as the Kotlin version with 30 ms."
   }
  },
  {
   "h": "What flowOn builds: a wall with a mailbox slot",
   "body": S2,
   "figure": {"svg": FIG, "caption": "flowOn(io) is a wall with a mailbox slot: a second coroutine cooks behind it on io, and the collector's side drains the mailbox without ever moving."},
   "try": {
    "title": "Build flowOn by hand and compare",
    "minutes": 5,
    "steps": [
     "Read `HandMadeFlowOn.kt`. Predict the three numbers that `ahead` prints, for the plain flow, `myFlowOn(io)` and `flowOn(io)`.",
     "Run it. Then find your `flow { }` block in the printed stack. Is it there?",
     "Change `capacity = 64` in `myFlowOn` to `capacity = 10`. Predict its `ahead` number, then run it.",
     "Run `HandMadeFlowOnJava` and compare its stack with the Kotlin one."
    ],
    "code": tryit("HandMadeFlowOn.kt", "HandMadeFlowOnJava.java"),
    "expect": "The plain flow gives 0, and both `myFlowOn(io)` and `flowOn(io)` give 65: 64 in the channel plus the one the collector holds. Every version still receives all 200. The stack shows your collector called from `emitAllImpl`, and the flow block is not on it. With `capacity = 10` your version gives 11. The Java consumer's stack has the drain loop (`flowOn`) and `main`, and none of the reader's frames."
   },
   "refs": [
    {"title": "flowOn (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow-on.html", "kind": "docs"}
   ]
  },
  {
   "h": "Several flowOn calls: rooms and walls",
   "body": S3,
   "try": {
    "title": "Count the rooms",
    "minutes": 4,
    "steps": [
     "Read `FlowOnThreads.kt`. For the first chain, predict the thread of each stage and how many coroutines the debug names will show.",
     "Run it. Check the fused `toString()` and the `CoroutineName` part: which thread and which coroutine number does the upstream use there?",
     "Swap the first chain's two `flowOn` lines (cpu first, then io). Predict the new rooms, then run it.",
     "Run `FlowOnThreadsJava`, the Reactor version."
    ],
    "code": tryit("FlowOnThreads.kt", "FlowOnThreadsJava.java"),
    "expect": "`emit` and `map1` run on `io-thread @coroutine#3`, `map2` on `cpu-thread @coroutine#2` and `collect` on `main @coroutine#1`: three coroutines and two channels. The fused flow prints `ChannelFlowOperatorImpl[context=Dispatchers.IO]`. With `CoroutineName`, emit and collect alternate on `main`, and the upstream shows `@renamed#1`. After the swap, `emit` and `map1` run on `cpu-thread` and `map2` on `io-thread`. The Reactor version puts `emit` and `map1` on `io-thread`, `map2` on `cpu-thread` and `collect` on `main`, using `publishOn` for the second wall."
   }
  },
  {
   "h": "channelFlow: several cooks, one mailbox",
   "body": S4,
   "try": {
    "title": "Fan in two feeds",
    "minutes": 4,
    "steps": [
     "Run `ChannelFlowDemo.kt`. Read the error from the `flow { }` version first.",
     "In the `channelFlow` part, check three things: the thread of the `sent` lines, the thread of the `collect` lines, and when the flow completes compared with the builder block.",
     "In the `produceIn` part, delete `mailbox.cancel()`. Predict what happens, then run it and stop it with Ctrl+C if it hangs.",
     "Run `ChannelFlowDemoJava`."
    ],
    "code": tryit("ChannelFlowDemo.kt", "ChannelFlowDemoJava.java"),
    "expect": "The `flow { }` version fails with \"Emission from another coroutine is detected\" and the hint to use `channelFlow`. In the `channelFlow` part the sends come from a `DefaultDispatcher-worker` thread, every `collect` line is on `main`, and the flow completes only after both children, well after the builder block returned. `produceIn` emits 1 before anyone receives. Without `cancel()` the program never ends: the producer waits forever on a full one-slot buffer, and the scope waits for it. The Java twin's subscriber runs on the producer threads, because a Reactor sink has no mailbox."
   },
   "refs": [
    {"title": "channelFlow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/channel-flow.html", "kind": "docs"},
    {"title": "produceIn (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/produce-in.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "Picture the kitchen from lesson 1 with a wall built across it. `flowOn(io)` hires a second cook for the room behind the wall, on the IO shift, and sets a mailbox with 64 slots into the wall. The second cook drops plates into the mailbox and goes straight back to cooking; the diner in front takes them out one at a time. Two `flowOn` calls build two walls and three rooms. Two `flowOn` calls side by side build one wall, labelled with the first sign that was hung. `flowOn(CoroutineName(...))` only repaints the sign on the same room, so there is no wall and no mailbox. `channelFlow` is several cooks in different rooms sharing one mailbox. And `withContext` around `emit` is a cook trying to push a plate through the wall by hand, which sets off the alarm. The picture breaks at the mailbox. A real mailbox is passive, but this one has a lock and a waiting line: when all 64 slots are full, the cook behind the wall is suspended until the diner takes one out, and when the diner stops collecting, the whole back room is cancelled.",
 "in_your_world": "Plenty of acquirer SDKs are still blocking: a reader for a settlement file on SFTP, a SOAP client, a JDBC call. In a Quarkus service, put `flowOn(io)` right under the blocking part, and keep the posting to the Oracle ledger in the collector. The ledger client is often tied to the caller, through a connection checked out from a pool of 20 for this job or a client that isn't thread-safe, and the collector is the only side that never moves. Fan-in is the other common case. When two acquirers report authorizations on separate feeds, `channelFlow` with one child per feed gives the risk engine a single stream. Remember that the children share one scope. If the north feed throws, the east feed is cancelled too and the whole flow fails, which is right for a reconciliation job and wrong for a live dashboard that should keep showing east.",
 "mistake": "The most common mistake, especially for people who know Reactor, is putting `flowOn` at the end of a chain and expecting it to apply to everything, or to what comes after it. It applies only to the operators above it. Here the ledger postings, which must stay in the caller's context, end up on `io` too:\n\n```kotlin\nreadLines(reader)\n    .map { parseSettlement(it) }\n    .onEach { ledger.post(it) }     // above flowOn, so this runs on io as well\n    .flowOn(io)\n    .collect()\n```\n\n```java\n// Java equivalent with Reactor: subscribeOn moves the source, and with no publishOn the postings run on io too\nreadLines(reader)\n    .map(Settlement::parse)\n    .doOnNext(ledger::post)          // runs on the io scheduler too\n    .subscribeOn(io)\n    .blockLast();\n```\n\nPeople do it because Reactor's `publishOn` works on what follows it, and because \"put the threading at the end\" looks tidy. Read `flowOn` from the bottom up instead, and put it directly below the last line that must move: `.map { parseSettlement(it) }.flowOn(io).onEach { ledger.post(it) }`.",
 "compare": {
  "title": "flowOn by hand: a channel in Kotlin, a BlockingQueue in Java",
  "java": {
   "title": "HandMadeFlowOnJava.java (abridged)",
   "src": "// Java equivalent: an executor runs the upstream, a 64-slot queue sits in between\nstatic <T> void flowOn(ExecutorService executor, Consumer<Consumer<T>> upstream, Consumer<T> downstream)\n        throws InterruptedException {\n    BlockingQueue<Object> mailbox = new ArrayBlockingQueue<>(64);\n    executor.execute(() -> {\n        upstream.accept(value -> put(mailbox, value));   // blocks a thread when full\n        put(mailbox, END);                              // a queue can't be closed: send a marker\n    });\n    for (Object v = mailbox.take(); v != END; v = mailbox.take()) downstream.accept((T) v);\n}"
  },
  "kotlin": {
   "title": "HandMadeFlowOn.kt (abridged)",
   "src": "@OptIn(ExperimentalCoroutinesApi::class)\nfun <T> Flow<T>.myFlowOn(dispatcher: CoroutineDispatcher): Flow<T> = flow {\n    coroutineScope {\n        val mailbox = produce(dispatcher, capacity = 64) {\n            this@myFlowOn.collect { send(it) }        // suspends when full\n        }                                              // closes the channel when the block ends\n        for (value in mailbox) emit(value)\n    }\n}"
  },
  "note": "The shape is the same: a second worker, a 64-slot buffer, and a drain loop on the caller's side. Three things differ, and all of them matter in production. A full `BlockingQueue` blocks a thread, while a full channel suspends a coroutine. A queue can't be closed, so the Java version needs an end marker, while `produce` closes its channel when its block ends. And the Kotlin version stops cleanly: if the collector fails or stops early, `coroutineScope` cancels the `produce` coroutine. In the Java version the reader thread keeps running, blocked on a full queue, until someone interrupts it."
 },
 "worked": {
  "title": "Make the settlement import testable in virtual time",
  "steps": [
   {
    "say": "The acquirer's file server allows one line per second, so the reader waits before each read. The first version hard-codes the dispatcher. A test with `runTest` looks fine but is slow, and its clock says nothing happened. In a run with three lines, `TestTime.kt` printed `virtual=0 ms, wall=3180 ms`: `Dispatchers.Default` lives outside the test scheduler, so its `delay` calls are real.",
    "code": "fun slowFeed() = flow { repeat(3) { delay(1_000); emit(it) } }   // one line per second\n\nrunTest {\n    slowFeed().flowOn(Dispatchers.Default).toList()   // virtual=0 ms, wall=3180 ms\n}",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// Java equivalent: a hard-coded executor makes the test wait in real time too\nExecutorService io = Executors.newFixedThreadPool(4);\nList<Integer> lines = CompletableFuture.supplyAsync(() -> readThreeLinesSlowly(), io).join();   // 3 s of real waiting"
   },
   {
    "say": "Inject the dispatcher instead. Production passes `Dispatchers.IO`, a test passes something else. Give it a default so callers don't have to care.",
    "code": "fun importSettlements(\n    reader: LineReader,\n    ledger: Ledger,\n    io: CoroutineDispatcher = Dispatchers.IO,        // 1. injected, with the production default\n): Flow<Settlement> =\n    flow { while (true) emit(reader.readLine() ?: break) }\n        .map { parseSettlement(it) }\n        .flowOn(io)                                  // 2. the wall uses whatever was passed in\n        .onEach { ledger.post(it) }",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// Java equivalent: take the Executor as a constructor argument\nfinal class SettlementImport {\n    private final Executor io;                        // 1. injected\n    SettlementImport(Executor io) { this.io = io; }\n\n    CompletableFuture<List<Settlement>> readAll(LineReader reader) {\n        return CompletableFuture.supplyAsync(() -> parseAll(reader), io);   // 2. used here\n    }\n}"
   },
   {
    "say": "For timing tests, pass a test dispatcher that shares the test's scheduler. Its `delay` calls move the virtual clock, so the same three lines run in milliseconds and the clock reads exactly 3000. `flowOn` still builds its channel, because a second `StandardTestDispatcher` is a different dispatcher object.",
    "code": "runTest {\n    slowFeed().flowOn(StandardTestDispatcher(testScheduler)).toList()\n    // virtual=3000 ms, wall=8 ms\n}",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// Java equivalent: a direct executor runs the task on the test thread, with no real pool\nExecutor direct = Runnable::run;\nList<Settlement> all = new SettlementImport(direct).readAll(fakeReader).join();"
   },
   {
    "say": "For \"which side ran where\" tests, pass a real executor with one named thread, and record thread names in the fakes. That is how the lab's test checks that `readLine` ran on `test-io` and `ledger.post` on the test thread. Strip the ` @coroutine#N` suffix that debug mode adds when tests run with `-ea`.",
    "code": "val io = Executors.newSingleThreadExecutor { r -> Thread(r, \"test-io\") }.asCoroutineDispatcher()\nfun threadName() = Thread.currentThread().name.substringBefore(\" @\")\n\nval reader = LineReader { readOn += threadName(); lines.removeFirstOrNull() }\nval ledger = Ledger { postedOn += threadName() }\n// after collecting: readOn contains only \"test-io\", postedOn only the test thread",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "ExecutorService io = Executors.newSingleThreadExecutor(r -> new Thread(r, \"test-io\"));\nLineReader reader = () -> { readOn.add(Thread.currentThread().getName()); return lines.poll(); };\n// after the run: readOn contains only \"test-io\""
   }
  ]
 },
 "lab": {
  "title": "Move only the reader, then fan in two feeds",
  "minutes": 12,
  "files": [f"{LAB}/main/{P}/SettlementImport.kt"],
  "run": "./gradlew :flows:test --tests 'workbench.flows.l03.*'",
  "steps": [
   "Run the tests. Three of the five fail. Read the messages: one lists the threads that called `ledger.post`, and two quote \"Emission from another coroutine is detected\".",
   "Fix `importSettlements` by moving one line. Reading and parsing must run on `io`; posting and the collector must not.",
   "Rewrite `bothAcquirers` with `channelFlow`: one `launch` per feed, and `send` where the stub calls `emit`.",
   "Run the tests until all five pass, then run them once more."
  ],
  "hints": [
   "`flowOn` moves the operators above it, up to the previous `flowOn`. Ask which lines must run on `io`, and put `flowOn` directly below the last of them.",
   "Inside `channelFlow { }`, `this` is a `ProducerScope`: a `CoroutineScope` you can `launch` in and a `SendChannel` you can `send` to. You don't need `awaitClose`; that's for `callbackFlow`.",
   "You don't need to close the channel or join the children. `channelFlow` completes by itself when its block and all its children are done.",
   "The test feeds use `delay`. `runTest`'s virtual clock covers them, because `channelFlow`'s children inherit the test dispatcher. The merged flow should complete at 390 ms of virtual time, the slower feed's last item."
  ],
  "done_when": "All five tests in `SettlementImportTest` pass."
 },
 "drill": {
  "title": "Write flowOn by hand from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `myFlowOn(dispatcher)` with `flow { }`, `coroutineScope`, `produce` and a `for` loop over the channel. Then answer without running it: where does the block of `flow { }` run, where does your `emit` run, and how many emits can return while the collector holds the first value?",
  "answer": {
   "lang": "kotlin",
   "src": "@OptIn(ExperimentalCoroutinesApi::class)\nfun <T> Flow<T>.myFlowOn(dispatcher: CoroutineDispatcher): Flow<T> = flow {\n    coroutineScope {\n        val mailbox = produce(dispatcher, capacity = 64) {   // the upstream runs on dispatcher\n            this@myFlowOn.collect { send(it) }\n        }\n        for (value in mailbox) emit(value)                    // our emit runs in the collector's coroutine\n    }\n}\n// the upstream's flow { } block runs in the produce coroutine, on dispatcher\n// 65 emits can return while the collector holds item 1: 64 in the channel, 1 in hand",
   "alt": {
    "lang": "java",
    "src": "// Java equivalent: an executor for the upstream, a 64-slot queue, a drain loop on the caller\nstatic <T> void flowOn(ExecutorService executor, Consumer<Consumer<T>> upstream, Consumer<T> downstream)\n        throws InterruptedException {\n    BlockingQueue<Object> mailbox = new ArrayBlockingQueue<>(64);\n    executor.execute(() -> {\n        upstream.accept(value -> put(mailbox, value));\n        put(mailbox, END);\n    });\n    for (Object v = mailbox.take(); v != END; v = mailbox.take()) downstream.accept((T) v);\n}"
   }
  }
 },
 "recap": [
  "The collector runs inside `emit`, so `emit` must run in the collector's context. `withContext` around `emit` would drag the collector onto another thread, and `flow { }` refuses it.",
  "When the dispatcher changes, `flowOn` runs the upstream in a second coroutine and puts a channel between the two halves, 64 slots by default. The producer can get 65 emits ahead.",
  "`flowOn` moves only the operators above it, up to the previous `flowOn`. Two calls make two walls and three rooms; two adjacent calls fuse, and the first one wins. With the same dispatcher, as in `flowOn(CoroutineName(...))`, there is no channel.",
  "To emit from several coroutines, use `channelFlow`: `send` is safe from any child, and the flow completes after every child. `produceIn` hands you the channel itself, hot, in your scope.",
  "In tests, inject the dispatcher that `flowOn` uses. `flowOn(Dispatchers.Default)` inside `runTest` runs on the real clock."
 ],
 "quiz": [
  {
   "q": "`flow { emit(1) }.map { a(it) }.flowOn(io).map { b(it) }.collect { c(it) }`. Where do `a`, `b` and `c` run?",
   "options": [
    "All three on io",
    "`a` on io; `b` and `c` in the collector's context",
    "`a` and `b` on io; `c` in the collector's context",
    "`a` in the collector's context; `b` and `c` on io"
   ],
   "answer": 1,
   "why": "`flowOn` moves what is above it, up to the previous `flowOn`, and nothing below it. The tempting answer \"`a` and `b` on io\" reads `flowOn` like Reactor's `publishOn`, which moves what follows it."
  },
  {
   "q": "A collector holds the first value and doesn't return. The upstream is `flow { repeat(200) { emit(it) } }.flowOn(io)`. How many `emit` calls return meanwhile?",
   "options": ["0", "1", "64", "65"],
   "answer": 3,
   "why": "`flowOn` with a new dispatcher puts a `Channel.BUFFERED` channel in between: 64 slots. The producer fills all 64, and one more value is already in the collector's hands, so 65 emits have returned. A plain flow gives 0."
  },
  {
   "q": "`flowOf(1, 2).flowOn(Dispatchers.IO).flowOn(Dispatchers.Default)`. Which dispatcher runs the upstream?",
   "options": [
    "Dispatchers.IO: adjacent flowOn calls fuse, and the first one wins",
    "Dispatchers.Default: the last flowOn wins",
    "Both, one after the other, through two channels",
    "Neither: the two calls cancel out and it runs on the collector's thread"
   ],
   "answer": 0,
   "why": "Adjacent `flowOn` calls fuse into one, and the context of the first one, nearest the source, takes precedence for each key. `toString()` shows `ChannelFlowOperatorImpl[context=Dispatchers.IO]`. A `map` between them would stop the fusion and give two walls."
  },
  {
   "q": "You have two flows, `north` and `east`, and want one flow that delivers both as they arrive, without waiting for one to finish first. Which builder fits?",
   "options": [
    "`flow { coroutineScope { launch { north.collect { emit(it) } }; launch { east.collect { emit(it) } } } }`",
    "`flow { withContext(Dispatchers.IO) { north.collect { emit(it) } } }`",
    "`channelFlow { launch { north.collect { send(it) } }; launch { east.collect { send(it) } } }`",
    "`flow { north.collect { emit(it) }; east.collect { emit(it) } }`"
   ],
   "answer": 2,
   "why": "`channelFlow` gives each child a `send` that is safe from any coroutine, and completes after both. The `flow { }` with `launch` fails with \"Emission from another coroutine is detected\". The last option is legal but sequential: east starts only after north completes."
  },
  {
   "q": "From lesson 2: `flow { coroutineScope { emit(1) } }` passes the context check, but `flow { coroutineScope { launch { emit(1) } } }` fails. Why the second one?",
   "options": [
    "`launch` always switches to another dispatcher",
    "The emitting Job is a launched child, not a scope, so two coroutines could emit at once into a collector that isn't thread-safe",
    "`coroutineScope` is not allowed inside `flow { }`",
    "`launch` runs after the flow has already completed"
   ],
   "answer": 1,
   "why": "The check allows a different `Job` only if it reaches the collector's `Job` through scope coroutines such as `coroutineScope`. A `launch`ed child could run at the same time as another, so the inspector refuses its emits and points you to `channelFlow`. `launch` keeps the parent's dispatcher unless you pass one.",
   "from": "flow-02"
  }
 ],
 "flashcards": [
  {"front": "Why does `flow { }` refuse `withContext(Dispatchers.IO) { emit(x) }`?", "back": "The collector runs inside `emit`, so it would run on an IO thread it never asked for. Use `flowOn` on the upstream instead."},
  {"front": "What does `flowOn(io)` build when `io` differs from the collector's dispatcher?", "back": "A second coroutine that runs the upstream on `io` and sends into a channel (64 slots by default), plus a drain loop that emits in the collector's coroutine."},
  {"front": "Which part of a chain does `flowOn` move?", "back": "Only the operators above it, up to the previous `flowOn`. The collector never moves."},
  {"front": "`.flowOn(CoroutineName(\"x\"))`: is there a channel?", "back": "No. The dispatcher is unchanged, so the upstream runs inline with the new name."},
  {"front": "`.flowOn(A).flowOn(B)` with nothing between them: which dispatcher runs the upstream?", "back": "A. Adjacent `flowOn` calls fuse into one, and the first one (nearest the source) wins for each context key."},
  {"front": "When does a `channelFlow` complete?", "back": "When its block and every coroutine launched inside it have finished. The block itself may return much earlier."},
  {"front": "Why inject the dispatcher you pass to `flowOn`?", "back": "`flowOn(Dispatchers.Default)` inside `runTest` runs on the real clock: three 1 s delays took about 3 s of wall time and 0 ms of virtual time."}
 ],
 "terms": [
  {"term": "flowOn", "plain": "An operator that runs the part of the flow above it in another context, through a channel when the dispatcher changes."},
  {"term": "Channel", "plain": "A queue between coroutines: `send` suspends when it is full, `receive` suspends when it is empty."},
  {"term": "ChannelFlow", "plain": "The internal base class behind `flowOn`, `buffer`, `channelFlow` and `produceIn`: a flow that can run its upstream in a second coroutine and drain a channel."},
  {"term": "Operator fusion", "plain": "Adjacent channel-based operators merging into one channel with one combined configuration."},
  {"term": "channelFlow", "plain": "A builder whose block can launch coroutines that all `send` into one channel. It completes after all of them."},
  {"term": "produceIn", "plain": "Launches a coroutine in your scope that collects a flow, and returns its channel: a hot stream you must consume or cancel."},
  {"term": "ProducerScope", "plain": "The receiver of `channelFlow`'s block: a `CoroutineScope` and a `SendChannel` in one."}
 ],
 "explain_back": {
  "prompt": "A teammate moved a blocking acquirer reader with `withContext(Dispatchers.IO) { emit(record) }`, got \"Flow invariant is violated\", and asks why Kotlin forbids something so obvious. Explain it, and say what `flowOn` does instead.",
  "answer": "In a flow, emit isn't a hand-off. It's a direct call into the collector, so the collector's code runs inside emit. If emit ran inside withContext(Dispatchers.IO), our collector, the part that posts to the ledger, would suddenly run on an IO thread it never asked for, maybe with a client that isn't thread-safe. flow { } checks every emit and refuses that. flowOn solves it by breaking the call chain. When the dispatcher changes, it starts a second coroutine on IO that runs everything above flowOn and sends each value into a channel with 64 slots, and on our side a loop takes values out and calls our collector in its own coroutine. So the reader runs on IO, can get up to 65 values ahead, and the collector stays exactly where it was. It only moves what's above it, so we put it right under the blocking read."
 },
 "deeper": {
  "minutes": 10,
  "body": "Some details of `flowOn` only show up in production.\n\nIt can lose in-flight values on cancellation. Its KDoc says that \"flows operating across different dispatchers might lose some in-flight elements when cancelled\", and that the operator \"ensures that downstream flow does not resume on cancellation even if the element was already emitted by the upstream flow\". For a settlement import that means the reader may have read lines that nobody posted. If that matters, track what was posted, not what was read.\n\nWhether a channel appears depends on dispatcher objects, not threads. With a collector already on `Dispatchers.IO`, `flowOn(Dispatchers.IO)` stays sequential, with no channel. With a collector on `Dispatchers.Default`, `flowOn(Dispatchers.IO)` creates one, even though the two dispatchers share threads, because they are different objects.\n\nStability in 1.11.0: `flowOn`, `channelFlow`, `callbackFlow` and `produceIn` compile with no opt-in. `CoroutineScope.produce`, which the hand-built `myFlowOn` uses, is `@ExperimentalCoroutinesApi`. Use the library's operators in real code and keep `myFlowOn` as the model in your head.\n\n`callbackFlow`, from lesson 9 of the coroutines track, is a subclass of the same `channelFlow` builder. The difference is one check: if its block returns while the channel is still open, it throws an `IllegalStateException` telling you to call `awaitClose { ... }` at the end. Lesson 8 of this track wraps a listener API with it.\n\n`buffer()` is the same machine as `flowOn` without the context change, and neighbouring channel operators fuse into one channel. Lesson 4 of this track takes that apart, using `toString()` as a peek under the hood."
 },
 "sources": [
  {"title": "flowOn (kotlinx.coroutines API, 1.11.0)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow-on.html"},
  {"title": "channelFlow (kotlinx.coroutines API, 1.11.0)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/channel-flow.html"},
  {"title": "Context.kt at tag 1.11.0: flowOn and buffer (kotlinx.coroutines source)", "url": "https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/operators/Context.kt"},
  {"title": "ChannelFlow.kt at tag 1.11.0 (kotlinx.coroutines source)", "url": "https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/internal/ChannelFlow.kt"},
  {"title": "Asynchronous Flow: flowOn and channelFlow (Kotlin docs)", "url": "https://kotlinlang.org/docs/coroutines-flow.html"}
 ]
}

out = ROOT / "content/lessons/flow-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
