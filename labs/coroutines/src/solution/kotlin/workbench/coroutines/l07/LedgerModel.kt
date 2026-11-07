package workbench.coroutines.l07

// Shared model. This file is the same in src/main and src/solution.

data class LedgerEntry(val id: String, val amountCents: Long)

data class LedgerPage(val entries: List<LedgerEntry>, val nextCursor: String?)

/** The ledger service's paged API. The first page has cursor null; the last page has nextCursor null. */
fun interface LedgerApi {
    suspend fun page(accountId: String, cursor: String?): LedgerPage
}

/** A legacy reader for the acquirer's settlement file. readLine() BLOCKS, and returns null at the end. */
fun interface LineReader {
    fun readLine(): String?
}

data class SettlementRecord(val paymentId: String, val amountCents: Long, val currency: String)

/** Parses "pay-1,4250,EUR". */
fun parseRecord(line: String): SettlementRecord {
    val (id, amount, currency) = line.split(",")
    return SettlementRecord(id, amount.toLong(), currency)
}

sealed interface ImportEvent {
    data class Imported(val paymentId: String) : ImportEvent
    data class Aborted(val reason: String) : ImportEvent
}
