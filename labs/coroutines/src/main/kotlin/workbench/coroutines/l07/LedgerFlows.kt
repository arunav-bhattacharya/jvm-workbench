package workbench.coroutines.l07

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.withContext

/**
 * Every entry of [accountId], page by page, in order.
 *
 * The flow must be cold and lazy: building it calls nothing, each collection starts again from
 * the first page, and a collector that stops early (for example with take(3)) must not cause
 * more pages to be fetched than it needed.
 */
fun ledgerEntries(api: LedgerApi, accountId: String): Flow<LedgerEntry> =
    TODO("flow { } that asks for pages until nextCursor is null, emitting each entry")

/**
 * The records of a settlement file, parsed with [parseRecord].
 *
 * [LineReader.readLine] blocks, so the reading must run on [io]. The collector must stay on
 * its own dispatcher.
 *
 * Bug: emit() inside withContext breaks the flow's context rule, and the flow throws
 * IllegalStateException ("Flow invariant is violated").
 */
fun settlementRecords(reader: LineReader, io: CoroutineDispatcher): Flow<SettlementRecord> = flow {
    withContext(io) {
        while (true) {
            val line = reader.readLine() ?: break
            emit(parseRecord(line))
        }
    }
}

/**
 * Imports settlement records: each one becomes ImportEvent.Imported(paymentId).
 *
 * - If [records] fails (a truncated file, a parse error), emit ImportEvent.Aborted(<message>)
 *   and complete normally.
 * - An exception thrown by whoever collects the result is THEIR failure: it must reach them
 *   unchanged, never as an Aborted event.
 * - Call [onDone] exactly once when the flow ends: with null after a normal end, with the
 *   exception when the records failed, the collector failed or the collector stopped early.
 *
 * Bug: the try/catch around collect also catches exceptions that come from downstream
 * (thrown out of emit), which breaks exception transparency. And onDone is skipped on failure.
 */
fun importReport(records: Flow<SettlementRecord>, onDone: (cause: Throwable?) -> Unit): Flow<ImportEvent> = flow {
    try {
        records.collect { emit(ImportEvent.Imported(it.paymentId)) }
    } catch (e: Exception) {
        emit(ImportEvent.Aborted(e.message ?: e.toString()))
    }
    onDone(null)
}
