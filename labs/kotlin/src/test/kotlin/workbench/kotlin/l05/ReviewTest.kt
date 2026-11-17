package workbench.kotlin.l05

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.catchThrowable
import org.junit.jupiter.api.Test

class ReviewTest {

    private val lines = mutableListOf<String>()
    private val logbook = Logbook { lines += it }
    private val ok = JobRequest(250, "a4", "flyer.pdf")

    @Test
    fun `ensure returns normally and never builds the message when the condition holds`() {
        var built = 0
        Callers.ensuring(true, "NEVER") { built++; "unused" }
        assertThat(built).isEqualTo(0)
    }

    @Test
    fun `ensure throws JobRejected with the code and message, building the message once`() {
        var built = 0
        val thrown = catchThrowable { Callers.ensuring(false, "TOO_MANY") { built++; "too many copies" } }
        assertThat(thrown).isInstanceOf(JobRejected::class.java).hasMessage("too many copies")
        assertThat((thrown as JobRejected).code).isEqualTo("TOO_MANY")
        assertThat(built).isEqualTo(1)
    }

    @Test
    fun `review accepts a job within the limit and writes one line with the shift name`() {
        val decision = context(logbook, Shift("early")) { ok.review(maxCopies = 1_000) }
        assertThat(decision).isEqualTo(Decision.Accepted)
        assertThat(lines).containsExactly("[early] accepted 250 on A4")
    }

    @Test
    fun `review rejects a job over the limit and writes why`() {
        val decision = context(logbook, Shift("late")) { ok.copy(copies = 5_000).review(1_000) }
        assertThat(decision).isEqualTo(Decision.Rejected("TOO_MANY"))
        assertThat(lines).containsExactly("[late] rejected TOO_MANY: copies 5000 is over the limit 1000")
    }

    @Test
    fun `review checks the rules in order and reports the first one that fails`() {
        context(logbook, Shift("night")) {
            assertThat(ok.copy(copies = 0).review(1_000)).isEqualTo(Decision.Rejected("COPIES_INVALID"))
            assertThat(ok.copy(paper = null).review(1_000)).isEqualTo(Decision.Rejected("PAPER_MISSING"))
            assertThat(ok.copy(file = "flyer.docx").review(1_000)).isEqualTo(Decision.Rejected("FILE_MISSING"))
            assertThat(ok.copy(paper = null, file = null).review(1_000)).isEqualTo(Decision.Rejected("PAPER_MISSING"))
        }
        assertThat(lines).hasSize(4).allMatch { it.startsWith("[night] rejected ") }
    }

    @Test
    fun `implicit receivers from with() also satisfy context parameters`() {
        val decision = with(logbook) { with(Shift("weekend")) { ok.review(1_000) } }
        assertThat(decision).isEqualTo(Decision.Accepted)
        assertThat(lines).containsExactly("[weekend] accepted 250 on A4")
    }
}
