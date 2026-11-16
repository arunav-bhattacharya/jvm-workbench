package workbench.flows.l08

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlin.time.Duration.Companion.milliseconds

class StatusTracker {
    private val _status = MutableStateFlow("PENDING")
    val status: StateFlow<String> = _status.asStateFlow()
    fun authorizeAndCapture() { _status.value = "AUTHORIZED"; _status.value = "CAPTURED" } // no suspension between
}

// The edges of the test clock. runTest is called from main here; in a test it is the body.
@OptIn(ExperimentalCoroutinesApi::class)
fun main() {
    runTest {
        println("== 1. advanceTimeBy(n) runs what is due BEFORE now + n")
        val fired = mutableListOf<Long>()
        launch { delay(100); fired += currentTime }
        launch { delay(200); fired += currentTime }
        advanceTimeBy(100); println("  after advanceTimeBy(100): t=$currentTime fired=$fired")
        runCurrent();       println("  after runCurrent():       t=$currentTime fired=$fired")
        advanceUntilIdle(); println("  after advanceUntilIdle(): t=$currentTime fired=$fired")
    }
    runTest {
        println("== 2. advanceUntilIdle() stops once only backgroundScope work is left")
        var polls = 0
        backgroundScope.launch { while (true) { delay(1_000); polls++ } } // a settlement poller
        advanceUntilIdle();                  println("  after advanceUntilIdle():               t=$currentTime polls=$polls")
        advanceTimeBy(5_000); runCurrent();  println("  after advanceTimeBy(5000) + runCurrent(): t=$currentTime polls=$polls")
    }
    runTest {
        println("== 3. a StateFlow set twice in a row, collected three ways")
        val a = StatusTracker(); val standard = mutableListOf<String>()
        backgroundScope.launch { a.status.toList(standard) }
        runCurrent(); a.authorizeAndCapture(); runCurrent()
        val b = StatusTracker(); val unconfined = mutableListOf<String>()
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { b.status.toList(unconfined) }
        b.authorizeAndCapture()
        println("  Standard collector:   $standard")
        println("  Unconfined collector: $unconfined")
    }
    println("== 4. take(3) on that StateFlow (runTest timeout 500 ms of REAL time)")
    try {
        runTest(timeout = 500.milliseconds) {
            val t = StatusTracker()
            val three = async { t.status.take(3).toList() }
            runCurrent()
            t.authorizeAndCapture()
            println("  got ${three.await()}")
        }
    } catch (e: Throwable) { println("  ${e::class.qualifiedName}: ${e.message?.lines()?.first()}") }
    println("== 5. stateIn(this, WhileSubscribed()) inside runTest, over flowOf(1, 2, 3)")
    try {
        runTest(timeout = 500.milliseconds) {
            val s = flowOf(1, 2, 3).stateIn(this, SharingStarted.WhileSubscribed(), 0)
            println("  saw ${s.first { it == 3 }}, test body done")
        }
        println("  test passed")
    } catch (e: Throwable) { println("  ${e::class.qualifiedName}: ${e.message?.lines()?.first()?.replace(Regex("@[0-9a-f]+"), "@...")}") }
}
