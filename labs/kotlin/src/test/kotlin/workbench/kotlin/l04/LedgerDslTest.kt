package workbench.kotlin.l04

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

class LedgerDslTest {

    private fun payout() = journalEntry("payout-981") {
        memo = "merchant payout"
        debit("merchant:981", 12_000)
        credit("bank:clearing", 11_850)
        credit("revenue:fees", 150)
    }

    @Test
    fun `journalEntry builds a balanced entry with the postings in order`() {
        val e = payout()
        assertThat(e.id).isEqualTo("payout-981")
        assertThat(e.memo).isEqualTo("merchant payout")
        assertThat(e.postings).containsExactly(
            Posting("merchant:981", Side.DEBIT, 12_000),
            Posting("bank:clearing", Side.CREDIT, 11_850),
            Posting("revenue:fees", Side.CREDIT, 150),
        )
    }

    @Test
    fun `an unbalanced entry is rejected with both totals in the message`() {
        assertThatThrownBy {
            journalEntry("refund-7") {
                debit("revenue:sales", 5_000)
                credit("customer:42", 4_900)
            }
        }.isInstanceOf(IllegalArgumentException::class.java)
            .hasMessageContaining("refund-7")
            .hasMessageContaining("5000")
            .hasMessageContaining("4900")
    }

    @Test
    fun `non-positive amounts and single-posting entries are rejected`() {
        assertThatThrownBy { journalEntry("x") { debit("a", 0); credit("b", 0) } }
            .isInstanceOf(IllegalArgumentException::class.java)
        assertThatThrownBy { journalEntry("x") { debit("a", -100); credit("b", -100) } }
            .isInstanceOf(IllegalArgumentException::class.java)
        assertThatThrownBy { journalEntry("x") { memo = "empty" } }
            .isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `batch collects entries in order and rejects a duplicate entry id`() {
        val b = batch("batch-17") {
            entry("payout-981") { debit("merchant:981", 100); credit("bank:clearing", 100) }
            entry("payout-982") { debit("merchant:982", 250); credit("bank:clearing", 250) }
        }
        assertThat(b.entries.map { it.id }).containsExactly("payout-981", "payout-982")

        assertThatThrownBy {
            batch("batch-18") {
                entry("payout-1") { debit("a", 1); credit("b", 1) }
                entry("payout-1") { debit("a", 1); credit("b", 1) }
            }
        }.isInstanceOf(IllegalArgumentException::class.java).hasMessageContaining("payout-1")

        assertThatThrownBy { batch("batch-19") { } }.isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `a built entry keeps its own copy of the postings`() {
        val builder = EntryBuilder("e-1")
        builder.debit("merchant:981", 100)
        builder.credit("bank:clearing", 100)
        val first = builder.build()
        builder.debit("merchant:981", 50)              // the builder carries on...
        builder.credit("bank:clearing", 50)
        assertThat(first.postings).hasSize(2)         // ...but the entry already built must not change
        assertThat(builder.build().postings).hasSize(4)
    }

    @Test
    fun `both builders carry the LedgerDsl marker`() {
        for (builder in listOf(EntryBuilder::class.java, BatchBuilder::class.java)) {
            assertThat(builder.isAnnotationPresent(LedgerDsl::class.java)).`as`(builder.simpleName).isTrue()
        }
    }
}
