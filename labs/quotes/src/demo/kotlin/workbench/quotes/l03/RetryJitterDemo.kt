package workbench.quotes.l03

import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import kotlin.random.Random
import kotlin.time.Duration.Companion.milliseconds

/** 1,000 clients fail together at 0 ms and retry after a nominal 100 ms. When do the retries land? */
fun main() = runTest {
    for (jitter in listOf(0.0, 0.5)) {
        val random = Random(7)
        val retryAt = IntArray(1_000)
        val t0 = currentTime
        coroutineScope {
            repeat(1_000) { client ->
                launch {
                    val factor = 1 + jitter * (random.nextDouble() * 2 - 1)   // 1 - jitter .. 1 + jitter
                    delay(100.milliseconds * factor)
                    retryAt[client] = (currentTime - t0).toInt()
                }
            }
        }
        val buckets = retryAt.groupBy { it / 25 * 25 }.toSortedMap()
        println("jitter $jitter: " + buckets.entries.joinToString("  ") { (from, hits) -> "$from-${from + 24} ms: ${hits.size}" })
        println("   most retries in one millisecond: ${retryAt.groupBy { it }.values.maxOf { it.size }}")
    }
}
