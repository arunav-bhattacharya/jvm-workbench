package workbench.injector.app.l03

import workbench.injector.annotations.Inject
import workbench.injector.annotations.Named
import workbench.injector.annotations.Singleton
import workbench.injector.app.l03.maps.Route

@Singleton
class MovingDay @Inject constructor(
    val crew: Crew,
    @Named("back roads") val familyRoute: Route,
) {
    fun plan(): List<String> = listOf(
        "${crew.truck.driver.name} drives truck ${crew.truck.plate} on the ${crew.truck.driver.route.name}",
        "the family takes the ${familyRoute.name}",
        crew.kitchenPacker.pack("kitchen"),
        crew.kitchenPacker.pack("pantry"),
        crew.bedroomPacker.pack("bedroom"),
    )
}
