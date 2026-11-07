package workbench.concurrency.l09

import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.BlockingQueue
import java.util.concurrent.LinkedBlockingQueue
import java.util.concurrent.SynchronousQueue
import java.util.concurrent.TimeUnit
import kotlin.concurrent.thread

// The four ways to add to a full BlockingQueue, and two queues that surprise people.
fun main() {
    val q: BlockingQueue<String> = ArrayBlockingQueue(2)
    q.put("e-1")
    q.put("e-2")                                                   // now full

    try { q.add("e-3") } catch (e: IllegalStateException) { println("add:            throws $e") }
    println("offer:          ${q.offer("e-3")}")
    val t0 = System.nanoTime()
    val timed = q.offer("e-3", 300, TimeUnit.MILLISECONDS)
    println("offer(300 ms):  $timed after ${(System.nanoTime() - t0) / 1_000_000} ms")

    val producer = thread { q.put("e-3") }
    Thread.sleep(200)
    println("put:            producer is ${producer.state} until space opens")
    println("take:           ${q.take()} (frees a slot)")
    producer.join()
    println("queue now:      $q")

    // Kotlin won't even compile q.offer(null) on a BlockingQueue<String>; the JDK would throw NullPointerException

    println("LinkedBlockingQueue() capacity: ${LinkedBlockingQueue<String>().remainingCapacity()}")
    println("SynchronousQueue.offer with no taker waiting: ${SynchronousQueue<String>().offer("e-9")}")
}
