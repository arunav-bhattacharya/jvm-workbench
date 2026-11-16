package workbench.executors.l04

import java.util.concurrent.Executors

@Volatile private var sink = 0L          // keeps each result, so the JIT can't skip the work
@Volatile private var cancelledAt = 0L   // when main called cancel, for the ignorer's report

// a few milliseconds of CPU work: 400 of them take a second or more
private fun slice(start: Long): Long {
    var x = start
    for (i in 0 until 2_000_000) x = x * 31 + i
    return x
}

/** cancel(true) on three tasks: one that sleeps, one that checks the flag, one that never looks. */
fun main() {
    Executors.newFixedThreadPool(3).use { pool ->
        val sleeper = pool.submit {
            try {
                Thread.sleep(5_000)
                println("sleeper: woke up normally")
            } catch (e: InterruptedException) {
                println("sleeper: InterruptedException, stopping")
            }
        }
        val checker = pool.submit {
            var x = 0L
            for (s in 0 until 400) {
                if (Thread.currentThread().isInterrupted) {
                    println("checker: saw the flag after $s slices, stopping")
                    return@submit
                }
                x = slice(x)
            }
            sink = x
            println("checker: finished all 400 slices")
        }
        val ignorer = pool.submit {
            var x = 0L
            repeat(400) { x = slice(x) }                // never looks at the flag
            sink = x
            val late = (System.nanoTime() - cancelledAt) / 1_000_000
            println("ignorer: finished all 400 slices anyway, $late ms after the cancel")
        }

        Thread.sleep(100)
        cancelledAt = System.nanoTime()
        listOf(sleeper, checker, ignorer).forEach { it.cancel(true) }
        println("after cancel: isCancelled=%b/%b/%b isDone=%b/%b/%b".format(
            sleeper.isCancelled, checker.isCancelled, ignorer.isCancelled,
            sleeper.isDone, checker.isDone, ignorer.isDone))
    }   // close() waits: the ignorer is still burning CPU
    println("pool closed")
}
