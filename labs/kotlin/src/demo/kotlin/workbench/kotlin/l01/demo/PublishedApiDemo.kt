package workbench.kotlin.l01.demo

import java.util.concurrent.atomic.AtomicInteger

/**
 * A public inline function is pasted into callers, possibly in another module. So its body may
 * only use declarations those callers could use themselves.
 */
inline fun <T> traced(operation: String, block: () -> T): T {
    val id = nextTraceId()
    println("[$id] start $operation")
    val result = block()
    println("[$id] end $operation")
    return result
}

/** Not part of the Kotlin API, but public in the bytecode, so the pasted copies can call it. */
@PublishedApi
internal fun nextTraceId(): String = "trace-" + counter.incrementAndGet()

private val counter = AtomicInteger()   // fine: nextTraceId is not inline, so its body is never copied

/** An inline property: no backing field, and the getter is pasted into each caller. */
val Long.asEuros: String
    inline get() = "EUR " + (this / 100) + "." + (this % 100).toString().padStart(2, '0')

fun main() {
    val refunded = traced("refund pay_7") { 1_999L }
    println("refunded ${refunded.asEuros}")

    // Wrong move. Change `@PublishedApi internal` on nextTraceId to `private`, predict, run.
}
