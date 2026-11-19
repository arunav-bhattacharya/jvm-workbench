package workbench.injector.app.l02

import workbench.injector.annotations.Module
import workbench.injector.annotations.Named
import workbench.injector.annotations.Provides
import workbench.injector.annotations.Singleton
import workbench.injector.app.l02.maps.Route

/** Two routes of the same type, told apart by name. */
@Module
object RouteModule {
    @Provides @Singleton @Named("highway")
    fun highway(): Route = Route("highway", 42)

    @Provides @Singleton @Named("back roads")
    fun backRoads(): Route = Route("back roads", 51)
}
