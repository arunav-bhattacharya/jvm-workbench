package workbench.coroutines.l07

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.withContext

/**
 * Every item in [aisle] of the grocer's shop, page by page, in order.
 *
 * The flow must be cold and lazy: building it calls nothing, each collection starts again from
 * the first page, and a collector that stops early (for example with take(3)) must not cause
 * more pages to be fetched than it needed.
 */
fun aisleItems(shop: GroceryShop, aisle: String): Flow<Item> =
    TODO("flow { } that asks for pages until nextCursor is null, emitting each item")

/**
 * The lines of a delivery note, parsed with [parseLine].
 *
 * [LineReader.readLine] blocks, so the reading must run on [io]. The collector must stay on
 * its own dispatcher.
 *
 * Bug: emit() inside withContext breaks the flow's context rule, and the flow throws
 * IllegalStateException ("Flow invariant is violated").
 */
fun deliveryLines(reader: LineReader, io: CoroutineDispatcher): Flow<DeliveryLine> = flow {
    withContext(io) {
        while (true) {
            val line = reader.readLine() ?: break
            emit(parseLine(line))
        }
    }
}

/**
 * Puts a delivery away: each line becomes StockEvent.Stocked(item).
 *
 * - If [lines] fails (a torn note, a line that doesn't parse), emit StockEvent.Aborted(<message>)
 *   and complete normally.
 * - An exception thrown by whoever collects the result is THEIR failure: it must reach them
 *   unchanged, never as an Aborted event.
 * - Call [onDone] exactly once when the flow ends: with null after a normal end, with the
 *   exception when the lines failed, the collector failed or the collector stopped early.
 *
 * Bug: the try/catch around collect also catches exceptions that come from downstream
 * (thrown out of emit), which breaks exception transparency. And onDone is skipped on failure.
 */
fun stockReport(lines: Flow<DeliveryLine>, onDone: (cause: Throwable?) -> Unit): Flow<StockEvent> = flow {
    try {
        lines.collect { emit(StockEvent.Stocked(it.item)) }
    } catch (e: Exception) {
        emit(StockEvent.Aborted(e.message ?: e.toString()))
    }
    onDone(null)
}
