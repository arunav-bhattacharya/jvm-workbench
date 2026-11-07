# Track: cap3, "Capstone: a typed event library" (lab: labs/events, package workbench.events.lNN)

Part 3, Types and design (gen, pat, dop, kt). Draws on every track in the part.
Dependencies: none beyond the shared setup (the kotlin-reflect artifact is allowed if needed).

The program: a small in-process event library for a payments service: a sealed event model, a typed
event bus, and an API that is pleasant from both Kotlin and Java.

- cap3-01 The model: payment events as a sealed hierarchy (Kotlin sealed interface with data classes;
  Java sealed interface with records in the compare), value classes for ids and money, exhaustive
  when/switch over events, and parsing at the edge into the model. Tests: exhaustiveness, validation.
- cap3-02 The bus: subscribe<T : Event> with reified type parameters, a registry keyed by KClass,
  variance done right (a handler of Event can handle PaymentCaptured: in-projection), observer plus
  chain of responsibility for middleware, decorator for timing. Tests: dispatch by subtype, a
  Handler<Event> accepted where Handler<PaymentCaptured> is expected, ordering of middleware.
- cap3-03 The API: a type-safe DSL with @DslMarker for subscriptions, inline helpers, a Java-friendly
  surface (@JvmStatic, @JvmOverloads, Class<T> token overloads for Java callers), and a Java test that
  uses it. Ends with the design review (which generics and patterns choices would you undo?).
