package workbench.reactive.l07

import reactor.core.publisher.Flux
import reactor.core.scheduler.Schedulers
import java.time.Duration
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong

private fun run(title: String, strategy: (Flux<Long>) -> Flux<Long>) {
    val produced = AtomicLong()
    val seen = CopyOnWriteArrayList<Long>()
    var error: String? = null
    try {
        strategy(Flux.interval(Duration.ofMillis(1)).doOnNext(produced::set))
            .publishOn(Schedulers.single(), 1)          // the screen asks for one tick at a time
            .doOnNext { Thread.sleep(10) }              // and takes 10 ms to draw it
            .take(20)
            .doOnNext { seen += it }
            .blockLast()
    } catch (e: RuntimeException) {
        error = e.message
    }
    println("%-28s ticker reached %3d, screen got %s".format(title, produced.get(), seen))
    if (error != null) println("%30sthen the error: %s".format("", error))
}

/** A ticker that can't slow down (one tick per ms) and a screen that needs 10 ms per tick. */
fun main() {
    run("1. no strategy") { it }
    val dropped = AtomicInteger()
    run("2. onBackpressureDrop") { it.onBackpressureDrop { dropped.incrementAndGet() } }
    println("%30s(%d ticks dropped)".format("", dropped.get()))
    run("3. onBackpressureLatest") { it.onBackpressureLatest() }
    run("4. onBackpressureBuffer(10)") { it.onBackpressureBuffer(10) }
    run("5. onBackpressureBuffer()") { it.onBackpressureBuffer() }
}
