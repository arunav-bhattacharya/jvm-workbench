import json, pathlib

ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/flows/src"
P = "kotlin/workbench/flows/l02"
J = "java/workbench/flows/l02"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{LAB}/demo/{P}/{name}"
jdemo = lambda name: f"{LAB}/demo/{J}/{name}"
run = lambda cls: f"./gradlew :flows:demo -Pmain=workbench.flows.l02.{cls}"


def tryit(kt, java):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(demo(kt)), "run": run(k + "Kt"), "file": demo(kt),
            "alt": {"lang": "java", "title": java, "src": read(jdemo(java)), "run": run(j), "file": jdemo(java)}}


FIG = (
    '<svg viewBox="0 0 700 300" role="img" aria-label="The flow block on the left hands each value to an inspector, SafeCollector, '
    'which runs three checks: is the collecting coroutine still active, is the emit in the same context, did the last emit throw. '
    'The library\'s own map and filter pass values on with no inspector. Your collector is on the right. A red arrow along the bottom '
    'shows the abort exception from take flying back from the collector to the flow block, running the producer\'s finally on the way.">'
    '<text class="t-s t-m" x="285" y="34" text-anchor="middle">flow { } puts an inspector at the hatch</text>'
    '<rect class="box" x="10" y="110" width="130" height="60" rx="8"/>'
    '<text class="t" x="75" y="136" text-anchor="middle">flow { } block</text>'
    '<text class="t-s t-m" x="75" y="156" text-anchor="middle">the cook</text>'
    '<line class="ln" x1="140" y1="140" x2="166" y2="140" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="170" y="52" width="230" height="176" rx="8"/>'
    '<text class="t-s t-b" x="285" y="78" text-anchor="middle">SafeCollector: the inspector</text>'
    '<text class="t-s" x="285" y="112" text-anchor="middle">1. still open? ensureActive()</text>'
    '<text class="t-s" x="285" y="140" text-anchor="middle">2. same context as collect?</text>'
    '<text class="t-s" x="285" y="168" text-anchor="middle">3. did the last emit throw?</text>'
    '<text class="t-s t-bad" x="285" y="204" text-anchor="middle">any no: emit throws</text>'
    '<line class="ln" x1="400" y1="140" x2="426" y2="140" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="485" y="98" text-anchor="middle">unsafeFlow: no inspector</text>'
    '<rect class="box" x="430" y="110" width="110" height="60" rx="8"/>'
    '<text class="t" x="485" y="136" text-anchor="middle">map, filter</text>'
    '<text class="t-s t-m" x="485" y="156" text-anchor="middle">trusted staff</text>'
    '<line class="ln" x1="540" y1="140" x2="566" y2="140" marker-end="url(#arr)"/>'
    '<rect class="box-a" x="570" y="110" width="120" height="60" rx="8"/>'
    '<text class="t" x="630" y="136" text-anchor="middle">your collector</text>'
    '<text class="t-s t-m" x="630" y="156" text-anchor="middle">the diner</text>'
    '<path class="ln-bad" d="M 630 170 L 630 246 L 75 246 L 75 174" marker-end="url(#arr)"/>'
    '<text class="t-s t-bad" x="352" y="268" text-anchor="middle">take(n): a red card with its owner\'s name flies back through every emit</text>'
    '<text class="t-s t-m" x="352" y="288" text-anchor="middle">the cook\'s finally runs as it passes</text>'
    '</svg>'
)

S1 = """A batch job posts settlements to the ledger. Someone wrapped each `emit` in a try/catch, so that one bad posting can't stop the batch:

```kotlin
val postings = flow {
    for ((id, cents) in batch) {             // pay-1: 4250, pay-2: -990, pay-3: 12000
        try {
            emit(id to cents)
        } catch (e: Exception) {
            log.warn("posting $id failed, skipping it: ${e.message}")
        }
    }
}
postings.collect { (id, cents) -> ledger.post(id, cents) }   // refuses negative amounts
```

```java
// Java equivalent: a hand-written push "flow" (lesson 1) with the same try/catch around the call
static void postings(BiConsumer<String, Long> ledgerWriter) {
    for (Posting p : BATCH) {
        try {
            ledgerWriter.accept(p.id(), p.cents());
        } catch (RuntimeException e) {
            log.warn("posting " + p.id() + " failed, skipping it: " + e.getMessage());
        }
    }
}
```

From lesson 1 you know the collector runs inside `emit`, so that catch also catches the ledger's exception. That's why it's there. You'd expect pay-1 and pay-3 to be posted and pay-2 to be logged. The Java version and lesson 1's toy flow do exactly that. The real `flow { }` doesn't:

```text
WARN posting pay-2 failed, skipping it: LedgerException: negative amount -990 for pay-2
WARN posting pay-3 failed, skipping it: IllegalStateException: Flow exception transparency is violated:
    Previous 'emit' call has thrown exception workbench.flows.l02.LedgerException: negative amount -990 for pay-2, but then emission attempt of value '(pay-3, 12000)' has been detected.
    Emissions from 'catch' blocks are prohibited in order to avoid unspecified behaviour, 'Flow.catch' operator can be used instead.
    For a more detailed explanation, please refer to Flow documentation.
collect returned normally. posted=[pay-1]
```

Look at the last line. `collect` returned normally, and only pay-1 reached the ledger. pay-3 was never offered to the ledger at all: `emit` refused it, and the same try/catch swallowed the refusal. In production that is a batch that reports success with a hole in it, plus a warning nobody reads.

So `flow { }` is more than the toy. Something stands between your block and the collector. It noticed that the collector had already failed once, and it refused the next value. You met its name in lesson 1's stack trace: `SafeCollector`."""

