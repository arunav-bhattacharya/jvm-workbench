import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l08"
K = "kotlin/workbench/patterns/l08"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l08.{cls}"


def code(lang, name, cls, alt_lang, alt_name, alt_cls):
    d1 = J if lang == "java" else K
    d2 = J if alt_lang == "java" else K
    return {"lang": lang, "title": name, "src": read(f"{lab}/demo/{d1}/{name}"), "run": demo(cls), "file": f"{lab}/demo/{d1}/{name}",
            "alt": {"lang": alt_lang, "title": alt_name, "src": read(f"{lab}/demo/{d2}/{alt_name}"), "run": demo(alt_cls), "file": f"{lab}/demo/{d2}/{alt_name}"}}


FIG = """<svg viewBox="0 0 680 250" role="img" aria-label="A caller creates a Capture command record. It is either run now, applied and pushed on an undo stack, or stored in an outbox row, Kafka or Temporal history and run later by a worker, possibly twice">
<rect class="box" x="16" y="96" width="104" height="52" rx="8"/>
<text class="t" x="68" y="118" text-anchor="middle">caller</text>
<text class="t-s t-m" x="68" y="137" text-anchor="middle">API, consumer</text>
<rect class="box-a" x="160" y="88" width="180" height="68" rx="8"/>
<text class="t t-code" x="250" y="116" text-anchor="middle">Capture(id, 1250)</text>
<text class="t-s" x="250" y="138" text-anchor="middle">a command is data</text>
<rect class="box" x="384" y="22" width="280" height="60" rx="8"/>
<text class="t" x="524" y="46" text-anchor="middle">run now</text>
<text class="t-s t-m" x="524" y="66" text-anchor="middle">apply, then push on the undo stack</text>
<rect class="box-b" x="384" y="160" width="280" height="60" rx="8"/>
<text class="t" x="524" y="184" text-anchor="middle">store, run later</text>
<text class="t-s t-m" x="524" y="204" text-anchor="middle">outbox row, Kafka, Temporal history</text>
<line class="ln-a" x1="120" y1="122" x2="156" y2="122" marker-end="url(#arr)"/>
<line class="ln" x1="340" y1="108" x2="380" y2="58" marker-end="url(#arr)"/>
<line class="ln" x1="340" y1="138" x2="380" y2="186" marker-end="url(#arr)"/>
<text class="t-s t-bad" x="524" y="240" text-anchor="middle">a stored command can run twice: make it idempotent</text>
</svg>""".replace("\n", "")

S1 = """A posting hits the ledger, and four parts of the service care: the balance view, the receipt email, analytics and fraud scoring. If `post` calls all four directly, the ledger depends on every one of them, and a broken analytics endpoint makes postings fail. **Observer** inverts that. The ledger, the subject, keeps a list of listeners and tells each one what happened. It doesn't know who they are.

```java
final class EventBus<E> {
    private final List<Consumer<? super E>> listeners = new CopyOnWriteArrayList<>();

    AutoCloseable subscribe(Consumer<? super E> listener) {
        listeners.add(listener);
        return () -> listeners.remove(listener);          // the handle that prevents leaks
    }

    void publish(E event) {
        for (Consumer<? super E> l : listeners) {
            try {
                l.accept(event);
            } catch (RuntimeException e) {
                log.warn("listener failed", e);           // one bad listener must not starve the rest
            }
        }
    }
}
```

```kotlin
class EventBus<E> {
    private val listeners = CopyOnWriteArrayList<(E) -> Unit>()

    fun subscribe(listener: (E) -> Unit): AutoCloseable {
        listeners += listener
        return AutoCloseable { listeners -= listener }    // the handle that prevents leaks
    }

    fun publish(event: E) {
        for (l in listeners) {
            try {
                l(event)
            } catch (e: RuntimeException) {
                log.warn("listener failed", e)            // one bad listener must not starve the rest
            }
        }
    }
}
```

No `PaymentListener` interface: `Consumer<E>` in Java and `(E) -> Unit` in Kotlin already say "something that takes an event".

Each line here prevents a real bug. `subscribe` returns a handle, because a listener that is never removed is a **lapsed listener**: the bus holds a reference to it forever, so it can't be garbage collected and keeps reacting to events long after its owner is gone. The `try`/`catch` stops one failing listener from cancelling delivery to the ones after it. `CopyOnWriteArrayList` iterates over a snapshot, so a listener may unsubscribe while it is being called; with an `ArrayList`, that throws `ConcurrentModificationException`. Copy-on-write makes every subscribe expensive and every publish cheap, which fits listener lists.

One property stays, whatever you do: delivery is synchronous. Every listener runs on the publishing thread, inside `post`. A 300 ms email call makes every posting 300 ms slower, and a listener that publishes another event starts a nested round of delivery before the first round is done. Keep in-process listeners fast, and hand slow work to a queue."""

