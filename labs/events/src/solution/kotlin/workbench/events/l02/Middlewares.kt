package workbench.events.l02

import java.util.concurrent.ConcurrentHashMap

/**
 * Drops an event equal to one it has already passed on, such as a Kafka redelivery of the same
 * capture. Data classes compare by value, so "equal" means same type, id and amount.
 * It remembers every event forever; a production version needs a bound (see lesson 3).
 */
class DropDuplicates : Middleware {
    private val seen: MutableSet<PaymentEvent> = ConcurrentHashMap.newKeySet()

    override fun intercept(event: PaymentEvent, next: Next): Int =
        if (seen.add(event)) next.proceed(event) else 0     // add is the check and the act in one step
}
