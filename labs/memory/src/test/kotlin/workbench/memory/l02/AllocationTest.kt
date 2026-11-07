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

    private val merchants = 500
    private val random = Random(42)
    private val ids = IntArray(20_000) { random.nextInt(merchants) }
    private val amounts = LongArray(20_000) { 1_000L + random.nextLong(250_000) }

    private var sink: Any? = null   // results go here, so the measured code can't be optimized away

    @Test
    fun `the meter counts a 1 MiB array as its payload plus a 16-byte header`() {
        val bytes = AllocationMeter.bytesAllocatedBy { sink = ByteArray(1 shl 20) }
        assertThat(bytes).isBetween((1L shl 20), (1L shl 20) + 64)
    }

    @Test
    fun `the meter counts nothing for code that only does arithmetic`() {
        var total = 0L
        val bytes = AllocationMeter.bytesAllocatedBy { for (a in amounts) total += a }
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
    fun `totalsByMerchant adds up every payment`() {
        val batch = SettlementBatch(3)
        val totals = batch.totalsByMerchant(intArrayOf(0, 2, 0, 2, 2), longArrayOf(1_000, 250, 4_500, 250, 9_999))
        assertThat(totals).containsExactly(5_500L, 0L, 10_499L)

        val expected = LongArray(merchants)
        for (i in ids.indices) expected[ids[i]] += amounts[i]
        assertThat(SettlementBatch(merchants).totalsByMerchant(ids, amounts)).containsExactly(*expected)
    }

    @Test
    fun `totalsByMerchant for 20,000 payments allocates only its result`() {
        val batch = SettlementBatch(merchants)
        batch.totalsByMerchant(intArrayOf(1), longArrayOf(1))          // warm-up: load every class it uses first
        val bytes = allocated { sink = batch.totalsByMerchant(ids, amounts) }
        assertThat(bytes).`as`("bytes allocated (the result alone is %d)", longArrayBytes(merchants))
            .isLessThanOrEqualTo(longArrayBytes(merchants) + 512)
    }

    @Test
    fun `rollingSums sums each window`() {
        val batch = SettlementBatch(1)
        assertThat(batch.rollingSums(longArrayOf(100, 200, 300, 400), 2)).containsExactly(300L, 500L, 700L)
        assertThat(batch.rollingSums(longArrayOf(100, 200, 300, 400), 4)).containsExactly(1_000L)
        assertThat(batch.rollingSums(longArrayOf(7, 8, 9), 1)).containsExactly(7L, 8L, 9L)

        val window = 25
        val expected = LongArray(amounts.size - window + 1) { start -> (start until start + window).sumOf { amounts[it] } }
        assertThat(batch.rollingSums(amounts, window)).containsExactly(*expected)
    }

    @Test
    fun `rollingSums over 20,000 amounts allocates only its result`() {
        val batch = SettlementBatch(1)
        batch.rollingSums(longArrayOf(1, 2, 3), 2)                       // warm-up
        val window = 25
        val bytes = allocated { sink = batch.rollingSums(amounts, window) }
        val result = longArrayBytes(amounts.size - window + 1)
        assertThat(bytes).`as`("bytes allocated (the result alone is %d)", result).isLessThanOrEqualTo(result + 512)
    }
}
