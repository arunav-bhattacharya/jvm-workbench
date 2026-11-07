package workbench.performance.l04

import kotlin.concurrent.thread

// Kotlin twin of FalseSharingDemo.java: two threads, each incrementing its OWN volatile counter.
// Run 1: the counters sit next to each other. Run 2: they are padded apart (KPadded from LayoutDemo.kt).
// Whether you see a difference depends on your CPU and where the OS puts the threads.

private const val N = 25_000_000

private fun timeTwo(a: () -> Unit, b: () -> Unit): Long {
    val t0 = System.nanoTime()
    val t1 = thread { a() }
    val t2 = thread { b() }
    t1.join(); t2.join()
    return (System.nanoTime() - t0) / 1_000_000
}

fun main() {
    for (round in 1..3) {
        val adj = KAdjacent()
        val msAdjacent = timeTwo({ repeat(N) { adj.card++ } }, { repeat(N) { adj.sepa++ } })
        val pad = KPadded()
        val msPadded = timeTwo({ repeat(N) { pad.card++ } }, { repeat(N) { pad.sepa++ } })
        println("round %d: adjacent %,5d ms   padded %,5d ms   (counts %d/%d, %d/%d)"
            .format(round, msAdjacent, msPadded, adj.card, adj.sepa, pad.card, pad.sepa))
    }
}
