package workbench.memory.l02

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.lang.management.ManagementFactory
import java.util.concurrent.atomic.AtomicReference
import kotlin.random.Random

class AllocationTest {
    // the tests measure with their own counter, so a bug in your AllocationMeter can't hide the other results
    private val threads = ManagementFactory.getThreadMXBean() as com.sun.management.ThreadMXBean

    private fun allocated(block: () -> Unit): Long {
        val before = threads.currentThreadAllocatedBytes
        block()
        return threads.currentThreadAllocatedBytes - before
    }

    /** Bytes of the LongArray the methods return: 16 bytes of header and length, 8 per element. */
    private fun longArrayBytes(n: Int) = 16L + 8L * n

    private val users = 500
    private val random = Random(42)
    private val ids = IntArray(20_000) { random.nextInt(users) }
    private val sizes = LongArray(20_000) { 1_000L + random.nextLong(250_000) }   // bytes per upload

    private var sink: Any? = null   // results go here, so the measured code can't be optimized away

    @Test
    fun `the meter counts a 1 MiB array as its payload plus a 16-byte header`() {
        val bytes = AllocationMeter.bytesAllocatedBy { sink = ByteArray(1 shl 20) }
        assertThat(bytes).isBetween((1L shl 20), (1L shl 20) + 64)
    }

    @Test
    fun `the meter counts nothing for code that only does arithmetic`() {
        var total = 0L
        val bytes = AllocationMeter.bytesAllocatedBy { for (s in sizes) total += s }
        assertThat(bytes).isZero()
        assertThat(total).isPositive()
    }

    @Test
    fun `the meter refuses to measure on a virtual thread`() {
        val failure = AtomicReference<Throwable>()
        Thread.ofVirtual().start {
            try { AllocationMeter.bytesAllocatedBy { } } catch (e: Throwable) { failure.set(e) }
        }.join()
        assertThat(failure.get()).isInstanceOf(IllegalStateException::class.java)
    }

    @Test
    fun `bytesByUser adds up every upload`() {
        val report = UploadReport(3)
        val totals = report.bytesByUser(intArrayOf(0, 2, 0, 2, 2), longArrayOf(1_000, 250, 4_500, 250, 9_999))
        assertThat(totals).containsExactly(5_500L, 0L, 10_499L)

        val expected = LongArray(users)
        for (i in ids.indices) expected[ids[i]] += sizes[i]
        assertThat(UploadReport(users).bytesByUser(ids, sizes)).containsExactly(*expected)
    }

    @Test
    fun `bytesByUser for 20,000 uploads allocates only its result`() {
        val report = UploadReport(users)
        report.bytesByUser(intArrayOf(1), longArrayOf(1))              // warm-up: load every class it uses first
        val bytes = allocated { sink = report.bytesByUser(ids, sizes) }
        assertThat(bytes).`as`("bytes allocated (the result alone is %d)", longArrayBytes(users))
            .isLessThanOrEqualTo(longArrayBytes(users) + 512)
    }

    @Test
    fun `rollingSums sums each window`() {
        val report = UploadReport(1)
        assertThat(report.rollingSums(longArrayOf(100, 200, 300, 400), 2)).containsExactly(300L, 500L, 700L)
        assertThat(report.rollingSums(longArrayOf(100, 200, 300, 400), 4)).containsExactly(1_000L)
        assertThat(report.rollingSums(longArrayOf(7, 8, 9), 1)).containsExactly(7L, 8L, 9L)

        val window = 25
        val expected = LongArray(sizes.size - window + 1) { start -> (start until start + window).sumOf { sizes[it] } }
        assertThat(report.rollingSums(sizes, window)).containsExactly(*expected)
    }

    @Test
    fun `rollingSums over 20,000 sizes allocates only its result`() {
        val report = UploadReport(1)
        report.rollingSums(longArrayOf(1, 2, 3), 2)                      // warm-up
        val window = 25
        val bytes = allocated { sink = report.rollingSums(sizes, window) }
        val result = longArrayBytes(sizes.size - window + 1)
        assertThat(bytes).`as`("bytes allocated (the result alone is %d)", result).isLessThanOrEqualTo(result + 512)
    }
}
