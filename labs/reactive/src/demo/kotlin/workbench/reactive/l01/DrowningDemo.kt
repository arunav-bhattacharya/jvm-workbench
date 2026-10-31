package workbench.reactive.l01

import java.util.concurrent.Executors
import java.util.concurrent.Flow
import java.util.concurrent.SubmissionPublisher
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicLong

private const val EVENTS = 100_000

/** A fast producer and a slow ledger writer, first with plain push, then with demand. */
fun main() {
    pushWithoutDemand()
    pushWithDemand()
}

// Plain push: the producer hands every event to the writer's executor. Its queue has no limit.
private fun pushWithoutDemand() {
    val writer = Executors.newSingleThreadExecutor()
    val written = AtomicLong()
    val t0 = System.nanoTime()
    repeat(EVENTS) {
        writer.execute { writeToLedger(); written.incrementAndGet() }
    }
    val ms = (System.nanoTime() - t0) / 1_000_000
    val w = written.get()
    println("plain push:  producer done in %,5d ms, ledger wrote %,6d, %,6d events waiting in memory".format(ms, w, EVENTS - w))
    writer.shutdownNow()
}

// With demand: the writer asks for one event at a time. submit() blocks when the 256-slot buffer is full.
private fun pushWithDemand() {
    val written = AtomicLong()
    var maxLag = 0L
    val t0 = System.nanoTime()
    SubmissionPublisher<Int>().use { publisher ->
        publisher.subscribe(object : Flow.Subscriber<Int> {
            private lateinit var s: Flow.Subscription
            override fun onSubscribe(s: Flow.Subscription) { this.s = s; s.request(1) }
            override fun onNext(event: Int) { writeToLedger(); written.incrementAndGet(); s.request(1) }
            override fun onError(t: Throwable) = t.printStackTrace()
            override fun onComplete() {}
        })
        for (i in 0 until EVENTS) {
            publisher.submit(i)                                    // waits while the buffer is full
            maxLag = maxOf(maxLag, publisher.estimateMaximumLag().toLong())
        }
        val ms = (System.nanoTime() - t0) / 1_000_000
        println("with demand: producer done in %,5d ms, ledger wrote %,6d, never more than %,d waiting".format(ms, written.get(), maxLag))
    }
    TimeUnit.MILLISECONDS.sleep(50)
}

// stands in for a 10-microsecond ledger write
private fun writeToLedger() {
    val until = System.nanoTime() + 10_000
    while (System.nanoTime() < until) Thread.onSpinWait()
}
