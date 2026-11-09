package workbench.functional.l08

import kotlinx.collections.immutable.persistentListOf
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.math.BigDecimal
import java.time.Clock
import java.time.LocalDate
import java.time.ZoneOffset

class FunctionalCoreTest {

    private val today = LocalDate.of(2026, 3, 10)
    private val merchants = mapOf(
        "m-acme" to Merchant("m-acme", BigDecimal("0.029"), holdDays = 2),
        "m-globex" to Merchant("m-globex", BigDecimal("0.015"), holdDays = 7),
    )

    private fun pay(id: String, merchant: String, euros: String, daysAgo: Long, refunded: Boolean = false) =
        Payment(id, merchant, BigDecimal(euros), today.minusDays(daysAgo), refunded)

    // ---- the core: plain values in, a plan out; no clock, no store, no fakes ----

    @Test
    fun `due payments are summed per merchant with the fee rounded to cents`() {
        val plan = planSettlement(listOf(pay("p1", "m-acme", "100.00", 3), pay("p2", "m-acme", "25.50", 2)), merchants, today)
        // 125.50 * 0.029 = 3.63950, rounded HALF_EVEN to 3.64
        assertThat(plan.payouts).containsExactly(Payout("m-acme", BigDecimal("125.50"), BigDecimal("3.64"), BigDecimal("121.86")))
    }

    @Test
    fun `payments still inside the hold period are held`() {
        val plan = planSettlement(listOf(pay("p1", "m-acme", "10.00", 1), pay("p2", "m-acme", "20.00", 2)), merchants, today)
        assertThat(plan.held).containsExactly("p1")
        assertThat(plan.payouts.single().gross).isEqualTo(BigDecimal("20.00"))
    }

    @Test
    fun `refunded payments are skipped and unknown merchants are reported`() {
        val plan = planSettlement(
            listOf(pay("p1", "m-acme", "10.00", 5, refunded = true), pay("p2", "m-initech", "99.00", 5), pay("p3", "m-acme", "40.00", 5)),
            merchants, today,
        )
        assertThat(plan.unknownMerchants).containsExactly("p2")
        assertThat(plan.held).isEmpty()
        assertThat(plan.payouts.map { it.gross }).containsExactly(BigDecimal("40.00"))
    }

    @Test
    fun `payouts are ordered by merchant id`() {
        val plan = planSettlement(listOf(pay("p1", "m-globex", "200.00", 9), pay("p2", "m-acme", "50.00", 9)), merchants, today)
        assertThat(plan.payouts.map { it.merchantId }).containsExactly("m-acme", "m-globex")
        assertThat(plan.payouts[1]).isEqualTo(Payout("m-globex", BigDecimal("200.00"), BigDecimal("3.00"), BigDecimal("197.00")))
    }

    @Test
    fun `an empty day gives an empty plan`() {
        assertThat(planSettlement(emptyList(), merchants, today)).isEqualTo(SettlementPlan(emptyList(), emptyList(), emptyList()))
    }

    @Test
    fun `the date is an input, so a later day can release held money`() {
        val payments = listOf(pay("p1", "m-globex", "80.00", 3))
        assertThat(planSettlement(payments, merchants, today).held).containsExactly("p1")
        assertThat(planSettlement(payments, merchants, today.plusDays(4)).held).isEmpty()
    }

    @Test
    fun `posting returns a new ledger and leaves the old one alone`() {
        val before = Ledger(persistentListOf(Entry("opening", BigDecimal("0.00"), "init")))
        val after = before.posting(listOf(Payout("m-acme", BigDecimal("125.50"), BigDecimal("3.64"), BigDecimal("121.86"))), "settlement-2026-03-10")
        assertThat(after.entries).containsExactly(
            Entry("opening", BigDecimal("0.00"), "init"),
            Entry("payout:m-acme", BigDecimal("121.86"), "settlement-2026-03-10"),
            Entry("fee-income", BigDecimal("3.64"), "settlement-2026-03-10"),
        )
        assertThat(before.entries).`as`("the ledger we posted to").containsExactly(Entry("opening", BigDecimal("0.00"), "init"))
    }

    // ---- the shell: one test with fakes checks the wiring ----

    private class FakeStore(private val payments: List<Payment>, private val merchants: Map<String, Merchant>) : PaymentStore {
        val saved = mutableListOf<Ledger>()
        override fun capturedPayments() = payments
        override fun merchants() = merchants
        override fun loadLedger() = Ledger(persistentListOf())
        override fun saveLedger(ledger: Ledger) { saved += ledger }
    }

    @Test
    fun `the shell sends every payout and saves the ledger once`() {
        val store = FakeStore(listOf(pay("p1", "m-globex", "200.00", 9), pay("p2", "m-acme", "50.00", 9), pay("p3", "m-acme", "5.00", 0)), merchants)
        val sent = mutableListOf<Payout>()
        val clock = Clock.fixed(today.atStartOfDay().toInstant(ZoneOffset.UTC), ZoneOffset.UTC)

        val plan = SettlementJob(store, { sent += it }, clock).run()

        assertThat(sent).isEqualTo(plan.payouts)
        assertThat(sent.map { it.merchantId }).containsExactly("m-acme", "m-globex")
        assertThat(plan.held).containsExactly("p3")
        assertThat(store.saved).`as`("ledger saves").hasSize(1)
        assertThat(store.saved.single().entries.map { it.ref }.distinct()).containsExactly("settlement-2026-03-10")
        assertThat(store.saved.single().entries).hasSize(4)
    }
}
