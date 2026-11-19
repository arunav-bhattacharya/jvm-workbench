package workbench.injector.app.l03

import workbench.injector.annotations.Inject
import workbench.injector.annotations.Singleton

/** The truck switches its GPS on the first time someone asks for directions, not before. */
@Singleton
class Truck @Inject constructor(
    val driver: Driver,
    private val gps: Lazy<GpsUnit>,
) {
    val plate: String = "MOVE-1"

    fun directions(): String = gps.value.directionsTo("the new house")
}
