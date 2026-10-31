package workbench.reactive.l05

import reactor.core.publisher.Mono
import reactor.util.retry.Retry
import java.time.Duration
import java.util.concurrent.TimeoutException
import java.util.concurrent.atomic.AtomicInteger

/** timeout turns silence into an error you can handle. Where you put it decides what it limits. */
fun main() {
    val slowRate: Mono<String> = Mono.delay(Duration.ofMillis(300)).thenReturn("live rate 1.08")
        .doOnCancel { println("  slow call cancelled") }

    try {
        slowRate.timeout(Duration.ofMillis(100)).block()
    } catch (e: RuntimeException) {
        println("timeout: ${e.cause}")
    }

    val rate = slowRate.timeout(Duration.ofMillis(100))
        .onErrorResume(TimeoutException::class.java) { Mono.just("cached rate 1.07") }
        .block()
    println("with fallback: $rate")

    val attempts = AtomicInteger()
    val t0 = System.nanoTime()
    try {
        Mono.defer { attempts.incrementAndGet(); slowRate }
            .timeout(Duration.ofMillis(100))                        // per attempt
            .retryWhen(Retry.backoff(5, Duration.ofMillis(50)).jitter(0.0))
            .timeout(Duration.ofMillis(400))                        // budget for the whole call
            .block()
    } catch (e: RuntimeException) {
        println("budget: gave up after %d attempts and %d ms: %s".format(
            attempts.get(), (System.nanoTime() - t0) / 1_000_000, e.cause?.javaClass?.simpleName))
    }
}
