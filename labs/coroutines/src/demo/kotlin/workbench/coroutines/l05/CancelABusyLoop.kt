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

/** Pure CPU work: looking at one lentil (a little arithmetic stands in for it). 60 million take about 1.5 s. */
private fun inspect(i: Long): Long {
    var x = i
    repeat(20) {
        x = x xor (x ushr 33)
        x *= -0xae502812aa7333L
        x = x xor (x ushr 29)
    }
    return x
}

private const val LENTILS = 60_000_000L

@Volatile
private var sink = 0L // keeps the JIT from deleting loops whose result nobody reads

fun main() = runBlocking {
    // each loop gets the launched coroutine as its receiver, so isActive and ensureActive() look at
    // that coroutine's job (in a plain lambda they would quietly pick up runBlocking's scope instead)
    val loops: Map<String, suspend CoroutineScope.() -> Long> = mapOf(
        "no check" to {
            var sum = 0L
            for (i in 0 until LENTILS) sum += inspect(i)
            sum
        },
        "while (isActive)" to {
            var sum = 0L
            var i = 0L
            while (isActive && i < LENTILS) { sum += inspect(i); i++ }
            sum
        },
        "ensureActive() every 1,000" to {
            var sum = 0L
            for (i in 0 until LENTILS) {
                if (i % 1_000 == 0L) ensureActive()
                sum += inspect(i)
            }
            sum
        },
        "yield() every 1,000" to {
            var sum = 0L
            for (i in 0 until LENTILS) {
                if (i % 1_000 == 0L) yield()
                sum += inspect(i)
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
