package workbench.injector.l02.demo.twice

import workbench.injector.annotations.Component
import workbench.injector.annotations.Inject
import workbench.injector.annotations.Module
import workbench.injector.annotations.Provides

class Route(val name: String)                           // from a maps library: no @Inject possible

@Module
object RouteModule {
    @Provides fun highway(): Route = Route("highway")
    @Provides fun backRoads(): Route = Route("back roads")
}

class Driver @Inject constructor(val route: Route)      // meant the highway
class Truck @Inject constructor(val driver: Driver)
class Crew @Inject constructor(val truck: Truck)
class MovingDay @Inject constructor(val crew: Crew)

@Component
interface TwicePlan {
    fun movingDay(): MovingDay
}
