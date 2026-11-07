package workbench.patterns.l08

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import java.util.concurrent.CopyOnWriteArrayList

data class Posted(val account: String, val amountMinor: Long)

class ObservableLedger {
    // events: a SharedFlow delivers every value, equal or not. A StateFlow here would drop the second
    // of two equal postings, because it conflates values by equals().
    private val _events = MutableSharedFlow<Posted>()        // replay 0: emit waits for current collectors
    val events: SharedFlow<Posted> = _events.asSharedFlow()

    // state: only the latest total matters, so StateFlow's conflation is exactly right
    private val _balance = MutableStateFlow(0L)
    val balance: StateFlow<Long> = _balance.asStateFlow()

    // CopyOnWriteArrayList: iteration works on a snapshot, so a listener can unsubscribe mid-delivery
    private val listeners = CopyOnWriteArrayList<(Posted) -> Unit>()

    fun subscribe(listener: (Posted) -> Unit): AutoCloseable {
        listeners += listener
        return AutoCloseable { listeners -= listener }        // the handle that prevents lapsed listeners
    }

    suspend fun post(account: String, amountMinor: Long) {
        _balance.update { it + amountMinor }                  // atomic read-modify-write
        val event = Posted(account, amountMinor)
        for (listener in listeners) {
            try {
                listener(event)
            } catch (e: RuntimeException) {
                // log and carry on: one broken listener must not starve the others or fail the posting
            }
        }
        _events.emit(event)
    }
}
