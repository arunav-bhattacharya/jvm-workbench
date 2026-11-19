package workbench.injector.app.l03

import workbench.injector.annotations.Inject
import workbench.injector.annotations.Named
import workbench.injector.annotations.Singleton
import workbench.injector.app.l03.maps.Route

/** The truck driver takes the highway. */
@Singleton
class Driver @Inject constructor(@Named("highway") val route: Route) {
    val name: String = "Sam"
}
