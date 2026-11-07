package workbench.bytecode.l07

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

class CallCountingAgentTest {
    private val settle = "workbench.bytecode.l07.SettlementJob.settle"
    private val audit = "workbench.bytecode.l07.SettlementJob.audit"
    private var installed: Installed? = null

    @BeforeEach
    fun reset() = CallCounts.reset()

    @AfterEach
    fun uninstall() {
        installed?.uninstall()
        installed = null
    }

    @Test
    fun `the agent can retransform classes that are already loaded`() {
        val inst = CallCountingAgent.instrumentation()
        assertThat(inst.isRetransformClassesSupported).isTrue()
        assertThat(inst.isModifiableClass(SettlementJob::class.java)).isTrue()
        assertThat(inst.allLoadedClasses).contains(SettlementJob::class.java)
    }

    @Test
    fun `an instance created before the agent was installed is counted afterwards`() {
        val job = SettlementJob()
        job.settle("B-1")                                        // before: not counted
        installed = CallCountingAgent.countCalls(SettlementJob::class.java, "settle")
        job.settle("B-2")
        job.settle("B-3")
        assertThat(CallCounts.of(settle)).isEqualTo(2)
        assertThat(job.javaClass).isSameAs(SettlementJob::class.java)   // same class, new method body
    }

    @Test
    fun `only the matched method is counted`() {
        installed = CallCountingAgent.countCalls(SettlementJob::class.java, "settle")
        SettlementJob().audit("B-4")
        assertThat(CallCounts.of(audit)).isZero()
    }

    @Test
    fun `calls a method makes on this are counted too, because the advice is inside the method`() {
        installed = CallCountingAgent.countCalls(SettlementJob::class.java, "settle")
        assertThat(SettlementJob().settleAll(listOf("B-5", "B-6", "B-7"))).isEqualTo(3)
        assertThat(CallCounts.of(settle)).isEqualTo(3)
    }

    @Test
    fun `retransformation keeps static state and the method still does its work`() {
        SettlementJob().settle("B-8")
        val before = SettlementJob.processed
        installed = CallCountingAgent.countCalls(SettlementJob::class.java, "settle")
        assertThat(SettlementJob().settle("B-9")).isEqualTo("settled B-9")
        assertThat(SettlementJob.processed).isEqualTo(before + 1)          // no static initializer ran again
    }

    @Test
    fun `uninstalling restores the original method body`() {
        val job = SettlementJob()
        installed = CallCountingAgent.countCalls(SettlementJob::class.java, "settle")
        job.settle("B-10")
        installed!!.uninstall()
        installed = null
        job.settle("B-11")
        assertThat(CallCounts.of(settle)).isEqualTo(1)
    }
}
