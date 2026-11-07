package workbench.ledger.l01.demo

import java.util.concurrent.CountDownLatch
import java.util.concurrent.ThreadLocalRandom
import kotlin.concurrent.thread

private const val ACCOUNTS = 50
private const val OPENING = 10_000L              // cents per account: 500,000 in total

/** A ledger with no locks: 8 threads move money between 50 accounts. Count what goes wrong. */
fun main(args: Array<String>) {
    val perThread = args.firstOrNull()?.toInt() ?: 100_000
    for (run in 1..3) {
        val balance = LongArray(ACCOUNTS) { OPENING }
        val go = CountDownLatch(1)
        val workers = List(8) {
            thread {
                val rnd = ThreadLocalRandom.current()
                go.await()
                repeat(perThread) {
                    val from = rnd.nextInt(ACCOUNTS)
                    val to = rnd.nextInt(ACCOUNTS)
                    if (from != to) {
                        val cents = 1 + rnd.nextLong(5_000)
                        if (balance[from] >= cents) {     // check
                            balance[from] -= cents        // act: read, subtract, write
                            balance[to] += cents          //      read, add, write
                        }
                    }
                }
            }
        }
        go.countDown()
        workers.forEach { it.join() }
        val total = balance.sum()
        println("run %d: total %,d cents, expected 500,000, off by %,d".format(run, total, total - ACCOUNTS * OPENING))
    }
}
