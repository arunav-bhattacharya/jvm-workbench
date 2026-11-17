package workbench.flows.l03

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch

/** The grocer's delivery note, one item per line. readLine() BLOCKS the thread, and returns null at the end. */
fun interface LineReader {
    fun readLine(): String?
}

/** One line of the delivery note, such as "flour,2000,g". */
data class DeliveryLine(val item: String, val amount: Long, val unit: String)

/** Given: parses "flour,2000,g". */
fun parseDeliveryLine(line: String): DeliveryLine {
    val (item, amount, unit) = line.split(",")
    return DeliveryLine(item, amount.toLong(), unit)
}

/** The pantry. Storing an item also writes it in the pantry book, which is not thread-safe: call it only from the collector's own context. */
fun interface Pantry {
    suspend fun store(line: DeliveryLine)
}

/**
 * Reads every line with [reader], parses it, stores it in [pantry], and emits each line once it is stored.
 *
 * readLine() blocks, so reading and parsing must run on [io]. Storing must stay in the collector's
 * context, because the pantry book is not thread-safe. The collector stays where it is too.
 *
 * Bug: the flowOn sits at the end of the chain, so it moves the storing onto io as well.
 */
fun importDelivery(reader: LineReader, pantry: Pantry, io: CoroutineDispatcher): Flow<DeliveryLine> =
    flow {
        while (true) {
            val line = reader.readLine() ?: break
            emit(line)
        }
    }
        .map { parseDeliveryLine(it) }
        .onEach { pantry.store(it) }
        .flowOn(io)

/** One plate from one of the cooks. */
data class Plate(val cook: String, val dish: String)

/**
 * Every plate from both cooks, in the order they are ready. Each cook's own order is
 * kept, and the flow completes when both cooks have finished.
 *
 * Bug: flow { } refuses emits from launched coroutines. Run the tests and read the message.
 */
fun bothCooks(grill: Flow<Plate>, oven: Flow<Plate>): Flow<Plate> = flow {
    coroutineScope {
        launch { grill.collect { emit(it) } }
        launch { oven.collect { emit(it) } }
    }
}
