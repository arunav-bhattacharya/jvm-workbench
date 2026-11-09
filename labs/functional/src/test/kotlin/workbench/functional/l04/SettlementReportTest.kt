package workbench.functional.l04

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.assertj.core.api.Assertions.entry
import org.junit.jupiter.api.Test
import workbench.functional.l04.Status.FAILED
import workbench.functional.l04.Status.PENDING
import workbench.functional.l04.Status.SETTLED

class SettlementReportTest {
    private val p1 = Payment("pay_1", "acme", 1_500, SETTLED)
    private val p2 = Payment("pay_2", "globex", 9_900, PENDING)
    private val p3 = Payment("pay_3", "acme", 2_000, SETTLED, refundCents = 500)
    private val p4 = Payment("pay_4", "initech", 12_000, FAILED)
    private val p5 = Payment("pay_5", "globex", 700, SETTLED)
    private val day = listOf(Batch("b1", listOf(p1, p2, p3)), Batch("b2", listOf(p4, p5)))
    private val all = listOf(p1, p2, p3, p4, p5)

    @Test
    fun `allPayments flattens the batches in order`() {
        assertThat(allPayments(day)).containsExactly(p1, p2, p3, p4, p5)
        assertThat(allPayments(listOf(Batch("empty", emptyList())))).isEmpty()
    }

    @Test
    fun `settledCents counts only settled payments, and 0 for none`() {
        assertThat(settledCents(all)).isEqualTo(4_200)
        assertThat(settledCents(listOf(p2, p4))).isEqualTo(0)
        assertThat(settledCents(emptyList())).isEqualTo(0)
    }

    @Test
    fun `refundedCents adds up the refunds that exist`() {
        assertThat(refundedCents(all)).isEqualTo(500)
        assertThat(refundedCents(listOf(p1, p2))).isEqualTo(0)
    }

    @Test
    fun `netByMerchant subtracts refunds and keeps merchants in first-seen order`() {
        assertThat(netByMerchant(all)).containsExactly(entry("acme", 3_000L), entry("globex", 700L))
        val zetaFirst = listOf(Payment("z1", "zeta", 100, SETTLED), Payment("a1", "alpha", 200, SETTLED), Payment("z2", "zeta", 50, SETTLED))
        assertThat(netByMerchant(zetaFirst).keys).`as`("first-seen order, not sorted").containsExactly("zeta", "alpha")
        assertThat(netByMerchant(listOf(p2, p4))).isEmpty()
    }

    @Test
    fun `failedIds lists failed payments in input order`() {
        val p6 = Payment("pay_6", "acme", 300, FAILED)
        assertThat(failedIds(all + p6)).containsExactly("pay_4", "pay_6")
        assertThat(failedIds(emptyList())).isEmpty()
    }

    @Test
    fun `largestSettled ignores unsettled payments and is null when nothing settled`() {
        assertThat(largestSettled(all)).`as`("pay_4 and pay_2 are bigger, but not settled").isEqualTo(p3)
        assertThat(largestSettled(listOf(p2, p4))).isNull()
        assertThat(largestSettled(emptyList())).isNull()
    }

    @Test
    fun `closingBalance folds every payment into the opening balance`() {
        assertThat(closingBalance(10_000, all)).isEqualTo(13_700)   // + 1,500 + (2,000 - 500) + 700
        assertThat(closingBalance(10_000, emptyList())).isEqualTo(10_000)
        assertThat(closingBalance(0, listOf(p2, p4))).isEqualTo(0)
    }

    @Test
    fun `indexById maps each id to its payment`() {
        val index = indexById(all)
        assertThat(index).hasSize(5)
        assertThat(index["pay_3"]).isEqualTo(p3)
        assertThat(indexById(emptyList())).isEmpty()
    }

    @Test
    fun `indexById rejects repeated ids and names each one once, in first-seen order`() {
        val p7 = Payment("pay_7", "acme", 10, SETTLED)
        val redelivered = listOf(p1, p2, p7, p2.copy(), p7.copy(amountCents = 11), p2.copy())
        assertThatThrownBy { indexById(redelivered) }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("duplicate payment ids: pay_2, pay_7")
    }

    @Test
    fun `settlementReport matches the loop version on a normal day`() {
        val expected = SettlementReport(5, 4_200, 500, mapOf("acme" to 3_000L, "globex" to 700L), listOf("pay_4"), p3)
        assertThat(settlementReport(day)).isEqualTo(expected)
        assertThat(settlementReport(day)).isEqualTo(settlementReportLoop(day))
    }

    @Test
    fun `settlementReport on an empty day gives zeros, not an exception`() {
        val empty = SettlementReport(0, 0, 0, emptyMap(), emptyList(), null)
        assertThat(settlementReport(emptyList())).isEqualTo(empty)
        assertThat(settlementReport(listOf(Batch("b1", emptyList())))).isEqualTo(empty)
    }

    @Test
    fun `settlementReport refuses a day where a payment arrived in two batches`() {
        val redelivered = listOf(Batch("b1", listOf(p1, p2)), Batch("b1-retry", listOf(p2, p3)))
        assertThatThrownBy { settlementReport(redelivered) }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("duplicate payment ids: pay_2")
    }
}
