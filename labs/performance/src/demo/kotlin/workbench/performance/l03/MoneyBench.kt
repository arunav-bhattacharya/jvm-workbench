package workbench.performance.l03

// MoneyBench.java measures with JMH, which needs Java classes in this lab. This Kotlin twin runs
// the same two fee calculations written in Kotlin and reads the JVM's per-thread allocation
// counter around 100,000 calls: the same bytes-per-call idea as JMH's gc.alloc.rate.norm.
// Allocation is steady enough to count this way. Time is not (remember NanoLoop).
import java.lang.management.ManagementFactory
import java.math.BigDecimal
import java.math.RoundingMode

private val amounts = Array(100) { BigDecimal.valueOf(1_999L + it, 2) }
private val cents = LongArray(100) { 1_999L + it }

fun feeBigDecimal(): BigDecimal {
    var total = BigDecimal.ZERO
    for (a in amounts) {
        // a new rate object per line; the operators call multiply and add
        total += (a * BigDecimal("0.029")).setScale(2, RoundingMode.HALF_EVEN)
    }
    return total
}

fun feeLongCents(): Long {
    var total = 0L
    for (c in cents) total += (c * 29 + 500) / 1000   // 2.9% in integer cents, rounded half up
    return total
}

private val threads = ManagementFactory.getThreadMXBean() as com.sun.management.ThreadMXBean
private var lastDecimal: BigDecimal? = null              // results go somewhere the JIT can't ignore
private var lastCents = 0L

private inline fun bytesPerCall(calls: Int, block: () -> Unit): Double {
    repeat(50_000) { block() }                           // warm up first, so C2 code is measured
    val before = threads.currentThreadAllocatedBytes
    repeat(calls) { block() }
    return (threads.currentThreadAllocatedBytes - before).toDouble() / calls
}

fun main() {
    val big = bytesPerCall(100_000) { lastDecimal = feeBigDecimal() }
    val small = bytesPerCall(100_000) { lastCents += feeLongCents() }
    println("feeBigDecimal: %10.3f B/op".format(big))
    println("feeLongCents:  %10.3f B/op".format(small))
    println("(results: $lastDecimal, $lastCents)")
}
