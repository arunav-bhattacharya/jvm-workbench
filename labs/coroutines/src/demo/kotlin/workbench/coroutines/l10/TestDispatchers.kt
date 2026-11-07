package workbench.coroutines.l10

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest

@OptIn(ExperimentalCoroutinesApi::class)
fun main() = runTest {
    // 1. runTest's default, StandardTestDispatcher: launch only queues the child
    val standard = mutableListOf<String>()
    launch { standard += "child ran" }
    standard += "after launch"
    runCurrent() // run what is due now
    println("StandardTestDispatcher:  $standard")

    // 2. UnconfinedTestDispatcher: the child starts at once, up to its first suspension
    val unconfined = mutableListOf<String>()
    launch(UnconfinedTestDispatcher(testScheduler)) { unconfined += "child ran" }
    unconfined += "after launch"
    println("UnconfinedTestDispatcher: $unconfined")

    // 3. backgroundScope: for work that never ends, such as a rate poller
    var polls = 0
    backgroundScope.launch { while (true) { delay(1_000); polls++ } }
    advanceTimeBy(5_500)
    println("polls after advanceTimeBy(5_500): $polls")
    advanceUntilIdle()
    println("polls after advanceUntilIdle(): $polls (background work doesn't keep it busy)")
    // when the test body ends, runTest cancels everything in backgroundScope
}
