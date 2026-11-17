package workbench.reactive.l02

import reactor.core.publisher.Mono
import java.util.concurrent.atomic.AtomicInteger

private val calls = AtomicInteger()

private fun fetchFlourPrice(): String {
    calls.incrementAndGet()
    return "flour=1.20/kg"
}

/** Mono.just, fromCallable and defer, each subscribed twice. Count the calls. */
fun main() {
    run("just") { Mono.just(fetchFlourPrice()) }
    run("fromCallable") { Mono.fromCallable { fetchFlourPrice() } }
    run("defer") { Mono.defer { Mono.just(fetchFlourPrice()) } }
}

private fun run(name: String, build: () -> Mono<String>) {
    calls.set(0)
    val price = build()
    val atAssembly = calls.get()
    price.block()
    price.block()
    println("%-13s calls at assembly: %d, after 2 subscriptions: %d".format(name, atAssembly, calls.get()))
}
