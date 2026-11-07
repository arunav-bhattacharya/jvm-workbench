package workbench.kotlin.l04

/** Marks the receivers of the ledger DSL. Finished: TODO 5 puts it to use. */
@DslMarker
@Target(AnnotationTarget.CLASS, AnnotationTarget.TYPE)
annotation class LedgerDsl

enum class Side { DEBIT, CREDIT }

data class Posting(val account: String, val side: Side, val amountMinor: Long)

data class JournalEntry(val id: String, val memo: String, val postings: List<Posting>)

data class Batch(val id: String, val entries: List<JournalEntry>)

/**
 * Builds one double-entry journal entry:
 *
 *     journalEntry("payout-981") {
 *         memo = "merchant payout"
 *         debit("merchant:981", 12_000)
 *         credit("bank:clearing", 11_850)
 *         credit("revenue:fees", 150)
 *     }
 *
 * TODO 1: keep the postings in a private list, in the order they were added.
 * debit and credit reject an amount <= 0 with IllegalArgumentException, right away.
 * TODO 2: build() throws IllegalArgumentException if there are fewer than two postings, or if the
 * debits don't add up to the credits. The message for the second case is
 * "unbalanced entry <id>: debits <d>, credits <c>". It returns an entry with a copy of the postings.
 */
class EntryBuilder(private val id: String) {
    var memo: String = ""

    fun debit(account: String, amountMinor: Long): Unit = TODO("add a DEBIT posting")

    fun credit(account: String, amountMinor: Long): Unit = TODO("add a CREDIT posting")

    fun build(): JournalEntry = TODO("validate, then JournalEntry(id, memo, copy of postings)")
}

/**
 * Builds a batch of entries that are posted together.
 *
 * TODO 3: entry(id) { ... } builds one entry with a fresh EntryBuilder and keeps it. A second entry with
 * the same id throws IllegalArgumentException. build() throws IllegalArgumentException when there
 * are no entries.
 */
class BatchBuilder(private val id: String) {
    fun entry(id: String, block: EntryBuilder.() -> Unit): Unit = TODO("EntryBuilder(id).apply(block).build()")

    fun build(): Batch = TODO("Batch(id, copy of entries)")
}

/** TODO 4: run block with a fresh EntryBuilder as `this`, then build. One line. */
fun journalEntry(id: String, block: EntryBuilder.() -> Unit): JournalEntry = TODO("EntryBuilder(id).apply(block).build()")

fun batch(id: String, block: BatchBuilder.() -> Unit): Batch = TODO("BatchBuilder(id).apply(block).build()")

/*
 * TODO 5: put @LedgerDsl on both builder classes (the last test checks it). Before you do, write a
 * scratch function that calls entry("e2") { ... } inside another entry { } block. It compiles and
 * quietly adds e2 to the batch. Add the marker and read the error you get instead.
 */
