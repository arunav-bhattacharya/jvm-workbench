package workbench.reactive.l05

import reactor.core.publisher.Mono
import reactor.util.retry.Retry
import java.time.Duration
import java.util.concurrent.atomic.AtomicInteger

private val calls = AtomicInteger()
private var t0 = 0L

// fails on the first two calls, succeeds on the third
private fun callIssuer(): String {
    val n = calls.incrementAndGet()
    println("  [%3d ms] attempt %d".format((System.nanoTime() - t0) / 1_000_000, n))
    if (n < 3) throw IllegalStateException("issuer busy")
    return "APPROVED"
}

private fun alwaysFails(): String {
    callIssuer()
    throw IllegalStateException("issuer down")
}

// a client that calls the issuer when the function is called, and wraps the answer in a Mono
private fun eagerClient(): Mono<String> =
    try {
        Mono.just(callIssuer())
    } catch (e: RuntimeException) {
        Mono.error(e)
    }

private fun start(title: String) {
    println(title)
    calls.set(0)
    t0 = System.nanoTime()
}

/** retry re-subscribes. What gets re-run depends on how the source was built. */
fun main() {
    // warm up Reactor and the formatter, so the first timings don't include class loading
    Mono.fromCallable { 1 }.retryWhen(Retry.backoff(1, Duration.ofMillis(1))).block()
    "%3d".format(0)

    start("1. fromCallable + retryWhen(backoff 50 ms, no jitter)")
    println("  -> " + Mono.fromCallable { callIssuer() }
        .retryWhen(Retry.backoff(3, Duration.ofMillis(50)).jitter(0.0))
        .block())

    start("2. retry(2) on a source that always fails")
    try {
        Mono.fromCallable { alwaysFails() }.retry(2).block()
    } catch (e: RuntimeException) {
        println("  -> $e")
    }

    start("3. backoff exhausted")
    try {
        Mono.fromCallable { alwaysFails() }
            .retryWhen(Retry.backoff(3, Duration.ofMillis(50)).jitter(0.0))
            .block()
    } catch (e: RuntimeException) {
        println("  -> $e\n     cause: ${e.cause}")
    }

    start("4. retry(3) on a Mono built from one eager call")
    val subscriptions = AtomicInteger()
    try {
        eagerClient().doOnSubscribe { subscriptions.incrementAndGet() }.retry(3).block()
    } catch (e: RuntimeException) {
        println("  -> $e after ${subscriptions.get()} subscriptions")
    }
}
