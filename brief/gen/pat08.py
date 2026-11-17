import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l08"
K = "kotlin/workbench/patterns/l08"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l08.{cls}"


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def pair_kj(kotlin, java):
    """A Kotlin fence first, then its Java twin (the site still shows Java first)."""
    return f"```kotlin\n{kotlin}\n```\n\n```java\n{java}\n```"


def code(lang, name, cls, alt_lang, alt_name, alt_cls):
    d1 = J if lang == "java" else K
    d2 = J if alt_lang == "java" else K
    return {"lang": lang, "title": name, "src": read(f"{lab}/demo/{d1}/{name}"), "run": demo(cls), "file": f"{lab}/demo/{d1}/{name}",
            "alt": {"lang": alt_lang, "title": alt_name, "src": read(f"{lab}/demo/{d2}/{alt_name}"), "run": demo(alt_cls), "file": f"{lab}/demo/{d2}/{alt_name}"}}


FIG = """<svg viewBox="0 0 680 250" role="img" aria-label="A caller creates a Sell command record. It is either run now, applied and pushed on an undo stack, or stored in a file, a table or another program and run later, possibly twice">
<rect class="box" x="16" y="96" width="104" height="52" rx="8"/>
<text class="t" x="68" y="118" text-anchor="middle">caller</text>
<text class="t-s t-m" x="68" y="137" text-anchor="middle">the counter</text>
<rect class="box-a" x="160" y="88" width="180" height="68" rx="8"/>
<text class="t t-code" x="250" y="116" text-anchor="middle">Sell(5)</text>
<text class="t-s" x="250" y="138" text-anchor="middle">a command is data</text>
<rect class="box" x="384" y="22" width="280" height="60" rx="8"/>
<text class="t" x="524" y="46" text-anchor="middle">run now</text>
<text class="t-s t-m" x="524" y="66" text-anchor="middle">apply, then push on the undo stack</text>
<rect class="box-b" x="384" y="160" width="280" height="60" rx="8"/>
<text class="t" x="524" y="184" text-anchor="middle">store, run later</text>
<text class="t-s t-m" x="524" y="204" text-anchor="middle">a file, a table, another program</text>
<line class="ln-a" x1="120" y1="122" x2="156" y2="122" marker-end="url(#arr)"/>
<line class="ln" x1="340" y1="108" x2="380" y2="58" marker-end="url(#arr)"/>
<line class="ln" x1="340" y1="138" x2="380" y2="186" marker-end="url(#arr)"/>
<text class="t-s t-bad" x="524" y="240" text-anchor="middle">a stored command can run twice: make it safe to repeat</text>
</svg>""".replace("\n", "")

