package workbench.functional.l01

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import java.math.BigDecimal
import java.time.Clock
import java.time.Instant
import java.time.LocalTime
import java.time.ZoneOffset

class PureFeeTest {
    private fun money(s: String) = BigDecimal(s)

    // The shell tests touch two globals, so every test has to reset them. The core tests don't need this.
    @BeforeEach
    @AfterEach
    fun resetGlobals() {
        FeeConfig.rates = STANDARD_RATES
        AuditLog.lines.clear()
    }

    // ---- the functional core: plain values in, a value out, no clock anywhere ----

    @Test
    fun `payoutFee charges the percentage, rounded half-even to cents`() {
        assertThat(payoutFee(money("200.00"), STANDARD_RATES, LocalTime.of(9, 30))).isEqualByComparingTo("3.00")
        assertThat(payoutFee(money("150.50"), STANDARD_RATES, LocalTime.of(9, 30))).isEqualByComparingTo("2.26")
        // 43.00 x 1.5 % = 0.645: half-even rounds to the even neighbour, 0.64 (HALF_UP would give 0.65)
        assertThat(payoutFee(money("43.00"), STANDARD_RATES, LocalTime.of(9, 30))).isEqualByComparingTo("0.64")
    }

    @Test
    fun `payoutFee never charges less than the minimum`() {
        assertThat(payoutFee(money("10.00"), STANDARD_RATES, LocalTime.of(9, 30))).isEqualByComparingTo("0.50")
    }

    @Test
    fun `payoutFee adds the late surcharge at and after the cut-off, not before`() {
        val amount = money("200.00")
        assertThat(payoutFee(amount, STANDARD_RATES, LocalTime.of(15, 59, 59))).isEqualByComparingTo("3.00")
        assertThat(payoutFee(amount, STANDARD_RATES, LocalTime.of(16, 0))).isEqualByComparingTo("4.00")
        assertThat(payoutFee(money("10.00"), STANDARD_RATES, LocalTime.of(23, 0))).isEqualByComparingTo("1.50")
    }

    @Test
    fun `payoutFee reads nothing but its arguments`() {
        FeeConfig.rates = STANDARD_RATES.copy(percent = money("0.50"))   // an absurd global: 50 %
        val premium = STANDARD_RATES.copy(percent = money("0.025"), cutoff = LocalTime.of(18, 0))
        assertThat(payoutFee(money("200.00"), STANDARD_RATES, LocalTime.of(9, 0)))
            .`as`("payoutFee must use the rates it is given, not FeeConfig")
            .isEqualByComparingTo("3.00")
        assertThat(payoutFee(money("200.00"), premium, LocalTime.of(17, 0))).isEqualByComparingTo("5.00")
    }

    @Test
    fun `payoutFee changes nothing, gives the same answer every call and writes no audit lines`() {
        val calls = List(3) { payoutFee(money("200.00"), STANDARD_RATES, LocalTime.of(16, 30)) }
        assertThat(calls).allSatisfy { assertThat(it).isEqualByComparingTo("4.00") }
        assertThat(AuditLog.lines).`as`("the core must not write the audit log; the shell does").isEmpty()
    }

    @Test
    fun `auditLine builds the text the shell will write`() {
        assertThat(auditLine(money("200.00"), money("3.00"), LocalTime.of(15, 30)))
            .isEqualTo("payout fee 3.00 on 200.00 at 15:30")
    }

    // ---- the imperative shell: these already pass on the original code and must keep passing ----

    private fun clockAt(hhmm: String): Clock = Clock.fixed(Instant.parse("2026-03-02T$hhmm:00Z"), ZoneOffset.UTC)

    @Test
    fun `quotePayoutFee before the cut-off quotes the fee and writes one audit line`() {
        assertThat(quotePayoutFee(money("200.00"), clockAt("15:30"))).isEqualByComparingTo("3.00")
        assertThat(AuditLog.lines).containsExactly("payout fee 3.00 on 200.00 at 15:30")
    }

    @Test
    fun `quotePayoutFee at the cut-off adds the surcharge`() {
        assertThat(quotePayoutFee(money("200.00"), clockAt("16:00"))).isEqualByComparingTo("4.00")
        assertThat(AuditLog.lines).containsExactly("payout fee 4.00 on 200.00 at 16:00")
    }

    @Test
    fun `quotePayoutFee follows the global config`() {
        FeeConfig.rates = STANDARD_RATES.copy(percent = money("0.020"))
        assertThat(quotePayoutFee(money("200.00"), clockAt("10:00"))).isEqualByComparingTo("4.00")
        assertThat(AuditLog.lines).hasSize(1)
    }
}
