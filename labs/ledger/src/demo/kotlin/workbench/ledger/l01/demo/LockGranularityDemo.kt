package workbench.ledger.l01.demo

import java.util.concurrent.CountDownLatch
import java.util.concurrent.ThreadLocalRandom
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.thread
import kotlin.concurrent.withLock

private class GranularityAccount(val id: Int) {
    val lock = ReentrantLock()
    var balance = 10_000L                            // guarded by lock (or by the global lock)
}

private val inside = AtomicInteger()                 // transfers inside a critical section right now
private val mostInside = AtomicInteger()

/** The same random transfers under one ledger-wide lock, then under per-account locks taken in id order. */
fun main(args: Array<String>) {
    val work = args.firstOrNull()?.toInt() ?: 50     // extra steps inside the lock, per transfer
    val global = ReentrantLock()
    val oneLock = { from: GranularityAccount, to: GranularityAccount, cents: Long ->
        global.withLock {                            // every transfer waits for every other one
            if (from.balance >= cents) { from.balance -= cents; to.balance += cents }
            sign(work)                               // stands in for real work: an entry, a signature
        }
    }
    val perAccount = { from: GranularityAccount, to: GranularityAccount, cents: Long ->
        val first = if (from.id < to.id) from else to   // lower id first: no cycle can form
        val second = if (first === from) to else from
        first.lock.withLock {
            second.lock.withLock {
                if (from.balance >= cents) { from.balance -= cents; to.balance += cents }
                sign(work)
            }
        }
    }
    println("8 threads x 50,000 transfers, 50 accounts, $work steps of work inside the lock")
    for (round in 0 until 3) {                       // round 0 only warms up the JIT
        time("one ledger lock  ", oneLock, round > 0)
        time("per-account locks", perAccount, round > 0)
    }
}

private fun sign(steps: Int) {
    val now = inside.incrementAndGet()
    mostInside.accumulateAndGet(now, ::maxOf)
    repeat(steps) { Thread.onSpinWait() }
    inside.decrementAndGet()
}

private fun time(label: String, mover: (GranularityAccount, GranularityAccount, Long) -> Unit, print: Boolean) {
    val accounts = Array(50) { GranularityAccount(it) }
    val go = CountDownLatch(1)
    val workers = List(8) {
        thread {
            val rnd = ThreadLocalRandom.current()
            go.await()
            repeat(50_000) {
                val a = rnd.nextInt(50)
                var b = rnd.nextInt(49)
                if (b >= a) b++
                mover(accounts[a], accounts[b], 1 + rnd.nextLong(5_000))
            }
        }
    }
    val t0 = System.nanoTime()
    go.countDown()
    workers.forEach { it.join() }
    val ms = (System.nanoTime() - t0) / 1_000_000
    val total = accounts.sumOf { it.balance }        // after join(): every write is visible
    if (print) println("%s %5d ms, total %,d, most transfers in progress at once: %d".format(label, ms, total, mostInside.get()))
    mostInside.set(0)
}
