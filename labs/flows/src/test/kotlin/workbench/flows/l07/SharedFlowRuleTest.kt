package workbench.flows.l07

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.CsvSource

@OptIn(ExperimentalCoroutinesApi::class) // runCurrent and advanceTimeBy on TestScope are experimental in 1.11.0
class SharedFlowRuleTest {

    private class Real(val tryEmits: List<Boolean>, val received: List<Int>)

    /** The real flow, under the setup the KDoc describes: subscribers waiting, then back-to-back tryEmits. */
    private fun real(replay: Int, extra: Int, policy: BufferOverflow, subscribers: Int, calls: Int): Real {
        lateinit var result: Real
        runTest {
            val flow = MutableSharedFlow<Int>(replay, extra, policy)
            val got = mutableListOf<Int>()
            repeat(subscribers) { s ->
                backgroundScope.launch { flow.collect { if (s == 0) got += it; delay(100) } }
            }
            runCurrent() // every subscriber has subscribed and is suspended, waiting for a value
            val results = (1..calls).map { flow.tryEmit(it) } // nobody runs between these calls
            advanceTimeBy(10_000); runCurrent() // not advanceUntilIdle: it ignores backgroundScope
            result = Real(results, got.toList())
        }
        return result
    }

    @ParameterizedTest(name = "replay={0}, extra={1}, {2}, subscribers={3}")
    @CsvSource(
        "0, 0, SUSPEND, 0",
        "0, 0, SUSPEND, 1",
        "0, 0, SUSPEND, 3",
        "0, 2, SUSPEND, 1",
        "2, 0, SUSPEND, 1",
        "1, 2, SUSPEND, 1",
        "1, 2, SUSPEND, 3",
        "0, 2, DROP_OLDEST, 1",
        "0, 2, DROP_LATEST, 1",
        "2, 10, SUSPEND, 0",
        "1, 2, DROP_OLDEST, 2",
    )
    fun `predictTryEmits gives what a real MutableSharedFlow returns`(replay: Int, extra: Int, policy: BufferOverflow, subscribers: Int) {
        val expected = real(replay, extra, policy, subscribers, calls = 6).tryEmits
        assertThat(predictTryEmits(replay, extra, policy, subscribers, calls = 6))
            .`as`("tryEmit(1..6) results")
            .isEqualTo(expected)
    }

    @ParameterizedTest(name = "replay={0}, extra={1}, {2}")
    @CsvSource(
        "0, 0, SUSPEND",
        "0, 2, SUSPEND",
        "2, 0, SUSPEND",
        "1, 2, SUSPEND",
        "0, 2, DROP_OLDEST",
        "1, 2, DROP_OLDEST",
        "0, 2, DROP_LATEST",
        "1, 3, DROP_LATEST",
    )
    fun `predictReceived gives what the waiting subscriber really gets`(replay: Int, extra: Int, policy: BufferOverflow) {
        val expected = real(replay, extra, policy, subscribers = 1, calls = 6).received
        assertThat(predictReceived(replay, extra, policy, calls = 6))
            .`as`("values the subscriber received after tryEmit(1..6)")
            .isEqualTo(expected)
    }
}
