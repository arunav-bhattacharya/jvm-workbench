package workbench.reactive.l06

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import reactor.core.scheduler.Schedulers
import java.util.concurrent.ConcurrentHashMap

private val threads: MutableSet<Thread> = ConcurrentHashMap.newKeySet()

// a call through a blocking database driver: it holds the calling thread for 100 ms
private fun loavesLeft(shop: String): Int {
    threads += Thread.currentThread()
    Thread.sleep(100)
    return 10
}

private fun run(title: String, counts: Flux<Int>) {
    threads.clear()
    val t0 = System.nanoTime()
    val n = counts.count().block()
    val one = threads.first()
    println("%-34s %d calls in %3d ms on %d thread(s), e.g. %s (virtual=%s)".format(title, n,
        (System.nanoTime() - t0) / 1_000_000, threads.size, one.name, one.isVirtual))
}

/** Eight blocking stock-book calls of 100 ms each. Where you put subscribeOn decides how long they take. */
fun main(args: Array<String>) {
    if (args.firstOrNull() == "virtual") {
        // must be set before Reactor's Schedulers class is first used; normally a -D JVM flag
        System.setProperty("reactor.schedulers.defaultBoundedElasticOnVirtualThreads", "true")
    }
    val shops = listOf("shop-1", "shop-2", "shop-3", "shop-4", "shop-5", "shop-6", "shop-7", "shop-8")

    run("1. fromCallable, no scheduler", Flux.fromIterable(shops)
        .flatMap { s -> Mono.fromCallable { loavesLeft(s) } })

    run("2. subscribeOn on the outer Flux", Flux.fromIterable(shops)
        .flatMap { s -> Mono.fromCallable { loavesLeft(s) } }
        .subscribeOn(Schedulers.boundedElastic()))

    run("3. subscribeOn on each call", Flux.fromIterable(shops)
        .flatMap { s -> Mono.fromCallable { loavesLeft(s) }.subscribeOn(Schedulers.boundedElastic()) })
}
