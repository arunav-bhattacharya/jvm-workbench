package workbench.concurrency.scratch

import java.time.Duration
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.CyclicBarrier
import java.util.concurrent.Phaser
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit
import kotlin.concurrent.thread

fun s10Latch() {
    val warmedUp = CountDownLatch(3)

    // each warm-up thread, when it is done (in a finally):
    warmedUp.countDown()

    // the thread that opens the service for traffic:
    if (!warmedUp.await(30, TimeUnit.SECONDS)) {
        throw IllegalStateException("caches not warm after 30 s")
    }
}

fun s10Barrier(me: Int, day: Int, simulate: (Int, Int) -> Long, recordExposure: (Long) -> Unit) {
    val shares = LongArray(4)
    val endOfDay = CyclicBarrier(4) { recordExposure(shares.sum()) }   // the barrier action

    // each of the 4 workers, for every simulated day:
    shares[me] = simulate(me, day)
    endOfDay.await()          // the 4th to arrive runs the action, then all 4 go on
}

class S10Request
class S10Authorization
class S10Issuer { fun authorize(r: S10Request) = S10Authorization() }

class S10Gate(private val issuer: S10Issuer) {
    private val issuerPermits = Semaphore(20)

    fun authorize(r: S10Request): S10Authorization {
        issuerPermits.acquire()              // before the try, like lock()
        try {
            return issuer.authorize(r)       // at most 20 threads in here
        } finally {
            issuerPermits.release()
        }
    }

    // compare
    fun authorize2(r: S10Request): S10Authorization =
        issuerPermits.withPermit { issuer.authorize(r) }    // at most 20 threads in here
}

inline fun <T> Semaphore.withPermit(block: () -> T): T {
    acquire()                     // before the try, like lock()
    try {
        return block()
    } finally {
        release()                 // exactly the permit we took
    }
}

fun s10Phaser() {
    val phaser = Phaser(1)          // the coordinator is a party
    phaser.register()               // each worker joins when it starts
    phaser.arriveAndAwaitAdvance()  // wait for everyone still registered
    phaser.arriveAndDeregister()    // leave; later phases wait for one party fewer
}

class S10Partition(val id: Int)
class S10Mismatch

fun s10Recon(partitions: List<S10Partition>, reconcile: (S10Partition) -> List<S10Mismatch>, report: (List<S10Mismatch>) -> Unit) {
    val done = CountDownLatch(partitions.size)
    val found = CopyOnWriteArrayList<S10Mismatch>()
    val failures = CopyOnWriteArrayList<Throwable>()
    for (p in partitions) {
        thread(name = "recon-${p.id}") {
            try {
                found.addAll(reconcile(p))          // 1. do the work
            } catch (e: Throwable) {
                failures.add(e)                      // 2. remember the failure instead of losing it
            } finally {
                done.countDown()                     // 3. always count down
            }
        }
    }
    if (!done.await(10, TimeUnit.MINUTES)) {         // 4. never wait forever
        throw IllegalStateException("reconciliation still running after 10 min")
    }
    if (failures.isNotEmpty()) throw IllegalStateException("partitions failed: $failures")
    report(found)                                    // 5. countDown happens-before await returns: all results visible
}

fun s10ReconBroken(partitions: List<S10Partition>, reconcile: (S10Partition) -> List<S10Mismatch>, report: (List<S10Mismatch>) -> Unit) {
    val done = CountDownLatch(4)
    val found = CopyOnWriteArrayList<S10Mismatch>()
    for (p in partitions) {
        thread {
            found.addAll(reconcile(p))
            done.countDown()
        }
    }
    done.await()
    report(found)
}

fun awaitAll(tasks: List<() -> Unit>, deadline: Duration): Boolean {
    val done = CountDownLatch(tasks.size)
    for (task in tasks) {
        thread {
            try {
                task()
            } finally {
                done.countDown()          // even when the task throws
            }
        }
    }
    return done.await(deadline.toMillis(), TimeUnit.MILLISECONDS)
}
