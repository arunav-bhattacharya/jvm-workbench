package workbench.flows.l07

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest

// When does tryEmit return false? One subscriber subscribes and waits, then tryEmit(1..6)
// runs back to back, so the subscriber can't take anything between two calls. Virtual time.
@OptIn(ExperimentalCoroutinesApi::class)
private fun table(label: String, flow: MutableSharedFlow<Int>, subscribers: Int = 1) = runTest {
    val got = mutableListOf<Int>()
    repeat(subscribers) { s -> backgroundScope.launch { flow.collect { if (s == 0) got += it; delay(100) } } }
    runCurrent()
    val results = (1..6).map { flow.tryEmit(it) }.joinToString(" ") { if (it) "T" else "f" }
    advanceTimeBy(10_000); runCurrent() // advanceUntilIdle() would not run backgroundScope
    println("%-30s subscribers=%d  tryEmit: %s  received: %s".format(label, subscribers, results, got))
}

// The rendezvous: with no buffer, emit waits until the subscriber has TAKEN the value.
@OptIn(ExperimentalCoroutinesApi::class)
private fun rendezvous() = runTest {
    val bus = MutableSharedFlow<Int>()
    backgroundScope.launch { bus.collect { println("  t=$currentTime subscriber took $it"); delay(100) } }
    runCurrent()
    for (v in 1..3) { bus.emit(v); println("  t=$currentTime emit($v) returned") }
}

// A late subscriber gets the replay cache, then live values. Never the slow one's backlog.
@OptIn(ExperimentalCoroutinesApi::class)
private fun late() = runTest {
    val bus = MutableSharedFlow<Int>(replay = 1, extraBufferCapacity = 10)
    val s1 = mutableListOf<Int>(); val s2 = mutableListOf<Int>()
    backgroundScope.launch { bus.collect { s1 += it; delay(100) } }
    runCurrent()
    (1..5).forEach { bus.emit(it) }   // S1 is still busy with 1
    backgroundScope.launch { bus.collect { s2 += it } }
    advanceTimeBy(1_000); runCurrent()
    println("  S1 (there from the start) got $s1, S2 (joined after 5) got $s2")
}

fun main() {
    println("== tryEmit(1..6) with a waiting subscriber")
    table("MutableSharedFlow()", MutableSharedFlow(), subscribers = 0)
    table("MutableSharedFlow()", MutableSharedFlow())
    table("MutableSharedFlow()", MutableSharedFlow(), subscribers = 3)
    table("extraBufferCapacity=2", MutableSharedFlow(extraBufferCapacity = 2))
    table("replay=2", MutableSharedFlow(replay = 2))
    table("replay=1, extra=2", MutableSharedFlow(replay = 1, extraBufferCapacity = 2))
    table("extra=2, DROP_OLDEST", MutableSharedFlow(extraBufferCapacity = 2, onBufferOverflow = BufferOverflow.DROP_OLDEST))
    table("extra=2, DROP_LATEST", MutableSharedFlow(extraBufferCapacity = 2, onBufferOverflow = BufferOverflow.DROP_LATEST))
    println("== emit on MutableSharedFlow(), subscriber needs 100 ms per value")
    rendezvous()
    println("== a late subscriber, replay=1, extra=10")
    late()
}
