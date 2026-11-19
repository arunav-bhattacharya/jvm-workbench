package workbench.injector.app.l01

import workbench.injector.annotations.Inject
import workbench.injector.annotations.Singleton

/** The way to the new house. One for the whole day. */
@Singleton
class Route @Inject constructor() {
    val name: String = "highway"
    val minutes: Int = 42
}
