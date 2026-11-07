package workbench.coroutines.l07

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.onCompletion

fun ledgerEntries(api: LedgerApi, accountId: String): Flow<LedgerEntry> = flow {
    // the body runs once per collector, and only when it collects: cold and lazy
    var cursor: String? = null
    do {
        val page = api.page(accountId, cursor)
        for (entry in page.entries) emit(entry) // emit suspends until the collector is done with it,
        cursor = page.nextCursor               // so take(3) cancels us before the next page is fetched
    } while (cursor != null)
}

fun settlementRecords(reader: LineReader, io: CoroutineDispatcher): Flow<SettlementRecord> =
    flow {
        while (true) {
            val line = reader.readLine() ?: break
            emit(parseRecord(line))
        }
    }.flowOn(io) // moves everything ABOVE this line to io; the collector stays where it is

fun importReport(records: Flow<SettlementRecord>, onDone: (cause: Throwable?) -> Unit): Flow<ImportEvent> =
    records
        .map<SettlementRecord, ImportEvent> { ImportEvent.Imported(it.paymentId) }
        // onCompletion is the flow's finally: it sees normal ends (null), upstream and downstream
        // failures, and cancellation. Placed before catch, it sees the original error.
        .onCompletion { cause -> onDone(cause) }
        // catch only sees exceptions from ABOVE it, so the collector's own failures pass through
        .catch { e -> emit(ImportEvent.Aborted(e.message ?: e.toString())) }
