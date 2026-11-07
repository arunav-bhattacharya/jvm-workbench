package workbench.modernjava.l04

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import workbench.modernjava.l04.AuthResult.Approved
import workbench.modernjava.l04.AuthResult.Declined
import workbench.modernjava.l04.AuthResult.RetryLater
import workbench.modernjava.l04.Parsed.Ok
import workbench.modernjava.l04.Parsed.Rejected
import java.time.Duration

class AuthModelTest {

    private fun reply(
        status: String? = null, authCode: String? = null, declineCode: String? = null,
        retryAfterSeconds: Long? = null, amountMinor: Long? = null,
    ) = RawReply(status, authCode, declineCode, retryAfterSeconds, amountMinor)

    // ---- the model refuses values that can't be real ----

    @Test
    fun `an auth code is exactly six upper-case letters or digits`() {
        assertThat(AuthCode("A1B2C3").value).isEqualTo("A1B2C3")
        assertThatThrownBy { AuthCode("A1B2C") }.isInstanceOf(IllegalArgumentException::class.java)
        assertThatThrownBy { AuthCode("a1b2c3") }.isInstanceOf(IllegalArgumentException::class.java)
        assertThatThrownBy { AuthCode("A1B2C3D") }.isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `an approval needs a positive amount`() {
        assertThat(Approved(AuthCode("A1B2C3"), 1).amountMinor).isEqualTo(1)
        assertThatThrownBy { Approved(AuthCode("A1B2C3"), 0) }.isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `a retry wait is between one second and one hour`() {
        assertThat(RetryLater(Duration.ofSeconds(1)).after).isEqualTo(Duration.ofSeconds(1))
        assertThat(RetryLater(Duration.ofHours(1)).after).isEqualTo(Duration.ofHours(1))
        assertThatThrownBy { RetryLater(Duration.ZERO) }.isInstanceOf(IllegalArgumentException::class.java)
        assertThatThrownBy { RetryLater(Duration.ofSeconds(3_601)) }.isInstanceOf(IllegalArgumentException::class.java)
    }

    // ---- parse: the boundary ----

    @Test
    fun `parse turns a complete approval into Approved`() {
        assertThat(parse(reply("APPROVED", authCode = "A1B2C3", amountMinor = 4_200)))
            .isEqualTo(Ok(Approved(AuthCode("A1B2C3"), 4_200)))
    }

    @Test
    fun `parse rejects an approval without a code or an amount, or with a code the model refuses`() {
        assertThat(parse(reply("APPROVED", amountMinor = 4_200))).isInstanceOf(Rejected::class.java)
        assertThat(parse(reply("APPROVED", authCode = "A1B2C3"))).isInstanceOf(Rejected::class.java)
        assertThat(parse(reply("APPROVED", authCode = "12", amountMinor = 4_200))).isInstanceOf(Rejected::class.java)
        assertThat(parse(reply("APPROVED", authCode = "A1B2C3", amountMinor = 0))).isInstanceOf(Rejected::class.java)
    }

    @Test
    fun `parse rejects a reply that contradicts itself`() {
        val both = reply("APPROVED", authCode = "A1B2C3", declineCode = "51", amountMinor = 4_200)
        assertThat(parse(both)).isInstanceOf(Rejected::class.java)
    }

    @Test
    fun `parse maps decline codes, and an unknown or missing code is OTHER`() {
        assertThat(parse(reply("DECLINED", declineCode = "51"))).isEqualTo(Ok(Declined(DeclineReason.INSUFFICIENT_FUNDS)))
        assertThat(parse(reply("DECLINED", declineCode = "62"))).isEqualTo(Ok(Declined(DeclineReason.CARD_BLOCKED)))
        assertThat(parse(reply("DECLINED", declineCode = "59"))).isEqualTo(Ok(Declined(DeclineReason.SUSPECTED_FRAUD)))
        assertThat(parse(reply("DECLINED", declineCode = "05"))).isEqualTo(Ok(Declined(DeclineReason.OTHER)))
        assertThat(parse(reply("DECLINED"))).isEqualTo(Ok(Declined(DeclineReason.OTHER)))
    }

    @Test
    fun `parse reads a soft decline into RetryLater and rejects one without a usable wait`() {
        assertThat(parse(reply("SOFT_DECLINE", retryAfterSeconds = 30))).isEqualTo(Ok(RetryLater(Duration.ofSeconds(30))))
        assertThat(parse(reply("SOFT_DECLINE"))).isInstanceOf(Rejected::class.java)
        assertThat(parse(reply("SOFT_DECLINE", retryAfterSeconds = 0))).isInstanceOf(Rejected::class.java)
    }

    @Test
    fun `parse rejects an unknown or missing status`() {
        assertThat(parse(reply("PENDING"))).isInstanceOf(Rejected::class.java)
        assertThat(parse(reply())).isInstanceOf(Rejected::class.java)
    }

    // ---- an operation, kept apart from the data ----

    @Test
    fun `customerMessage has one message per outcome and never says fraud`() {
        assertThat(customerMessage(Approved(AuthCode("A1B2C3"), 4_200))).isEqualTo("Payment approved.")
        assertThat(customerMessage(Declined(DeclineReason.INSUFFICIENT_FUNDS))).isEqualTo("Not enough funds. Try another card.")
        assertThat(customerMessage(Declined(DeclineReason.SUSPECTED_FRAUD))).isEqualTo("Payment declined. Please contact your bank.")
        assertThat(customerMessage(Declined(DeclineReason.CARD_BLOCKED))).isEqualTo("Payment declined.")
        assertThat(customerMessage(RetryLater(Duration.ofSeconds(30)))).isEqualTo("Your bank is busy. We'll try again in 30 seconds.")
    }
}
