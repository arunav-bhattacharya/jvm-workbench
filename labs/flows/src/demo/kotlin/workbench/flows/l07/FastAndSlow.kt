package workbench.flows.l07

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest

// One transition bus, two subscribers: a notifier that is fast, and an audit writer that
// needs 1,000 ms per row. Six transitions are emitted 10 ms apart.
// All times are virtual milliseconds (runTest), so the output is the same on every run.
@OptIn(ExperimentalCoroutinesApi::class)
private fun busWith(policy: BufferOverflow, auditHasOwnBuffer: Boolean = false) = runTest {
    val bus = MutableSharedFlow<Int>(extraBufferCapacity = 2, onBufferOverflow = policy)
    val notifier = mutableListOf<Int>()
    val audit = mutableListOf<Int>()
    backgroundScope.launch { bus.collect { notifier += it } }
    val auditSide = if (auditHasOwnBuffer) bus.buffer(64) else bus   // a channel of its own in front of the slow work
    backgroundScope.launch { auditSide.collect { audit += it; delay(1_000) } }
    runCurrent() // both have subscribed and wait for a value

    val returned = mutableListOf<String>()
    for (transition in 1..6) {
        bus.emit(transition)
        returned += "$transition@t=$currentTime"
        delay(10)
    }
    advanceTimeBy(10_000); runCurrent()
    println(if (auditHasOwnBuffer) "$policy, audit collects bus.buffer(64)" else "$policy")
    println("  notifier got $notifier")
    println("  audit got    $audit")
    println("  emit returned: $returned")
}

fun main() {
    busWith(BufferOverflow.DROP_LATEST)
    busWith(BufferOverflow.SUSPEND)
    busWith(BufferOverflow.DROP_OLDEST)
    busWith(BufferOverflow.SUSPEND, auditHasOwnBuffer = true)
}
