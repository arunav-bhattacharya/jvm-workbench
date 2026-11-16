@file:OptIn(ExperimentalCoroutinesApi::class)

package workbench.flows.l01

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

class ToyFlowTest {

    // ---- cold: building runs nothing, every collect runs the body again ----

    @Test
    fun `building a toy flow and its operators runs nothing`() = runTest {
        var bodyRuns = 0
        val built = toyFlow { bodyRuns++; emit(1) }.map { it * 100 }.filter { it > 0 }.take(1)
        assertThat(bodyRuns).`as`("body runs after building only").isZero()
        assertThat(built.toList()).containsExactly(100)
        assertThat(bodyRuns).isEqualTo(1)
    }

    @Test
    fun `every collect runs the body again from the top`() = runTest {
        var bodyRuns = 0
        val payments = toyFlow { bodyRuns++; emit("pay-1"); emit("pay-2") }
        assertThat(payments.toList()).containsExactly("pay-1", "pay-2")
        assertThat(payments.toList()).containsExactly("pay-1", "pay-2")
        assertThat(bodyRuns).isEqualTo(2)
    }

    // ---- sequential: emit returns only after the collector's code has finished ----

    @Test
    fun `emit returns only after the collector has finished with the value`() = runTest {
        val events = mutableListOf<String>()
        toyFlow {
            for (id in 1..3) {
                events += "before emit $id"
                emit(id)
                events += "after emit $id"
            }
        }.collect { events += "got $it" }
        assertThat(events).containsExactly(
            "before emit 1", "got 1", "after emit 1",
            "before emit 2", "got 2", "after emit 2",
            "before emit 3", "got 3", "after emit 3",
        )
    }

    @Test
    fun `map and filter run inside the upstream's emit, one value at a time`() = runTest {
        val events = mutableListOf<String>()
        toyFlow {
            for (id in 1..3) {
                events += "emit $id"
                emit(id)
                events += "emit $id returned"
            }
        }
            .map { events += "map $it"; it * 100 }
            .filter { events += "filter $it"; it != 200 }
            .collect { events += "got $it" }
        assertThat(events).containsExactly(
            "emit 1", "map 1", "filter 100", "got 100", "emit 1 returned",
            "emit 2", "map 2", "filter 200", "emit 2 returned",
            "emit 3", "map 3", "filter 300", "got 300", "emit 3 returned",
        )
    }

    // ---- backpressure for free, in virtual time ----

    @Test
    fun `a slow collector slows the producer down`() = runTest {
        val emitTimes = mutableListOf<Long>()
        toyFlow {
            for (id in 1..3) {
                delay(100)                 // the producer needs 100 ms per item
                emitTimes += currentTime
                emit(id)
            }
        }.collect { delay(300) }           // the collector needs 300 ms per item
        assertThat(emitTimes).`as`("virtual time of each emit").containsExactly(100L, 500L, 900L)
        assertThat(currentTime).isEqualTo(1200L)
    }

    // ---- take stops the producer ----

    @Test
    fun `take stops the producer after n values and runs its finally`() = runTest {
        val events = mutableListOf<String>()
        val payments = toyFlow {
            try {
                for (id in 1..5) {
                    events += "emit $id"
                    emit(id)
                }
            } finally {
                events += "producer finally"
            }
        }
        assertThat(payments.take(2).toList()).containsExactly(1, 2)
        assertThat(events).containsExactly("emit 1", "emit 2", "producer finally")
    }

    @Test
    fun `take lets an abort from a take further down fly past it`() = runTest {
        val events = mutableListOf<String>()
        val inner = toyFlow {
            try {
                for (id in 1..5) emit(id)
            } finally {
                events += "inner producer finally"
            }
        }.take(3)
        val outer = toyFlow {
            inner.collect { emit(it) }
            events += "outer body went on after inner"   // must not happen: take(1) said stop
            emit(99)
        }.take(1)
        assertThat(outer.toList()).containsExactly(1)
        assertThat(events).containsExactly("inner producer finally")
    }

    @Test
    fun `take rejects a count of zero when the flow is built`() {
        assertThatThrownBy { toyFlow { emit(1) }.take(0) }.isInstanceOf(IllegalArgumentException::class.java)
    }
}
