package workbench.functional.l06

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class ScopeFunctionsTest {

    private val payment = Payment("pay-311", Money(1_999, "EUR"), Status.AUTHORIZED, "tok_4242")

    /** A ledger that remembers what it posted and counts every call. */
    private class FakeLedger(alreadyPosted: Set<String> = emptySet()) : Ledger {
        private val posted = alreadyPosted.toMutableSet()
        var calls = 0
        override fun post(payment: Payment): String? {
            calls++
            return if (posted.add(payment.id)) "LE-${payment.id}" else null
        }
    }

    private class CountingFetch(private val payment: Payment) : () -> Payment {
        var calls = 0
        override fun invoke(): Payment { calls++; return payment }
    }

    // ---- settle ----

    @Test
    fun `settle posts the cached payment without touching the database`() {
        val ledger = FakeLedger()
        val fetch = CountingFetch(payment)
        assertThat(settle(payment, ledger, fetch)).isEqualTo(SettleResult.Posted("LE-pay-311"))
        assertThat(fetch.calls).`as`("database fetches").isZero()
    }

    @Test
    fun `settle fetches and posts on a cache miss`() {
        val ledger = FakeLedger()
        val fetch = CountingFetch(payment)
        assertThat(settle(null, ledger, fetch)).isEqualTo(SettleResult.Posted("LE-pay-311"))
        assertThat(fetch.calls).isEqualTo(1)
    }

    @Test
    fun `settle reports a duplicate on a cache hit without fetching or posting again`() {
        val ledger = FakeLedger(alreadyPosted = setOf("pay-311"))
        val fetch = CountingFetch(payment)
        assertThat(settle(payment, ledger, fetch)).isEqualTo(SettleResult.AlreadyPosted("pay-311"))
        assertThat(fetch.calls).`as`("database fetches on a cache hit").isZero()
        assertThat(ledger.calls).`as`("ledger posts").isEqualTo(1)
    }

    @Test
    fun `settle reports a duplicate on a cache miss`() {
        val ledger = FakeLedger(alreadyPosted = setOf("pay-311"))
        assertThat(settle(null, ledger, CountingFetch(payment))).isEqualTo(SettleResult.AlreadyPosted("pay-311"))
        assertThat(ledger.calls).isEqualTo(1)
    }

    // ---- capture ----

    @Test
    fun `capture marks an authorized payment as captured`() {
        assertThat(capture(payment)).isEqualTo(payment.copy(status = Status.CAPTURED))
    }

    @Test
    fun `capture leaves a declined payment alone`() {
        val declined = payment.copy(status = Status.DECLINED)
        assertThat(capture(declined)).isEqualTo(declined)
    }

    // ---- buildRequest ----

    @Test
    fun `buildRequest puts the order id in the request's reference`() {
        val request = buildRequest(Order("ord-981", "m-42", Money(4_250, "EUR")))
        assertThat(request.reference).`as`("the idempotency key on the request").isEqualTo("ord-981")
        assertThat(request.metadata.reference).`as`("the merchant's free-text reference").isEmpty()
    }

    @Test
    fun `buildRequest copies amount and merchant and sets the channel`() {
        val request = buildRequest(Order("ord-981", "m-42", Money(4_250, "EUR")))
        assertThat(request.amount).isEqualTo(Money(4_250, "EUR"))
        assertThat(request.merchantId).isEqualTo("m-42")
        assertThat(request.metadata.channel).isEqualTo("ecom")
    }

    // ---- feeLabel ----

    private val merchants = mapOf(
        "m-1" to Merchant("m-1", "Acme Books", "eu-standard"),
        "m-2" to Merchant("m-2", "Globex Travel", "eu-premium"),
    )
    private val schedules = mapOf("eu-standard" to FeeSchedule("eu-standard", "standard-eu", 290))

    @Test
    fun `feeLabel names the merchant and its rate`() {
        assertThat(feeLabel("m-1", merchants, schedules)).isEqualTo("Acme Books: 290 bps")
    }

    @Test
    fun `feeLabel handles a missing merchant and a missing schedule`() {
        assertThat(feeLabel("m-7", merchants, schedules)).isEqualTo("m-7: no fee schedule")
        assertThat(feeLabel("m-2", merchants, schedules)).isEqualTo("m-2: no fee schedule")
    }
}
