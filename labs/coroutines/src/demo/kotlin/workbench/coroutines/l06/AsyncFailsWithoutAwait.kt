package workbench.coroutines.l06

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.supervisorScope

/** The exception the demos of this lesson throw for a ruined dish. */
class BurnedException(message: String) : Exception(message)

private var t0 = 0L
private fun log(msg: String) = println("%5d ms  %s".format((System.nanoTime() - t0) / 1_000_000, msg))

fun main(args: Array<String>) = runBlocking {
    t0 = System.nanoTime()
    val supervised = args.firstOrNull() == "supervisor"
    try {
        val mainCourse: suspend CoroutineScope.() -> Unit = {
            val gravy = async { delay(100); throw BurnedException("the gravy burned") }  // nobody awaits this yet
            launch {
                try { delay(1_000); log("potatoes: done") } finally { log("potatoes: finally") }
            }
            delay(500)
            log("body: still running at 500 ms, about to await the gravy")
            gravy.await()
        }
        if (supervised) supervisorScope(mainCourse) else coroutineScope(mainCourse)
        log("scope returned normally")
    } catch (e: BurnedException) {
        log("caller caught: ${e.message}")
    }
}
