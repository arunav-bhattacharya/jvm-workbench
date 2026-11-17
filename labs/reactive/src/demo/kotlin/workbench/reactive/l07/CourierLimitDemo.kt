package workbench.reactive.l07

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.Duration
import java.util.concurrent.Semaphore
import java.util.concurrent.atomic.AtomicInteger

private val openRequests = Semaphore(20)
private val refused = AtomicInteger()

// the courier: 50 ms per booking, and a 21st open request is refused
private fun courierCall(id: Int): Mono<String> = Mono.defer {
    if (!openRequests.tryAcquire()) {
        refused.incrementAndGet()
        Mono.error(IllegalStateException("too many open requests"))
    } else {
        Mono.delay(Duration.ofMillis(50)).map {
            openRequests.release()                      // the answer frees the slot
            "van-$id"
        }
    }
}

private fun run(title: String, book: (Flux<Int>) -> Flux<String>) {
    refused.set(0)
    val t0 = System.nanoTime()
    val booked = book(Flux.range(1, 200)).count().block()
    println("%-22s %3d booked, %3d refused, in %3d ms".format(
        title, booked, refused.get(), (System.nanoTime() - t0) / 1_000_000))
}

/** 200 delivery bookings against a courier service that allows 20 open requests per customer. */
fun main() {
    courierCall(0).block()                                 // warm-up, so the timings below are fair
    // a refused call is skipped, so one refusal doesn't end the whole batch (lesson 5 of this track)
    run("1. flatMap(call)") { f -> f.flatMap { id -> courierCall(id).onErrorResume { Mono.empty() } } }
    run("2. flatMap(call, 20)") { f -> f.flatMap({ id -> courierCall(id).onErrorResume { Mono.empty() } }, 20) }
}
