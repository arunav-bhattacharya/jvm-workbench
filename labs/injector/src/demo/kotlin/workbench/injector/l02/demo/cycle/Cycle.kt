package workbench.injector.l02.demo.cycle

import workbench.injector.annotations.Component
import workbench.injector.annotations.Inject

class Route @Inject constructor()
class Driver @Inject constructor(val route: Route, val truck: Truck)    // waits for the truck
class Truck @Inject constructor(val driver: Driver)                     // which waits for the driver
class Crew @Inject constructor(val truck: Truck)
class MovingDay @Inject constructor(val crew: Crew)

@Component
interface CyclePlan {
    fun movingDay(): MovingDay
}
