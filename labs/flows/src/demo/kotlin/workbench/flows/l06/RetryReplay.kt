package workbench.flows.l06

import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.retry
import kotlinx.coroutines.flow.retryWhen
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.test.TestCoroutineScheduler
import kotlinx.coroutines.test.runTest
import java.io.IOException

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
private suspend fun now() = currentCoroutineContext()[TestCoroutineScheduler]!!.currentTime
private suspend fun log(msg: String) = println("%5d ms  %s".format(now(), msg))

fun main() {
    runTest {
        println("== the delivery note: the reader loses the connection after line 2 on the first attempt; retry(3)")
        var attempt = 0
        val feed = flow {
            attempt++
            log("  attempt $attempt starts")
            for (i in 1..3) {
                delay(10)
                if (attempt == 1 && i == 3) throw IOException("reader lost the connection")
                emit(listOf("flour", "eggs", "butter")[i - 1])
            }
        }
        log("the pantry received ${feed.retry(3).toList()}")
    }
    runTest {
        println("== retry(2) on a note that always fails after two lines")
        var calls = 0
        val r = flow { calls++; emit("flour"); emit("eggs"); throw IOException("dropped #$calls") }
            .retry(2)
            .catch { e -> log("  gave up: ${e.message}"); emit("PHONE THE GROCER") }
            .toList()
        log("collector saw $r after $calls collections")
        try { flow { emit(1) }.retry(0) } catch (e: IllegalArgumentException) { println("  retry(0): ${e.message}") }
    }
    runTest {
        println("== retryWhen with exponential backoff: 100, 200, 400 ms; IOException only")
        var n = 0
        val result = flow { n++; log("  call $n to the bakery"); if (n <= 5) throw IOException("line dropped (call $n)"); emit("ok") }
            .retryWhen { cause, attempt ->
                val retry = cause is IOException && attempt < 3
                log("  attempt=$attempt -> ${if (retry) "retry in ${100L shl attempt.toInt()} ms" else "give up"}")
                if (retry) delay(100L shl attempt.toInt())
                retry
            }
            .catch { e -> log("  the original error comes out: ${e::class.simpleName}: ${e.message}"); emit("crackers") }
            .toList()
        log("result $result")
    }
}
