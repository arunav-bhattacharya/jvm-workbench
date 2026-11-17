package workbench.events.l02

import java.util.concurrent.ConcurrentHashMap

/**
 * Drops an event equal to one it has already passed on, such as the same scan sent twice by a
 * rider's scanner. Data classes compare by value, so "equal" means same type, id and weight.
 * It remembers every event forever; a production version needs a bound (see lesson 3).
 */
class DropDuplicates : Middleware {
    private val seen: MutableSet<ParcelEvent> = ConcurrentHashMap.newKeySet()

    /**
     * TODO 6: pass a new event on and return what next returns; return 0 for one seen before.
     * Eight threads may publish the same event at once: the check and the act must be one step.
     */
    override fun intercept(event: ParcelEvent, next: Next): Int = TODO("pass on each distinct event once")
}
