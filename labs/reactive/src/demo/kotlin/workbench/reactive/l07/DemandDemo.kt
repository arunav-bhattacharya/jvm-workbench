package workbench.reactive.l07

import org.reactivestreams.Subscription
import reactor.core.publisher.BaseSubscriber
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import reactor.core.scheduler.Schedulers
import java.time.Duration
import java.util.concurrent.CopyOnWriteArrayList

private fun show(title: String, source: Flux<Int>, operator: (Flux<Int>) -> Flux<Int>) {
    val requests = CopyOnWriteArrayList<Long>()
    operator(source.doOnRequest { requests += it }).blockLast()
    println("%-24s the source saw %s".format(title, requests))
}

/** Demand made visible: the requests that reach the source, for one subscriber and five operators. */
fun main() {
    println("1. a subscriber that asks for 2, then 1 more after each item")
    Flux.range(1, 4)
        .doOnRequest { n -> println("   request($n)") }
        .subscribe(object : BaseSubscriber<Int>() {
            override fun hookOnSubscribe(s: Subscription) {
                request(2)
            }

            override fun hookOnNext(item: Int) {
                println("   got $item")
                request(1)
            }
        })

    show("2. blockLast() alone", Flux.range(1, 40)) { it }
    show("3. take(3)", Flux.range(1, 40)) { it.take(3) }
    show("4. limitRate(10)", Flux.range(1, 40)) { it.limitRate(10) }
    show("5. publishOn(single())", Flux.range(1, 600)) { it.publishOn(Schedulers.single()) }
    show("6. flatMap(call, 4)", Flux.range(1, 8)) { f ->
        f.flatMap({ i -> Mono.delay(Duration.ofMillis(10)).thenReturn(i) }, 4)
    }
}
