import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """This track builds one small program from start to finish: the order program of a corner shop in a small town, which delivers by bike with Pedal Post or by van with Big Blue Vans. Along the way you meet the classic design patterns, named designs from a famous 1994 book that programmers still use to talk about code. Each one arrives with a scene from the town: the town hall for Singleton, the bakery counter for Factory Method, gift paper around a teapot for Decorator, the "ring me when the bread arrives" sheet for Observer, the fuse box in the back room for the circuit breaker. By the end you can name the patterns in the code you read, and you know which ones modern Java and Kotlin have turned into a few lines: Strategy and Command into lambdas, State and Visitor into sealed types with an exhaustive `switch` or `when`, Builder into named arguments, Decorator into Kotlin's `by`. You can also tell when a pattern still earns its own class: an adapter at the edge of your program, a facade over a job with several steps, a proxy with rules of its own, and the concurrency patterns that keep a busy program working when a service it calls goes quiet. The last lesson builds a circuit breaker and a bulkhead by hand, out of State, Decorator and compare-and-set.

You need to read basic Java and Kotlin, including Kotlin data classes and lambdas. Records, sealed interfaces and pattern matching are explained where they first appear, and the modern Java data modeling track right after this one covers them in depth. The concurrency and memory model tracks help with lessons 1 and 11. Install JDK 25; the labs compile with `release 21`, so they also run on JDK 21. Kotlin samples use 2.4.21, and guards in `when` need Kotlin 2.2 or later.

The labs live in `labs/patterns`, one package per lesson (`workbench.patterns.l01` to `l11`). About half are in Java and half in Kotlin, and every code sample and Try-it demo in the lessons comes in both languages. Most labs are refactors: the tests pin the behavior, and you change the shape. From `labs/`, run `./gradlew :patterns:test --tests 'workbench.patterns.lNN.*'` until it passes, and `./gradlew :patterns:solutionTest` to run the same tests against the reference answers. The tests that use threads rely on latches, counters and a fake clock, so they pass or fail the same way on every run."""

