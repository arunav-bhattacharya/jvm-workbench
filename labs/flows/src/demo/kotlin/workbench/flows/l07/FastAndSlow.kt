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

// One house bell with a slate, two listeners: the waiter, who is fast, and the diary keeper, who
// copies each announcement into the kitchen diary by hand, 1,000 ms a line. Six announcements, 10 ms apart.
// All times are virtual milliseconds (runTest), so the output is the same on every run.
@OptIn(ExperimentalCoroutinesApi::class)
private fun bellWith(policy: BufferOverflow, diaryHasOwnBuffer: Boolean = false) = runTest {
    val bell = MutableSharedFlow<Int>(extraBufferCapacity = 2, onBufferOverflow = policy)
    val waiter = mutableListOf<Int>()
    val diary = mutableListOf<Int>()
    backgroundScope.launch { bell.collect { waiter += it } }
    val diarySide = if (diaryHasOwnBuffer) bell.buffer(64) else bell   // a channel of its own in front of the slow work
    backgroundScope.launch { diarySide.collect { diary += it; delay(1_000) } }
    runCurrent() // both have subscribed and wait for a value

    val returned = mutableListOf<String>()
    for (announcement in 1..6) {
        bell.emit(announcement)
        returned += "$announcement@t=$currentTime"
        delay(10)
    }
    advanceTimeBy(10_000); runCurrent()
    println(if (diaryHasOwnBuffer) "$policy, the diary collects bell.buffer(64)" else "$policy")
    println("  waiter got $waiter")
    println("  diary got  $diary")
    println("  emit returned: $returned")
}

fun main() {
    bellWith(BufferOverflow.DROP_LATEST)
    bellWith(BufferOverflow.SUSPEND)
    bellWith(BufferOverflow.DROP_OLDEST)
    bellWith(BufferOverflow.SUSPEND, diaryHasOwnBuffer = true)
}
