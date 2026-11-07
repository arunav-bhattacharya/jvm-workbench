package workbench.reactive.l06

import reactor.core.publisher.Flux
import reactor.core.scheduler.Schedulers

private fun where(step: String) = println("  %-22s on %s".format(step, Thread.currentThread().name))

/** publishOn moves what comes after it. subscribeOn moves the source, wherever you write it. */
fun main() {
    println("1. publishOn(single) in the middle")
    Flux.range(1, 1)
        .doOnNext { where("source") }
        .publishOn(Schedulers.single())
        .doOnNext { where("after publishOn") }
        .blockLast()

    println("2. subscribeOn(boundedElastic) written last")
    Flux.range(1, 1)
        .doOnNext { where("source") }
        .publishOn(Schedulers.single())
        .doOnNext { where("after publishOn") }
        .subscribeOn(Schedulers.boundedElastic())
        .blockLast()

    println("3. two subscribeOn calls")
    Flux.range(1, 1)
        .doOnNext { where("source") }
        .subscribeOn(Schedulers.single())               // nearest to the source: this one wins
        .subscribeOn(Schedulers.boundedElastic())       // only adds a thread hop
        .doOnNext { where("downstream") }
        .blockLast()
}
