package workbench.modernjava.l04

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import workbench.modernjava.l04.HoldResult.Ready
import workbench.modernjava.l04.HoldResult.Unavailable
import workbench.modernjava.l04.HoldResult.Waitlisted
import workbench.modernjava.l04.Parsed.Ok
import workbench.modernjava.l04.Parsed.Rejected
import java.time.Duration

class HoldModelTest {

    private fun reply(
        status: String? = null, pickupCode: String? = null, reasonCode: String? = null,
        waitDays: Int? = null, holdShelf: Int? = null,
    ) = RawReply(status, pickupCode, reasonCode, waitDays, holdShelf)

    // ---- the model refuses values that can't be real ----

    @Test
    fun `a pickup code is exactly six upper-case letters or digits`() {
        assertThat(PickupCode("K7P2QX").value).isEqualTo("K7P2QX")
        assertThatThrownBy { PickupCode("K7P2Q") }.isInstanceOf(IllegalArgumentException::class.java)
        assertThatThrownBy { PickupCode("k7p2qx") }.isInstanceOf(IllegalArgumentException::class.java)
        assertThatThrownBy { PickupCode("K7P2QXY") }.isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `a ready hold needs a shelf numbered from 1 up`() {
        assertThat(Ready(PickupCode("K7P2QX"), 1).shelf).isEqualTo(1)
        assertThatThrownBy { Ready(PickupCode("K7P2QX"), 0) }.isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `a wait on the waiting list is between one day and one year`() {
        assertThat(Waitlisted(Duration.ofDays(1)).wait).isEqualTo(Duration.ofDays(1))
        assertThat(Waitlisted(Duration.ofDays(365)).wait).isEqualTo(Duration.ofDays(365))
        assertThatThrownBy { Waitlisted(Duration.ZERO) }.isInstanceOf(IllegalArgumentException::class.java)
        assertThatThrownBy { Waitlisted(Duration.ofDays(366)) }.isInstanceOf(IllegalArgumentException::class.java)
    }

    // ---- parse: the edge ----

    @Test
    fun `parse turns a complete ready reply into Ready`() {
        assertThat(parse(reply("READY", pickupCode = "K7P2QX", holdShelf = 12)))
            .isEqualTo(Ok(Ready(PickupCode("K7P2QX"), 12)))
    }

    @Test
    fun `parse rejects a ready reply without a code or a shelf, or with a value the model refuses`() {
        assertThat(parse(reply("READY", holdShelf = 12))).isInstanceOf(Rejected::class.java)
        assertThat(parse(reply("READY", pickupCode = "K7P2QX"))).isInstanceOf(Rejected::class.java)
        assertThat(parse(reply("READY", pickupCode = "12", holdShelf = 12))).isInstanceOf(Rejected::class.java)
        assertThat(parse(reply("READY", pickupCode = "K7P2QX", holdShelf = 0))).isInstanceOf(Rejected::class.java)
    }

    @Test
    fun `parse rejects a reply that contradicts itself`() {
        val both = reply("READY", pickupCode = "K7P2QX", reasonCode = "10", holdShelf = 12)
        assertThat(parse(both)).isInstanceOf(Rejected::class.java)
    }

    @Test
    fun `parse maps reason codes, and an unknown or missing code is OTHER`() {
        assertThat(parse(reply("UNAVAILABLE", reasonCode = "10"))).isEqualTo(Ok(Unavailable(Reason.LOST)))
        assertThat(parse(reply("UNAVAILABLE", reasonCode = "20"))).isEqualTo(Ok(Unavailable(Reason.NOT_IN_CATALOGUE)))
        assertThat(parse(reply("UNAVAILABLE", reasonCode = "30"))).isEqualTo(Ok(Unavailable(Reason.ACCOUNT_BLOCKED)))
        assertThat(parse(reply("UNAVAILABLE", reasonCode = "99"))).isEqualTo(Ok(Unavailable(Reason.OTHER)))
        assertThat(parse(reply("UNAVAILABLE"))).isEqualTo(Ok(Unavailable(Reason.OTHER)))
    }

    @Test
    fun `parse reads a waiting-list reply into Waitlisted and rejects one without a usable wait`() {
        assertThat(parse(reply("WAITLISTED", waitDays = 30))).isEqualTo(Ok(Waitlisted(Duration.ofDays(30))))
        assertThat(parse(reply("WAITLISTED"))).isInstanceOf(Rejected::class.java)
        assertThat(parse(reply("WAITLISTED", waitDays = 0))).isInstanceOf(Rejected::class.java)
    }

    @Test
    fun `parse rejects an unknown or missing status`() {
        assertThat(parse(reply("PENDING"))).isInstanceOf(Rejected::class.java)
        assertThat(parse(reply())).isInstanceOf(Rejected::class.java)
    }

    // ---- an operation, kept apart from the data ----

    @Test
    fun `screenMessage has one message per outcome and never says what is wrong with an account`() {
        assertThat(screenMessage(Ready(PickupCode("K7P2QX"), 12))).isEqualTo("Your book is waiting on hold shelf 12.")
        assertThat(screenMessage(Unavailable(Reason.NOT_IN_CATALOGUE))).isEqualTo("We don't have this title. Ask us to order it.")
        assertThat(screenMessage(Unavailable(Reason.ACCOUNT_BLOCKED))).isEqualTo("Please ask at the desk.")
        assertThat(screenMessage(Unavailable(Reason.LOST))).isEqualTo("This title is not available right now.")
        assertThat(screenMessage(Waitlisted(Duration.ofDays(30)))).isEqualTo("You're on the waiting list. Expected wait: 30 days.")
    }
}
