package workbench.injector.app.l02

import workbench.injector.annotations.Inject
import workbench.injector.annotations.Singleton

@Singleton
class Truck @Inject constructor(val driver: Driver) {
    val plate: String = "MOVE-1"
}
