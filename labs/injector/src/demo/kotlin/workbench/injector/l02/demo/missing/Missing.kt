package workbench.injector.l02.demo.missing

import workbench.injector.annotations.Component
import workbench.injector.annotations.Inject

class Route @Inject constructor()
class Driver(val route: Route)                          // forgot @Inject
class Truck @Inject constructor(val driver: Driver)
class Crew @Inject constructor(val truck: Truck)
class MovingDay @Inject constructor(val crew: Crew)

@Component
interface MissingPlan {
    fun movingDay(): MovingDay
}
