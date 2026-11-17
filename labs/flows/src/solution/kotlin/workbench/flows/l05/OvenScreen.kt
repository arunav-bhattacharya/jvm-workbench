package workbench.flows.l05

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine

fun ovenGaps(readings: Flow<Int>, dial: Flow<Int>): Flow<OvenGap> =
    // combine keeps a slate with the latest value of each flow. It emits once both lines are filled,
    // then once per update. zip would pair the n-th reading with the n-th turn of the dial instead.
    combine(readings, dial) { celsius, setting -> OvenGap(celsius, setting, setting - celsius) }
