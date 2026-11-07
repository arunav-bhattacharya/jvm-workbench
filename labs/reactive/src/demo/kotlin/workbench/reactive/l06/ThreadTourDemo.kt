package workbench.reactive.l06

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.Duration

private fun where(step: String) = println("  %-26s on %s".format(step, Thread.currentThread().name))

/** Where does each step run? Reactor stays on whatever thread delivered the last signal. */
fun main() {
    println("1. no scheduler anywhere")
    Flux.range(1, 2)
        .doOnNext { i -> where("source emits $i") }
        .map { i -> i * 10 }
        .subscribe { i -> where("subscriber gets $i") }

    println("2. after a timer (Mono.delay)")
    Mono.delay(Duration.ofMillis(10))
        .doOnNext { where("timer fires") }
        .map { "ok" }
        .doOnNext { where("map after the timer") }
        .block()

    println("3. flatMap over three timers")
    Flux.range(1, 3)
        .flatMap { i -> Mono.delay(Duration.ofMillis(10L * i)).thenReturn(i) }
        .doOnNext { i -> where("downstream gets $i") }
        .blockLast()
}
