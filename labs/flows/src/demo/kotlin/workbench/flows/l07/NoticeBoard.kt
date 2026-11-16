package workbench.flows.l07

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import java.math.BigDecimal
import java.util.concurrent.atomic.AtomicInteger

data class Quote(val pair: String, val mid: BigDecimal)

// A StateFlow is a notice board with one slot. Parts A, B, C and E use virtual time.
@OptIn(ExperimentalCoroutinesApi::class)
fun main() {
    runTest {
        println("== A: equal values")
        val first = Quote("EURUSD", BigDecimal("1.0850"))
        val board = MutableStateFlow(first)
        val seen = mutableListOf<Quote>()
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { board.collect { seen += it } }
        board.value = Quote("EURUSD", BigDecimal("1.0850"))   // equal fields
        println("  after an equal set: board still holds the first object? ${board.value === first}")
        board.value = Quote("EURUSD", BigDecimal("1.08500"))  // one more zero
        println("  collector saw ${seen.map { it.mid }}")
    }
    runTest {
        println("== B: AUTHORIZED -> CAPTURED -> AUTHORIZED while the collector is busy")
        val status = MutableStateFlow("AUTHORIZED")
        val log = mutableListOf<String>()
        backgroundScope.launch { status.collect { log += "t=$currentTime $it"; delay(100) } }
        runCurrent()
        delay(10); status.value = "CAPTURED"
        delay(10); status.value = "AUTHORIZED"
        advanceTimeBy(500); runCurrent()
        println("  busy collector saw $log")
    }
    println("== C: compareAndSet")
    val count = MutableStateFlow(10)
    println("  cas(10, 11) = ${count.compareAndSet(10, 11)}, value ${count.value}")
    println("  cas(10, 12) = ${count.compareAndSet(10, 12)}, value ${count.value}  (stale expect)")
    println("  cas(11, 11) = ${count.compareAndSet(11, 11)}, value ${count.value}  (true, and nobody is woken)")

    println("== D: update { } from 8 coroutines x 100,000 on Dispatchers.Default (REAL threads)")
    val calls = AtomicInteger()
    val counter = MutableStateFlow(0)
    runBlocking(Dispatchers.Default) {
        repeat(8) { launch { repeat(100_000) { counter.update { calls.incrementAndGet(); it + 1 } } } }
    }
    println("  value=${counter.value}, the lambda ran ${calls.get()} times")

    runTest {
        println("== E: subscriptionCount keeps every change")
        val events = MutableSharedFlow<Int>()
        val counts = mutableListOf<Int>()
        backgroundScope.launch { events.subscriptionCount.collect { counts += it } }
        runCurrent()
        val visitor = backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { events.collect { } }
        visitor.cancel() // joined and left before the observer ran again
        runCurrent()
        val plain = MutableStateFlow(0); val plainSeen = mutableListOf<Int>()
        backgroundScope.launch { plain.collect { plainSeen += it } }
        runCurrent()
        plain.value = 1; plain.value = 0; runCurrent()
        println("  subscriptionCount observer saw $counts; a plain StateFlow doing 0 -> 1 -> 0 showed $plainSeen")
    }
}
