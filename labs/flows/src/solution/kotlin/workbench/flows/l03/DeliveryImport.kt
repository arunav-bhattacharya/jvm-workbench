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

data class DeliveryLine(val item: String, val amount: Long, val unit: String)

fun parseDeliveryLine(line: String): DeliveryLine {
    val (item, amount, unit) = line.split(",")
    return DeliveryLine(item, amount.toLong(), unit)
}

fun interface Pantry {
    suspend fun store(line: DeliveryLine)
}

fun importDelivery(reader: LineReader, pantry: Pantry, io: CoroutineDispatcher): Flow<DeliveryLine> =
    flow {
        while (true) {
            val line = reader.readLine() ?: break
            emit(line)
        }
    }
        .map { parseDeliveryLine(it) }
        .flowOn(io)                        // the wall: everything above runs on io, in a second coroutine
        .onEach { pantry.store(it) }       // below the wall: the collector's context

fun bothCooks(grill: Flow<Plate>, oven: Flow<Plate>): Flow<Plate> = channelFlow {
    // two cooks, one hatch: send is safe from any coroutine started in here
    launch { grill.collect { send(it) } }
    launch { oven.collect { send(it) } }
    // the block returns now; the flow completes when both children have finished
}

data class Plate(val cook: String, val dish: String)
