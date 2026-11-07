package workbench.concurrency.scratch

import java.util.concurrent.BlockingQueue
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit
import java.util.concurrent.locks.ReentrantLock
import java.util.concurrent.locks.ReentrantReadWriteLock

private val PILL = String(charArrayOf('P', 'I', 'L', 'L'))

fun s12Consumer(queue: BlockingQueue<String>, settle: (String) -> Unit) {
    // consumer
    while (true) {
        val record = queue.take()          // waits while the queue is empty
        if (record === PILL) break         // identity: a record "PILL" is still a record
        settle(record)
    }
}

fun s12Coordinator(queue: BlockingQueue<String>, consumers: Int) {
    // coordinator, after every producer has finished:
    repeat(consumers) { queue.put(PILL) }  // one pill per consumer
}

fun s12Forks(forks: Array<ReentrantLock>, seat: Int, n: Int, seats: Semaphore, eatWithBothForks: () -> Unit) {
    val left = seat
    val right = (seat + 1) % n
    val first = forks[minOf(left, right)]     // the last philosopher reaches right first
    val second = forks[maxOf(left, right)]
    first.lock(); second.lock(); second.unlock(); first.unlock()

    seats.acquire()                 // Semaphore(n - 1): one chair short, so someone can always eat
    try { eatWithBothForks() } finally { seats.release() }
}

fun s12Rw() {
    val a = ReentrantReadWriteLock()        // non-fair: a new reader waits if a writer is next in line
    val b = ReentrantReadWriteLock(true)    // fair: strict arrival order, lower throughput
}

class S12Pipeline(private val queue: BlockingQueue<String>, private val producers: List<Thread>, private val consumers: List<Thread>) {
    @Volatile var running = true

    fun shutdown() {
        running = false                                    // 1. producers stop polling Kafka
        producers.forEach { it.join() }                    // 2. wait until no producer can put again
        repeat(consumers.size) { queue.put(PILL) }         // 3. one pill per consumer, behind every real record
        val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(30)
        for (c in consumers) {
            c.join(maxOf(1L, TimeUnit.NANOSECONDS.toMillis(deadline - System.nanoTime())))   // 4. one deadline for all
        }
        consumers.filter { it.isAlive }.forEach { it.interrupt() }   // 5. still busy: interrupt; Kafka redelivers
    }
}
