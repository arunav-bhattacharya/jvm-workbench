package workbench.injector.app.l02

import workbench.injector.annotations.Inject
import workbench.injector.annotations.Named
import workbench.injector.annotations.Singleton
import workbench.injector.app.l02.maps.Route

/** The truck driver takes the highway. */
@Singleton
class Driver @Inject constructor(
    @Named("highway") val route: Route,
    // val truck: Truck,      // Try it: uncomment this line, and the driver waits for the truck that waits for him
) {
    val name: String = "Sam"
}
