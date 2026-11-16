package workbench.flows.l03

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.channelFlow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch

// Reference answer. Same names and signatures as src/main.

fun interface LineReader {
    fun readLine(): String?
}

data class Settlement(val paymentId: String, val amountCents: Long, val currency: String)

fun parseSettlement(line: String): Settlement {
    val (id, cents, currency) = line.split(",")
    return Settlement(id, cents.toLong(), currency)
}

fun interface Ledger {
    suspend fun post(settlement: Settlement)
}

fun importSettlements(reader: LineReader, ledger: Ledger, io: CoroutineDispatcher): Flow<Settlement> =
    flow {
        while (true) {
            val line = reader.readLine() ?: break
            emit(line)
        }
    }
        .map { parseSettlement(it) }
        .flowOn(io)                        // the wall: everything above runs on io, in a second coroutine
        .onEach { ledger.post(it) }        // below the wall: the collector's context

fun bothAcquirers(north: Flow<Authorization>, east: Flow<Authorization>): Flow<Authorization> = channelFlow {
    // two cooks, one mailbox: send is safe from any coroutine started in here
    launch { north.collect { send(it) } }
    launch { east.collect { send(it) } }
    // the block returns now; the flow completes when both children have finished
}

data class Authorization(val acquirer: String, val paymentId: String)
