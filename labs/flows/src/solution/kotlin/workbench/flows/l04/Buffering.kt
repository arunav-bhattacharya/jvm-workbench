package workbench.flows.l04

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.conflate
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.mapLatest

fun everyReading(readings: Flow<Reading>, show: suspend (Reading) -> Shown): Flow<Shown> =
    readings.buffer()                 // the thermometer runs in its own coroutine, 64 spots ahead
        .map { show(it) }             // drawing runs in the collector's coroutine, below the buffer

fun latestReading(readings: Flow<Reading>, show: suspend (Reading) -> Shown): Flow<Shown> =
    readings.conflate()               // a shelf with one spot: a new reading replaces the waiting one
        .map { show(it) }             // a drawing that has started always finishes

@OptIn(ExperimentalCoroutinesApi::class) // mapLatest is experimental in 1.11.0
fun cancelStale(readings: Flow<Reading>, show: suspend (Reading) -> Shown): Flow<Shown> =
    readings.mapLatest { show(it) }   // a new reading cancels the block in progress, waits for it, starts again

fun towardsTable(plates: Flow<Plate>): Flow<Plate> =
    plates.buffer(64)                 // SUSPEND (the default policy): a full shelf makes the cook wait.
                                      // buffer(onBufferOverflow = DROP_OLDEST) is a ONE-spot buffer that drops
