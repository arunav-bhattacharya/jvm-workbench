package workbench.jmm.l03

import java.util.concurrent.atomic.AtomicInteger
import java.util.function.IntConsumer
import kotlin.concurrent.thread

/*
 * The store-buffering test from lesson 1 of this track, three ways: no @Volatile, only x @Volatile,
 * both fields @Volatile. Thread A runs `x = 1; r1 = y` and thread B runs `y = 1; r2 = x`.
 * Counts the trials where both threads read 0.
 */
private class NoVolatile { var x = 0; var y = 0 }
private class XVolatile { @Volatile var x = 0; var y = 0 }
private class BothVolatile { @Volatile var x = 0; @Volatile var y = 0 }

private const val TRIALS = 1 shl 19
private const val BATCH = 32

fun main() {
    for (run in 1..3) {
        println("run %d: both read 0 in  plain: %,7d   only x @Volatile: %,7d   both @Volatile: %,d"
            .format(run, plain(), xOnly(), both()))
    }
}

private fun plain(): Int {
    val s = Array(TRIALS) { NoVolatile() }
    val r1 = IntArray(TRIALS)
    val r2 = IntArray(TRIALS)
    race(IntConsumer { i -> s[i].x = 1; r1[i] = s[i].y }, IntConsumer { i -> s[i].y = 1; r2[i] = s[i].x })
    return bothZero(r1, r2)
}

private fun xOnly(): Int {
    val s = Array(TRIALS) { XVolatile() }
    val r1 = IntArray(TRIALS)
    val r2 = IntArray(TRIALS)
    race(IntConsumer { i -> s[i].x = 1; r1[i] = s[i].y }, IntConsumer { i -> s[i].y = 1; r2[i] = s[i].x })
    return bothZero(r1, r2)
}

private fun both(): Int {
    val s = Array(TRIALS) { BothVolatile() }
    val r1 = IntArray(TRIALS)
    val r2 = IntArray(TRIALS)
    race(IntConsumer { i -> s[i].x = 1; r1[i] = s[i].y }, IntConsumer { i -> s[i].y = 1; r2[i] = s[i].x })
    return bothZero(r1, r2)
}

// Runs a(i) and b(i) for every trial on two threads, in lockstep batches so they overlap.
private fun race(a: IntConsumer, b: IntConsumer) {
    val doneA = AtomicInteger()
    val doneB = AtomicInteger()
    val ta = thread { runSide(a, doneA, doneB) }
    val tb = thread { runSide(b, doneB, doneA) }
    ta.join(); tb.join()
}

private fun runSide(side: IntConsumer, mine: AtomicInteger, other: AtomicInteger) {
    for (batch in 0 until TRIALS / BATCH) {
        mine.set(batch)
        while (other.get() < batch) Thread.onSpinWait()
        for (i in batch * BATCH until (batch + 1) * BATCH) side.accept(i)
    }
}

private fun bothZero(r1: IntArray, r2: IntArray): Int = r1.indices.count { r1[it] == 0 && r2[it] == 0 }
