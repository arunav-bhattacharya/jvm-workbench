package workbench.executors.l04

import java.util.concurrent.Executors

// about a second of CPU work, in slices
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
            println("checker: finished all slices ${x and 1}")
        }
        val ignorer = pool.submit {
            var x = 0L
            repeat(400) { x = slice(x) }                // never looks at the flag
            println("ignorer: finished all 400 slices anyway ${x and 1}")
        }

        Thread.sleep(100)
        listOf(sleeper, checker, ignorer).forEach { it.cancel(true) }
        println("after cancel: isCancelled=%b/%b/%b isDone=%b/%b/%b".format(
            sleeper.isCancelled, checker.isCancelled, ignorer.isCancelled,
            sleeper.isDone, checker.isDone, ignorer.isDone))
    }   // close() waits: the ignorer is still burning CPU
    println("pool closed")
}
