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
        val refresh = d1.byName("catalog-refresh")!!
        assertThat(refresh.state).isEqualTo("RUNNABLE")
        assertThat(refresh.nid).isEqualTo(25040L)
        assertThat(refresh.frames.first()).startsWith("sun.nio.ch.SocketDispatcher.read0")
        // the catalog monitor, and the socket's own read lock (a ReentrantLock inside NioSocketImpl)
        assertThat(refresh.holds).containsExactlyInAnyOrder("0x0000000735c08070", "0x000000072b4b85d8")
        assertThat(d1.byName("report-worker-1")!!.waitsFor).isEqualTo("0x0000000735c08070")
        // Object.wait() gives its monitor back, so the Finalizer holds nothing
        assertThat(d1.byName("Finalizer")!!.holds).isEmpty()
        // the deadlock report at the end of a dump is not parsed as more threads
        assertThat(deadlock1.threads.filter { it.name == "merge-A" }).hasSize(1)
    }

    @Test
    fun `hottest puts the spinning thread first, with its CPU growth`() {
        val top = DumpReader.hottest(d1, d2, 1)
        assertThat(top).hasSize(1)
        assertThat(top[0].name).isEqualTo("index-rebuild")
        assertThat(top[0].cpuMs).isCloseTo(6288.02 - 4089.43, within(0.01))
    }

    @Test
    fun `hottest leaves out RUNNABLE threads that use no CPU, such as a socket read`() {
        val names = DumpReader.hottest(d1, d2, 100).map { it.name }
        assertThat(names).doesNotContain("catalog-refresh", "report-worker-1", "export-worker-1")
        assertThat(DumpReader.hottest(d1, d2, 100)).allSatisfy { assertThat(it.cpuMs).isPositive() }
        assertThat(DumpReader.hottest(d1, d2, 3)).hasSizeLessThanOrEqualTo(3)
    }

    @Test
    fun `hottest matches threads by nid, because two threads can share a name`() {
        // the dump order is not a promise: reverse the first dump so a name lookup finds the wrong "worker"
        val before = ThreadDump(deadlock1.threads.reversed())
        val top = DumpReader.hottest(before, deadlock2, 1).single()
        assertThat(top.name).isEqualTo("worker")
        assertThat(top.nid).isEqualTo(24426L)
        assertThat(top.cpuMs).isCloseTo(2032.23 - 1055.03, within(0.01))
    }

    @Test
    fun `blockedChain follows a synchronized wait to the thread that holds the lock`() {
        assertThat(DumpReader.blockedChain(d1, "report-worker-3")).containsExactly("report-worker-3", "catalog-refresh")
    }

    @Test
    fun `blockedChain follows a ReentrantLock to its owner's ownable synchronizers`() {
        assertThat(DumpReader.blockedChain(d1, "archive-reader")).containsExactly("archive-reader", "archive-writer")
    }

    @Test
    fun `blockedChain shows a deadlock as a cycle`() {
        assertThat(DumpReader.blockedChain(deadlock1, "merge-A")).containsExactly("merge-A", "merge-B", "merge-A")
        assertThat(DumpReader.blockedChain(deadlock1, "merge-B")).containsExactly("merge-B", "merge-A", "merge-B")
    }

    @Test
    fun `blockedChain ends at once for a thread that waits for nobody`() {
        assertThat(DumpReader.blockedChain(d1, "index-rebuild")).containsExactly("index-rebuild")
        // an idle pool thread parks on a condition, and a condition has no owner
        assertThat(DumpReader.blockedChain(d1, "export-worker-1")).containsExactly("export-worker-1")
        assertThat(DumpReader.blockedChain(d1, "no-such-thread")).isEmpty()
    }

    @Test
    fun `stuck finds the waiting threads, not the hot one and not the idle ones`() {
        assertThat(DumpReader.stuck(listOf(d1, d2, d3), "workbench.")).containsExactly(
            "archive-reader", "archive-writer", "catalog-refresh",
            "report-worker-1", "report-worker-2", "report-worker-3", "report-worker-4",
        )
    }

    @Test
    fun `stuck needs the thread in every dump, matched by nid`() {
        val withoutWriter = ThreadDump(d2.threads.filterNot { it.name == "archive-writer" })
        assertThat(DumpReader.stuck(listOf(d1, withoutWriter, d3), "workbench."))
            .doesNotContain("archive-writer")
            .contains("archive-reader")
    }

    @Test
    fun `stuck needs the same frames in every dump`() {
        // pretend report-worker-2 moved on to another line by the third dump
        val moved = ThreadDump(d3.threads.map {
            if (it.name == "report-worker-2") it.copy(frames = listOf("workbench.Elsewhere.run(Elsewhere.kt:1)")) else it
        })
        assertThat(DumpReader.stuck(listOf(d1, d2, moved), "workbench.")).doesNotContain("report-worker-2")
    }
}
