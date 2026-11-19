package workbench.injector.app.l01

import workbench.injector.annotations.Inject
import workbench.injector.annotations.Singleton

/** The driver needs the route before the day can start. */
@Singleton
class Driver @Inject constructor(val route: Route) {
    val name: String = "Sam"
}
