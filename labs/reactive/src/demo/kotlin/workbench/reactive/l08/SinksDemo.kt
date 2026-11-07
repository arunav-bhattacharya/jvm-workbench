package workbench.reactive.l08

import reactor.core.publisher.Sinks
import java.time.Duration
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

private val failures = AtomicInteger()

private fun race(title: String, emit: (Sinks.Many<Int>, Int) -> Unit) {
    val sink = Sinks.many().multicast().onBackpressureBuffer<Int>()
    val received = AtomicInteger()
    sink.asFlux().subscribe { received.incrementAndGet() }
    failures.set(0)
    val go = CountDownLatch(1)
    val threads = List(8) {
        thread {
            go.await()
            repeat(10_000) { i -> emit(sink, i) }
        }
    }
    go.countDown()
    threads.forEach { it.join() }
    println("%-32s received %,d of 80,000 (%,d emits failed)".format(title, received.get(), failures.get()))
}

/** Sinks push values into Reactor from ordinary code. Who receives what, and what happens with 8 threads? */
fun main() {
    val multicast = Sinks.many().multicast().onBackpressureBuffer<Int>()
    val early = CopyOnWriteArrayList<Int>()
    val late = CopyOnWriteArrayList<Int>()
    multicast.tryEmitNext(10)                                 // nobody is subscribed yet
    multicast.asFlux().subscribe { early += it }
    multicast.tryEmitNext(1)
    multicast.tryEmitNext(2)
    multicast.asFlux().subscribe { late += it }
    multicast.tryEmitNext(3)
    println("1. multicast:        early=$early  late=$late")

    val replay = Sinks.many().replay().limit<Int>(2)
    replay.tryEmitNext(1)
    replay.tryEmitNext(2)
    replay.tryEmitNext(3)
    val lateReplay = CopyOnWriteArrayList<Int>()
    replay.asFlux().subscribe { lateReplay += it }
    println("2. replay().limit(2): late=$lateReplay")

    val unicast = Sinks.many().unicast().onBackpressureBuffer<Int>()
    unicast.asFlux().subscribe()
    unicast.asFlux().subscribe({ }, { e -> println("3. unicast, second subscriber: ${e.message}") })

    race("4. tryEmitNext from 8 threads") { sink, i ->
        if (sink.tryEmitNext(i).isFailure) failures.incrementAndGet()
    }
    race("5. emitNext + busyLooping") { sink, i ->
        sink.emitNext(i, Sinks.EmitFailureHandler.busyLooping(Duration.ofSeconds(1)))
    }
}