S2 = """Here is what `flow { }` is in kotlinx.coroutines 1.11.0, slightly abridged:

```kotlin solo
public fun <T> flow(block: suspend FlowCollector<T>.() -> Unit): Flow<T> = SafeFlow(block)

private class SafeFlow<T>(private val block: suspend FlowCollector<T>.() -> Unit) : AbstractFlow<T>() {
    override suspend fun collectSafely(collector: FlowCollector<T>) { collector.block() }
}

// in AbstractFlow
final override suspend fun collect(collector: FlowCollector<T>) {
    val safeCollector = SafeCollector(collector, coroutineContext)
    try { collectSafely(safeCollector) } finally { safeCollector.releaseIntercepted() }
}
```

It's lesson 1's toy builder with one change. `collect` is `final` in `AbstractFlow`, and before it runs your block, it wraps your collector in a `SafeCollector` together with the context of the coroutine that is collecting. Your block's `emit` calls go to that wrapper, never straight to your collector.

Picture an inspector at the serving hatch between the cook and the diner. Each plate gets three checks on its way through.

1. Is the kitchen still open? `emit` first calls `ensureActive()`. If the collecting coroutine was cancelled, `emit` throws `CancellationException`.
2. Is it the same kitchen and the same cook's badge? Every element of the emitting context except the `Job` must be the same object as in the collector's context, and the `Job` may only differ by scopes such as `coroutineScope`. If not, `emit` throws "Flow invariant is violated". The check only runs when the context object changed since the last `emit`, so on the happy path it runs once per flow.
3. Did the diner throw the last plate back? If the previous `emit` threw, the next one throws "Flow exception transparency is violated".

The second check looks at every element of the context, and the dispatcher is only one of them. `withContext(CoroutineName("other")) { emit(1) }` fails too. `withContext(EmptyCoroutineContext)` and `coroutineScope { emit(1) }` pass, because they keep every element and only add a scope. The third check is what bit the batch job, and you can build it in a few lines. This is the shape of the lab's `SafeToyCollector`, without the context check:

```kotlin
class SafeToyCollector<T>(private val downstream: ToyCollector<T>) : ToyCollector<T> {
    private var downstreamFailure: Throwable? = null

    override suspend fun emit(value: T) {
        downstreamFailure?.let { throw IllegalStateException("Flow exception transparency is violated: $it") }
        try {
            downstream.emit(value)
        } catch (e: Throwable) {
            downstreamFailure = e          // remember: the hatch stays shut from now on
            throw e
        }
    }
}
```

```java
final class SafeToyCollector<T> implements ToyCollector<T> {
    private final ToyCollector<T> downstream;
    private Throwable downstreamFailure;

    SafeToyCollector(ToyCollector<T> downstream) { this.downstream = downstream; }

    public void emit(T value) {
        if (downstreamFailure != null)
            throw new IllegalStateException("Flow exception transparency is violated: " + downstreamFailure);
        try {
            downstream.emit(value);
        } catch (RuntimeException e) {
            downstreamFailure = e;         // remember: the hatch stays shut from now on
            throw e;
        }
    }
}
```

Notice what the real one throws away. The `IllegalStateException` has `cause == null` and no suppressed exceptions. The ledger's error survives only as text inside the message."""

S3 = """Not every flow has an inspector. The library's own operators are built on an internal builder that skips it:

```kotlin solo
@PublishedApi
internal inline fun <T> unsafeFlow(crossinline block: suspend FlowCollector<T>.() -> Unit): Flow<T> =
    object : Flow<T> {
        override suspend fun collect(collector: FlowCollector<T>) { collector.block() }
    }
```

That is lesson 1's toy builder, nearly word for word. Its KDoc says it is used "in our own operators where we trust the context of invocations". `Transform.kt` imports it under the name `flow`, so `map`, `filter` and `onEach` are written on it. So are `take`, `flowOf` and every `asFlow()`. These are trusted staff who walk past the inspector: a chain of them costs one nested call per value and no checks. The library can trust `map` because `map` never changes the context, and it calls `emit` only from inside the upstream's `emit`. Your lambda inside `map` gets a value, never a collector, so it has no way to emit at the wrong time. The public `transform { }` is different. Your code there receives the collector itself, so `transform` is built with the real `flow { }`. The class names show which is which:

```text
flow { }      -> kotlinx.coroutines.flow.SafeFlow
flowOf(1, 2)  -> kotlinx.coroutines.flow.FlowKt__BuildersKt$flowOf$$inlined$unsafeFlow$1
asFlow()      -> kotlinx.coroutines.flow.FlowKt__BuildersKt$asFlow$$inlined$unsafeFlow$9
transform { } -> kotlinx.coroutines.flow.SafeFlow
```

Skipping the inspector also skips the first check. `flowOf` and `asFlow` never call `ensureActive()` between items. Usually that doesn't matter, because a collector that suspends (I/O, `delay`) notices cancellation at its next suspension. It matters for a CPU-only collector. Take a reconciliation job that cancels its own coroutine at the first mismatch, item 3, and never suspends:

| Flow | The collector gets |
|---|---|
| `flow { for (i in 1..5) emit(i) }` | 1, 2, 3 |
| `(1..5).asFlow()` | 1, 2, 3, 4, 5 |
| `flowOf(1, 2, 3, 4, 5)` | 1, 2, 3, 4, 5 |
| `(1..5).asFlow().cancellable()` | 1, 2, 3 |
| `(1..5).asFlow().map { it }` | 1, 2, 3, 4, 5 |
| `(1..5).asFlow().transform { emit(it) }` | 1, 2, 3 |

`cancellable()` is the fix. It wraps the flow so that each `emit` calls `ensureActive()` first. On a flow that already checks, such as anything built with `flow { }`, it returns the same flow, so it costs nothing there. My rule: put it right after `asFlow()` whenever a non-suspending collector can cancel.

```kotlin
fun batchIds(ids: List<String>): Flow<String> = ids.asFlow().cancellable()
```

```java
// Java equivalent: a loop is only as cancellable as its checks
for (String id : ids) {
    if (Thread.currentThread().isInterrupted()) return;   // like ensureActive()
    collector.emit(id);
}
```"""

