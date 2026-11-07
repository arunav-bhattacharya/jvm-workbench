package workbench.coroutines.l08

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.runningFold
import kotlinx.coroutines.flow.stateIn

fun liveCapturedTotal(captures: Flow<Long>, scope: CoroutineScope): StateFlow<Long> =
    captures
        .runningFold(0L) { total, cents -> total + cents }
        // one shared upstream collection, started by the first subscriber and stopped
        // 5 s after the last one leaves (a reload within 5 s keeps it running)
        .stateIn(scope, SharingStarted.WhileSubscribed(stopTimeoutMillis = 5_000), 0L)
