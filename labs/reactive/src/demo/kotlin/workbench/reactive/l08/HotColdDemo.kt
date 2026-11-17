package workbench.reactive.l08

import reactor.core.publisher.Flux
import java.time.Duration
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

private val connections = AtomicInteger()

// a cold feed: every subscriber opens its own connection and gets readings from the start, one per 100 ms
private fun thermometer(): Flux<String> =
    Flux.interval(Duration.ofMillis(100)).take(5)
        .map { i -> "20$i" }
        .doOnSubscribe { connections.incrementAndGet() }

private fun run(title: String, feed: Flux<String>) {
    connections.set(0)
    val a = CopyOnWriteArrayList<String>()
    val b = CopyOnWriteArrayList<String>()
    val done = CountDownLatch(2)
    feed.doFinally { done.countDown() }.subscribe { a += it }
    Thread.sleep(250)
    feed.doFinally { done.countDown() }.subscribe { b += it }
    done.await(3, TimeUnit.SECONDS)
    println("%-28s connections=%d%n%5sA=%s%n%5sB=%s".format(title, connections.get(), "", a, "", b))
}

/** One cold thermometer feed, shared five ways between screen A (starts now) and screen B (joins 250 ms later). */
fun main() {
    run("1. cold", thermometer())
    run("2. share()", thermometer().share())
    run("3. replay(1).refCount()", thermometer().replay(1).refCount())
    run("4. cache()", thermometer().cache())
    run("5. publish().autoConnect(2)", thermometer().publish().autoConnect(2))
}
