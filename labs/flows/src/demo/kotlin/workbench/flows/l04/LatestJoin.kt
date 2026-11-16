package workbench.flows.l04

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.cancel
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.cancellable
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext

// A repricing that is cancelled must release a quote lock first: 50 ms that can't be cancelled.
private fun repricingTimeline() = runTest {
    val t = { testScheduler.currentTime }
    flow { for (tick in 1..3) { delay(100); println("t=${t()} emit $tick"); emit(tick) } }
        .collectLatest { tick ->
            println("t=${t()} start $tick")
            try {
                delay(300); println("t=${t()} done $tick")
            } catch (e: CancellationException) {
                println("t=${t()} cancelled $tick (${e::class.simpleName})")
                withContext(NonCancellable) { delay(50) }      // release the lock
                println("t=${t()} cleanup of $tick finished")
                throw e
            }
        }
}

// A collector that never suspends cancels itself at 3. What else reaches it?
private suspend fun cpuOnly(label: String, f: Flow<Int>) = coroutineScope {
    val seen = mutableListOf<Int>()
    launch { f.collect { seen += it; if (it == 3) cancel() } }.join()
    println("%-30s the collector got %d values after cancelling at 3".format(label, seen.size - 3))
}

fun main() {
    println("== collectLatest: cancel the old block, wait for it, then start the new one")
    repricingTimeline()
    println("== cancel() behind a buffer, with a collector that never suspends")
    runTest {
        val src = flow { for (i in 1..100) emit(i) }
        cpuOnly("flow { }", src)
        cpuOnly("flow { }.buffer(10)", src.buffer(10))
        cpuOnly("flow { }.buffer()", src.buffer())
        cpuOnly("flow { }.buffer().cancellable()", src.buffer().cancellable())
    }
}
