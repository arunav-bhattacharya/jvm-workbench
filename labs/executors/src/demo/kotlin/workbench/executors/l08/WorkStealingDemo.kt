package workbench.executors.l08

import java.util.TreeMap
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.ForkJoinPool
import java.util.concurrent.RecursiveTask
import java.util.concurrent.atomic.LongAdder

private val leaves = ConcurrentHashMap<String, LongAdder>()

private fun fee(amountCents: Long): Long {
    var h = amountCents
    for (i in 0 until 100) h = (h * 31 + i) % 1_000_003         // stands in for real fee rules
    return amountCents * 29 / 1_000 + 30 + h % 2
}

private class Fees(
    val amounts: LongArray, val from: Int, val to: Int, val threshold: Int, val wrong: Boolean,
) : RecursiveTask<Long>() {
    override fun compute(): Long {
        if (to - from <= threshold) {
            leaves.computeIfAbsent(Thread.currentThread().name) { LongAdder() }.increment()
            var sum = 0L
            for (i in from until to) sum += fee(amounts[i])
            return sum
        }
        val mid = (from + to) ushr 1
        val left = Fees(amounts, from, mid, threshold, wrong)
        val right = Fees(amounts, mid, to, threshold, wrong)
        left.fork()
        if (wrong) {
            val leftFees = left.join()                 // waits for the left half before starting the right one
            return leftFees + right.compute()
        }
        val rightFees = right.compute()                // works on the right half while the left one can be stolen
        return left.join() + rightFees
    }
}

/** Fees over 2,000,000 ledger entries on a 4-worker ForkJoinPool. Args: [right|wrong] [threshold]. */
fun main(args: Array<String>) {
    val wrong = args.getOrNull(0) == "wrong"
    val threshold = args.getOrNull(1)?.toInt() ?: 50_000
    val amounts = LongArray(2_000_000) { i -> 100 + (i * 7919L) % 250_000 }

    val s0 = System.nanoTime()
    var expected = 0L
    for (a in amounts) expected += fee(a)                          // one thread, for comparison
    println("one thread:  %,d ms".format((System.nanoTime() - s0) / 1_000_000))

    ForkJoinPool(4).use { pool ->
        val t0 = System.nanoTime()
        val total = pool.submit(Fees(amounts, 0, amounts.size, threshold, wrong)).join()
        val ms = (System.nanoTime() - t0) / 1_000_000
        TreeMap(leaves).forEach { (thread, n) -> println("%-24s %4d leaves".format(thread, n.sum())) }
        println("%s order, threshold %,d: %,d ms, %d steals, same total: %b".format(
            if (wrong) "wrong" else "right", threshold, ms, pool.stealCount, total == expected))
    }
}
