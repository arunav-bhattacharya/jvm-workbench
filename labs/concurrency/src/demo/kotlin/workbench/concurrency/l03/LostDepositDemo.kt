package workbench.concurrency.l03

import java.util.concurrent.ConcurrentHashMap
import kotlin.concurrent.thread

// Eight teller threads put one-cent deposits into the same bank account, three ways.
private const val TELLERS = 8
private const val DEPOSITS = 200_000                         // per thread, one cent each
private const val ACCOUNT = "account-42"

// @Volatile only so the JIT re-reads the field every time, as in RaceDemo. It does NOT make += safe.
@Volatile private var balanceCents = 0L
private val balances = ConcurrentHashMap<String, Long>()

fun main() {
    balanceCents = 0
    runTellers { balanceCents += 1 }                                    // 1. a plain field
    report("balanceCents += 1", balanceCents)

    balances[ACCOUNT] = 0L
    runTellers { balances[ACCOUNT] = balances.getValue(ACCOUNT) + 1 }   // 2. a thread-safe map, two calls
    report("put(get() + 1)", balances.getValue(ACCOUNT))

    balances[ACCOUNT] = 0L
    runTellers { balances.merge(ACCOUNT, 1L, Long::plus) }              // 3. the same map, one call
    report("merge(1, Long::plus)", balances.getValue(ACCOUNT))
}

private fun runTellers(deposit: () -> Unit) {
    val tellers = List(TELLERS) { c ->
        thread(name = "teller-$c") { repeat(DEPOSITS) { deposit() } }
    }
    tellers.forEach { it.join() }
}

private fun report(how: String, cents: Long) {
    val expected = TELLERS.toLong() * DEPOSITS
    println("%-20s expected %,d cents, got %,d (lost %,d)".format(how, expected, cents, expected - cents))
}