CHEATSHEET = """## What a pattern is

A pattern is a name for a design you keep meeting, with its trade-offs. Learn the intent, so you recognize the language feature that replaced it, and so you know when the feature isn't enough.

The running example is the order program of a corner shop in a small town: a price list, parcels, two couriers (Pedal Post's bikes and Big Blue Vans), boxes of goods, orders that move from placed to delivered. Each pattern has a scene from that town, in the "Picture it" column, and each lesson says where its picture breaks.

## Creational: making objects

| Pattern | Picture it | Java 21+ | Kotlin | Watch out for |
|---|---|---|---|---|
| Singleton | the town hall: one, and everyone knows where it is | `enum`; holder idiom; double-checked locking with `volatile` | `object`; `by lazy` (default `SYNCHRONIZED`) | Prefer passing the one instance in; `PUBLICATION` may run the initializer twice |
| Factory Method | the bakery counter: ask for "a loaf for sandwiches", the baker picks | static factory, private constructor; `Supplier<T>` | companion `of`, `operator fun invoke`, a top-level function named like the type | Return a sealed result; no `default` in the caller's switch |
| Abstract Factory | the furniture maker's matching table and chairs | one interface that builds a matching set | the same; `when` over the set | A new product touches every set |
| Builder | the sandwich counter: add parts as you go, checked at the end | a validating record plus a builder that only collects | named and default arguments, `copy()`, a DSL with `@DslMarker` | Validate in the compact constructor or `init` |
| Prototype | the photocopier: copy the form, change two lines | copy constructor, withers | `copy()` | Every copy is shallow; `Cloneable` has no `clone`; `@ConsistentCopyVisibility` |

## Structural: fitting objects together

| Pattern | Picture it | Java 21+ | Kotlin | Watch out for |
|---|---|---|---|---|
| Adapter | the travel plug adapter | a class that implements your interface and translates results and errors | the same; an extension function for data | Kotlin lets another library's checked exception through without a word |
| Facade | the hotel reception desk | one class that runs a job with several steps | the same | It owns the order of the steps and what to undo, nothing else |
| Decorator | gift paper and a ribbon around a teapot | a wrapper with the same interface; default-method combinators | `by` delegation; extension decorators | The order of the layers changes results; `by` never calls back into the wrapper |
| Proxy | the receptionist who answers for the busy manager | `java.lang.reflect.Proxy`; unwrap `InvocationTargetException` | a `reified` helper | A call to `this.method()` skips the proxy; Kotlin classes are final unless `open` |
| Composite | the Saturday breakfast box of boxes | sealed records plus an exhaustive switch | sealed interface plus `when` | Keep trees immutable: `List.copyOf`, `toList()` |
| Bridge | one TV remote for any brand of TV | the abstraction holds an implementor interface | the implementor as a `fun interface` or a function type | Planned up front; skip it when only one side varies |
| Flyweight | the sign shop's single A stencil | private constructor plus a `computeIfAbsent` pool; the `Integer` cache from -128 to 127 | the same; `enum class`, `object` | `==` on boxed numbers in Java; pools must be bounded |

## Behavioral: sharing out the work

| Pattern | Picture it | Java 21+ | Kotlin | Watch out for |
|---|---|---|---|---|
| Strategy | choosing a courier: cheapest, fastest, or the van in the rain | a lambda, `Comparator.comparing`; `EnumMap` for open sets, a switch for closed ones | function types, `compareBy` | A missing map entry fails when the program runs, a missing case at compile time |
| Template Method | the recipe card with one blank | a final skeleton with hooks; better, execute around | an `inline` higher-order function | Never call a hook from a constructor |
| Observer | the "ring me when the bread arrives" sheet | a `CopyOnWriteArrayList` of listeners plus a handle to leave; `SubmissionPublisher` | `SharedFlow` for events, `StateFlow` for state | StateFlow drops a value equal to the current one |
| Command | order slips on a spike, done, undone, done again | sealed records; `Runnable` | sealed data classes; `() -> Unit` | Record for undo only after success; work that left the program needs a new command, not undo |
| State | the order board: a column per state, a rule card above it | sealed states and events, one pure transition function | the same, with `when` guards | No `default` on the switch over states |
| Chain of Responsibility | a complaint passed from the assistant to the manager to head office | a list of handlers folded into one function | `foldRight` over `fun interface`s | Order is behavior; never skip or double `next` |
| Visitor | the inspector with a different check for each kind of goods | a sealed type plus a switch with record patterns | a sealed type plus `when` and guards | Keep Visitor for open or library hierarchies |
| Iterator | walking along a shelf one item at a time | a hand-written `Iterator`, with `while` in `hasNext` | `sequence {}`, `iterator {}` | Sequences are cold; a `finally` inside may never run |
| Mediator | the town's dispatcher, so bikes and vans never phone each other | a hub that holds the routing rules | the same; one shared `SharedFlow` | The hub turning into a god object |
| Memento | a photo of the shelf before you rearrange it | a private record behind an opaque interface, copied on save and restore | a private data class, `toList()` | Shallow snapshots; unbounded history |

## Concurrency: many threads, one shop

| Pattern | Picture it | Java 21+ | Kotlin | Watch out for |
|---|---|---|---|---|
| Producer-consumer | the packing rail: the counter clips slips on, packers take them off | a bounded `BlockingQueue`, one poison pill per consumer | `Channel(capacity)`, `close()`, a `for` loop in each worker | Unbounded queues; `consumeEach` in many workers |
| Thread-per-message | a fresh helper for every order | `newVirtualThreadPerTaskExecutor()` | `launch` per message | Always pair it with a limit |
| Active object | the stock worker who alone touches the shelves | a single-thread executor as a mailbox, methods return futures | a coroutine that owns the state and reads a `Channel` | Waiting on its own future from inside |
| Guarded suspension | waiting for the courier to confirm a pickup | `CompletableFuture`, `CountDownLatch`, `wait` in a `while` loop | `CompletableDeferred`, `withTimeout` | Waiting without a timeout |
| Balking | the stock count that won't start while one is running | `AtomicBoolean.compareAndSet(false, true)` | the same, or `Mutex.tryLock()` | One program only; across copies, use a shared lock |
| Read-write lock | many people reading the price board, one person changing it | `ReentrantReadWriteLock`, or an `AtomicReference` to an immutable snapshot | the same | No read-to-write upgrade |
| Bulkhead | twenty phone lines for each courier, and a busy tone when they're full | `Semaphore.tryAcquire`, release in `finally` | `kotlinx.coroutines.sync.Semaphore` | Size it to the service, not to your threads |
| Circuit breaker | the fuse box in the back room, which tries again by itself | sealed states in an `AtomicReference`, an injected `Clock`; Resilience4j 2.4.0 | the same | Count only failures that mean "sick"; Resilience4j's default `minimumNumberOfCalls` is 100 |

## Rules that cover most cases

- No `default` or `else` on a switch over your own sealed type or enum. Use one, and make it throw, only for open sets you don't control, such as another program's codes and strings read from settings.
- Copy every changeable part at every boundary: compact constructors, composites, mementos, factories.
- One-method patterns (Strategy, Command, Template Method, a chain's handler, a single-method adapter) are functions first. Give them a named interface when the name helps.
- Framework annotations live in proxies: they run only for calls that go through the proxy.
- Retry in one layer, around calls that are safe to run twice, outside the breaker, and never on `CallNotPermitted` or a full bulkhead."""

