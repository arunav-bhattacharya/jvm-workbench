package workbench.reactive.l08

import reactor.core.publisher.Mono
import reactor.test.StepVerifier
import reactor.test.publisher.TestPublisher
import java.time.Duration
import java.util.concurrent.atomic.AtomicInteger

/** Five StepVerifier habits, most of them shown by breaking them. */
fun main() {
    val subscriptions = AtomicInteger()
    val bake = Mono.fromCallable { "baked" }.doOnSubscribe { subscriptions.incrementAndGet() }
    StepVerifier.create(bake).expectNext("burnt").expectComplete()              // no verify(): nothing runs
    println("1. no verify():     subscriptions=${subscriptions.get()}, wrong expectation unnoticed")

    val real = StepVerifier.withVirtualTime { Mono.delay(Duration.ofDays(1)).thenReturn("stale") }
        .expectSubscription()
        .expectNoEvent(Duration.ofDays(1))
        .expectNext("stale")
        .verifyComplete()
    println("2. virtual time:    one day took ${real.toMillis()} ms of real time")

    try {
        StepVerifier.withVirtualTime { Mono.delay(Duration.ofDays(1)) }
            .expectNoEvent(Duration.ofDays(1))                                       // subscription counts as an event
            .expectNext(0L)
            .verifyComplete()
    } catch (e: AssertionError) {
        println("3. expectNoEvent first: ${e.message}")
    }

    val builtTooEarly = Mono.delay(Duration.ofDays(1)).thenReturn("stale")          // grabs the real clock
    try {
        StepVerifier.withVirtualTime { builtTooEarly }
            .expectSubscription()
            .thenAwait(Duration.ofDays(1))
            .expectNext("stale")
            .expectComplete()
            .verify(Duration.ofSeconds(1))
    } catch (e: AssertionError) {
        println("4. built outside the supplier: ${e.message}")
    }

    val readings = TestPublisher.create<String>()
    StepVerifier.create(readings.flux().map { r -> "$r C" })
        .then { readings.next("200", "201") }                                         // push values by hand
        .expectNext("200 C", "201 C")
        .then { readings.complete() }
        .expectComplete()
        .verify(Duration.ofSeconds(1))
    println("5. TestPublisher:   passed; the map requested ${if (readings.wasRequested()) "some" else "no"} items")
}
