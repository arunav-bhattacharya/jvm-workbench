package workbench.concurrency.l09

import java.util.concurrent.ConcurrentHashMap

// Memoized Fibonacci where the mapping function calls back into the same map. The Javadoc forbids it.
private lateinit var memo: MutableMap<Int, Long>

private fun fib(n: Int): Long {
    if (n < 2) return n.toLong()
    return memo.computeIfAbsent(n) { k -> fib(k - 1) + fib(k - 2) }   // modifies the map from inside compute
}

fun main() {
    for (m in listOf<MutableMap<Int, Long>>(ConcurrentHashMap(), HashMap())) {
        memo = m
        try {
            println("${m.javaClass.simpleName}: fib(30) = ${fib(30)}")
        } catch (e: RuntimeException) {
            println("${m.javaClass.simpleName}: threw $e")
        }
    }
    // the fix: build the table bottom-up, outside any compute call
    val table = ConcurrentHashMap(mapOf(0 to 0L, 1 to 1L))
    for (n in 2..30) table[n] = table.getValue(n - 1) + table.getValue(n - 2)
    println("bottom-up: fib(30) = ${table[30]}")
}
