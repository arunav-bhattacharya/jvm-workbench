package workbench.kotlin.l04

/** Marks the receivers of the ledger DSL. Inside an inner block, the outer builders are no longer implicit. */
@DslMarker
@Target(AnnotationTarget.CLASS, AnnotationTarget.TYPE)
annotation class LedgerDsl

enum class Side { DEBIT, CREDIT }

data class Posting(val account: String, val side: Side, val amountMinor: Long)

data class JournalEntry(val id: String, val memo: String, val postings: List<Posting>)

data class Batch(val id: String, val entries: List<JournalEntry>)

/** Builds one double-entry journal entry. */
@LedgerDsl
class EntryBuilder(private val id: String) {
    var memo: String = ""
    private val postings = mutableListOf<Posting>()

    fun debit(account: String, amountMinor: Long) = post(account, Side.DEBIT, amountMinor)

    fun credit(account: String, amountMinor: Long) = post(account, Side.CREDIT, amountMinor)

    private fun post(account: String, side: Side, amountMinor: Long) {
        // fail at the line that is wrong, not later in build()
        require(amountMinor > 0) { "amount must be positive, was $amountMinor on $account" }
        postings += Posting(account, side, amountMinor)
    }

    /** The one place that sees the whole entry, so it checks the rules that span postings. */
    fun build(): JournalEntry {
        require(postings.size >= 2) { "entry $id needs at least two postings" }
        val debits = postings.filter { it.side == Side.DEBIT }.sumOf { it.amountMinor }
        val credits = postings.filter { it.side == Side.CREDIT }.sumOf { it.amountMinor }
        require(debits == credits) { "unbalanced entry $id: debits $debits, credits $credits" }
        return JournalEntry(id, memo, postings.toList())   // copy: the builder can't change it later
    }
}

/** Builds a batch of entries that are posted together. */
@LedgerDsl
class BatchBuilder(private val id: String) {
    private val entries = mutableListOf<JournalEntry>()

    fun entry(id: String, block: EntryBuilder.() -> Unit) {
        require(entries.none { it.id == id }) { "duplicate entry id $id in batch ${this.id}" }
        entries += EntryBuilder(id).apply(block).build()
    }

    fun build(): Batch {
        require(entries.isNotEmpty()) { "batch $id has no entries" }
        return Batch(id, entries.toList())
    }
}

/** Entry point: runs [block] with a fresh EntryBuilder as `this`, then validates. */
fun journalEntry(id: String, block: EntryBuilder.() -> Unit): JournalEntry =
    EntryBuilder(id).apply(block).build()

fun batch(id: String, block: BatchBuilder.() -> Unit): Batch =
    BatchBuilder(id).apply(block).build()
