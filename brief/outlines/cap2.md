# Track: cap2, "Capstone: a non-blocking quote service" (lab: labs/quotes, package workbench.quotes.lNN)

Part 2, Async, reactive and servers (rx, co, io). Draws on every track in the part.
Dependencies allowed in labs/quotes/build.gradle.kts: netty-all, kotlinx-coroutines-core and -test,
reactor-core and reactor-test (versions from the root versions map).

The program: a small TCP or HTTP quote service that fans out to three slow, flaky providers and
answers within a deadline, without ever blocking its event loop.

- cap2-01 The server shell on Netty: a line or length-field codec, a handler that never blocks the
  event loop (prove it with a test that measures loop responsiveness by counts, not time), writability
  based backpressure, clean close. Fake providers are in-process and controllable.
- cap2-02 The fan-out with coroutines: a scope per request bound to the channel's lifetime, async to
  three providers, withTimeout and a cached fallback, supervisorScope so one provider failure does not
  cancel the others, cancellation when the client disconnects. Show the same fan-out in Reactor
  (Mono.zip with timeout and onErrorResume) in the compare block; the lab is Kotlin. Tests use
  virtual time.
- cap2-03 Under load: bounded concurrency to each provider (Semaphore or a channel worker pool),
  retry with backoff and jitter for idempotent calls only, a hedged request for the slowest provider,
  load shedding when the queue is full, and graceful shutdown. Tests: provider concurrency cap holds,
  no leaked coroutines after shutdown, shed requests get a clear error. Ends with the design review
  (event loop vs virtual threads for this service: when would you switch?).
