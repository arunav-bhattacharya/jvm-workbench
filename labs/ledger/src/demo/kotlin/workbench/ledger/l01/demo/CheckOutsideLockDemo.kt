package workbench.ledger.l01.demo

import java.util.concurrent.CountDownLatch
import java.util.concurrent.ThreadLocalRandom
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.thread
import kotlin.concurrent.withLock

private class CheckedAccount(val id: Int) {
    val lock = ReentrantLock()
    var balance = 10_000L                            // guarded by lock

    fun read(): Long = lock.withLock { balance }
}

private val overdrafts = AtomicInteger()             // debits that left a balance below zero

// the bug: the check runs under from's lock, but that lock is released before the move
private fun checkFirst(from: CheckedAccount, to: CheckedAccount, cents: Long) {
    if (from.read() < cents) return                  // check
    lookUpFee()                                      // a slow step, outside any lock
    locked(from, to) { move(from, to, cents) }       // act, later
}

// the fix: check and act inside the same two locks
private fun checkInside(from: CheckedAccount, to: CheckedAccount, cents: Long) {
    lookUpFee()                                      // the same slow step, still outside the locks
    locked(from, to) {
        if (from.balance >= cents) move(from, to, cents)
    }
}

private fun move(from: CheckedAccount, to: CheckedAccount, cents: Long) {
    from.balance -= cents
    to.balance += cents
    if (from.balance < 0) overdrafts.incrementAndGet()   // the invariant, checked at the moment it can break
}

// stands in for a call to a fee table; it widens the gap between check and act
private fun lookUpFee() = repeat(200) { Thread.onSpinWait() }

private fun locked(a: CheckedAccount, b: CheckedAccount, body: () -> Unit) {
    val first = if (a.id < b.id) a else b
    val second = if (first === a) b else a
    first.lock.withLock { second.lock.withLock { body() } }
}

/**
 * Two ledgers that both lock accounts in id order. One checks the balance before it takes the
 * locks, the other checks after. Run each under 8 threads and test every invariant.
 */
fun main() {
    runVariant("check, then lock and move", ::checkFirst)
    runVariant("lock, then check and move", ::checkInside)
}

private fun runVariant(label: String, mover: (CheckedAccount, CheckedAccount, Long) -> Unit) {
    val accounts = Array(50) { CheckedAccount(it) }
    val go = CountDownLatch(1)
    val workers = List(8) {
        thread {
            val rnd = ThreadLocalRandom.current()
            go.await()
            repeat(100_000) {
                val a = rnd.nextInt(50)
                var b = rnd.nextInt(49)
                if (b >= a) b++
                mover(accounts[a], accounts[b], 1 + rnd.nextLong(5_000))
            }
        }
    }
    go.countDown()
    workers.forEach { it.join() }
    val total = accounts.sumOf { it.balance }
    val negative = accounts.count { it.balance < 0 }
    println(label)
    println("  total %,d %s, negative at the end: %d, overdrafts while running: %,d"
        .format(total, if (total == 500_000L) "(conserved)" else "(WRONG)", negative, overdrafts.getAndSet(0)))
}
