package workbench.ledger.l02.demo

import java.util.concurrent.ThreadLocalRandom
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock

private class SnapshotAccount(val id: Int) {
    val lock = ReentrantLock()
    var balance = 1_000L                                      // guarded by lock: 50,000 in total
}

/**
 * Four threads move money between 50 accounts while a reader adds up all the balances.
 * Pass "locked" to make the reader hold every account lock while it adds.
 */
fun main(args: Array<String>) {
    val locked = args.firstOrNull() == "locked"
    val accounts = Array(50) { SnapshotAccount(it) }
    val writers = List(4) {
        Thread.ofPlatform().start {
            val rnd = ThreadLocalRandom.current()
            repeat(200_000) {
                val a = rnd.nextInt(50)
                var b = rnd.nextInt(49)
                if (b >= a) b++
                move(accounts[a], accounts[b], 1 + rnd.nextLong(500))
            }
        }
    }
    var taken = 0L
    var torn = 0L
    var worst = 0L
    while (writers.any { it.isAlive }) {
        val sum = if (locked) sumAllLocked(accounts) else sumOneByOne(accounts)
        taken++
        if (sum != 50_000L) {
            torn++
            worst = maxOf(worst, Math.abs(sum - 50_000))
        }
    }
    println("%s: %,d snapshots, %,d torn (worst off by %,d cents)"
        .format(if (locked) "every lock held" else "one account at a time", taken, torn, worst))
}

// each read is safe on its own; the sum is not, because money moves between reads
private fun sumOneByOne(accounts: Array<SnapshotAccount>): Long =
    accounts.sumOf { a -> a.lock.withLock { a.balance } }

// every lock, in id order: no transfer can run while we add, so the sum is one instant
private fun sumAllLocked(accounts: Array<SnapshotAccount>): Long {
    accounts.forEach { it.lock.lock() }
    try {
        return accounts.sumOf { it.balance }
    } finally {
        accounts.reversed().forEach { it.lock.unlock() }
    }
}

private fun move(from: SnapshotAccount, to: SnapshotAccount, cents: Long) {
    val first = if (from.id < to.id) from else to
    val second = if (first === from) to else from
    first.lock.withLock {
        second.lock.withLock {
            if (from.balance >= cents) { from.balance -= cents; to.balance += cents }
        }
    }
}
