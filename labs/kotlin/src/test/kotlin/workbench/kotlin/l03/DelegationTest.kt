package workbench.kotlin.l03

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

class DelegationTest {

    @Test
    fun `recorded properties return their value and log only real changes, in order`() {
        val job = PrintJob(ChangeLog())
        assertThat(job.status).isEqualTo("NEW")
        job.status = "QUEUED"
        job.status = "QUEUED"                // same value: not a change
        job.copies = 250
        job.note = "staple top left"
        job.status = "PRINTED"
        assertThat(job.status).isEqualTo("PRINTED")
        assertThat(job.copies).isEqualTo(250)
        assertThat(job.log.changes).containsExactly(
            Change("status", "NEW", "QUEUED"),
            Change("copies", 1, 250),
            Change("note", null, "staple top left"),
            Change("status", "QUEUED", "PRINTED"),
        )
    }

    @Test
    fun `provideDelegate registers every property while the object is built, before any access`() {
        val log = ChangeLog()
        PrintJob(log)
        assertThat(log.tracked).containsExactly("status", "copies", "note")
        assertThat(log.changes).isEmpty()
        // and the compiler kept what provideDelegate returned in a hidden field
        assertThat(PrintJob::class.java.getDeclaredField("status\$delegate").type).isEqualTo(Recorded::class.java)
    }

    @Test
    fun `a log refuses to track the same property name twice`() {
        val shared = ChangeLog()
        PrintJob(shared)
        assertThatThrownBy { PrintJob(shared) }
            .isInstanceOf(IllegalStateException::class.java)
            .hasMessageContaining("status")
    }

    @Test
    fun `paperSize ignores values that are not A0 to A6`() {
        val job = PrintJob(ChangeLog())
        assertThat(job.paperSize).isEqualTo("A4")
        job.paperSize = "a3"
        assertThat(job.paperSize).isEqualTo("A4")
        job.paperSize = "A44"
        assertThat(job.paperSize).isEqualTo("A4")
        job.paperSize = "B5"
        assertThat(job.paperSize).isEqualTo("A4")
        job.paperSize = "A3"
        assertThat(job.paperSize).isEqualTo("A3")
    }

    @Test
    fun `PrinterProfile reads from the map, and a missing key fails on access`() {
        val ok = PrinterProfile(mapOf("name" to "Laser 7", "dailyPageLimit" to 5_000L))
        assertThat(ok.name).isEqualTo("Laser 7")
        assertThat(ok.dailyPageLimit).isEqualTo(5_000L)

        val partial = PrinterProfile(mapOf("name" to "Laser 8"))   // building it is fine
        assertThat(partial.name).isEqualTo("Laser 8")
        assertThatThrownBy { partial.dailyPageLimit }
            .isInstanceOf(NoSuchElementException::class.java)
            .hasMessageContaining("dailyPageLimit")
    }
}
