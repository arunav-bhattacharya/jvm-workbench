package workbench.flows.l04

import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.buffer

/**
 * Shows EVERY reading, in order. The thermometer may run ahead of a slow [show], so the
 * thermometer's waits and the screen's drawing overlap.
 * With a reading every 100 ms and 300 ms to draw one, three readings take 1000 ms, not 1200.
 */
fun everyReading(readings: Flow<Reading>, show: suspend (Reading) -> Shown): Flow<Shown> =
    TODO("let the thermometer run ahead into a buffer, then show")

/**
 * Shows the NEWEST reading: while [show] is busy, readings that arrive meanwhile are
 * skipped except the latest. Every drawing that starts is finished.
 * Three readings at 100 ms with 300 ms per drawing: readings 1 and 3, done at 700 ms.
 * A screen faster than the thermometer shows every reading.
 */
fun latestReading(readings: Flow<Reading>, show: suspend (Reading) -> Shown): Flow<Shown> =
    TODO("keep only the newest reading while the screen is busy")

/**
 * A new reading CANCELS the drawing in progress, so only the newest reading is shown in the end.
 * Three readings at 100 ms with 300 ms per drawing: only reading 3, done at 600 ms.
 */
fun cancelStale(readings: Flow<Reading>, show: suspend (Reading) -> Shown): Flow<Shown> =
    TODO("cancel the stale drawing when a new reading arrives")

/**
 * Lets the cook run ahead of a slow diner, so cooking and eating overlap.
 *
 * Rules: a plate must NEVER be dropped (a dropped plate is a guest with no dinner), and the cook may
 * run at most 64 plates ahead (64 waiting on the shelf, plus the one in the diner's hands), so memory
 * stays bounded.
 *
 * Bug: a helper wrote this to "keep the latest 64 if the table falls behind".
 */
fun towardsTable(plates: Flow<Plate>): Flow<Plate> =
    plates.buffer(onBufferOverflow = BufferOverflow.DROP_OLDEST)
