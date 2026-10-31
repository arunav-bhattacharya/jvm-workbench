package workbench.reactive.l02

import reactor.core.publisher.Mono
import java.util.concurrent.atomic.AtomicInteger

private val calls = AtomicInteger()

private fun fetchFxRate(): String {
    calls.incrementAndGet()
    return "EURUSD=1.08"
}

/** Mono.just, fromCallable and defer, each subscribed twice. Count the calls. */
fun main() {
    run("just") { Mono.just(fetchFxRate()) }
    run("fromCallable") { Mono.fromCallable { fetchFxRate() } }
    run("defer") { Mono.defer { Mono.just(fetchFxRate()) } }
}

private fun run(name: String, build: () -> Mono<String>) {
    calls.set(0)
    val rate = build()
    val atAssembly = calls.get()
    rate.block()
    rate.block()
    println("%-13s calls at assembly: %d, after 2 subscriptions: %d".format(name, atAssembly, calls.get()))
}
