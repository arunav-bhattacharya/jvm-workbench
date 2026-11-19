package workbench.injector.app.l02

import workbench.injector.annotations.Inject
import workbench.injector.annotations.Named
import workbench.injector.annotations.Singleton
import workbench.injector.app.l02.maps.Route

/** The family drives their own car on the back roads, while the truck takes the highway. */
@Singleton
class MovingDay @Inject constructor(
    val crew: Crew,
    @Named("back roads") val familyRoute: Route,
) {
    fun plan(): List<String> = listOf(
        "${crew.truck.driver.name} drives truck ${crew.truck.plate} on the ${crew.truck.driver.route.name} (${crew.truck.driver.route.minutes} min)",
        "the family takes the ${familyRoute.name} (${familyRoute.minutes} min)",
        "packers use tape rolls #${crew.kitchenPacker.tape.number} and #${crew.bedroomPacker.tape.number}",
    )
}
