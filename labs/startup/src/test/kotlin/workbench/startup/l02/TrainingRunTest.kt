package workbench.startup.l02

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class TrainingRunTest {
    private val parent = TrainingRunTest::class.java.classLoader
    private val prefix = "workbench.startup.l02.fixtures."
    private val desk = prefix + "ParcelDesk"

    @Test
    fun `a training run lists exactly the classes the workload touched`() {
        val list = TrainingRun.classList(parent, prefix, desk, listOf("track PX-1042", "track PX-2001"))
        // compare names, never counts: Redirect was never needed, so it is not there
        assertThat(list).containsExactlyInAnyOrder(prefix + "ParcelDesk", prefix + "Track", prefix + "Status")
    }

    @Test
    fun `the entry class comes first in the list`() {
        val list = TrainingRun.classList(parent, prefix, desk, listOf("redirect PX-1042"))
        assertThat(list.first()).isEqualTo(desk)
        assertThat(list).containsExactlyInAnyOrder(prefix + "ParcelDesk", prefix + "Redirect", prefix + "Status")
    }

    @Test
    fun `a workload with no requests only loads the entry class`() {
        assertThat(TrainingRun.classList(parent, prefix, desk, emptyList())).containsExactly(desk)
    }

    @Test
    fun `production traffic the training never saw is missing from the list`() {
        val training = TrainingRun.classList(parent, prefix, desk, listOf("track PX-1042"))
        val production = TrainingRun.classList(parent, prefix, desk, listOf("track PX-1042", "redirect PX-1042"))
        assertThat(TrainingRun.missing(training, production)).containsExactly(prefix + "Redirect")
        assertThat(TrainingRun.missing(production, training)).isEmpty()
    }
}