RECAP = [
 "Patterns are names for designs you keep meeting. In Java 21 and Kotlin, many of them are now a language feature: lambdas, sealed types with an exhaustive `switch` or `when`, records and data classes, named arguments and `by` delegation.",
 "Creational: pass shared objects in instead of hand-rolling singletons, give constructors names with validating factories, use named arguments or a record plus a builder, and remember that every copy (`copy()`, withers) is shallow.",
 "Structural: adapters translate an old program's codes and errors at the edge, facades own jobs with several steps, decorators add behavior behind the same interface (the order of the layers matters), and proxies carry framework behavior with rules of their own, calls to `this` above all.",
 "Composite, State and Visitor become sealed types plus pure functions. Leave the default off the switch over your own types, and the compiler lists every place a new case needs a rule.",
 "Strategy, Command, Template Method and Chain of Responsibility become functions: lambdas, comparators, execute-around helpers and folded lists of handlers.",
 "Observer: return a handle to leave by and keep listener failures apart; use SharedFlow for events and StateFlow for state. Memento and Command both give undo, by snapshot or by opposite.",
 "Iterator and Mediator: a `sequence {}` walks pages lazily but runs again for every walk, and a mediator routes messages between parts that shouldn't know each other, and does nothing else.",
 "Concurrency patterns answer who owns the state and who waits: bounded producer-consumer queues, balking with compare-and-set, guarded suspension with futures, and one owner for each piece of changeable state.",
 "Cheap threads don't make services cheap: put a fail-fast bulkhead in front of each service, a circuit breaker that stops calling a failing one, and one retry layer around calls that are safe to repeat."
]

