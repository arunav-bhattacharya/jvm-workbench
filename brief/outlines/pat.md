# Track: pat, "Design patterns in Java and Kotlin" (lab: labs/patterns, package workbench.patterns.lNN)

Research notes: design_patterns.md (every sample compiled with javac 21 and kotlinc 2.4.21; reuse
its measured outputs, misconceptions and 13 exercises). Every lesson needs a `compare` block: the
modern Java version (records, sealed interfaces, switch patterns, lambdas) and the idiomatic Kotlin
version, with a note on what the language makes unnecessary. Ground every pattern in the learner's
world (payments, card issuers, Kafka, Quarkus/Spring proxies, Temporal) and point to a real use in
the JDK or a framework (the notes have a table). Take positions: say when a pattern is obsolete in
Kotlin and what replaces it. Labs can be Java or Kotlin; use both across the track. The patterns
module has kotlinx-coroutines-core and -test available (for the Observer lesson). No other dependencies:
for circuit breaker/bulkhead, build a small one by hand and mention Resilience4j 2.4.0 in prose.
Do not teach StableValue/LazyConstant as final (preview, per notes).

Lessons:
- pat-01 Patterns in a modern language, and Singleton: what a pattern is (a name for a recurring
  design, not a template), how lambdas, sealed types and delegation changed the list; Singleton:
  enum, holder idiom, DCL with volatile (link back to jmm-05), Kotlin `object` and `lazy`, why
  dependency injection usually beats a hand-rolled singleton (testability). Lab: a thread-safe
  lazily-initialized registry plus a test that proves one instance under contention.
- pat-02 Factory Method and Abstract Factory: static factories (Effective Java item 1), companion
  object factories and `invoke`, sealed result types from factories, abstract factory for a family of
  card-network clients (Visa/Mastercard sandboxes). Lab: replace constructor sprawl with factories.
- pat-03 Builder and Prototype: Java builders vs Kotlin named and default args, when a builder still
  helps (validation, Java callers), type-safe DSL builders with lambdas with receivers and @DslMarker;
  Prototype via copy constructors, record withers by hand, data class `copy()` (shallow; the private
  constructor + copy() trap and @ConsistentCopyVisibility from notes); why Cloneable is discouraged.
  Lab: a payment-request DSL with validation; a deep-copy fix.
- pat-04 Adapter and Facade: adapting a legacy card-issuer SDK to your port interface, extension
  functions as lightweight adapters, a facade over payment + ledger + notification. Lab: adapter + facade.
- pat-05 Decorator and Proxy: java.io streams, Collections.unmodifiableList, Kotlin `by` class
  delegation (and the putAll bypass trap), dynamic proxies with java.lang.reflect.Proxy, how Spring and
  Quarkus use proxies and the self-invocation pitfall (Quarkus intercepts self-invocation, per notes).
  Lab: a fee-calculator decorator chain (use the notes' 320/420/500/1,500 outputs) and a timing proxy.
- pat-06 Composite, Bridge and Flyweight: composite pricing rules or a menu/tree, bridge between
  notification type and channel, flyweight (Integer cache, String interning, currency instances).
- pat-07 Strategy and Template Method: functions as strategies (Comparator.comparing), refactor a big
  if/else payment router into strategies (a map of functions, or a sealed type), template method vs
  passing functions. Lab: the router refactor with tests that pin behavior.
- pat-08 Observer and Command: listeners, Kotlin Flow/SharedFlow as observable streams (StateFlow drops
  equal values, so it is wrong for payment events, per notes), Reactor in one line; Command with undo
  and as the shape of queued jobs and Temporal activities. Lab: an observable ledger and an undoable command stack.
- pat-09 State and Chain of Responsibility: a payment lifecycle state machine with sealed types and
  exhaustive switch/when (use the captured compiler errors as a "compiler as to-do list" exercise),
  chain of responsibility as servlet filters, interceptors, a fraud-check pipeline.
- pat-10 Visitor, Iterator, Mediator and Memento: visitor vs sealed types + pattern matching (the
  expression problem in plain words), Kotlin `sequence {}`/`iterator {}` builders, mediator in brief,
  memento for undo/snapshots.
- pat-11 Concurrency patterns that tie it all together: producer-consumer, worker pool, active object,
  guarded suspension, balking, read-write lock, immutable object, thread-per-message, future/promise,
  circuit breaker and bulkhead. Link back to earlier tracks. Lab: a hand-built circuit breaker with
  closed/open/half-open states tested with a fake clock, and a semaphore bulkhead.
