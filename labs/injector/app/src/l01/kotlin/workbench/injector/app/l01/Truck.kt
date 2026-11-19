package workbench.injector.app.l01

import workbench.injector.annotations.Inject
import workbench.injector.annotations.Singleton

/** One truck for the whole day, and it needs a driver. */
@Singleton
class Truck @Inject constructor(val driver: Driver) {
    val plate: String = "MOVE-1"
}
