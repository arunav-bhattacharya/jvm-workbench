package workbench.coroutines.l05

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.yield

/** Pure CPU work: a checksum over one fake card number. 60 million of them take about 1.5 s. */
private fun checksum(i: Long): Long {
    var x = i
    repeat(20) {
        x = x xor (x ushr 33)
        x *= -0xae502812aa7333L
        x = x xor (x ushr 29)
    }
    return x
}

private const val ROWS = 60_000_000L

@Volatile
private var sink = 0L // keeps the JIT from deleting loops whose result nobody reads

fun main() = runBlocking {
    // each loop gets the launched coroutine as its receiver, so isActive and ensureActive() look at
    // that coroutine's job (in a plain lambda they would quietly pick up runBlocking's scope instead)
    val loops: Map<String, suspend CoroutineScope.() -> Long> = mapOf(
        "no check" to {
            var sum = 0L
            for (i in 0 until ROWS) sum += checksum(i)
            sum
        },
        "while (isActive)" to {
            var sum = 0L
            var i = 0L
            while (isActive && i < ROWS) { sum += checksum(i); i++ }
            sum
        },
        "ensureActive() every 1,000" to {
            var sum = 0L
            for (i in 0 until ROWS) {
                if (i % 1_000 == 0L) ensureActive()
                sum += checksum(i)
            }
            sum
        },
        "yield() every 1,000" to {
            var sum = 0L
            for (i in 0 until ROWS) {
                if (i % 1_000 == 0L) yield()
                sum += checksum(i)
            }
            sum
        },
    )
    for ((label, loop) in loops) {
        val job = launch(Dispatchers.Default) { sink = loop() }
        delay(100) // let it get going
        val asked = System.nanoTime()
        job.cancelAndJoin()
        println("%-28s stopped %5d ms after cancel()".format(label, (System.nanoTime() - asked) / 1_000_000))
    }
}
