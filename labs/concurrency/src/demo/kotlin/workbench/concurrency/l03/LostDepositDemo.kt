package workbench.concurrency.l03

import java.util.concurrent.ConcurrentHashMap
import kotlin.concurrent.thread

// Eight consumer threads post one-cent deposits to the same merchant account, three ways.
private const val CONSUMERS = 8
private const val DEPOSITS = 200_000                         // per thread, one cent each
private const val MERCHANT = "merchant-42"

// @Volatile only so the JIT re-reads the field every time, as in RaceDemo. It does NOT make += safe.
@Volatile private var balanceCents = 0L
private val balances = ConcurrentHashMap<String, Long>()

fun main() {
    balanceCents = 0
    post { balanceCents += 1 }                                       // 1. a plain field
    report("balanceCents += 1", balanceCents)

    balances[MERCHANT] = 0L
    post { balances[MERCHANT] = balances.getValue(MERCHANT) + 1 }    // 2. a thread-safe map, two calls
    report("put(get() + 1)", balances.getValue(MERCHANT))

    balances[MERCHANT] = 0L
    post { balances.merge(MERCHANT, 1L, Long::plus) }                // 3. the same map, one call
    report("merge(1, Long::plus)", balances.getValue(MERCHANT))
}

private fun post(deposit: () -> Unit) {
    val consumers = List(CONSUMERS) { c ->
        thread(name = "consumer-$c") { repeat(DEPOSITS) { deposit() } }
    }
    consumers.forEach { it.join() }
}

private fun report(how: String, cents: Long) {
    val expected = CONSUMERS.toLong() * DEPOSITS
    println("%-20s expected %,d cents, got %,d (lost %,d)".format(how, expected, cents, expected - cents))
}
