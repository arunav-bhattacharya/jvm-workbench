package workbench.coroutines.l10

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext

@OptIn(ExperimentalCoroutinesApi::class)
fun main() {
    val realStart = System.nanoTime()
    fun real() = (System.nanoTime() - realStart) / 1_000_000
    // runTest is meant for tests, but a plain main can call it too
    runTest {
        fun TestScope.log(what: String) = println("virtual %5d ms (real %4d ms)  %s".format(currentTime, real(), what))
        launch {
            delay(1_000); log("settlement file fetched")
            delay(200); log("file parsed")
            delay(2_000); log("ledger posted")
        }
        val fx = async {
            delay(3_000); log("FX rates fetched")
            delay(500); log("rates cached")
        }
        fx.await()
        log("await returned")
    }
    println("whole runTest took %d ms of real time".format(real()))

    runTest {
        val before = real()
        withContext(Dispatchers.Default) { delay(1_000) } // escapes the test scheduler
        println("withContext(Default) { delay(1_000) }: virtual $currentTime ms, real ${real() - before} ms")
    }
}