S4 = """Lesson 1's toy `take` threw an exception from its collector and caught it on the way out. The library does the same. Here is `take` in 1.11.0, slightly trimmed:

```kotlin
public fun <T> Flow<T>.take(count: Int): Flow<T> {
    require(count > 0) { ... }
    return unsafeFlow {
        val ownershipMarker = Any()
        var consumed = 0
        try {
            collect { value ->
                if (++consumed < count) return@collect emit(value)
                else return@collect emitAbort(value, ownershipMarker)   // emit it, then throw AbortFlowException
            }
        } catch (e: AbortFlowException) {
            e.checkOwnership(owner = ownershipMarker)                   // rethrows it if it isn't ours
        }
    }
}
```

```java
// Java equivalent: the toy take from lesson 1's lab, as a default method in the Java ToyFlow
default ToyFlow<T> take(int count) {
    if (count <= 0) throw new IllegalArgumentException("count must be positive, was " + count);
    return downstream -> {
        Object marker = new Object();
        int[] consumed = {0};
        try {
            this.collect(value -> {
                downstream.emit(value);
                if (++consumed[0] == count) throw new ToyAbortException(marker);
            });
        } catch (ToyAbortException e) {
            if (e.owner != marker) throw e;      // someone else's card: let it fly on
        }
    };
}
```

`AbortFlowException` is a `CancellationException` with the message "Flow was aborted, no more elements needed". It leaves `take`'s collector, flies back up through the producer's `emit`, and lands in `take`'s catch. On its way it passes through the producer's code, so the producer's `finally` runs, and an `onCompletion` above `take` sees it as its cause:

```text
  [take] emit 1
  got 1
  [take] emit 2
  got 2
  [take] emit threw kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed
  [take] finally
  [take] onCompletion cause=kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed
```

The owner marker is the name on the red card. Only the `take` that raised it may catch it, and any other `take` on the way rethrows it. `first()` works the same way: it aborts the producer right after `emit 1`, and `first { it > 2 }` right after `emit 3`. If the flow ends before anything arrives, `first()` throws `NoSuchElementException` with "Expected at least one element", and `first { }` with "Expected at least one element matching the predicate". `single()` needs no red card. It is a plain `collect` that fails with "Flow has more than one element" as soon as a second value arrives, or with "Flow is empty" if none came.

Now the batch job's try/catch has a second victim. A producer that catches `Exception` or `Throwable` around `emit` also catches the red card. Then it emits again, and the inspector fires with "Previous 'emit' call has thrown exception kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed". With `take(1)` over 1,000 items, a `catch (e: Exception)` loop around `emit` logged 1,000 warnings, one for the red card and 999 for refused emits. With `while (true)` it never stops.

So the rule I follow is simple: never put a try/catch around `emit`. A try/finally is fine, because it lets the exception go. If the producer's own work can fail, catch around that work. If the ledger can refuse a posting and the batch should go on, catch inside the collector, where the failure happens."""