OPENING = """By the corner shop's door hangs a sign-up sheet: "ring me when the fresh bread arrives". When the bread van comes, the shopkeeper rings every name on it. The van doesn't know who signed up, and anyone can cross their name off. Behind the counter, order slips wait on a spike, a metal pin for paper. Each slip says what to do, such as "restock rye bread, 12 loaves", and it can wait, be done, be crossed out or be done again.

The shop's program needs both. When an order arrives, the stock view, the confirmation email and the sales chart all want to hear about it. And a change to a shelf should be something you can keep, undo and replay. The easy traps are a listener nobody removes, a broken chart that stops the email, and a slip written into the undo history before it was done.

Last lesson, we passed one decision in as a function. In this lesson, we'll tell many listeners what happened (Observer), let Kotlin's flows keep the list for us, and turn a request into a value (Command). Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_BUS = """final class EventBus<E> {
    private final List<Consumer<? super E>> listeners = new CopyOnWriteArrayList<>();

    AutoCloseable subscribe(Consumer<? super E> listener) {
        listeners.add(listener);
        return () -> listeners.remove(listener);          // the handle: a way to leave
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
}"""
K_BUS = """class EventBus<E> {
    private val listeners = CopyOnWriteArrayList<(E) -> Unit>()

    fun subscribe(listener: (E) -> Unit): AutoCloseable {
        listeners += listener
        return AutoCloseable { listeners -= listener }    // the handle: a way to leave
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
}"""

S0 = """An order arrives at the corner shop, and several parts of the program care. The stock view shows what's left on the shelves, the confirmation email tells the customer, and the sales chart in the back office counts the day's orders. If `place` calls all three directly, the order code depends on every one of them. A broken chart then makes orders fail, and adding a fourth part means editing `place` again.

**Observer** turns that around. The object that knows what happened, called the **subject**, keeps a list of **listeners** and tells each one, without knowing who they are. It's the sign-up sheet by the shop door: when the bread arrives, the shopkeeper rings every name on it. Anyone can add a name, and anyone can cross theirs off.

Here is a small subject that any part of the program can use. It's called an event bus, because it carries events, values that say what happened, to everyone who subscribed:

""" + pair(J_BUS, K_BUS) + """

There is no `OrderListener` interface. `Consumer<E>` in Java and `(E) -> Unit` in Kotlin already say "something that takes an event".

Each line prevents a real bug. `subscribe` returns a handle, because a listener nobody removes is a **lapsed listener**. The bus holds a reference to it forever, so the garbage collector, the part of the JVM that frees objects nobody uses, can't free it. It keeps reacting long after its owner is gone.

The `try`/`catch` stops one failing listener from cancelling delivery to the ones after it. `EventBusDemo`, in the Try it, subscribes three listeners, and the second one always throws:

```text
stock view got   Ordered[customer=Ana, item=rye bread]
  (a listener failed: the sales chart is down)
email sender got Ordered[customer=Ana, item=rye bread]
```

Delete the `try`/`catch` and the program stops after the first line, with `IllegalStateException: the sales chart is down`. The email sender never hears a thing, and in the real shop the order itself would fail.

`CopyOnWriteArrayList` loops over a snapshot, a copy of the list taken when the loop starts, so a listener may unsubscribe while it's being called. With an `ArrayList`, that throws `ConcurrentModificationException`. Copy-on-write makes every subscribe expensive and every publish cheap, which suits listener lists: people sign up rarely, and the bell rings all day.

The sign-up sheet picture breaks in two places. The shopkeeper rings one number at a time and waits on each call, and so does `publish`: every listener runs on the publishing thread, inside `place`. A 300 ms email makes every order 300 ms slower. And a customer who moved away stops answering, but a listener nobody removed answers forever.

**Give every listener a way out, and never let one listener break the others.**

Keeping that list safe took care. Kotlin's coroutine library ships subjects that do the bookkeeping for us."""

# ---------------------------------------------------------------- section 1
K_FLOW = """class Counter {
    private val _lastSold = MutableStateFlow("nothing yet")
    val lastSold: StateFlow<String> = _lastSold.asStateFlow()      // state: the latest value

    private val _sales = MutableSharedFlow<String>()
    val sales: SharedFlow<String> = _sales.asSharedFlow()          // events: every one, to every collector

    suspend fun sell(item: String) {
        _sales.emit(item)       // with no buffer, waits until every current collector has taken it
        _lastSold.value = item
    }
}"""
J_FLOW = """// Closest Java equivalent: the JDK's java.util.concurrent.Flow, with SubmissionPublisher as a hot publisher
SubmissionPublisher<String> sales = new SubmissionPublisher<>();
CompletableFuture<Void> done = sales.consume(item -> System.out.println("sold " + item));   // one subscriber
sales.submit("rye bread");
sales.submit("rye bread");          // delivered again: a publisher has no idea of "same as last time"
sales.close();                      // ends the stream; done completes after the last item"""

S1 = """A **coroutine** is a Kotlin task that can pause while it waits without holding on to a thread, and a **flow** is a stream of values that a coroutine collects one by one. The coroutine library ships two ready-made subjects, and both are **hot**: they emit whether or not anyone is collecting. A `SharedFlow` hands every emitted value to every active collector. A `StateFlow` holds one current value. Its docs call it "a hot flow" that "never completes", and each new collector gets the current value first, then every change.

Both are thread-safe, and both do the last section's bookkeeping for you. There is no list to guard. Cancelling the collecting coroutine unsubscribes it, and each collector runs in its own coroutine, so one that fails doesn't stop the others:

""" + pair_kj(K_FLOW, J_FLOW) + """

Keep the mutable flow private and expose the read-only type, as above. When the new value depends on the old one, use `update`, as in `_itemsToday.update { it + quantity }` in the lab, because it reads and writes in one atomic step.

The rule that matters most is in the StateFlow docs: values "are conflated using `Any.equals` comparison in a similar way to `distinctUntilChanged`", and "a slow collector skips fast updates". **Conflation** means keeping only the latest value. A StateFlow is the chalkboard by the counter that shows the last thing sold. Whoever glances at it sees the latest, and writing "rye bread" over "rye bread" changes nothing. `StateVsShared`, in the Try it, sells two loaves and a jar of jam:

```text
StateFlow collector saw:  [nothing yet, rye bread, jam]
SharedFlow collector saw: [rye bread, rye bread, jam]
```

That's right for state. A screen showing the last sale needs only the latest one. It's wrong for events. Ana orders a rye loaf, and ten minutes later she orders another, so `Ordered("Ana", "rye bread", 1)` arrives twice. A StateFlow passes on one of them, and the bakery bakes one loaf. A slow collector also misses the values in between.

**State goes in a StateFlow. Events, where each one counts, go in a SharedFlow.**

Use a `Channel` instead when each item must go to exactly one consumer, like a queue of jobs. Java has the interfaces but few implementations. `java.util.concurrent.Flow` holds the Reactive Streams interfaces, a shared standard for streams of events (`Publisher`, `Subscriber`, `Subscription`), and `SubmissionPublisher` is the one hot publisher in the JDK. Reactor, a library for streams of events, has the same idea in its `Flux`, and `Sinks.many().multicast()` plays the role of a `MutableSharedFlow`. None of them drops equal values unless you ask with `distinctUntilChanged()`.

An event says what happened. The next pattern turns what we want to happen into a value."""

# ---------------------------------------------------------------- section 2
J_CMD = """sealed interface Command permits Restock, Sell {
    void apply(Shelf s);
    void undo(Shelf s);
}
record Restock(int units) implements Command {
    public void apply(Shelf s) { s.units += units; }
    public void undo(Shelf s)  { s.units -= units; }
}
record Sell(int units) implements Command {
    public void apply(Shelf s) {
        if (s.units < units) throw new IllegalStateException("not enough on the shelf");
        s.units -= units;
    }
    public void undo(Shelf s)  { s.units += units; }
}

final class CommandLog {
    private final Deque<Command> history = new ArrayDeque<>();
    void run(Command c, Shelf s) { c.apply(s); history.push(c); }       // record only after success
    void undoLast(Shelf s) { Command c = history.poll(); if (c != null) c.undo(s); }
}"""
K_CMD = """sealed interface Command {
    fun apply(s: Shelf)
    fun undo(s: Shelf)
}
data class Restock(val units: Int) : Command {
    override fun apply(s: Shelf) { s.units += units }
    override fun undo(s: Shelf) { s.units -= units }
}
data class Sell(val units: Int) : Command {
    override fun apply(s: Shelf) {
        check(s.units >= units) { "not enough on the shelf" }
        s.units -= units
    }
    override fun undo(s: Shelf) { s.units += units }
}

class CommandLog {
    private val history = ArrayDeque<Command>()
    fun run(c: Command, s: Shelf) { c.apply(s); history.addFirst(c) }   // record only after success
    fun undoLast(s: Shelf) { history.removeFirstOrNull()?.undo(s) }
}"""

S2 = """Back behind the counter, the spike holds order slips. Each slip says what to do and with what: "restock rye bread, 12 loaves". A slip can wait on the spike, be done now, be crossed out, or be copied and done again. **Command** turns a request into that kind of slip: an object that holds what to do and with which arguments, a value you can keep. Once a request is a value, you can queue it, log it, retry it and undo it.

For a shelf in the shop, a sealed interface of records is the natural shape:

""" + pair(J_CMD, K_CMD) + """

Two details carry the pattern. First, `run` records the command only after `apply` succeeds. `UndoDemo`, in the Try it, restocks 12 loaves, sells 5, and then tries to sell 40:

```text
rejected: not enough on the shelf
units 7, history [Sell[units=5], Restock[units=12]]
after one undo: units 12, history [Restock[units=12]]
```

Swap the two calls in `run`, so the command is recorded before it's applied, and the rejected sale of 40 sits on top of the history. The next undo puts back 40 loaves that never left, and the shelf shows 47. The baker will want to know where they came from.

Second, the commands are data. `Sell[units=5]` prints well, compares by value, and can be written to a file or a table and read back later.

The slip picture holds up well, and it breaks where the paper ends. Crossing out a slip is easy. Crossing out a sale is only safe while everything stays inside the program; the next section shows why.

**Record a command for undo only after it has succeeded.**

When a command needs no undo and no data, the class disappears. `Runnable`, `Callable` and `() -> Unit` are commands, and `executor.submit(() -> printLabel(orderNo))` hands one to an executor, the JDK's pool of worker threads, which works through its queue. Keep a named class when you need what a lambda can't give: equality, a readable log line, a way to store it, or a second method such as `undo`."""

# ---------------------------------------------------------------- section 3
S3 = """Once a command is a record, it can leave the program: written to a file, saved as a row in a database table, or sent to another program that runs it later. Picture the shop's program saving the slip "tell the bakery: 2 rye loaves for order 7781" in the same database write that saves the order. A database **transaction** is a group of writes that are all saved or all thrown away, so either the order and the slip are both saved, or neither is. A separate job reads new slips and sends them on, and a crash between the two can't lose the bakery's slip.

Stored slips bring two new rules. The first is about duplicates. A stored command is delivered **at least once**, never exactly once. The job might send the slip and crash before it marks the slip as sent; when it restarts, it sends it again. So every command that leaves the program must be safe to run twice. The bakery keeps the order numbers it has already baked for and skips a repeat, as the warehouse did with order numbers in *Decorator and Proxy*.

The second rule is about undo. Inside the program, undo puts the old state back. Across programs, you can't put a delivered parcel back on the shelf by popping a stack. You send a new command, a collection slip, with its own record, its own courier and its own ways to fail. A new command that reverses an earlier one is called a **compensation**. When a later step of a long job fails, you run the compensations for the earlier steps, in reverse order.

**A command that leaves the program must be safe to run twice. Reverse it with a new command, never with undo.**

The figure shows the two paths: run now, with undo on a stack, or stored and run later, perhaps twice.

Check yourself. The job sends "tell the bakery: 2 rye loaves for order 7781", then crashes before it marks the slip as sent. It restarts. How many loaves does the bakery bake if it bakes whatever each slip says, and what fixes it? (Four: the job sends the slip again, and the bakery bakes it twice. The bakery must remember which order numbers it has already baked for, and skip a repeat.)"""

ASIDE = {
 "title": "Is this what message queues do?",
 "body": "Yes, at a larger scale. Real services often keep outgoing commands in a database table written in the same transaction as the change itself, a layout known as the transactional outbox. A relay program then copies them to a message queue, a separate server that holds messages until other programs take them, such as Kafka or RabbitMQ. Workflow engines such as Temporal record each step of a long job as a command in a history, and run it again if the worker running it dies. All of them deliver at least once, so the rules from this section apply unchanged: make each command safe to repeat, and reverse finished work with a compensation."
}

L = {
 "id": "pat-08",
 "title": "Observer and Command",
 "minutes": 37,
 "goal": "By the end you can write a listener list that can't leak or be broken by one listener, choose SharedFlow for events and StateFlow for state, and model shelf changes as command records with a correct undo, knowing what changes when commands are stored and run later.",
 "opening": OPENING,
 "warmup": {
  "q": "A Kotlin program publishes each order through a `MutableStateFlow<Ordered>`. Ana orders a rye loaf and, a little later, another one, so `Ordered(\"Ana\", \"rye bread\", 1)` is set twice in a row. How many of those does a collector see?",
  "options": ["Two", "One", "None", "It depends on which thread the collector runs on"],
  "answer": 1,
  "why": "StateFlow conflates values with `equals`: setting a value equal to the current one does nothing, so the second loaf never reaches collectors. That is right for state, such as the latest count, and wrong for events, where each one counts. A `MutableSharedFlow` delivers both. The second section's Try it shows the two side by side."
 },
 "sections": [
  {
   "h": "Observer: tell everyone who signed up, then stay out of the way",
   "body": S0,
   "try": {
    "title": "Break a listener, then remove the safety net",
    "minutes": 4,
    "steps": [
     "Read `EventBusDemo.java` (or `EventBusDemo.kt`). Three listeners subscribe; the second always throws. Predict the five lines it prints.",
     "Run it with the command below.",
     "Delete the `try`/`catch` in `publish`, keeping the `l.accept(event)` (`l(event)` in Kotlin) line. Predict, then run. Put it back."
    ],
    "code": code("java", "EventBusDemo.java", "EventBusDemo", "kotlin", "EventBusDemo.kt", "EventBusDemoKt"),
    "expect": "The stock view and the email sender both get Ana's order, with `(a listener failed: the sales chart is down)` between them. After `email.close()`, only the stock view gets Ben's order, followed by the chart's failure again. Without the `try`/`catch`, the program prints the first stock line and stops with `IllegalStateException: the sales chart is down`: the email sender never hears anything, and in the real shop the order itself would fail."
   },
   "refs": [
    {"title": "CopyOnWriteArrayList (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CopyOnWriteArrayList.html", "kind": "docs"}
   ]
  },
  {
   "h": "Flows are observers with the bookkeeping done",
   "body": S1,
   "try": {
    "title": "Watch StateFlow drop a sale",
    "minutes": 5,
    "steps": [
     "Read `StateVsShared.kt` (or the Java twin, `StateVsSharedJava.java`). The same three sales go to a state holder and an event stream. Predict both lines.",
     "Run it with the command below.",
     "Kotlin: change `val events = MutableSharedFlow<String>()` to `val events = MutableStateFlow(\"nothing yet\")` and run. Java: delete the `if (Objects.equals(value, next)) return;` line and run. Predict each first."
    ],
    "code": code("kotlin", "StateVsShared.kt", "StateVsSharedKt", "java", "StateVsSharedJava.java", "StateVsSharedJava"),
    "expect": "The state side prints `[nothing yet, rye bread, jam]`: the starting value, then only real changes. The event side prints `[rye bread, rye bread, jam]`: every sale. With a StateFlow for events, the Kotlin event line becomes `[nothing yet, rye bread, jam]`, so the second loaf is gone and a sale of \"nothing yet\" appeared. Without the equality check, the Java state holder prints `[nothing yet, rye bread, rye bread, jam]`: that one check is the whole difference."
   },
   "refs": [
    {"title": "StateFlow (kotlinx.coroutines API)", "url": "https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/", "kind": "docs"},
    {"title": "SubmissionPublisher (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/SubmissionPublisher.html", "kind": "docs"}
   ]
  },
  {
   "h": "Command: a request on a slip you can keep, undo and replay",
   "body": S2,
   "try": {
    "title": "Record the command too early",
    "minutes": 4,
    "steps": [
     "Run `UndoDemo` in either language and read the three lines.",
     "In `CommandLog.run`, swap the two lines so the command is recorded before it is applied. Predict the history and the units after one undo, then run.",
     "Swap them back."
    ],
    "code": code("java", "UndoDemo.java", "UndoDemo", "kotlin", "UndoDemo.kt", "UndoDemoKt"),
    "expect": "`rejected: not enough on the shelf`, then `units 7` with a history of `Sell` 5 and `Restock` 12, then `after one undo: units 12`. With the lines swapped, the rejected `Sell` of 40 sits on top of the history, and the undo puts back 40 loaves that never left: `after one undo: units 47`."
   }
  },
  {
   "h": "Commands that leave the program",
   "body": S3,
   "figure": {"svg": FIG, "caption": "A command is data. Run now, it goes on an undo stack; stored, it goes to a file, a table or another program, and may run more than once."},
   "aside": ASIDE
  }
 ],
 "compare": {
  "title": "A command queue worked through by one worker",
  "java": {"title": "StockWorker.java", "src": """sealed interface StockCommand permits Restock, Sell, Stop {}
record Restock(String item, int units) implements StockCommand {}
record Sell(String item, int units) implements StockCommand {}
record Stop() implements StockCommand {}                        // a "poison pill": a Java queue can't be closed

final class StockWorker implements Runnable {
    private final BlockingQueue<StockCommand> queue = new ArrayBlockingQueue<>(1_000);   // bounded: put waits when full
    private final Map<String, Integer> shelves = new HashMap<>();   // touched only by the thread running run()

    void submit(StockCommand c) throws InterruptedException { queue.put(c); }
    void stop() throws InterruptedException { queue.put(new Stop()); }

    @Override public void run() {
        try {
            while (true) {
                switch (queue.take()) {                          // commands are data: switch on them
                    case Restock r -> shelves.merge(r.item(), r.units(), Integer::sum);
                    case Sell s -> shelves.merge(s.item(), -s.units(), Integer::sum);
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
  "kotlin": {"title": "StockWorker.kt", "src": """sealed interface StockCommand {
    data class Restock(val item: String, val units: Int) : StockCommand
    data class Sell(val item: String, val units: Int) : StockCommand
}

class StockWorker {
    private val queue = Channel<StockCommand>(capacity = 1_000)     // bounded: send pauses when full
    private val shelves = mutableMapOf<String, Int>()               // touched only by the coroutine in start()

    fun start(scope: CoroutineScope): Job = scope.launch {
        for (c in queue) {                                          // ends after stop(), once the queue is empty
            when (c) {                                              // commands are data: when on them
                is StockCommand.Restock -> shelves.merge(c.item, c.units) { a, b -> a + b }
                is StockCommand.Sell -> shelves.merge(c.item, -c.units) { a, b -> a + b }
            }
        }
    }

    suspend fun submit(c: StockCommand) = queue.send(c)
    fun stop() = queue.close()                                      // a closed channel is the poison pill
}"""},
  "note": "The shape is the same: commands are sealed data, a bounded queue holds them, and one worker applies them in turn, so the shelves map needs no lock because only one thread or coroutine ever touches it. Two things differ. A Kotlin `Channel` can be closed, and `for (c in queue)` ends after the last queued command, so the `Stop` command that Java needs as a poison pill (a special item that tells the worker to finish) disappears. And `send` pauses the coroutine when the queue is full, where Java's `put` blocks a thread; with virtual threads that blocking is cheap too, so the real gain is the built-in close. Neither language needs a `Command` class hierarchy with an `execute()` method: a sealed type plus an exhaustive `switch` or `when` in the worker does that job."
 },
 "worked": {
  "title": "Take the side effects out of the order desk's place method",
  "steps": [
   {"say": "The order desk's `place` grew one call at a time. Before reading on, list what happens to an order when the sales chart is down.",
    "code": """void place(Order o) {
    orderBook.write(o);
    stock.reserve(o.item(), o.quantity());
    email.sendConfirmation(o);             // a 300 ms call to the mail server
    salesChart.count(o);                   // throws when the chart is down
    bakery.bake(o.item(), o.quantity());
}""", "lang": "java",
    "alt_code": """fun place(o: Order) {
    orderBook.write(o)
    stock.reserve(o.item, o.quantity)
    email.sendConfirmation(o)              // a 300 ms call to the mail server
    salesChart.count(o)                    // throws when the chart is down
    bakery.bake(o.item, o.quantity)
}""", "alt_lang": "kotlin"},
   {"say": "The order is already written down, but `place` throws, so the website tries again and may place it twice. The bakery is never told, and every order waits for the mail server. First split the work by what it is: writing the order and reserving the stock are the order itself; the rest are reactions to it.",
    "code": """void place(Order o) {
    orderBook.write(o);                                         // 1. the order itself
    stock.reserve(o.item(), o.quantity());
    bus.publish(new Ordered(o.customer(), o.item(), o.quantity()));   // 2. everything else is a reaction
}""", "lang": "java",
    "alt_code": """fun place(o: Order) {
    orderBook.write(o)                                          // 1. the order itself
    stock.reserve(o.item, o.quantity)
    bus.publish(Ordered(o.customer, o.item, o.quantity))        // 2. everything else is a reaction
}""", "alt_lang": "kotlin"},
   {"say": "Wire the reactions in one place, when the program starts. The bus keeps failures apart, so a broken chart costs one log line. Which of these listeners can we afford to lose if the program crashes right after the order is written?",
    "code": """bus.subscribe(e -> stockView.refresh());             // 3. fast and losable: fine as listeners
bus.subscribe(e -> salesChart.count(e));             //    a missed order is a blip on a chart
// the email and the bakery are NOT subscribed here: see the next step""", "lang": "java",
    "alt_code": """bus.subscribe { stockView.refresh() }                // 3. fast and losable: fine as listeners
bus.subscribe { salesChart.count(it) }               //    a missed order is a blip on a chart
// the email and the bakery are NOT subscribed here: see the next step""", "alt_lang": "kotlin"},
   {"say": "The bakery's slip and the confirmation email must survive a crash, so they become stored commands, saved in the same transaction as the order. A separate job sends them on, at least once, so the bakery and the mailer must each skip a slip they've already handled.",
    "code": """void place(Order o) {
    db.inTransaction(() -> {                                    // 4. all saved, or none
        orderBook.write(o);
        stock.reserve(o.item(), o.quantity());
        slips.save(new Slip("bakery.bake", o.orderNo()));
        slips.save(new Slip("email.confirm", o.orderNo()));
    });
    bus.publish(new Ordered(o.customer(), o.item(), o.quantity()));   // 5. listeners: best effort only
}""", "lang": "java",
    "alt_code": """fun place(o: Order) {
    db.inTransaction {                                          // 4. all saved, or none
        orderBook.write(o)
        stock.reserve(o.item, o.quantity)
        slips.save(Slip("bakery.bake", o.orderNo))
        slips.save(Slip("email.confirm", o.orderNo))
    }
    bus.publish(Ordered(o.customer, o.item, o.quantity))        // 5. listeners: best effort only
}""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "Observable orders and an undoable shelf",
  "minutes": 14,
  "files": [f"{lab}/main/{K}/ObservableOrders.kt", f"{lab}/main/{K}/CommandStack.kt"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l08.*'",
  "steps": [
   "Run the tests once: all eight fail.",
   "In `ObservableOrders`, add a private `MutableSharedFlow<Ordered>` and a private `MutableStateFlow(0)`, and replace the two `get() = TODO(...)` getters with read-only views of them (`= _events.asSharedFlow()`, `= _itemsToday.asStateFlow()`).",
   "Write `subscribe` with a list that tolerates removal while it's being looped over, returning an `AutoCloseable` that removes the listener.",
   "Write `place`: add the quantity to the count atomically, call each listener inside its own `try`/`catch`, then `emit` the event.",
   "In `CommandStack.kt`, write `apply` and `undo` for `Restock` and `Sell`, then `run`, `undo` and `redo` with two `ArrayDeque`s.",
   "Run the tests until all eight pass."
  ],
  "hints": [
   "`CopyOnWriteArrayList<(Ordered) -> Unit>()` gives you snapshot loops. `AutoCloseable { listeners -= listener }` is the handle.",
   "`_itemsToday.update { it + quantity }` reads and writes in one atomic step. A `MutableSharedFlow` with no replay delivers only to collectors that are already collecting, which is what the test sets up.",
   "In `run`, call `cmd.apply(shelf)` before you touch either deque: if it throws, nothing else runs. `removeFirstOrNull() ?: return false` handles the empty cases in `undo` and `redo`."
  ],
  "done_when": "All eight tests in `ObserverCommandTest` pass."
 },
 "drill": {
  "title": "An event bus from memory",
  "minutes": 5,
  "prompt": "Close this page. Write a generic `EventBus<E>` with `subscribe` and `publish`. It must survive a listener that unsubscribes itself during delivery and a listener that throws, and it must give every subscriber a way to leave. Then compare: which of the three did you miss?",
  "answer": {"lang": "java", "src": """final class EventBus<E> {
    private final List<Consumer<? super E>> listeners = new CopyOnWriteArrayList<>();   // snapshot loops

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
    private val listeners = CopyOnWriteArrayList<(E) -> Unit>()   // snapshot loops

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
  "A safe listener list returns a handle to leave by, keeps each listener's failures to itself, and loops over a snapshot (`CopyOnWriteArrayList`). Delivery still runs on the publishing thread, so keep listeners fast.",
  "Use a `StateFlow` for state and a `SharedFlow` (or a `Channel`) for events: StateFlow drops a value equal to the current one, and slow collectors skip updates.",
  "Command turns a request into a value you can queue, log, retry and undo. Sealed records or data classes are the natural shape; `Runnable` and `() -> Unit` are commands without data.",
  "Record a command for undo only after it has succeeded.",
  "The limit: listeners and undo stacks live in memory and die with the program. A command stored to survive a crash may run twice, so it must be safe to repeat, and work that left the program is reversed by a new command, not by undo."
 ],
 "closing": "We started with a sign-up sheet by the door and a spike of order slips. The sheet became an event bus that hands each order to every listener, each in its own `try`, with a handle to leave by. A StateFlow, like the chalkboard by the counter, kept only the latest. The slips became command records, pushed on the undo stack only after they worked.\n\nNow look in your own code for a `subscribe` or `addListener` call whose result is thrown away. Who removes that listener?\n\nNext, we'll give an order a life of its own: placed, packed, on its way, delivered. When the state decides which commands are allowed, how do we keep those rules in one place?",
 "quiz": [
  {"q": "A Kotlin program publishes order events through a `MutableStateFlow`. The bakery needs every `Ordered` event to plan its baking. What will it miss?",
   "options": ["Nothing: StateFlow delivers every value", "An order equal to the previous one, and orders a slow collector didn't get to in time", "Only orders placed before it started collecting, like any hot flow", "Orders placed from another thread"],
   "answer": 1,
   "why": "StateFlow conflates by `equals`, so an order equal to the current value is never delivered, and a collector that falls behind only sees the latest value. Missing orders from before you started collecting is true of a SharedFlow with no replay too, but it isn't what makes StateFlow wrong here. StateFlow is thread-safe, so threads don't matter."},
  {"q": "A `CommandLog.run` pushes the command onto the history first and then applies it. The shelf holds 7 loaves. `Sell(40)` fails with \"not enough on the shelf\". The shopkeeper presses undo once. How many loaves does the shelf show?",
   "options": ["7", "12", "47", "40"],
   "answer": 2,
   "why": "The failed sale was recorded before it threw, so it's on top of the history. Undoing it adds back 40 loaves that never left: 7 + 40 = 47. Recording only after `apply` succeeds keeps undo honest."},
  {"q": "Each visit to the shop's website creates a small object that subscribes a listener to the program's one shared `EventBus` in its constructor, and never closes the handle. What happens over a busy day?",
   "options": ["Memory grows, and every old visit's listener keeps reacting to every order", "Nothing: listeners are removed when the visit ends", "The bus throws once it has too many listeners", "The listeners stop receiving events after a garbage collection"],
   "answer": 0,
   "why": "The shared bus's list holds a strong reference to each listener, and each listener's lambda captures its visit object, so none of them can be freed, and all of them keep running on every order. That is the lapsed-listener leak. Return a handle from `subscribe` and close it when the owner's life ends."},
  {"q": "The bakery must hear about every order, even if the program crashes a moment after the order is saved. Which design fits?",
   "options": ["A listener on the in-memory `EventBus`", "A `StateFlow` the bakery collects", "A `MutableSharedFlow` with `replay = 1`", "A slip saved in the same database transaction as the order, which a separate job sends on"],
   "answer": 3,
   "why": "Anything in memory dies with the program, so the bus and both flows lose orders made just before a crash. A slip saved in the order's transaction is saved with the order or not at all, and the job delivers it at least once, so the bakery must skip repeats."},
  {"q": "From *StateFlow, SharedFlow and hot streams*: a `MutableSharedFlow<Ordered>()` (no replay, no buffer) emits three orders, and only then does a new collector start. What does the new collector see?",
   "options": ["All three orders", "None of the three; only orders emitted after it starts", "Only the last order", "The first order, then it waits"],
   "answer": 1,
   "why": "A SharedFlow with `replay = 0` keeps nothing for late collectors: each emission goes to the collectors present at that moment. A StateFlow would hand the newcomer the latest value, and `replay = 1` would replay the last order.",
   "from": "co-08"}
 ],
 "flashcards": [
  {"front": "Why should `subscribe` return an `AutoCloseable` (or a similar handle)?", "back": "So the subscriber can leave. A forgotten listener stays referenced by the subject forever: the lapsed-listener leak."},
  {"front": "Why use `CopyOnWriteArrayList` for a listener list?", "back": "It loops over a snapshot, so a listener can unsubscribe during delivery without a `ConcurrentModificationException`. Writes are rare, reads happen all the time."},
  {"front": "What does a `publish` loop need around each listener call?", "back": "A try/catch, so one throwing listener doesn't stop delivery to the others or fail the publisher."},
  {"front": "StateFlow or SharedFlow for order events?", "back": "SharedFlow (or a Channel). StateFlow drops a value equal to the current one, and slow collectors skip updates."},
  {"front": "When does a command go on the undo history?", "back": "Only after `apply` succeeds. Recorded earlier, a failed command gets \"undone\" and corrupts the state."},
  {"front": "Is a collection slip the undo of a delivery?", "back": "No. Work that left the program can't be popped off a stack; a collection slip is a new compensating command with its own record and its own ways to fail."},
  {"front": "Why must a command that is stored and run later be safe to run twice?", "back": "Delivery is at least once: a crash after sending but before marking it sent makes it go out again."}
 ],
 "terms": [
  {"term": "Observer", "plain": "A subject keeps a list of listeners and tells each one when something happens."},
  {"term": "Lapsed listener", "plain": "A listener nobody removed: it holds memory and keeps reacting after its owner is gone."},
  {"term": "Hot flow", "plain": "A flow that exists and emits whether or not anyone collects, such as SharedFlow and StateFlow."},
  {"term": "Conflation", "plain": "Keeping only the latest value and dropping ones a collector didn't get to, or equal repeats."},
  {"term": "Command", "plain": "A request turned into a value: what to do, with which arguments, ready to store or queue."},
  {"term": "At-least-once delivery", "plain": "A promise that a stored message arrives, possibly more than once, so the receiver must skip repeats."},
  {"term": "Compensation", "plain": "A new action that reverses the effect of an earlier one, such as a collection slip for a delivery."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why `itemsToday` is a `StateFlow` but `events` is a `SharedFlow` in the lab's `ObservableOrders`, using Ana's two orders of one rye loaf as your example.",
  "answer": "`itemsToday` is state: whoever looks at it only needs the latest number. If it goes from 0 to 1 to 2 faster than a screen redraws, showing 2 is correct, and an update that leaves it unchanged gives nobody anything new. StateFlow does exactly that: it keeps the current value, gives it to new collectors right away, and drops repeats and values in between. The events are different, because each one is a fact someone must act on. Ana's two orders produce two equal `Ordered(\"Ana\", \"rye bread\", 1)` events. A StateFlow would treat the second as \"no change\" and drop it, so the bakery would bake one loaf and the email would confirm one order. A SharedFlow delivers every emitted value to every collector, so both orders arrive."
 },
 "deeper": {
  "minutes": 10,
  "body": """`StateFlow` is a special case of `SharedFlow`. Its docs describe it as a `MutableSharedFlow(replay = 1, onBufferOverflow = BufferOverflow.DROP_OLDEST)` combined with `distinctUntilChanged()`. Knowing the knobs helps when neither default fits. `replay` sets how many past values a new collector gets. `extraBufferCapacity` lets `emit` run ahead of slow collectors without pausing. `onBufferOverflow` decides what happens when that buffer is full: pause the emitter, drop the oldest value or drop the newest. For order events, the default (pause) is the safe choice, because dropping is silent.

Kotlin also has an observer for a single property: `var status by Delegates.observable(\"PLACED\") { _, old, new -> log(\"$old -> $new\") }` calls the handler after every assignment, and `Delegates.vetoable` runs before the assignment and can reject it. They are handy for state inside one object, and they run on the assigning thread, like a hand-rolled listener list.

Java has a history here. `java.util.Observable` and `java.util.Observer` shipped in Java 1.0 and were deprecated in Java 9. `Observable` is a class you must extend, the order in which it notifies observers is unspecified, and it isn't a good fit for code that runs on several threads. Use a `Consumer` list, `SubmissionPublisher` or a library for event streams instead.

Undo for operations that can't be reversed step by step, such as \"apply the weekend discount to every price\", doesn't fit the `apply`/`undo` pair. There, save a snapshot of the state before the command and restore it on undo. That is the Memento pattern, in lesson 10 of this track, *Visitor, Iterator, Mediator and Memento*."""
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
