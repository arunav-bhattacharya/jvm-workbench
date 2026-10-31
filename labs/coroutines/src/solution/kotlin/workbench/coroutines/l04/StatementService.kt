package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext

class StatementService(
    private val store: BlockingStatementStore,
    private val renderer: StatementRenderer,
    private val io: CoroutineDispatcher,
    private val cpu: CoroutineDispatcher,
) {
    suspend fun statementPdf(accountId: String): ByteArray {
        // 1. the blocking call runs on an IO thread; the caller's thread is free meanwhile
        val rows = withContext(io) { store.loadRows(accountId) }
        // 2. CPU work runs on the CPU dispatcher; withContext then resumes us on the caller's dispatcher
        return withContext(cpu) { renderer.render(rows) }
    }
}
