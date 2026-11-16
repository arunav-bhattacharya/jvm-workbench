package workbench.reactive.l01

import java.util.concurrent.Executors
import java.util.concurrent.Flow
import java.util.concurrent.SubmissionPublisher
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicLong

private const val LOAVES = 100_000

/** A fast oven and a slow packer, first with plain push, then with demand. */
fun main() {
    pushWithoutDemand()
    pushWithDemand()
}

// Plain push: the oven hands every loaf to the packer's executor. Its queue has no limit.
private fun pushWithoutDemand() {
    val packer = Executors.newSingleThreadExecutor()
    val boxed = AtomicLong()
    val t0 = System.nanoTime()
    repeat(LOAVES) {
        packer.execute { packLoaf(); boxed.incrementAndGet() }
    }
    val ms = (System.nanoTime() - t0) / 1_000_000
    val b = boxed.get()
    println("plain push:  oven done in %,5d ms, packer boxed %,7d, %,6d loaves waiting in memory".format(ms, b, LOAVES - b))
    packer.shutdownNow()
}

// With demand: the packer asks for one loaf at a time. submit() blocks when the 256-slot buffer is full.
private fun pushWithDemand() {
    val boxed = AtomicLong()
    var maxLag = 0L
    val t0 = System.nanoTime()
    SubmissionPublisher<Int>().use { publisher ->
        publisher.subscribe(object : Flow.Subscriber<Int> {
            private lateinit var s: Flow.Subscription
            override fun onSubscribe(s: Flow.Subscription) { this.s = s; s.request(1) }
            override fun onNext(loaf: Int) { packLoaf(); boxed.incrementAndGet(); s.request(1) }
            override fun onError(t: Throwable) = t.printStackTrace()
            override fun onComplete() {}
        })
        for (i in 0 until LOAVES) {
            publisher.submit(i)                                    // waits while the buffer is full
            maxLag = maxOf(maxLag, publisher.estimateMaximumLag().toLong())
        }
        val ms = (System.nanoTime() - t0) / 1_000_000
        println("with demand: oven done in %,5d ms, packer boxed %,7d, never more than %,d waiting".format(ms, boxed.get(), maxLag))
    }
    TimeUnit.MILLISECONDS.sleep(50)
}

// stands in for 10 microseconds of packing one loaf
private fun packLoaf() {
    val until = System.nanoTime() + 10_000
    while (System.nanoTime() < until) Thread.onSpinWait()
}
