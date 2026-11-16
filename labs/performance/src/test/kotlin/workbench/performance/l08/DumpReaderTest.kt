package workbench.performance.l08

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.within
import org.junit.jupiter.api.Test

class DumpReaderTest {

    // Real `jcmd <pid> Thread.print -l` dumps (JDK 25) of the FrozenService demo, taken 5 seconds apart,
    // and two dumps of a small program with a deadlock and two threads that are both called "worker".
    private fun load(name: String): ThreadDump =
        ThreadDump.parse(javaClass.getResource(name)!!.readText())

    private val d1 = load("dump-1.txt")
    private val d2 = load("dump-2.txt")
    private val d3 = load("dump-3.txt")
    private val deadlock1 = load("deadlock-1.txt")
    private val deadlock2 = load("deadlock-2.txt")

    @Test
    fun `the given parser reads the fixtures`() {
        val refresh = d1.byName("issuer-refresh")!!
        assertThat(refresh.state).isEqualTo("RUNNABLE")
        assertThat(refresh.nid).isEqualTo(29189L)
        assertThat(refresh.frames.first()).startsWith("sun.nio.ch.SocketDispatcher.read0")
        // the cache monitor, and the socket's own read lock (a ReentrantLock inside NioSocketImpl)
        assertThat(refresh.holds).containsExactlyInAnyOrder("0x0000000735c101a0", "0x0000000735c17a88")
        assertThat(d1.byName("auth-worker-1")!!.waitsFor).isEqualTo("0x0000000735c101a0")
        // Object.wait() gives its monitor back, so the Finalizer holds nothing
        assertThat(d1.byName("Finalizer")!!.holds).isEmpty()
        // the deadlock report at the end of a dump is not parsed as more threads
        assertThat(deadlock1.threads.filter { it.name == "refund-A" }).hasSize(1)
    }

    @Test
    fun `hottest puts the spinning thread first, with its CPU growth`() {
        val top = DumpReader.hottest(d1, d2, 1)
        assertThat(top).hasSize(1)
        assertThat(top[0].name).isEqualTo("fee-recalc")
        assertThat(top[0].cpuMs).isCloseTo(8882.05 - 3689.36, within(0.01))
    }

    @Test
    fun `hottest leaves out RUNNABLE threads that use no CPU, such as a socket read`() {
        val names = DumpReader.hottest(d1, d2, 100).map { it.name }
        assertThat(names).doesNotContain("issuer-refresh", "auth-worker-1", "settle-worker-1")
        assertThat(DumpReader.hottest(d1, d2, 100)).allSatisfy { assertThat(it.cpuMs).isPositive() }
        assertThat(DumpReader.hottest(d1, d2, 3)).hasSizeLessThanOrEqualTo(3)
    }

    @Test
    fun `hottest matches threads by nid, because two threads can share a name`() {
        // the dump order is not a promise: reverse the first dump so a name lookup finds the wrong "worker"
        val before = ThreadDump(deadlock1.threads.reversed())
        val top = DumpReader.hottest(before, deadlock2, 1).single()
        assertThat(top.name).isEqualTo("worker")
        assertThat(top.nid).isEqualTo(29885L)
        assertThat(top.cpuMs).isCloseTo(4343.47 - 2220.05, within(0.01))
    }

    @Test
    fun `blockedChain follows a synchronized wait to the thread that holds the lock`() {
        assertThat(DumpReader.blockedChain(d1, "auth-worker-3")).containsExactly("auth-worker-3", "issuer-refresh")
    }

    @Test
    fun `blockedChain follows a ReentrantLock to its owner's ownable synchronizers`() {
        assertThat(DumpReader.blockedChain(d1, "ledger-reader")).containsExactly("ledger-reader", "ledger-writer")
    }

    @Test
    fun `blockedChain shows a deadlock as a cycle`() {
        assertThat(DumpReader.blockedChain(deadlock1, "refund-A")).containsExactly("refund-A", "refund-B", "refund-A")
        assertThat(DumpReader.blockedChain(deadlock1, "refund-B")).containsExactly("refund-B", "refund-A", "refund-B")
    }

    @Test
    fun `blockedChain ends at once for a thread that waits for nobody`() {
        assertThat(DumpReader.blockedChain(d1, "fee-recalc")).containsExactly("fee-recalc")
        // an idle pool thread parks on a condition, and a condition has no owner
        assertThat(DumpReader.blockedChain(d1, "settle-worker-1")).containsExactly("settle-worker-1")
        assertThat(DumpReader.blockedChain(d1, "no-such-thread")).isEmpty()
    }

    @Test
    fun `stuck finds the waiting threads, not the hot one and not the idle ones`() {
        assertThat(DumpReader.stuck(listOf(d1, d2, d3), "workbench.")).containsExactly(
            "auth-worker-1", "auth-worker-2", "auth-worker-3", "auth-worker-4",
            "issuer-refresh", "ledger-reader", "ledger-writer",
        )
    }

    @Test
    fun `stuck needs the thread in every dump, matched by nid`() {
        val withoutWriter = ThreadDump(d2.threads.filterNot { it.name == "ledger-writer" })
        assertThat(DumpReader.stuck(listOf(d1, withoutWriter, d3), "workbench."))
            .doesNotContain("ledger-writer")
            .contains("ledger-reader")
    }

    @Test
    fun `stuck needs the same frames in every dump`() {
        // pretend auth-worker-2 moved on to another line by the third dump
        val moved = ThreadDump(d3.threads.map {
            if (it.name == "auth-worker-2") it.copy(frames = listOf("workbench.Elsewhere.run(Elsewhere.kt:1)")) else it
        })
        assertThat(DumpReader.stuck(listOf(d1, d2, moved), "workbench.")).doesNotContain("auth-worker-2")
    }
}
