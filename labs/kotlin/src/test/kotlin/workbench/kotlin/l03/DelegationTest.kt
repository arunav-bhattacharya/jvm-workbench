package workbench.kotlin.l03

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

class DelegationTest {

    @Test
    fun `recorded properties return their value and log only real changes, in order`() {
        val draft = PaymentDraft(ChangeLog())
        assertThat(draft.status).isEqualTo("NEW")
        draft.status = "AUTHORIZED"
        draft.status = "AUTHORIZED"          // same value: not a change
        draft.amountMinor = 1_999
        draft.note = "split order"
        draft.status = "CAPTURED"
        assertThat(draft.status).isEqualTo("CAPTURED")
        assertThat(draft.amountMinor).isEqualTo(1_999)
        assertThat(draft.log.changes).containsExactly(
            Change("status", "NEW", "AUTHORIZED"),
            Change("amountMinor", 0L, 1_999L),
            Change("note", null, "split order"),
            Change("status", "AUTHORIZED", "CAPTURED"),
        )
    }

    @Test
    fun `provideDelegate registers every property while the object is built, before any access`() {
        val log = ChangeLog()
        PaymentDraft(log)
        assertThat(log.tracked).containsExactly("status", "amountMinor", "note")
        assertThat(log.changes).isEmpty()
        // and the compiler kept what provideDelegate returned in a hidden field
        assertThat(PaymentDraft::class.java.getDeclaredField("status\$delegate").type).isEqualTo(Recorded::class.java)
    }

    @Test
    fun `a log refuses to track the same property name twice`() {
        val shared = ChangeLog()
        PaymentDraft(shared)
        assertThatThrownBy { PaymentDraft(shared) }
            .isInstanceOf(IllegalStateException::class.java)
            .hasMessageContaining("status")
    }

    @Test
    fun `currency ignores values that are not three capital letters`() {
        val draft = PaymentDraft(ChangeLog())
        assertThat(draft.currency).isEqualTo("EUR")
        draft.currency = "usd"
        assertThat(draft.currency).isEqualTo("EUR")
        draft.currency = "EURO"
        assertThat(draft.currency).isEqualTo("EUR")
        draft.currency = "GBP"
        assertThat(draft.currency).isEqualTo("GBP")
    }

    @Test
    fun `MerchantConfig reads from the map, and a missing key fails on access`() {
        val ok = MerchantConfig(mapOf("name" to "Kiosk 7", "dailyLimitMinor" to 500_000L))
        assertThat(ok.name).isEqualTo("Kiosk 7")
        assertThat(ok.dailyLimitMinor).isEqualTo(500_000L)

        val partial = MerchantConfig(mapOf("name" to "Kiosk 8"))   // building it is fine
        assertThat(partial.name).isEqualTo("Kiosk 8")
        assertThatThrownBy { partial.dailyLimitMinor }
            .isInstanceOf(NoSuchElementException::class.java)
            .hasMessageContaining("dailyLimitMinor")
    }
}
