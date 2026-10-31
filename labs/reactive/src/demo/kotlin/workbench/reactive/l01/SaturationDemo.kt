package workbench.reactive.l01

import java.util.concurrent.Flow
import java.util.concurrent.ForkJoinPool
import java.util.concurrent.SubmissionPublisher
import java.util.concurrent.atomic.AtomicInteger

/** A SubmissionPublisher with a 2-slot buffer and a subscriber that never asks for anything. */
fun main() {
    println("default buffer: ${Flow.defaultBufferSize()}")
    val dropped = AtomicInteger()
    SubmissionPublisher<Int>(ForkJoinPool.commonPool(), 2).use { publisher ->
        publisher.subscribe(object : Flow.Subscriber<Int> {
            override fun onSubscribe(s: Flow.Subscription) {}             // never calls request(n)
            override fun onNext(item: Int) = println("got $item")
            override fun onError(t: Throwable) {}
            override fun onComplete() {}
        })
        for (i in 1..10) {
            // offer() does not block. When the buffer is full it calls the drop handler instead.
            val lag = publisher.offer(i) { _, _ ->
                dropped.incrementAndGet()
                false                                                   // false: don't retry, drop it
            }
            println("offer($i) -> $lag")
        }
        println("dropped ${dropped.get()} of 10, lag ${publisher.estimateMaximumLag()}")
    }
}
