package workbench.events.l02

import java.util.concurrent.ConcurrentHashMap

/**
 * Drops an event equal to one it has already passed on, such as the same scan sent twice by a
 * rider's scanner. Data classes compare by value, so "equal" means same type, id and weight.
 * It remembers every event forever; a production version needs a bound (see lesson 3).
 */
class DropDuplicates : Middleware {
    private val seen: MutableSet<ParcelEvent> = ConcurrentHashMap.newKeySet()

    override fun intercept(event: ParcelEvent, next: Next): Int =
        if (seen.add(event)) next.proceed(event) else 0     // add is the check and the act in one step
}
