package workbench.flows.l03

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch

/** The acquirer's settlement file. readLine() BLOCKS the thread, and returns null at the end. */
fun interface LineReader {
    fun readLine(): String?
}

data class Settlement(val paymentId: String, val amountCents: Long, val currency: String)

/** Given: parses "pay-1,4250,EUR". */
fun parseSettlement(line: String): Settlement {
    val (id, cents, currency) = line.split(",")
    return Settlement(id, cents.toLong(), currency)
}

/** The ledger client. It is not thread-safe: call it only from the import job's own coroutine context. */
fun interface Ledger {
    suspend fun post(settlement: Settlement)
}

/**
 * Reads every line with [reader], parses it, posts it to [ledger], and emits each settlement once it is posted.
 *
 * readLine() blocks, so reading and parsing must run on [io]. Posting must stay in the collector's
 * context, because the ledger client is not thread-safe. The collector stays where it is too.
 *
 * Bug: the flowOn sits at the end of the chain, so it moves the postings onto io as well.
 */
fun importSettlements(reader: LineReader, ledger: Ledger, io: CoroutineDispatcher): Flow<Settlement> =
    flow {
        while (true) {
            val line = reader.readLine() ?: break
            emit(line)
        }
    }
        .map { parseSettlement(it) }
        .onEach { ledger.post(it) }
        .flowOn(io)

data class Authorization(val acquirer: String, val paymentId: String)

/**
 * Every authorization from both acquirer feeds, in the order they arrive. Each feed's own order is
 * kept, and the flow completes when both feeds have completed.
 *
 * Bug: flow { } refuses emits from launched coroutines. Run the tests and read the message.
 */
fun bothAcquirers(north: Flow<Authorization>, east: Flow<Authorization>): Flow<Authorization> = flow {
    coroutineScope {
        launch { north.collect { emit(it) } }
        launch { east.collect { emit(it) } }
    }
}
