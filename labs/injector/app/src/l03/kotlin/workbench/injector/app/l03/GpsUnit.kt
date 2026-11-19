package workbench.injector.app.l03

import workbench.injector.annotations.Inject
import workbench.injector.annotations.Singleton

/** Slow to switch on: it has to find the satellites first. The truck asks for it lazily. */
@Singleton
class GpsUnit @Inject constructor() {
    init {
        Thread.sleep(300)      // a teaching delay that stands in for finding the satellites
        switchedOn++
    }

    fun directionsTo(place: String): String = "GPS: turn left at the bakery for $place"

    companion object {
        var switchedOn: Int = 0
            private set
    }
}
