package workbench.flows.l05

import kotlinx.coroutines.flow.Flow

/**
 * What the oven-door screen shows: every thermometer reading against the LATEST dial setting.
 *
 * - Nothing is shown until there is both a reading and a dial setting.
 * - After that, a new reading or a turn of the dial each produce one OvenGap right away.
 * - toGo = dial - celsius: how many degrees the oven still has to climb.
 */
fun ovenGaps(readings: Flow<Int>, dial: Flow<Int>): Flow<OvenGap> =
    TODO("pair each update with the latest value of the other flow")
