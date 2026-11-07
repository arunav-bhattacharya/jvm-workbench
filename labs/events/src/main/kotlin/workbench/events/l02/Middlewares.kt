package workbench.events.l02

import java.util.concurrent.ConcurrentHashMap

/**
 * Drops an event equal to one it has already passed on, such as a Kafka redelivery of the same
 * capture. Data classes compare by value, so "equal" means same type, id and amount.
 * It remembers every event forever; a production version needs a bound (see lesson 3).
 */
class DropDuplicates : Middleware {
    private val seen: MutableSet<PaymentEvent> = ConcurrentHashMap.newKeySet()

    /**
     * TODO 6: pass a new event on and return what next returns; return 0 for one seen before.
     * Eight threads may publish the same event at once: the check and the act must be one step.
     */
    override fun intercept(event: PaymentEvent, next: Next): Int = TODO("pass on each distinct event once")
}
