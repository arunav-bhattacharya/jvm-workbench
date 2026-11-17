package workbench.reactive.l03

import reactor.core.publisher.Flux

/** map and filter are synchronous and work one item at a time. Watch the demand they send upstream. */
fun main() {
    Flux.range(1, 10)
        .doOnRequest { n -> println("  oven asked for $n") }
        .filter { loaf -> loaf % 3 == 0 }                        // only every third loaf has seeds
        .map { loaf -> "sliced loaf-$loaf" }
        .take(2)                                                 // we only want two
        .subscribe { s -> println("got $s") }

    // Reactor 3.8 marks its API with JSpecify nullness, so in Kotlin a null-returning mapper doesn't compile:
    //   .map { flour -> if (flour == "rye") "dark bread" else null }
    //   error: Return type mismatch: expected 'Any', actual 'String?'.
    // handle() is a map and a filter in one: emit when you have a value, skip otherwise.
    Flux.just("rye", "spelt")
        .handle<String> { flour, sink -> if (flour == "rye") sink.next("dark bread") }
        .subscribe({ s -> println("made $s") }, { e -> println("error: $e") })
}
