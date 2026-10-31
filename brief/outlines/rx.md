# Track: rx, "Reactive programming" (lab: labs/reactive, package workbench.reactive.lNN)

Research notes: reactive_programming.md (verified against reactor-core 3.8.8 with local runs; use its
measured outputs). Labs in Java with Reactor 3.8.8 and StepVerifier; a Kotlin `compare` where useful
(Flux vs Kotlin Flow, Mono vs suspend). Prefer `StepVerifier.withVirtualTime` over real delays.
No new dependencies (BlockHound, reactor-tools, context-propagation are NOT available; mention them in prose only).

Lessons:
- rx-01 Why reactive: push vs pull, backpressure, non-blocking IO, the Reactive Streams contract
  (Publisher, Subscriber, Subscription, Processor and the key rules), java.util.concurrent.Flow and
  SubmissionPublisher. Lab: implement a tiny Flow.Subscriber that requests in batches, against a
  SubmissionPublisher; test the request pattern.
- rx-02 Mono and Flux: assembly vs subscription, nothing happens until subscribe, cold publishers,
  Mono.just vs fromCallable vs defer. Lab: make an eager pipeline lazy; count subscriptions.
- rx-03 Transforming streams: map, filter, flatMap (and its concurrency/prefetch), concatMap,
  flatMapSequential, switchMap; the measured ordering demo from the notes. Lab: pick the right operator
  for three scenarios, tested with virtual time.
- rx-04 Combining streams: zip (and Mono.zip with empty), merge, concat, combineLatest, mergeSequential.
- rx-05 Errors, retries and timeouts: errors are terminal, onErrorReturn/Resume/Map, why onErrorContinue
  is discouraged, retry vs retryWhen(Retry.backoff) (the 4-attempt fact), timeout. Lab: retry a flaky
  card-issuer call with backoff and a fallback, tested with virtual time.
- rx-06 Schedulers: publishOn vs subscribeOn (the one nearest the source wins), parallel,
  boundedElastic (and its virtual-thread option), wrapping blocking calls with fromCallable +
  subscribeOn(boundedElastic), block() rules.
- rx-07 Backpressure in practice: request(n), limitRate (the [10, 8, 8...] pattern), onBackpressure
  Buffer/Drop/Latest/Error, flatMap concurrency as a rate limiter.
- rx-08 Hot and cold publishers, Sinks, and StepVerifier: Sinks.many() variants, share/publish/
  refCount/autoConnect, cache/replay, testing with StepVerifier, TestPublisher, expectNoEvent,
  virtual time; debugging with checkpoint and log. End with when reactive is still worth it vs
  virtual threads and coroutines (cite the Spring docs statements in the notes).
