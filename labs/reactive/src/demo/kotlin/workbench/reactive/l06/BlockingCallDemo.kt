package workbench.reactive.l06

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import reactor.core.scheduler.Schedulers
import java.math.BigDecimal
import java.util.concurrent.ConcurrentHashMap

private val threads: MutableSet<Thread> = ConcurrentHashMap.newKeySet()

// a JDBC-style call: it holds the calling thread for 100 ms
private fun balance(account: String): BigDecimal {
    threads += Thread.currentThread()
    Thread.sleep(100)
    return BigDecimal.TEN
}

private fun run(title: String, balances: Flux<BigDecimal>) {
    threads.clear()
    val t0 = System.nanoTime()
    val n = balances.count().block()
    val one = threads.first()
    println("%-34s %d calls in %3d ms on %d thread(s), e.g. %s (virtual=%s)".format(title, n,
        (System.nanoTime() - t0) / 1_000_000, threads.size, one.name, one.isVirtual))
}

/** Eight blocking ledger calls of 100 ms each. Where you put subscribeOn decides how long they take. */
fun main(args: Array<String>) {
    if (args.firstOrNull() == "virtual") {
        // must be set before Reactor's Schedulers class is first used; normally a -D JVM flag
        System.setProperty("reactor.schedulers.defaultBoundedElasticOnVirtualThreads", "true")
    }
    val accounts = listOf("a-1", "a-2", "a-3", "a-4", "a-5", "a-6", "a-7", "a-8")

    run("1. fromCallable, no scheduler", Flux.fromIterable(accounts)
        .flatMap { a -> Mono.fromCallable { balance(a) } })

    run("2. subscribeOn on the outer Flux", Flux.fromIterable(accounts)
        .flatMap { a -> Mono.fromCallable { balance(a) } }
        .subscribeOn(Schedulers.boundedElastic()))

    run("3. subscribeOn on each call", Flux.fromIterable(accounts)
        .flatMap { a -> Mono.fromCallable { balance(a) }.subscribeOn(Schedulers.boundedElastic()) })
}
