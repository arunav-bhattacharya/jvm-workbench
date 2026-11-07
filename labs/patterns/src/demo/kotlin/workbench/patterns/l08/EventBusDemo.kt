package workbench.patterns.l08

import java.util.concurrent.CopyOnWriteArrayList

// A hand-rolled Observer: subscribe returns a handle, and one bad listener can't starve the rest.

class EventBus<E> {
    private val listeners = CopyOnWriteArrayList<(E) -> Unit>()

    fun subscribe(listener: (E) -> Unit): AutoCloseable {
        listeners += listener
        return AutoCloseable { listeners -= listener }            // the handle that prevents leaks
    }

    fun publish(event: E) {
        for (l in listeners) {
            try {
                l(event)
            } catch (e: RuntimeException) {                       // isolate each listener
                println("  (a listener failed: ${e.message})")
            }
        }
    }
}

data class PostedEvent(val account: String, val amountMinor: Long)

fun main() {
    val bus = EventBus<PostedEvent>()
    bus.subscribe { println("ledger view got  $it") }
    bus.subscribe { throw IllegalStateException("analytics dashboard is down") }
    val email = bus.subscribe { println("email sender got $it") }

    bus.publish(PostedEvent("acc-1", 450))
    email.close()                                                 // unsubscribe
    bus.publish(PostedEvent("acc-1", 900))
}
