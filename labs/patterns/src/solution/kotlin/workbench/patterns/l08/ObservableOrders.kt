package workbench.patterns.l08

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import java.util.concurrent.CopyOnWriteArrayList

data class Ordered(val customer: String, val item: String, val quantity: Int)

class ObservableOrders {
    // events: a SharedFlow delivers every value, equal or not. A StateFlow here would drop the second
    // of two equal orders, because it conflates values by equals().
    private val _events = MutableSharedFlow<Ordered>()        // replay 0: emit waits for current collectors
    val events: SharedFlow<Ordered> = _events.asSharedFlow()

    // state: only the latest count matters, so StateFlow's conflation is exactly right
    private val _itemsToday = MutableStateFlow(0)
    val itemsToday: StateFlow<Int> = _itemsToday.asStateFlow()

    // CopyOnWriteArrayList: iteration works on a snapshot, so a listener can unsubscribe mid-delivery
    private val listeners = CopyOnWriteArrayList<(Ordered) -> Unit>()

    fun subscribe(listener: (Ordered) -> Unit): AutoCloseable {
        listeners += listener
        return AutoCloseable { listeners -= listener }        // the handle that prevents lapsed listeners
    }

    suspend fun place(customer: String, item: String, quantity: Int) {
        _itemsToday.update { it + quantity }                  // atomic read-modify-write
        val event = Ordered(customer, item, quantity)
        for (listener in listeners) {
            try {
                listener(event)
            } catch (e: RuntimeException) {
                // log and carry on: one broken listener must not starve the others or fail the order
            }
        }
        _events.emit(event)
    }
}