L = {
 "id": "flow-02",
 "title": "Inside flow { }: the three checks, and how operators are built",
 "minutes": 35,
 "goal": "By the end you can name the three checks flow { } runs on every emit and the exact error each one throws, say which library flows skip them and what that costs, and explain how take and first stop a producer.",
 "warmup": {
  "q": "A `flow { }` wraps each `emit` in `try { ... } catch (e: Exception) { log.warn(...) }` so that one bad posting can't stop the batch. The collector throws for the second of three postings. What happens?",
  "options": [
   "Postings 1 and 3 reach the ledger and posting 2 is logged",
   "`collect` throws the collector's exception",
   "Only posting 1 reaches the ledger, postings 2 and 3 are both logged, and `collect` returns normally",
   "`collect` throws an IllegalStateException and nothing is logged"
  ],
  "answer": 2,
  "why": "The catch swallows the collector's exception for posting 2, as intended. But `flow { }` remembers that the downstream failed, and refuses the next `emit` with an IllegalStateException, \"Flow exception transparency is violated\". The same catch swallows that too, so posting 3 is logged instead of posted, and `collect` returns as if all went well. Option one is what a flow without checks would do."
 },
 "sections": [
  {
   "h": "A try/catch around emit that logs and continues",
   "body": S1,
   "try": {
    "title": "Run the batch job three ways",
    "minutes": 4,
    "steps": [
     "Read the first part of `TransparencyTrap.kt` and write down which postings you expect in `posted`. Then run it.",
     "Look at the second part: the same code on lesson 1's toy flow. Which postings reach the ledger there?",
     "Look at the third part, where `emit` is called inside the catch block with no try around it. What are the `cause` and `suppressed` of the exception that `collect` throws?",
     "Run the Java twin, `TransparencyTrapJava`."
    ],
    "code": tryit("TransparencyTrap.kt", "TransparencyTrapJava.java"),
    "expect": "With `flow { }`, `posted` is `[pay-1]`, two warnings are logged (the second one is the transparency message), and `collect` returns normally. The toy flow posts `[pay-1, pay-3]`, because nothing remembers the first failure, and the Java twin does the same. In the third part `collect` throws the IllegalStateException with `cause=null` and `suppressed=[]`: the ledger's exception is only text in the message."
   }
  },
  {
   "h": "The inspector at the hatch: SafeFlow and SafeCollector",
   "body": S2,
   "figure": {"svg": FIG, "caption": "flow { } puts an inspector at the hatch. The library's own operators are trusted staff who walk past it, and take stops the cook by throwing a named red card back through every emit."},
   "try": {
    "title": "Trip the context check",
    "minutes": 4,
    "steps": [
     "Read `Invariants.kt`. Predict which of the four `flow { }` attempts fail and which deliver `1`.",
     "Run it. Look at the first line: which thread did the hand-written raw `Flow` run the printer on?",
     "Add `attempt(\"launch\", flow { coroutineScope { launch { emit(1) } } })` at the end of `main` (import `kotlinx.coroutines.launch`). Predict whether it passes, then run it.",
     "Run `InvariantsJava`, the Reactor version of the raw flow."
    ],
    "code": tryit("Invariants.kt", "InvariantsJava.java"),
    "expect": "`withContext(IO)` and `withContext(CoroutineName)` fail with \"Flow invariant is violated\" and print both contexts. `withContext(Empty)` and `coroutineScope` collect 1. The raw `Flow` ran the printer on `DefaultDispatcher-worker-1`: with no inspector, the collector simply ran on the IO thread. The `launch` attempt fails too, with \"Emission from another coroutine is detected\" and a hint to use `channelFlow`. The Java twin prints `acquirer-io`, because Reactor has no such rule."
   },
   "refs": [
    {"title": "flow builder (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow.html", "kind": "docs"}
   ]
  },
  {
   "h": "Trusted staff walk past the inspector: unsafeFlow and cancellable()",
   "body": S3,
   "try": {
    "title": "Who stops at 3?",
    "minutes": 4,
    "steps": [
     "Cover the right column of the table above. Predict each row, then run `CancelTable.kt` and check.",
     "Add `yield()` after `if (v == 3) cancel()` in `stopAtThree` (import `kotlinx.coroutines.yield`). Predict the `asFlow()` and `flowOf` rows now, then run it.",
     "Run `CancelTableJava`, the same experiment with a thread that interrupts itself."
    ],
    "code": tryit("CancelTable.kt", "CancelTableJava.java"),
    "expect": "The table matches: `flow { }`, `cancellable()` and `transform` stop at `[1, 2, 3]`, while `asFlow()`, `flowOf` and `map` deliver all five. The class names show `SafeFlow` for `flow { }` and `transform`, and `unsafeFlow` for the others. With `yield()` every row stops at `[1, 2, 3]`: the collector now suspends, and a suspension point checks for cancellation. The Java loop that checks the interrupt flag stops at 3; the one without a check delivers all five."
   },
   "refs": [
    {"title": "cancellable (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/cancellable.html", "kind": "docs"}
   ]
  },
  {
   "h": "How take stops the producer: a red card with a name on it",
   "body": S4,
   "try": {
    "title": "Watch the red card fly",
    "minutes": 4,
    "steps": [
     "Read `TakeFirst.kt`. For `take(2)`, predict the line after `got 2`. Does `emit 3` ever print?",
     "Run it, and compare `first()` with `first { it > 2 }`: after which `emit` does each one stop the producer?",
     "Read the last part's message: what did the producer swallow, and what did the inspector refuse?",
     "Run `TakeFirstJava`, the same thing with Reactor."
    ],
    "code": tryit("TakeFirst.kt", "TakeFirstJava.java"),
    "expect": "After `got 2` the producer's `emit` throws `AbortFlowException: Flow was aborted, no more elements needed`, its `finally` runs, and `onCompletion` reports that exception as its cause. `emit 3` never prints. `first()` stops after `emit 1`, `first { it > 2 }` after `emit 3`. The swallowing producer gets \"Flow exception transparency is violated\" for value 2. In the Java twin, Reactor's `take` stops the source with a cancel signal instead: `doFinally` prints `cancel`, and no exception passes through the source."
   },
   "refs": [
    {"title": "take (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/take.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "Think of `flow { }` as a kitchen with an inspector at the serving hatch. The cook (your block) can only pass plates through the hatch, and the inspector looks at each one: is the restaurant still open, is this plate coming from the same kitchen and the same cook as the first one, and did the diner throw the last plate back? If any answer is wrong, the hatch slams shut. The library's own `map` and `filter` are trusted staff with a key to a side door, so they skip the inspector. `take` is a diner who raises a red card with their own name on it; the card is passed back through every hatch to the cook, and only the diner who raised it can take it back. The analogy breaks at what the inspector looks at. A real inspector checks the food. `SafeCollector` never looks at your values at all, only at who is emitting and what happened to the last plate.",
 "in_your_world": "Picture a Temporal activity that reads a settlement file as a flow and posts each line to the ledger. If the producer has the \"log and continue\" try/catch around `emit`, one bad line turns the rest of the file into warnings, and the activity still returns success. Temporal only retries activities that fail, so nobody retries it, and the reconciliation report finds the hole the next morning. Put the try/catch around `ledger.post` inside the collector for postings you really want to skip, and let everything else fail the activity so the retry policy can do its job. The same goes for a Kafka consumer built on `flow { }`: a swallowed exception there can mean an offset gets committed for an event that was never posted.",
 "mistake": "The most common mistake is catching `Exception` around a suspend call in the producer, out of habit, and wrapping `emit` in it:\n\n```kotlin\nflow {\n    while (true) {\n        try {\n            emit(acquirer.poll())            // emit is inside the try\n        } catch (e: Exception) {\n            log.warn(\"poll failed\", e)       // also catches take's AbortFlowException\n        }\n    }\n}.take(1)\n```\n\n```java\n// Java equivalent: the same habit around a push call\nwhile (true) {\n    try {\n        collector.emit(acquirer.poll());\n    } catch (Exception e) {\n        log.warn(\"poll failed\", e);\n    }\n}\n```\n\nPeople write it because a catch-all around I/O looks defensive. But `CancellationException` is an `Exception` on the JVM, and so is `take`'s `AbortFlowException`. The loop swallows the red card, every later `emit` is refused by the inspector, and the refusal is swallowed too. In a bounded run with 1,000 items it logged 1,000 warnings, and with `while (true)` it spins forever. Catch the narrow exception around the call that throws it: `val batch = try { acquirer.poll() } catch (e: IOException) { ... }`, then `emit(batch)` outside the try.",
 "compare": {
  "title": "Stopping a producer early: Flow's take and Reactor's take",
  "java": {
   "title": "TakeFirstJava.java (Reactor)",
   "src": "// Java equivalent: Reactor's take(2) cancels the source's subscription after the second item\nFlux.range(1, 5)\n    .doOnNext(i -> System.out.println(\"emit \" + i))\n    .doFinally(signal -> System.out.println(\"finally \" + signal))   // prints \"finally cancel\"\n    .take(2)\n    .doOnNext(v -> System.out.println(\"got \" + v))\n    .blockLast();"
  },
  "kotlin": {
   "title": "TakeFirst.kt (Flow)",
   "src": "flow {\n    try {\n        for (i in 1..5) { println(\"emit $i\"); emit(i) }\n    } catch (e: Throwable) {\n        println(\"emit threw $e\")         // AbortFlowException: Flow was aborted, no more elements needed\n        throw e\n    } finally {\n        println(\"finally\")\n    }\n}\n    .take(2)\n    .collect { println(\"got $it\") }"
  },
  "note": "Both stop the source after two items and both run the cleanup, but the signal travels differently. Reactor has a back channel: the subscriber holds a `Subscription` and calls `cancel()` on it, and the source learns about it through a method call. A Kotlin flow has no back channel, only the call stack that `emit` sits on, so the only way to tell the producer to stop is to throw through it. That is why a Kotlin producer can accidentally catch the stop signal, and a Reactor source can't."
 },
 "worked": {
  "title": "Fix the batch poster without losing postings",
  "steps": [
   {
    "say": "Start from the broken job. The try/catch sits around `emit`, so it catches the ledger's exception, and after that it catches the inspector's refusals. Find the line to move before reading on.",
    "code": "val postings = flow {\n    for ((id, cents) in batch) {\n        try {\n            emit(id to cents)                     // the downstream runs in here\n        } catch (e: Exception) {\n            log.warn(\"posting $id failed, skipping it: ${e.message}\")\n        }\n    }\n}\npostings.collect { (id, cents) -> ledger.post(id, cents) }",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// Java equivalent: the hand-written push flow from lesson 1\nfor (Posting p : batch) {\n    try {\n        ledgerWriter.accept(p.id(), p.cents());   // the downstream runs in here\n    } catch (RuntimeException e) {\n        log.warn(\"posting \" + p.id() + \" failed, skipping it: \" + e.getMessage());\n    }\n}"
   },
   {
    "say": "Move the catch to where the failure happens: inside the collector, around `ledger.post`. Catch only the exception that means \"skip this posting\". The flow itself becomes plain again.",
    "code": "val postings = flow {\n    for ((id, cents) in batch) emit(id to cents)   // 1. no try around emit\n}\npostings.collect { (id, cents) ->\n    try {\n        ledger.post(id, cents)                       // 2. the call that can refuse\n    } catch (e: LedgerException) {\n        log.warn(\"posting $id failed, skipping it: ${e.message}\")   // 3. the next posting still comes\n    }\n}",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "postings((id, cents) -> {\n    try {\n        ledger.post(id, cents);                      // 2. the call that can refuse\n    } catch (LedgerException e) {\n        log.warn(\"posting \" + id + \" failed, skipping it: \" + e.getMessage());   // 3. go on\n    }\n});"
   },
   {
    "say": "The producer can fail too, for example on a malformed line. Catch that around the producer's own work, and keep `emit` outside the try.",
    "code": "val postings = flow {\n    for (line in lines) {\n        val posting = try {\n            parsePosting(line)                       // 4. the producer's own work\n        } catch (e: NumberFormatException) {\n            log.warn(\"bad line skipped: $line\")\n            continue\n        }\n        emit(posting)                                // still outside any try\n    }\n}",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "for (String line : lines) {\n    Posting posting;\n    try {\n        posting = parsePosting(line);                // 4. the producer's own work\n    } catch (NumberFormatException e) {\n        log.warn(\"bad line skipped: \" + line);\n        continue;\n    }\n    ledgerWriter.accept(posting.id(), posting.cents());   // outside any try\n}"
   },
   {
    "say": "Decide what must not be skipped. A ledger that is down is not a bad posting: if `post` throws `IOException`, let it out, so the job fails and its caller (a Temporal retry, an operator) can act. The narrow catch in step 3 already does that, because it only catches `LedgerException`. Then count, so a hole can't hide: `posted + skipped` must equal the batch size, or the job fails.",
    "code": "var posted = 0\nvar skipped = 0\npostings.collect { (id, cents) ->\n    try { ledger.post(id, cents); posted++ }\n    catch (e: LedgerException) { skipped++; log.warn(\"posting $id skipped: ${e.message}\") }\n}\ncheck(posted + skipped == batch.size) { \"lost postings: $posted + $skipped != ${batch.size}\" }",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "int[] posted = {0}, skipped = {0};\npostings((id, cents) -> {\n    try { ledger.post(id, cents); posted[0]++; }\n    catch (LedgerException e) { skipped[0]++; log.warn(\"posting \" + id + \" skipped: \" + e.getMessage()); }\n});\nif (posted[0] + skipped[0] != batch.size())\n    throw new IllegalStateException(\"lost postings: \" + posted[0] + \" + \" + skipped[0] + \" != \" + batch.size());"
   }
  ]
 },
 "lab": {
  "title": "Write the inspector, then predict who stops",
  "minutes": 14,
  "files": [f"{LAB}/main/{P}/SafeToy.kt", f"{LAB}/main/{P}/Cancellation.kt"],
  "run": "./gradlew :flows:test --tests 'workbench.flows.l02.*'",
  "steps": [
   "Open `Cancellation.kt` first. Replace the six `TODO()`s in `CancelPredictions` with your predictions, without running anything.",
   "Fix `batchIds` so the reconciliation job gets no more ids after it cancels itself.",
   "In `SafeToy.kt`, write `safeToyFlow`: like `toyFlow`, but its `collect` wraps the collector in `SafeToyCollector(collector, currentCoroutineContext())` and runs the block on the wrapper.",
   "Write `SafeToyCollector.emit`: the four steps in its KDoc. For the context check, fold over the emitting context, skip the element whose key is `Job`, compare every other element with `collectContext[element.key]` using `===`, and then compare the element counts.",
   "Run the tests. If a prediction was wrong, say which check was missing for that flow before you change the list."
  ],
  "hints": [
   "`currentCoroutineContext()` inside `emit` is the context of the coroutine that is emitting. Inside `withContext(other) { emit(1) }` that's the `withContext` coroutine's context, with `other` as its dispatcher.",
   "Why skip the `Job`? `coroutineScope { emit(1) }` runs in a new scope coroutine, so its `Job` differs from the collector's while everything else stays the same. The real `SafeCollector` also checks that the emitting `Job` reaches the collector's `Job` through scope coroutines only. That's how it refuses `launch { emit() }`. Your version can skip that part.",
   "Count elements with `context.fold(0) { n, _ -> n + 1 }`. `withContext(CoroutineName(\"other\"))` changes an element and also adds one.",
   "The transparency check needs state: a `private var` in `SafeToyCollector` that holds the exception that came out of `downstream.emit`.",
   "If the log-and-continue test shows 12000 in `posted`, your transparency check is missing or runs after `downstream.emit` instead of before it."
  ],
  "done_when": "All 14 tests in `SafeToyCollectorTest` and `CancellationTest` pass."
 },
 "drill": {
  "title": "The three checks from memory",
  "minutes": 5,
  "prompt": "Close this page. Write down the three checks `SafeCollector` runs on every `emit`, in order, and what each one throws. Then write the batch poster that logs a refused posting and goes on, the right way round.",
  "answer": {
   "lang": "kotlin",
   "src": "// SafeCollector.emit, on every call:\n// 1. ensureActive() on the emitting coroutine        -> CancellationException\n// 2. same context as collect (Job may differ by scope) -> IllegalStateException \"Flow invariant is violated\"\n// 3. no emit after a failed emit                       -> IllegalStateException \"Flow exception transparency is violated\"\n\nval postings = flow {\n    for ((id, cents) in batch) emit(id to cents)       // no try around emit\n}\npostings.collect { (id, cents) ->\n    try {\n        ledger.post(id, cents)\n    } catch (e: LedgerException) {\n        log.warn(\"posting $id skipped: ${e.message}\")  // catch where the failure happens\n    }\n}",
   "alt": {
    "lang": "java",
    "src": "// Java equivalent: the push flow has no checks, so the right shape is all you have\nstatic void postings(BiConsumer<String, Long> ledgerWriter) {\n    for (Posting p : BATCH) ledgerWriter.accept(p.id(), p.cents());   // no try around the call\n}\n\npostings((id, cents) -> {\n    try {\n        ledger.post(id, cents);\n    } catch (LedgerException e) {\n        log.warn(\"posting \" + id + \" skipped: \" + e.getMessage());     // catch where it fails\n    }\n});"
   }
  }
 },
 "recap": [
  "`flow { }` is `SafeFlow`, an `AbstractFlow` whose final `collect` wraps your collector in a `SafeCollector` with the collector's context.",
  "Every `emit` is checked: `ensureActive()`, the same context (\"Flow invariant is violated\"), and no emit after a failed one (\"Flow exception transparency is violated\"). After a transparency failure, the original exception survives only as text.",
  "The library's `map`, `filter`, `onEach`, `take`, `flowOf` and `asFlow` use the unchecked `unsafeFlow`, so `flowOf` and `asFlow` keep delivering to a non-suspending collector that cancelled. `cancellable()` fixes that.",
  "`take` and `first` stop the producer by throwing `AbortFlowException` back through its `emit`, with an owner marker so that only they catch it. The producer's `finally` runs.",
  "Never wrap `emit` in try/catch. Catch narrow exceptions around the producer's own work, or inside the collector."
 ],
 "quiz": [
  {
   "q": "`flow { emit(1); withContext(CoroutineName(\"audit\")) { emit(2) } }` is collected. What happens?",
   "options": [
    "Both values arrive, because only a change of dispatcher is checked",
    "1 arrives, then `collect` throws IllegalStateException: \"Flow invariant is violated\"",
    "Nothing arrives, because the check runs before the first emit",
    "2 arrives on a new thread, after 1"
   ],
   "answer": 1,
   "why": "The context check compares every element except the Job, and a different `CoroutineName` is a different element. The first `emit` ran in the collector's own context and went through. Many people think the rule is only about threads; it isn't."
  },
  {
   "q": "A collector cancels its own coroutine at the value 3 and never suspends. Which flow still delivers 4 and 5?",
   "options": [
    "`flow { for (i in 1..5) emit(i) }`",
    "`(1..5).asFlow().cancellable()`",
    "`listOf(1, 2, 3, 4, 5).asFlow()`",
    "`(1..5).asFlow().transform { emit(it) }`"
   ],
   "answer": 2,
   "why": "`asFlow()` is built on the internal `unsafeFlow`, so nothing calls `ensureActive()` between items. `flow { }` and the public `transform` go through a `SafeCollector`, and `cancellable()` adds the check explicitly."
  },
  {
   "q": "A producer has `try { emit(x) } catch (e: Throwable) { log(e) }`, and the flow is collected with `.take(1)`. What does the log show first?",
   "options": [
    "Nothing: take cancels the coroutine without any exception",
    "A NoSuchElementException from take",
    "A TimeoutCancellationException",
    "AbortFlowException: Flow was aborted, no more elements needed"
   ],
   "answer": 3,
   "why": "`take` stops the producer by throwing `AbortFlowException`, a `CancellationException`, out of the producer's `emit`. A catch-all catches it. The next `emit` is then refused with the transparency error. Flow has no cancel call back to the producer, so an exception is its only way up."
  },
  {
   "q": "A flow of 50,000 settlement ids comes from `ids.asFlow()` and feeds a CPU-only matcher that cancels its own job at the first mismatch. Which change makes it stop right there?",
   "options": [
    "Add `.cancellable()` after `asFlow()`",
    "Add `.map { it }` after `asFlow()`",
    "Wrap the body of the collector in a try/catch",
    "Build it with `flowOf(*ids.toTypedArray())` instead"
   ],
   "answer": 0,
   "why": "`cancellable()` calls `ensureActive()` before each `emit`. `map` and `flowOf` are both built on `unsafeFlow`, so they don't check either. A try/catch changes nothing, because nothing throws."
  },
  {
   "q": "From lesson 1: `toyFlow { try { emit(1) } catch (e: Exception) { }; emit(2) }.collect { throw IllegalStateException(\"boom\") }`. The toy has no inspector. How often does the collector run, and what does `collect` throw?",
   "options": [
    "Once; `collect` throws boom",
    "Twice; `collect` throws boom from the second call",
    "Once; `collect` throws \"Flow exception transparency is violated\"",
    "Twice; `collect` returns normally"
   ],
   "answer": 1,
   "why": "Nothing in the toy remembers the first failure. `emit(1)` runs the collector, which throws; the producer's catch swallows it; `emit(2)` runs the collector again, and that throw has no catch around it. With `flow { }`, the second `emit` would be refused before the collector ran.",
   "from": "flow-01"
  }
 ],
 "flashcards": [
  {"front": "What does `flow { }` return in kotlinx.coroutines 1.11.0?", "back": "A `SafeFlow`: an `AbstractFlow` whose final `collect` wraps your collector in a `SafeCollector` before it runs your block."},
  {"front": "`flow { withContext(Dispatchers.IO) { emit(x) } }`: which check fires?", "back": "The context check: IllegalStateException, \"Flow invariant is violated\". The emit ran in a context with a different dispatcher and Job."},
  {"front": "After the downstream threw, the next `emit` fails with \"Flow exception transparency is violated\". Where is the original exception?", "back": "Only in the message text. The IllegalStateException has `cause == null` and no suppressed exceptions."},
  {"front": "Do `flowOf` and `asFlow()` check for cancellation between items?", "back": "No. They are built on the internal `unsafeFlow`. Add `.cancellable()` when a non-suspending collector must stop on cancel."},
  {"front": "What does `cancellable()` do to a flow built with `flow { }`?", "back": "Nothing: it returns the same flow, because `flow { }` already calls `ensureActive()` on every emit."},
  {"front": "How does `take(n)` stop the producer?", "back": "After the n-th value it throws `AbortFlowException` (a `CancellationException`) out of the producer's `emit`, tagged with its own owner marker, and catches only its own."},
  {"front": "Where does a \"log and continue\" try/catch belong in a flow?", "back": "Around the code that fails: the producer's own work, or inside the collector. Never around `emit`."}
 ],
 "terms": [
  {"term": "SafeCollector", "plain": "The internal wrapper that `flow { }` puts around your collector to check every `emit`."},
  {"term": "AbstractFlow", "plain": "The base class behind `flow { }`. Its final `collect` adds the SafeCollector. Extending it needs `@ExperimentalCoroutinesApi`."},
  {"term": "unsafeFlow", "plain": "The library's internal builder with no checks. Its own operators and `flowOf` and `asFlow` use it."},
  {"term": "Exception transparency", "plain": "A flow never hides an exception that came from downstream, and never emits again after one."},
  {"term": "Context preservation", "plain": "Every `emit` runs in the collector's coroutine context. Only `flowOn` changes the context of the upstream."},
  {"term": "AbortFlowException", "plain": "The internal CancellationException that `take` and `first` throw through `emit` to stop the producer."}
 ],
 "explain_back": {
  "prompt": "A teammate's settlement job reported success, but one posting is missing from the ledger, and the log has a strange \"Flow exception transparency is violated\" warning. Explain what happened and how you'd change the code.",
  "answer": "The job's flow wraps each emit in a try/catch that logs and goes on. In a flow the collector runs inside emit, so when the ledger refused a posting, that catch caught the ledger's exception. flow { } wraps our collector in a SafeCollector, which remembers that the downstream failed. When the loop tried to emit the next posting, the SafeCollector refused it with an IllegalStateException, and the same catch swallowed that too. So the next posting never reached the ledger, the only trace is the warning, and collect returned normally, which is why the job looked green. The fix is to take the try/catch away from emit. If a refused posting should be skipped, catch the ledger's narrow exception inside the collector, around the post call. If the producer's own parsing can fail, catch around the parse. And I'd count posted plus skipped against the batch size, so a hole fails the job."
 },
 "deeper": {
  "minutes": 10,
  "body": "A few details of `SafeCollector` explain why the checks cost so little.\n\nOn the JVM, `SafeCollector` extends `ContinuationImpl` \"to pretend it *is* a state-machine of its own `emit` method\". That way no state machine is allocated for each element, and its source calls the hot path \"effectively garbage-free\".\n\nThe context check doesn't run on every value. `SafeCollector` remembers the last emission context, and it only compares contexts when that object changed, which on the happy path is once per flow. The transparency check reuses the same mechanism: when the downstream throws, `SafeCollector` stores a special `DownstreamExceptionContext` as the last emission context. The next `emit` then sees a context mismatch and reports it as a transparency violation.\n\nThe full context rule has one more part than the lab's version. The emitting `Job` must reach the collector's `Job` through scope coroutines only, which is why `coroutineScope { emit(1) }` passes and `coroutineScope { launch { emit(1) } }` fails with \"Emission from another coroutine is detected\". Lesson 3 of this track uses that message to motivate `channelFlow`.\n\n`onStart`, `onCompletion` and `onEmpty` are written on `unsafeFlow` like the other operators, but they run your action through a fresh `SafeCollector`, because your action gets a collector it could misuse. The public `transform` is a real `flow { }` for the same reason: the comment in its source says \"safe flow is used here, because collector is exposed to transform on each operation\"."
 },
 "sources": [
  {"title": "flow builder (kotlinx.coroutines API, 1.11.0)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow.html"},
  {"title": "cancellable (kotlinx.coroutines API, 1.11.0)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/cancellable.html"},
  {"title": "SafeCollector.common.kt at tag 1.11.0 (kotlinx.coroutines source)", "url": "https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/internal/SafeCollector.common.kt"},
  {"title": "Limit.kt at tag 1.11.0: take and its abort (kotlinx.coroutines source)", "url": "https://raw.githubusercontent.com/Kotlin/kotlinx.coroutines/1.11.0/kotlinx-coroutines-core/common/src/flow/operators/Limit.kt"},
  {"title": "AbstractFlow (kotlinx.coroutines API, 1.11.0)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-abstract-flow/"}
 ]
}

out = ROOT / "content/lessons/flow-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
