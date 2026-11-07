package workbench.ledger.l01.demo

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.LongAdder

// the mutable row a parser fills in for each line, then reuses for the next line
private class ImportRow {
    var id = ""
    var cents = 0L
}

private data class ImportedTransfer(val id: String, val cents: Long)   // immutable: one new value per line

private val appliedCents = LongAdder()
private val appliedLines: MutableSet<String> = ConcurrentHashMap.newKeySet()
private val mixed = AtomicInteger()

/** An importer parses 100,000 lines and hands each one to a pool. Pass "record" to use an immutable value. */
fun main(args: Array<String>) {
    val immutable = args.firstOrNull() == "record"
    val pool = Executors.newFixedThreadPool(4)
    var fileCents = 0L
    val row = ImportRow()
    for (line in 0 until 100_000) {
        val cents = 100L + line % 900
        fileCents += cents
        if (immutable) {
            val t = ImportedTransfer("line-$line", cents)
            pool.execute { applyLine(t.id, t.cents) }
        } else {
            row.id = "line-$line"                        // overwrite the shared row...
            row.cents = cents
            pool.execute { applyLine(row.id, row.cents) }    // ...read it later
        }
    }
    pool.shutdown()
    pool.awaitTermination(30, TimeUnit.SECONDS)
    println("file: 100,000 lines, %,d cents".format(fileCents))
    println("applied: %,d different lines, %,d cents, %,d rows mixing two lines".format(appliedLines.size, appliedCents.sum(), mixed.get()))
}

// stands in for ledger.apply: records what the worker saw
private fun applyLine(id: String, cents: Long) {
    appliedCents.add(cents)
    appliedLines += id
    val line = id.removePrefix("line-").toInt()
    if (cents != 100L + line % 900) mixed.incrementAndGet()   // the id and the amount came from different lines
}
