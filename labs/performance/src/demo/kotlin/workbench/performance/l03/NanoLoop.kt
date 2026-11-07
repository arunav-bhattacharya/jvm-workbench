package workbench.performance.l03

import kotlin.math.sqrt

// Kotlin twin of NanoLoop.java: the same naive nanoTime benchmark, with the result
// thrown away and with the result used.
fun main() {
    val x = 2.0
    for (round in 1..5) {
        val t0 = System.nanoTime()
        for (i in 0 until 100_000_000) {
            sqrt(x)                                // result discarded
        }
        val t1 = System.nanoTime()

        var sum = 0.0
        for (i in 0 until 100_000_000) {
            sum += sqrt(x + i)                     // result used
        }
        val t2 = System.nanoTime()

        println("round %d: discarded %.4f ns/op, used %.4f ns/op (sum %.1f)"
            .format(round, (t1 - t0) / 1e8, (t2 - t1) / 1e8, sum))
    }
}
