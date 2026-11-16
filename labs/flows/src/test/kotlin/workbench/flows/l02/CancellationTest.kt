package workbench.flows.l02

import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.asFlow
import kotlinx.coroutines.flow.cancellable
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.transform
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class CancellationTest {

    /** Collects [f] in a new coroutine that cancels itself when it sees 3 and never suspends. */
    private suspend fun TestScope.stopAtThree(f: Flow<Int>): List<Int> {
        val seen = mutableListOf<Int>()
        launch { f.collect { v -> seen += v; if (v == 3) cancel() } }.join()
        return seen
    }

    @Test
    fun `your prediction for flow { } holds`() = runTest {
        assertThat(stopAtThree(flow { for (i in 1..5) emit(i) })).isEqualTo(CancelPredictions.flowBuilderLoop)
    }

    @Test
    fun `your prediction for asFlow() holds`() = runTest {
        assertThat(stopAtThree((1..5).asFlow())).isEqualTo(CancelPredictions.asFlowRange)
    }

    @Test
    fun `your prediction for flowOf holds`() = runTest {
        assertThat(stopAtThree(flowOf(1, 2, 3, 4, 5))).isEqualTo(CancelPredictions.flowOfFive)
    }

    @Test
    fun `your prediction for asFlow() then cancellable() holds`() = runTest {
        assertThat(stopAtThree((1..5).asFlow().cancellable())).isEqualTo(CancelPredictions.asFlowCancellable)
    }

    @Test
    fun `your prediction for asFlow() then map holds`() = runTest {
        assertThat(stopAtThree((1..5).asFlow().map { it })).isEqualTo(CancelPredictions.asFlowMap)
    }

    @Test
    fun `your prediction for asFlow() then transform holds`() = runTest {
        assertThat(stopAtThree((1..5).asFlow().transform { emit(it) })).isEqualTo(CancelPredictions.asFlowTransform)
    }

    @Test
    fun `batchIds stops delivering once the reconciliation job has cancelled itself`() = runTest {
        val seen = mutableListOf<String>()
        launch {
            batchIds((1..1000).map { "pay-$it" }).collect { id ->
                seen += id
                if (id == "pay-3") cancel()      // first mismatch: stop the job
            }
        }.join()
        assertThat(seen).containsExactly("pay-1", "pay-2", "pay-3")
    }
}