S2 = """Kotlin's coroutine library ships two ready-made subjects. A `SharedFlow` broadcasts every emitted value to every active collector. A `StateFlow` holds one current value: "a state flow is a hot flow", it "never completes", and each collector gets the current value first, then every change. Both are thread-safe, and both do the bookkeeping from the last section for you. There is no listener list to guard. Cancelling the collecting coroutine unsubscribes it, and each collector runs in its own coroutine, so one that fails doesn't stop the others.

```kotlin
class PaymentStatus {
    private val _state = MutableStateFlow("NEW")
    val state: StateFlow<String> = _state.asStateFlow()          // state: the latest value

    private val _events = MutableSharedFlow<String>()
    val events: SharedFlow<String> = _events.asSharedFlow()     // events: every one, to every collector

    suspend fun on(event: String) {
        _events.emit(event)       // with no buffer, waits until every current collector has taken it
        _state.value = event
    }
}
```

```java
// Closest Java equivalent: the JDK's java.util.concurrent.Flow, with SubmissionPublisher as a hot publisher
SubmissionPublisher<String> events = new SubmissionPublisher<>();
CompletableFuture<Void> done = events.consume(e -> System.out.println("got " + e));   // one subscriber
events.submit("AUTHORIZED");
events.submit("AUTHORIZED");          // delivered again: a publisher has no idea of "same as last time"
events.close();                       // completes the stream; done completes after the last item
```

Keep the mutable flow private and expose the read-only type, as above. Use `_state.update { ... }` when the new value depends on the old one, because it is an atomic read-modify-write.

The rule that matters for payments is in the StateFlow docs: values "are conflated using `Any.equals` comparison in a similar way to `distinctUntilChanged`", and "a slow collector skips fast updates". That is exactly right for state. A dashboard showing a payment's status needs only the latest one. It is wrong for events. Two 4.50 coffees on the same card, `Posted("acc-1", 450)` twice, arrive as one, and a slow consumer misses the updates in between. Use a `SharedFlow` for events, or a `Channel` when each item must go to exactly one consumer.

Java has the interfaces but few implementations. `java.util.concurrent.Flow` holds the Reactive Streams types (`Publisher`, `Subscriber`, `Subscription`), and `SubmissionPublisher` is the one hot publisher in the JDK. In Reactor, a `Flux` is the same idea with backpressure, and `Sinks.many().multicast()` plays the role of a `MutableSharedFlow`. None of them drops equal values unless you ask with `distinctUntilChanged()`."""

S3 = """**Command** turns a request into an object: what to do and with which arguments, as a value you can keep. Once a request is a value, you can queue it, log it, retry it and undo it.

For a ledger, a sealed interface of records is the natural shape:

```java
sealed interface Command permits Deposit, Withdraw {
    void apply(Account a);
    void undo(Account a);
}
record Deposit(long amount) implements Command {
    public void apply(Account a) { a.balance += amount; }
    public void undo(Account a)  { a.balance -= amount; }
}
record Withdraw(long amount) implements Command {
    public void apply(Account a) {
        if (a.balance < amount) throw new IllegalStateException("insufficient funds");
        a.balance -= amount;
    }
    public void undo(Account a)  { a.balance += amount; }
}

final class CommandLog {
    private final Deque<Command> history = new ArrayDeque<>();
    void run(Command c, Account a) { c.apply(a); history.push(c); }    // record only after success
    void undoLast(Account a) { Command c = history.poll(); if (c != null) c.undo(a); }
}
```

```kotlin
sealed interface Command {
    fun apply(a: Account)
    fun undo(a: Account)
}
data class Deposit(val amount: Long) : Command {
    override fun apply(a: Account) { a.balance += amount }
    override fun undo(a: Account) { a.balance -= amount }
}
data class Withdraw(val amount: Long) : Command {
    override fun apply(a: Account) {
        check(a.balance >= amount) { "insufficient funds" }
        a.balance -= amount
    }
    override fun undo(a: Account) { a.balance += amount }
}

class CommandLog {
    private val history = ArrayDeque<Command>()
    fun run(c: Command, a: Account) { c.apply(a); history.addFirst(c) }   // record only after success
    fun undoLast(a: Account) { history.removeFirstOrNull()?.undo(a) }
}
```

Two details carry the pattern. First, `run` records the command only after `apply` succeeds. Record it first, and a rejected 1,000.00 withdrawal sits in the history, so the next undo "refunds" money that never left. Second, the commands are data. `Withdraw(amount=30)` prints well, compares by value, and can be serialized and written to a table.

When a command needs no undo and no data, the class disappears. `Runnable`, `Callable` and `() -> Unit` are commands, and `executor.submit(() -> settle(batchId))` hands one to a queue that a worker drains. Keep a named class when you need what a lambda can't give: equality, a readable log line, serialization, or a second method such as `undo`."""

