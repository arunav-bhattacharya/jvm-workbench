package workbench.reactive.l03

import reactor.core.publisher.Flux

/** map and filter are synchronous and work one item at a time. Watch the demand they send upstream. */
fun main() {
    Flux.range(1, 10)
        .doOnRequest { n -> println("  source asked for $n") }
        .filter { amount -> amount % 3 == 0 }                    // drops 1, 2, 4, 5, ...
        .map { amount -> "EUR ${amount * 10}" }
        .take(2)                                                 // we only want two
        .subscribe { s -> println("got $s") }

    // Reactor 3.8 marks its API with JSpecify nullness, so in Kotlin a null-returning mapper doesn't compile:
    //   .map { bin -> if (bin.startsWith("4")) "VISA" else null }
    //   error: Return type mismatch: expected 'Any', actual 'String?'.
    // handle() is a map and a filter in one: emit when you have a value, skip otherwise.
    Flux.just("4111", "5500")
        .handle<String> { bin, sink -> if (bin.startsWith("4")) sink.next("VISA") }
        .subscribe({ s -> println("scheme $s") }, { e -> println("error: $e") })
}
