package workbench.reactive.l03

import reactor.core.publisher.Flux
import java.time.Duration

// a lookup that streams up to three suggestions, one every 60 ms
private fun suggestions(prefix: String): Flux<String> =
    Flux.interval(Duration.ofMillis(60))
        .map { n -> "$prefix-match$n" }
        .take(3)
        .doOnCancel { println("  cancelled lookup for $prefix") }

/** Card number lookup as the user types: each new prefix cancels the lookup for the previous one. */
fun main() {
    val typed = Flux.just("41", "4111").delayElements(Duration.ofMillis(100))   // at 100 ms and 200 ms

    val shown = typed
        .switchMap { prefix -> suggestions(prefix) }
        .doOnNext { s -> println("show $s") }
        .collectList()
        .block()
    println("all shown: $shown")
}