S4 = """Once a command is a record, it can leave the process, and most commands in a payment system do.

The transactional outbox is a queue of commands that survives crashes. In the same database transaction that captures a payment, you insert a row saying "send receipt for payment 7781". A relay reads new rows and publishes them to Kafka, and a consumer executes them. Either both the capture and the command commit, or neither does, so a crash between the two can't lose the receipt.

Temporal is built on the same idea. When a workflow calls a method on an activity stub, the SDK doesn't run your activity there. It records a command to schedule that activity, with its name and arguments, in the workflow's history, and a worker picks it up. If the worker dies, Temporal schedules it again, according to the retry options.

Both deliver at least once. A stored command can run twice: the relay crashed after publishing but before marking the row sent, or the activity finished but its result was lost. So every command that leaves the process must be idempotent. Charge with an idempotency key, and make "send receipt 7781" a no-op the second time.

Undo changes meaning too. In memory, undo puts the old state back. Across systems you can't un-send money. A captured payment is reversed by a new command, a `Refund`, with its own record, its own fees and its own failure modes. Sagas, including Temporal's, are lists of such compensating commands, run in reverse when a later step fails. Model a refund as a compensation, never as `undo` of a charge.

Check yourself. The outbox relay publishes "send receipt for payment 7781" to Kafka, then crashes before it marks the row sent. It restarts. How many receipts does the customer get if the consumer just sends one per message, and what fixes it? (Two, because the relay publishes the row again. The consumer must remember which payment ids it has already sent a receipt for, and skip a repeat.)"""

