package workbench.jmm.l06

import java.lang.invoke.MethodHandles
import java.lang.invoke.VarHandle
import java.util.concurrent.atomic.AtomicInteger
import java.util.function.IntConsumer
import kotlin.concurrent.thread

/*
 * The store-buffering test from lesson 1, once per VarHandle access mode. Thread A runs
 * `x = 1; r1 = y` and thread B runs `y = 1; r2 = x`. Count the trials where both read 0.
 */
private class IntPair { var x = 0; var y = 0 }

private val X: VarHandle = MethodHandles.lookup().findVarHandle(IntPair::class.java, "x", Int::class.javaPrimitiveType)
private val Y: VarHandle = MethodHandles.lookup().findVarHandle(IntPair::class.java, "y", Int::class.javaPrimitiveType)

private const val TRIALS = 1 shl 18
private const val BATCH = 32

fun main() {
    for (run in 1..3) {
        println("run %d: both read 0 with plain %,6d | opaque %,6d | release/acquire %,6d | volatile %,d  (of %,d)"
            .format(run, plain(), opaque(), releaseAcquire(), volatileMode(), TRIALS))
    }
}

private fun plain(): Int {
    val s = Array(TRIALS) { IntPair() }; val r1 = IntArray(TRIALS); val r2 = IntArray(TRIALS)
    race(IntConsumer { i -> X.set(s[i], 1); r1[i] = Y.get(s[i]) as Int },
         IntConsumer { i -> Y.set(s[i], 1); r2[i] = X.get(s[i]) as Int })
    return bothZero(r1, r2)
}

private fun opaque(): Int {
    val s = Array(TRIALS) { IntPair() }; val r1 = IntArray(TRIALS); val r2 = IntArray(TRIALS)
    race(IntConsumer { i -> X.setOpaque(s[i], 1); r1[i] = Y.getOpaque(s[i]) as Int },
         IntConsumer { i -> Y.setOpaque(s[i], 1); r2[i] = X.getOpaque(s[i]) as Int })
    return bothZero(r1, r2)
}

private fun releaseAcquire(): Int {
    val s = Array(TRIALS) { IntPair() }; val r1 = IntArray(TRIALS); val r2 = IntArray(TRIALS)
    race(IntConsumer { i -> X.setRelease(s[i], 1); r1[i] = Y.getAcquire(s[i]) as Int },
         IntConsumer { i -> Y.setRelease(s[i], 1); r2[i] = X.getAcquire(s[i]) as Int })
    return bothZero(r1, r2)
}

private fun volatileMode(): Int {
    val s = Array(TRIALS) { IntPair() }; val r1 = IntArray(TRIALS); val r2 = IntArray(TRIALS)
    race(IntConsumer { i -> X.setVolatile(s[i], 1); r1[i] = Y.getVolatile(s[i]) as Int },
         IntConsumer { i -> Y.setVolatile(s[i], 1); r2[i] = X.getVolatile(s[i]) as Int })
    return bothZero(r1, r2)
}

// Runs a(i) and b(i) for every trial on two threads. A small spin barrier every BATCH trials
// keeps the two threads on the same trial at about the same moment.
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
        while (other.get() < batch) Thread.onSpinWait()   // wait for the other thread
        for (i in batch * BATCH until (batch + 1) * BATCH) side.accept(i)
    }
}

private fun bothZero(r1: IntArray, r2: IntArray): Int = r1.indices.count { r1[it] == 0 && r2[it] == 0 }
