package workbench.concurrency.l01

import kotlin.concurrent.thread

// The same slice-and-join idea as LedgerTotals, written with Kotlin's thread {} builder.
fun main() {
    val amounts = LongArray(1_000) { it + 1L }
    val partial = LongArray(4)
    val chunk = amounts.size / partial.size

    val workers = List(partial.size) { w ->
        thread(name = "ledger-worker-$w") {       // starts at once: start = true is the default
            var sum = 0L
            for (i in w * chunk until (w + 1) * chunk) sum += amounts[i]
            partial[w] = sum
        }
    }
    workers.forEach { it.join() }                  // join is the same java.lang.Thread method

    println("total = ${partial.sum()} on ${workers.map { it.name }}")
}
