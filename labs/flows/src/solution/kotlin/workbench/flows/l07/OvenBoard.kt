package workbench.flows.l07

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.retry
import kotlinx.coroutines.flow.stateIn
import java.io.IOException

fun hallBoard(feed: Flow<Reading>, scope: CoroutineScope): StateFlow<Reading?> =
    feed
        // above stateIn: a failure restarts the feed instead of killing the sharing coroutine,
        // and the StateFlow keeps its last value while the retry waits
        .retry { e -> (e is IOException).also { retrying -> if (retrying) delay(1_000) } }
        // Eagerly: reading .value is not a subscription, so Lazily or WhileSubscribed never start
        .stateIn(scope, SharingStarted.Eagerly, null)

fun screenFeed(feed: Flow<Reading>, scope: CoroutineScope): StateFlow<Reading?> =
    feed.stateIn(
        scope,
        SharingStarted.WhileSubscribed(
            stopTimeoutMillis = 5_000,     // a screen back on within 5 s cancels the pending stop
            replayExpirationMillis = 0,    // on stop, reset to the initial null: no stale reading later
        ),
        null,
    )
