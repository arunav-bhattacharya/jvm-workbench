package workbench.reactive.l07

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.Duration
import java.util.concurrent.Semaphore
import java.util.concurrent.atomic.AtomicInteger

private val openRequests = Semaphore(20)
private val refused = AtomicInteger()

// the bank: 50 ms per call, and a 21st concurrent request is refused with a 429
private fun bankCall(id: Int): Mono<String> = Mono.defer {
    if (!openRequests.tryAcquire()) {
        refused.incrementAndGet()
        Mono.error(IllegalStateException("429 Too Many Requests"))
    } else {
        Mono.delay(Duration.ofMillis(50)).map {
            openRequests.release()                      // the response frees the slot
            "receipt-$id"
        }
    }
}

private fun run(title: String, settle: (Flux<Int>) -> Flux<String>) {
    refused.set(0)
    val t0 = System.nanoTime()
    val settled = settle(Flux.range(1, 200)).count().block()
    println("%-22s %3d settled, %3d refused with 429, in %3d ms".format(
        title, settled, refused.get(), (System.nanoTime() - t0) / 1_000_000))
}

/** 200 settlement calls against a bank that allows 20 open requests per client. */
fun main() {
    bankCall(0).block()                                 // warm-up, so the timings below are fair
    // a refused call is skipped, so one 429 doesn't end the whole batch (lesson 5 of this track)
    run("1. flatMap(call)") { f -> f.flatMap { id -> bankCall(id).onErrorResume { Mono.empty() } } }
    run("2. flatMap(call, 20)") { f -> f.flatMap({ id -> bankCall(id).onErrorResume { Mono.empty() } }, 20) }
}