QUIZ = [
 {"q": "The shop's program needs one shared `PriceList`. A teammate writes `object PriceList { ... }` and calls it directly from twelve classes. What is the main cost?",
  "options": ["It isn't thread-safe: two threads can create two instances", "Tests can't swap it for a pretend one, and its state leaks from one test to the next", "Kotlin creates a new instance for each class that uses it", "It can't hold changeable state"],
  "answer": 1,
  "why": "A Kotlin `object` is created once, safely, on first use, so thread safety isn't the problem. The cost is the hidden dependency: twelve classes reach for a global, so a test can't hand them a pretend price list, and anything one test changes is still there for the next. Pass the price list in through each class's constructor instead.",
  "from": "pat-01"},
 {"q": "A Kotlin 2.4 `data class Email private constructor(val value: String)` is meant to be created only through a validating factory, `Email.of`. What does `email.copy(value = \"not-an-email\")` do?",
  "options": ["It doesn't compile, because `copy()` is private like the constructor", "It deep-copies the email and rejects the bad value", "It compiles, with a warning: `copy()` stays public and skips the factory, though checks in `init` still run", "`copy()` isn't generated for a private constructor"],
  "answer": 2,
  "why": "In Kotlin 2.4, a private primary constructor doesn't make the generated `copy()` private; you get a warning unless you add `@ConsistentCopyVisibility`. So `copy()` goes around the factory, and only the rules in `init` still apply. That is why validation belongs in `init`.",
  "from": "pat-03"},
 {"q": "Name these four wrappers, in order: (1) a class that makes the old warehouse program's item numbers and two-digit codes look like the shop's own stock interface; (2) a `DeliveryFee` that wraps another one and adds 2.00 for fragile parcels; (3) the stand-in object a framework hands out so that an annotation such as `@Transactional` works; (4) one `placeOrder()` call that reserves stock, writes the order down and emails the customer.",
  "options": ["Adapter, Decorator, Proxy, Facade", "Decorator, Proxy, Adapter, Facade", "Adapter, Proxy, Decorator, Bridge", "Facade, Decorator, Proxy, Adapter"],
  "answer": 0,
  "why": "An adapter changes another program's interface into yours. A decorator keeps the interface and adds behavior. A proxy keeps the interface and controls access, here by running calls inside a database transaction. A facade puts one simple front door in front of several objects. Structure alone can't tell them apart; the intent does.",
  "from": "pat-05"},
 {"q": "The shop's notices come in four kinds (\"on its way\", \"sold out\" and two more) and go out by three channels, and both lists will grow. Which pattern keeps the code at N + M pieces instead of N x M classes?",
  "options": ["Composite", "Flyweight", "Adapter", "Bridge"],
  "answer": 3,
  "why": "Bridge splits two sides that vary on their own: each notice holds a `Channel` and calls it, like a remote that works with any TV, so a new channel works with every notice. Composite is for trees, Flyweight for sharing unchanging objects, and Adapter for fitting one existing class to your interface.",
  "from": "pat-06"},
 {"q": "Every call to a courier must be timed and logged the same way, around a different call each time. What is the modern replacement for a Template Method base class here?",
  "options": ["A higher-order function, `timed(\"courier.book\", timings) { ... }`, inline in Kotlin", "A Strategy map from call name to `Runnable`", "A Singleton that every call registers with", "A dynamic proxy around every lambda"],
  "answer": 0,
  "why": "The skeleton is fixed and only the middle changes, which is execute around: one function that does the before and after and takes the changing step as a lambda. It needs no subclass per call site, and it can't fall into the trap of a constructor calling a hook. In Kotlin, `inline` removes the lambda object too.",
  "from": "pat-07"},
 {"q": "The shop's program offers \"an order was placed\" events and the number of items sold today as Kotlin flows. Which pairing is right?",
  "options": ["StateFlow for both", "SharedFlow for both", "SharedFlow for the orders, StateFlow for the count", "StateFlow for the orders, SharedFlow for the count"],
  "answer": 2,
  "why": "Orders are events: two equal orders in a row, such as Ana's two rye loaves, are two real orders, and a StateFlow would drop the second because it compares values with `equals`. The count is state: whoever looks only needs the latest number, which is exactly what a StateFlow gives, including to late collectors.",
  "from": "pat-08"},
 {"q": "A Java switch over a sealed `OrderState` covers all five states with no `default`. A new `WaitingAtShop` state is added in a separately compiled jar, and a `WaitingAtShop` value reaches the old switch when the program runs. What happens?",
  "options": ["It falls into the first case", "It returns null", "The JVM throws `MatchException`", "Nothing: the compiler rejected the old jar"],
  "answer": 2,
  "why": "Exhaustiveness is checked at compile time against the subtypes known then. A subtype added later, in separately compiled code, is part of the remainder, and Java throws `MatchException` for it (Kotlin throws `NoWhenBranchMatchedException`; a null state throws `NullPointerException`). Recompiling the switch turns it back into a compile error.",
  "from": "pat-09"},
 {"q": "When does the classic Visitor pattern still make sense in modern Java or Kotlin?",
  "options": ["Whenever a hierarchy has more than five subtypes", "For any sealed hierarchy you own", "Never: pattern matching replaced it completely", "For hierarchies open to code you don't compile, or libraries that hand you one, such as annotation processing or tools that read compiled classes"],
  "answer": 3,
  "why": "For a closed hierarchy you own, a sealed type plus `switch` or `when` gives Visitor's benefit (cheap new jobs) without `accept` methods. Visitor still fits when the hierarchy isn't sealed or isn't yours, as in Java's annotation processing API or the ASM library.",
  "from": "pat-10"},
 {"q": "Big Blue Vans' booking service is down, and every call hangs until a 2-second timeout. Which tool stops the shop's threads from each waiting those 2 seconds?",
  "options": ["A bulkhead of 50", "A circuit breaker", "A retry with three attempts", "A bigger thread pool"],
  "answer": 1,
  "why": "Once its failure threshold is reached, the breaker opens and turns calls away at once, without calling the service. A bulkhead only caps how many calls wait at the same time, so 50 of them still wait 2 seconds each. Retries multiply the waiting, and a bigger pool just lets more threads wait.",
  "from": "pat-11"},
 {"q": "`Parcel.parse(input)` is a factory that returns a sealed `ParcelResult` with `Valid` and `Invalid`. What should the caller's `when` (or `switch`) look like?",
  "options": ["One branch per subtype and no `else`, so a new result type breaks the build here", "A single `else` branch, to be safe", "A `try`/`catch` around the call instead of a `when`", "An `is Valid` branch only, because bad input throws"],
  "answer": 0,
  "why": "A sealed result is a promise that the caller handles every outcome, and the compiler checks it only if there is no `else`. Add a `TooHeavy` result later, and every caller that needs to decide fails to compile. `parse` never throws for bad input; that's what `Invalid` is for.",
  "from": "pat-02"}
]

T = {"id": "pat", "intro": INTRO, "cheatsheet": CHEATSHEET, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/pat.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
