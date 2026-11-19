package workbench.injector.app.l01

import workbench.injector.annotations.Inject
import workbench.injector.annotations.Singleton

/** The whole day: the crew and the route. */
@Singleton
class MovingDay @Inject constructor(val crew: Crew, val route: Route) {
    fun plan(): List<String> = listOf(
        "${crew.truck.driver.name} drives truck ${crew.truck.plate} on the ${route.name} (${route.minutes} min)",
        "kitchen packer uses tape roll #${crew.kitchenPacker.tape.number}",
        "bedroom packer uses tape roll #${crew.bedroomPacker.tape.number}",
    )
}
