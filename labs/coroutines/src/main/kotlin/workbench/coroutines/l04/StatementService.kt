package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineDispatcher

/**
 * Builds a monthly statement PDF.
 *
 * Callers run on a small request pool. This version does all the work on the caller's thread:
 * the blocking JDBC call and the CPU-heavy render both hold a request thread.
 *
 * Move the blocking [BlockingStatementStore.loadRows] call to [io] and the
 * [StatementRenderer.render] call to [cpu]. The caller must get the result back on its own dispatcher.
 */
class StatementService(
    private val store: BlockingStatementStore,
    private val renderer: StatementRenderer,
    private val io: CoroutineDispatcher,
    private val cpu: CoroutineDispatcher,
) {
    suspend fun statementPdf(accountId: String): ByteArray {
        val rows = store.loadRows(accountId)
        return renderer.render(rows)
    }
}