L = {
 "id": "pat-08",
 "title": "Observer and Command",
 "minutes": 37,
 "goal": "By the end you can write an observer list that can't leak or be broken by one listener, choose SharedFlow for events and StateFlow for state, and model ledger operations as command records with a correct undo, knowing what changes when commands are queued or stored.",
 "warmup": {
  "q": "A Kotlin service exposes payment events as a `MutableStateFlow<Posted>`. A card buys two 4.50 coffees, so `Posted(\"acc-1\", 450)` is set twice in a row. How many of those does a collector see?",
  "options": ["Two", "One", "None", "It depends on the dispatcher"],
  "answer": 1,
  "why": "StateFlow conflates values with `equals`: setting a value equal to the current one does nothing, so the second coffee never reaches collectors. That is right for state (the latest balance) and wrong for events. A `MutableSharedFlow` delivers both."
 },
 "sections": [
  {
   "h": "Observer: tell the listeners, then stay out of their way",
   "body": S1,
   "try": {
    "title": "Break a listener, then remove the safety net",
    "minutes": 4,
    "steps": [
     "Read `EventBusDemo.java` (or `EventBusDemo.kt`). Three listeners subscribe; the second always throws. Predict the five lines it prints.",
     "Run it with the command below.",
     "Delete the `try`/`catch` in `publish`, keeping the `l.accept(event)` (`l(event)` in Kotlin) line. Predict, then run. Put it back."
    ],
    "code": code("java", "EventBusDemo.java", "EventBusDemo", "kotlin", "EventBusDemo.kt", "EventBusDemoKt"),
    "expect": "The ledger view and the email sender both get the 450 posting, with `(a listener failed: analytics dashboard is down)` between them. After `email.close()`, only the ledger view gets the 900 posting. Without the `try`/`catch`, the program prints the first ledger line and dies with `IllegalStateException: analytics dashboard is down`: the email sender never hears anything, and in a service the posting itself would fail."
   },
   "refs": [
    {"title": "CopyOnWriteArrayList (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CopyOnWriteArrayList.html", "kind": "docs"}
   ]
  },
  {
   "h": "Flows are observers with the bookkeeping done",
   "body": S2,
   "try": {
    "title": "Watch StateFlow drop an event",
    "minutes": 5,
    "steps": [
     "Read `StateVsShared.kt` (or the Java twin, `StateVsSharedJava.java`). The same three updates go to a state holder and an event stream. Predict both lines.",
     "Run it with the command below.",
     "Kotlin: change `val events = MutableSharedFlow<String>()` to `val events = MutableStateFlow(\"NEW\")` and run. Java: delete the `if (Objects.equals(value, next)) return;` line and run. Predict each first."
    ],
    "code": code("kotlin", "StateVsShared.kt", "StateVsSharedKt", "java", "StateVsSharedJava.java", "StateVsSharedJava"),
    "expect": "The state side prints `[NEW, AUTHORIZED, CAPTURED]`: the initial value, then only real changes. The event side prints `[AUTHORIZED, AUTHORIZED, CAPTURED]`: every event. With a StateFlow for events, the Kotlin event line becomes `[NEW, AUTHORIZED, CAPTURED]`, so the second authorization is gone and a fake `NEW` event appeared. Without the equality check, the Java state holder prints `[NEW, AUTHORIZED, AUTHORIZED, CAPTURED]`: that one check is the whole difference."
   },
   "refs": [
    {"title": "StateFlow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/", "kind": "docs"},
    {"title": "SubmissionPublisher (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/SubmissionPublisher.html", "kind": "docs"}
   ]
  },
  {
   "h": "Command: a request you can store, queue and undo",
   "body": S3,
   "try": {
    "title": "Record the command too early",
    "minutes": 4,
    "steps": [
     "Run `UndoDemo` in either language and read the three lines.",
     "In `CommandLog.run`, swap the two lines so the command is recorded before it is applied. Predict the history and the balance after one undo, then run.",
     "Swap them back."
    ],
    "code": code("java", "UndoDemo.java", "UndoDemo", "kotlin", "UndoDemo.kt", "UndoDemoKt"),
    "expect": "`rejected: insufficient funds`, then `balance 70` with a history of `Withdraw` 30 and `Deposit` 100, then `after one undo: balance 100`. With the lines swapped, the rejected `Withdraw` of 1,000 sits on top of the history, and the undo puts 1,000 back that never left: `balance 1070`."
   }
  },
  {
   "h": "Commands that leave the process",
   "body": S4,
   "figure": {"svg": FIG, "caption": "A command is data. Run now, it goes on an undo stack; stored, it goes through an outbox, Kafka or Temporal, and may run more than once."}
  }
 ],
 "analogy": "Observer is a newsletter: the publisher sends each issue to whoever is on the list, and every issue carries an unsubscribe link, which is the handle `subscribe` returns. Command is a restaurant order ticket. The waiter writes the order down instead of cooking it, puts it on the rail, and a cook works through the rail in order. A ticket can be voided before it's cooked, which is undo. Once the meal is served you can't un-serve it, so you comp a dessert, which is compensation. The analogy breaks on duplicates. A kitchen never cooks the same ticket twice by accident, but a message queue or a Temporal retry can deliver the same command twice, so the command itself must be safe to run again.",
 "in_your_world": "A Kafka consumer group is a durable observer of a topic: it keeps its position in the log, so it can catch up after a crash, which no in-process listener can. Quarkus has the in-process kind built in through CDI events: `Event<PaymentCaptured>.fire()` on one side and an `@Observes` method on the other. Use those for fast, losable work, such as metrics and cache eviction. Anything that must not be lost, like a receipt, a ledger entry or fraud scoring, goes through an outbox row and Kafka. On the command side, every Temporal activity call is a command recorded in the workflow history and retried by policy, and your capture, refund and payout activities should all take an idempotency key.",
 "mistake": "The most common mistake is using a `StateFlow` (or a \"latest value\" holder) for events. It looks like the obvious hot flow: it's thread-safe, it has a `value`, and the docs example is a counter. Then two identical postings, two equal status updates or two equal webhook notifications arrive in a row, and collectors see one. A slow collector also skips intermediate values, which for a payment can mean never seeing `AUTHORIZED` between `NEW` and `CAPTURED`. The rule: state goes in a `StateFlow` (only the latest value matters), events go in a `SharedFlow` or a `Channel` (each one matters). If a test emits two equal events and expects two, you'll catch it before production does.",
 "compare": {
  "title": "A command queue drained by one worker",
  "java": {"title": "LedgerWorker.java", "src": """sealed interface LedgerCommand permits Deposit, Withdraw, Stop {}
record Deposit(String account, long amountMinor) implements LedgerCommand {}
record Withdraw(String account, long amountMinor) implements LedgerCommand {}
record Stop() implements LedgerCommand {}                       // poison pill: a Java queue can't be closed

final class LedgerWorker implements Runnable {
    private final BlockingQueue<LedgerCommand> queue = new ArrayBlockingQueue<>(1_000);   // bounded: put blocks when full
    private final Map<String, Long> balances = new HashMap<>();  // touched only by the thread running run()

    void submit(LedgerCommand c) throws InterruptedException { queue.put(c); }
    void stop() throws InterruptedException { queue.put(new Stop()); }

    @Override public void run() {
        try {
            while (true) {
                switch (queue.take()) {                          // commands are data: switch on them
                    case Deposit d -> balances.merge(d.account(), d.amountMinor(), Long::sum);
                    case Withdraw w -> balances.merge(w.account(), -w.amountMinor(), Long::sum);
                    case Stop s -> { return; }
                }
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}

// start it after construction, never from the constructor:
// Thread.ofVirtual().start(worker);"""},
  "kotlin": {"title": "LedgerWorker.kt", "src": """sealed interface LedgerCommand {
    data class Deposit(val account: String, val amountMinor: Long) : LedgerCommand
    data class Withdraw(val account: String, val amountMinor: Long) : LedgerCommand
}

class LedgerWorker {
    private val queue = Channel<LedgerCommand>(capacity = 1_000)   // bounded: send suspends when full
    private val balances = mutableMapOf<String, Long>()           // touched only by the coroutine in start()

    fun start(scope: CoroutineScope): Job = scope.launch {
        for (c in queue) {                                        // ends after stop(), once the queue is drained
            when (c) {                                            // commands are data: when on them
                is LedgerCommand.Deposit -> balances.merge(c.account, c.amountMinor) { a, b -> a + b }
                is LedgerCommand.Withdraw -> balances.merge(c.account, -c.amountMinor) { a, b -> a + b }
            }
        }
    }

    suspend fun submit(c: LedgerCommand) = queue.send(c)
    fun stop() = queue.close()                                    // a closed channel is the poison pill
}"""},
  "note": "The shape is the same: commands are sealed data, a bounded queue holds them, and one worker applies them in order, so the balances map needs no lock because only one thread or coroutine ever touches it. Two things differ. A Kotlin `Channel` can be closed, and `for (c in queue)` ends after the last queued command, so the `Stop` poison-pill command that Java needs disappears. And `send` suspends the coroutine when the queue is full, where Java's `put` blocks a thread; with virtual threads that blocking is cheap too, so the real gain is the built-in close. Neither language needs a `Command` class hierarchy with an `execute()` method: a sealed type plus an exhaustive `switch` or `when` in the worker does that job."
 },
 "worked": {
  "title": "Take side effects out of the ledger's post method",
  "steps": [
   {"say": "The ledger's `post` grew one call at a time. Before reading on, list what happens to a posting when the analytics service is down.",
    "code": """void post(Posting p) {
    repository.insert(p);
    balances.add(p.account(), p.amountMinor());
    receipts.send(p);                    // 300 ms SMTP call
    analytics.track(p);                  // throws when the dashboard is down
    fraud.score(p);
}""", "lang": "java",
    "alt_code": """fun post(p: Posting) {
    repository.insert(p)
    balances.add(p.account, p.amountMinor)
    receipts.send(p)                     // 300 ms SMTP call
    analytics.track(p)                   // throws when the dashboard is down
    fraud.score(p)
}""", "alt_lang": "kotlin"},
   {"say": "The posting is already stored, but `post` throws, so the caller retries and may post twice. Fraud scoring is skipped, and every posting waits for SMTP. First split by what the work needs: the insert and the balance are the posting itself; the rest are reactions to it.",
    "code": """void post(Posting p) {
    repository.insert(p);                                  // 1. the posting itself
    balances.add(p.account(), p.amountMinor());
    bus.publish(new Posted(p.account(), p.amountMinor())); // 2. everything else is a reaction
}""", "lang": "java",
    "alt_code": """fun post(p: Posting) {
    repository.insert(p)                                   // 1. the posting itself
    balances.add(p.account, p.amountMinor)
    bus.publish(Posted(p.account, p.amountMinor))          // 2. everything else is a reaction
}""", "alt_lang": "kotlin"},
   {"say": "Wire the reactions in one place at startup. The bus isolates failures, so a broken dashboard costs one log line. Which of these listeners can we afford to lose if the pod dies right after the insert?",
    "code": """bus.subscribe(e -> metrics.increment("ledger.posted"));    // 3. fast and losable: fine in-process
bus.subscribe(e -> analytics.track(e));                    //    a missed event is a dashboard blip
// receipts and fraud scoring are NOT subscribed here: see the next step""", "lang": "java",
    "alt_code": """bus.subscribe { metrics.increment("ledger.posted") }        // 3. fast and losable: fine in-process
bus.subscribe { analytics.track(it) }                      //    a missed event is a dashboard blip
// receipts and fraud scoring are NOT subscribed here: see the next step""", "alt_lang": "kotlin"},
   {"say": "Receipts and fraud scoring must survive a crash, so they become stored commands: outbox rows written in the same transaction as the posting. A relay publishes them to Kafka, and each consumer handles a command at least once, so it must be idempotent.",
    "code": """@Transactional
void post(Posting p) {
    repository.insert(p);
    balances.add(p.account(), p.amountMinor());
    outbox.insert(new OutboxRow("receipt.send", p.id()));   // 4. same transaction: both commit or neither
    outbox.insert(new OutboxRow("fraud.score", p.id()));
    bus.publish(new Posted(p.account(), p.amountMinor()));  // 5. in-process listeners: best effort only
}""", "lang": "java",
    "alt_code": """@Transactional
fun post(p: Posting) {
    repository.insert(p)
    balances.add(p.account, p.amountMinor)
    outbox.insert(OutboxRow("receipt.send", p.id))         // 4. same transaction: both commit or neither
    outbox.insert(OutboxRow("fraud.score", p.id))
    bus.publish(Posted(p.account, p.amountMinor))          // 5. in-process listeners: best effort only
}""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "An observable ledger and an undoable command stack",
  "minutes": 14,
  "files": [f"{lab}/main/{K}/ObservableLedger.kt", f"{lab}/main/{K}/CommandStack.kt"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l08.*'",
  "steps": [
   "Run the tests once: all eight fail.",
   "In `ObservableLedger`, add a private `MutableSharedFlow<Posted>` and a private `MutableStateFlow(0L)`, and replace the two `get() = TODO(...)` getters with read-only views of them (`= _events.asSharedFlow()`, `= _balance.asStateFlow()`).",
   "Write `subscribe` with a list that tolerates removal during iteration, returning an `AutoCloseable` that removes the listener.",
   "Write `post`: update the balance atomically, call each listener inside its own `try`/`catch`, then `emit` the event.",
   "In `CommandStack.kt`, write `apply` and `undo` for `Deposit` and `Withdraw`, then `run`, `undo` and `redo` with two `ArrayDeque`s.",
   "Run the tests until all eight pass."
  ],
  "hints": [
   "`CopyOnWriteArrayList<(Posted) -> Unit>()` gives you snapshot iteration. `AutoCloseable { listeners -= listener }` is the handle.",
   "`_balance.update { it + amountMinor }` is an atomic read-modify-write. A `MutableSharedFlow` with no replay delivers only to collectors that are already collecting, which is what the test sets up.",
   "In `run`, call `cmd.apply(account)` before you touch either deque: if it throws, nothing else runs. `removeFirstOrNull() ?: return false` handles the empty cases in `undo` and `redo`."
  ],
  "done_when": "All eight tests in `ObserverCommandTest` pass."
 },
 "drill": {
  "title": "An event bus from memory",
  "minutes": 5,
  "prompt": "Close this page. Write a generic `EventBus<E>` with `subscribe` and `publish`. It must survive a listener that unsubscribes itself during delivery and a listener that throws, and it must give every subscriber a way to leave. Then compare: which of the three did you miss?",
  "answer": {"lang": "java", "src": """final class EventBus<E> {
    private final List<Consumer<? super E>> listeners = new CopyOnWriteArrayList<>();   // snapshot iteration

    AutoCloseable subscribe(Consumer<? super E> listener) {
        listeners.add(listener);
        return () -> listeners.remove(listener);           // the way to leave
    }

    void publish(E event) {
        for (Consumer<? super E> l : listeners) {
            try {
                l.accept(event);
            } catch (RuntimeException e) {
                // log it; the next listener still runs
            }
        }
    }
}""",
   "alt": {"lang": "kotlin", "title": "Kotlin", "src": """class EventBus<E> {
    private val listeners = CopyOnWriteArrayList<(E) -> Unit>()   // snapshot iteration

    fun subscribe(listener: (E) -> Unit): AutoCloseable {
        listeners += listener
        return AutoCloseable { listeners -= listener }       // the way to leave
    }

    fun publish(event: E) {
        for (l in listeners) {
            try {
                l(event)
            } catch (e: RuntimeException) {
                // log it; the next listener still runs
            }
        }
    }
}"""}}
 },
 "recap": [
  "Observer: the subject keeps a list of listeners and tells each one what happened, without knowing who they are. `Consumer<E>` and `(E) -> Unit` replace listener interfaces.",
  "A safe listener list returns an unsubscribe handle, isolates each listener's failures, and iterates a snapshot (`CopyOnWriteArrayList`). Delivery is still synchronous, so keep listeners fast.",
  "Use a `StateFlow` for state and a `SharedFlow` (or `Channel`) for events: StateFlow drops values equal to the current one, and slow collectors skip updates.",
  "Command turns a request into a value you can queue, log, retry and undo. Sealed records or data classes are the natural shape; `Runnable` and `() -> Unit` are commands without data.",
  "Record a command for undo only after it succeeded.",
  "Stored commands (outbox rows, Kafka messages, Temporal activities) can run twice, so make them idempotent, and reverse money with a compensating command such as `Refund`."
 ],
 "quiz": [
  {"q": "A Kotlin service publishes payment events through a `MutableStateFlow`. The fraud model needs every `Captured` event. What will it miss?",
   "options": ["Nothing: StateFlow delivers every value", "An event equal to the previous one, and events a slow collector didn't get to in time", "Only events emitted before it started collecting, like any hot flow", "Events emitted from another thread"],
   "answer": 1,
   "why": "StateFlow conflates by `equals`, so an event equal to the current value is never delivered, and a collector that falls behind only sees the latest value. Missing events from before you started collecting is true of a replay-0 SharedFlow too, but it isn't what makes StateFlow wrong here. StateFlow is thread-safe, so threads don't matter."},
  {"q": "A `CommandLog.run` pushes the command onto the history first and then applies it. The balance is 70. `Withdraw(1000)` fails with \"insufficient funds\". The user presses undo once. What is the balance?",
   "options": ["70", "40", "1,070", "1,000"],
   "answer": 2,
   "why": "The failed withdrawal was recorded before it threw, so it's on top of the history. Undoing it adds 1,000 that never left: 70 + 1,000 = 1,070. Recording only after `apply` succeeds keeps undo honest."},
  {"q": "A request-scoped object subscribes a listener to a singleton `EventBus` in its constructor and never closes the handle. What happens over a day of traffic?",
   "options": ["Memory grows, and every old request object keeps reacting to events", "Nothing: listeners are removed when the request ends", "The bus throws once it has too many listeners", "The listeners stop receiving events after a garbage collection"],
   "answer": 0,
   "why": "The singleton's list holds a strong reference to each listener, and each listener's lambda captures its request object, so none of them can be collected, and all of them keep running on every event. That is the lapsed-listener leak. Return a handle from `subscribe` and close it when the owner's life ends."},
  {"q": "Fraud scoring must see every ledger posting, even if the pod crashes a millisecond after the posting commits. Which design fits?",
   "options": ["An in-process `EventBus` listener", "A `StateFlow` the scorer collects", "A `MutableSharedFlow` with `replay = 1`", "An outbox row written in the posting's transaction and relayed to Kafka"],
   "answer": 3,
   "why": "Anything in memory dies with the pod, so the in-process bus and both flows lose events written just before a crash. An outbox row commits with the posting or not at all, and the relay delivers it at least once, so the scorer must be idempotent."},
  {"q": "From *StateFlow, SharedFlow and hot streams*: a `MutableSharedFlow<Posted>()` (no replay, no buffer) emits three postings, and only then does a new collector start. What does the new collector see?",
   "options": ["All three postings", "None of the three; only postings emitted after it starts", "Only the last posting", "The first posting, then it waits"],
   "answer": 1,
   "why": "A SharedFlow with `replay = 0` keeps nothing for late subscribers: each emission goes to the collectors present at that moment. A StateFlow would hand the newcomer the latest value, and `replay = 1` would replay the last posting.",
   "from": "co-08"}
 ],
 "flashcards": [
  {"front": "Why should `subscribe` return an `AutoCloseable` (or similar handle)?", "back": "So the subscriber can leave. A forgotten listener stays referenced by the subject forever: the lapsed-listener leak."},
  {"front": "Why use `CopyOnWriteArrayList` for a listener list?", "back": "It iterates over a snapshot, so a listener can unsubscribe during delivery without a `ConcurrentModificationException`. Writes are rare, reads are constant."},
  {"front": "What does a `publish` loop need around each listener call?", "back": "A try/catch, so one throwing listener doesn't stop delivery to the others or fail the publisher."},
  {"front": "StateFlow or SharedFlow for payment events?", "back": "SharedFlow (or a Channel). StateFlow drops values equal to the current one, and slow collectors skip updates."},
  {"front": "When does a command go on the undo history?", "back": "Only after `apply` succeeds. Recorded earlier, a failed command gets \"undone\" and corrupts the state."},
  {"front": "Is a refund the undo of a charge?", "back": "No. Money that moved can't be un-sent; a refund is a new compensating command with its own record and fees."},
  {"front": "Why must a command stored in an outbox or Temporal be idempotent?", "back": "Delivery is at least once: a crash or a lost result can make it run twice."}
 ],
 "terms": [
  {"term": "Observer", "plain": "A subject keeps a list of listeners and notifies each one when something happens."},
  {"term": "Lapsed listener", "plain": "A listener nobody removed: it leaks memory and keeps reacting after its owner is gone."},
  {"term": "Hot flow", "plain": "A flow that exists and emits whether or not anyone collects, such as SharedFlow and StateFlow."},
  {"term": "Conflation", "plain": "Keeping only the latest value and dropping ones a collector didn't get to, or equal repeats."},
  {"term": "Command", "plain": "A request turned into a value: what to do, with which arguments, ready to store or queue."},
  {"term": "Compensation", "plain": "A new action that reverses the effect of an earlier one, such as a refund for a capture."},
  {"term": "Transactional outbox", "plain": "A table of outgoing messages written in the same transaction as the state change, then relayed."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why the ledger's `balance` is a `StateFlow` but its `events` are a `SharedFlow`, using two 4.50 coffee purchases on the same card as your example.",
  "answer": "The balance is state: whoever looks at it only needs the latest number. If it goes from 0 to 450 to 900 faster than a dashboard redraws, showing 900 is correct, and if a posting left it unchanged there's nothing new to tell anyone. StateFlow does exactly that: it keeps the current value, gives it to new collectors right away, and drops repeats and intermediate values. The events are different, because each one is a fact someone must act on. Two coffees produce two equal `Posted(\"acc-1\", 450)` events. A StateFlow would treat the second as \"no change\" and drop it, so the receipt service would send one receipt and fraud scoring would see one purchase. A SharedFlow delivers every emitted value to every collector, so both coffees arrive."
 },
 "deeper": {
  "minutes": 10,
  "body": """`StateFlow` is a special case of `SharedFlow`. Its docs describe it as a `MutableSharedFlow(replay = 1, onBufferOverflow = BufferOverflow.DROP_OLDEST)` combined with `distinctUntilChanged()`. Knowing the knobs helps when neither default fits. `replay` sets how many past values a new collector gets. `extraBufferCapacity` lets `emit` run ahead of slow collectors without suspending. `onBufferOverflow` decides what happens when that buffer is full: suspend the emitter, drop the oldest value or drop the newest. For payment events, the default (suspend) is the safe choice, because dropping is silent.

Kotlin also has an observer for a single property: `var status by Delegates.observable("NEW") { _, old, new -> log(\"$old -> $new\") }` calls the handler after every assignment, and `Delegates.vetoable` runs before the assignment and can reject it. They are handy for in-object state, and they are synchronous, like a hand-rolled listener list.

Java has a history here. `java.util.Observable` and `java.util.Observer` shipped in Java 1.0 and were deprecated in Java 9. `Observable` is a class you must extend, its notification order is unspecified, and it isn't a good fit for concurrent code. Use a `Consumer` list, `SubmissionPublisher` or a reactive library instead.

Undo for operations that can't be inverted, such as \"apply discount rules\" or \"reformat the draft\", doesn't fit the `apply`/`undo` pair. There, save a snapshot of the state before the command and restore it on undo. That is the Memento pattern, in lesson 10 of this track, *Visitor, Iterator, Mediator and Memento*."""
 },
 "sources": [
  {"title": "StateFlow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/"},
  {"title": "Delegated properties: observable (Kotlin docs)", "url": "https://kotlinlang.org/docs/delegated-properties.html"},
  {"title": "Flow.java at jdk-25-ga (Reactive Streams interfaces)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/Flow.java"},
  {"title": "Channels (Kotlin docs)", "url": "https://kotlinlang.org/docs/channels.html"},
  {"title": "Reactor core README", "url": "https://raw.githubusercontent.com/reactor/reactor-core/main/README.md"}
 ]
}

out = ROOT / "content/lessons/pat-08.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
