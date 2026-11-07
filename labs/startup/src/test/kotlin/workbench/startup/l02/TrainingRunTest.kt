package workbench.startup.l02

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class TrainingRunTest {
    private val parent = TrainingRunTest::class.java.classLoader
    private val prefix = "workbench.startup.l02.fixtures."
    private val checkout = prefix + "Checkout"

    @Test
    fun `a training run lists exactly the classes the workload touched`() {
        val list = TrainingRun.classList(parent, prefix, checkout, listOf("authorize 12.50 EUR", "authorize 3.00 EUR"))
        // compare names, never counts: Refund was never needed, so it is not there
        assertThat(list).containsExactlyInAnyOrder(prefix + "Checkout", prefix + "Authorize", prefix + "Money")
    }

    @Test
    fun `the entry class comes first in the list`() {
        val list = TrainingRun.classList(parent, prefix, checkout, listOf("refund 9.90 EUR"))
        assertThat(list.first()).isEqualTo(checkout)
        assertThat(list).containsExactlyInAnyOrder(prefix + "Checkout", prefix + "Refund", prefix + "Money")
    }

    @Test
    fun `a workload with no requests only loads the entry class`() {
        assertThat(TrainingRun.classList(parent, prefix, checkout, emptyList())).containsExactly(checkout)
    }

    @Test
    fun `production traffic the training never saw is missing from the list`() {
        val training = TrainingRun.classList(parent, prefix, checkout, listOf("authorize 12.50 EUR"))
        val production = TrainingRun.classList(parent, prefix, checkout, listOf("authorize 12.50 EUR", "refund 9.90 EUR"))
        assertThat(TrainingRun.missing(training, production)).containsExactly(prefix + "Refund")
        assertThat(TrainingRun.missing(production, training)).isEmpty()
    }
}
