package workbench.coroutines.l06

import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

private var since = 0L
private fun stamp(msg: String) = println("%5d ms  %s".format((System.nanoTime() - since) / 1_000_000, msg))

fun main() = runBlocking {
    since = System.nanoTime()
    val request = launch {
        // looks like "a supervised child". It is a child of a brand-new SupervisorJob instead,
        // so it has left the request's tree: nobody waits for it and nobody cancels it.
        launch(SupervisorJob()) {
            delay(300)
            stamp("trap child: still running, nobody cancelled me")
        }
        launch {
            try { delay(300); stamp("normal child: done") } finally { stamp("normal child: finally") }
        }
    }
    delay(100)
    request.cancelAndJoin()
    stamp("request cancelled and joined")
    delay(400)
    stamp("main done")
}
