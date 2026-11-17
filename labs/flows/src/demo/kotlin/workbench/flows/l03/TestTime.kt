@file:OptIn(ExperimentalCoroutinesApi::class)

package workbench.flows.l03

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.runTest

/** A slow reader that may fetch only one line per second: three lines, one second apart. */
fun slowFeed() = flow { repeat(3) { delay(1_000); emit(it) } }

// runTest outside JUnit: does virtual time cover a flowOn pipeline?
fun main() {
    var wall = System.nanoTime()
    runTest {
        slowFeed().flowOn(Dispatchers.Default).toList()
        println("flowOn(Dispatchers.Default):            virtual=${testScheduler.currentTime} ms, wall=${(System.nanoTime() - wall) / 1_000_000} ms")
    }
    wall = System.nanoTime()
    runTest {
        slowFeed().flowOn(StandardTestDispatcher(testScheduler)).toList()
        println("flowOn(StandardTestDispatcher(testScheduler)): virtual=${testScheduler.currentTime} ms, wall=${(System.nanoTime() - wall) / 1_000_000} ms")
    }
}
