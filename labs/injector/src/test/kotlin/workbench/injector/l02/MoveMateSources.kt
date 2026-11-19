package workbench.injector.l02

import com.tschuchort.compiletesting.SourceFile

// The moving-day crew from cap5-02: Route now comes from a maps library nobody can put @Inject on, so a
// @Module provides two of them, told apart by @Named. Line 1 of each file is `package movemate`.
object MoveMateSources {
    /** Pretend this is a library class: you can't edit it. */
    val route = Src(
        "Route.kt",
        """
        package movemate

        class Route(val name: String, val minutes: Int)
        """,
    )
    val routeModule = Src(
        "RouteModule.kt",
        """
        package movemate

        import workbench.injector.annotations.Module
        import workbench.injector.annotations.Named
        import workbench.injector.annotations.Provides
        import workbench.injector.annotations.Singleton

        @Module
        object RouteModule {
            @Provides @Singleton @Named("highway")
            fun highway(): Route = Route("highway", 42)

            @Provides @Singleton @Named("back roads")
            fun backRoads(): Route = Route("back roads", 51)
        }
        """,
    )
    val driver = Src(
        "Driver.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject
        import workbench.injector.annotations.Named
        import workbench.injector.annotations.Singleton

        @Singleton
        class Driver @Inject constructor(
            @Named("highway") val route: Route,
        )
        """,
    )
    val truck = Src(
        "Truck.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject
        import workbench.injector.annotations.Singleton

        @Singleton
        class Truck @Inject constructor(
            val driver: Driver,
        )
        """,
    )
    val tapeRoll = Src(
        "TapeRoll.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject

        class TapeRoll @Inject constructor()
        """,
    )
    val packer = Src(
        "Packer.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject

        class Packer @Inject constructor(val tape: TapeRoll)
        """,
    )
    val crew = Src(
        "Crew.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject
        import workbench.injector.annotations.Singleton

        @Singleton
        class Crew @Inject constructor(val truck: Truck, val kitchenPacker: Packer, val bedroomPacker: Packer)
        """,
    )
    val movingDay = Src(
        "MovingDay.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject
        import workbench.injector.annotations.Named
        import workbench.injector.annotations.Singleton

        @Singleton
        class MovingDay @Inject constructor(
            val crew: Crew,
            @Named("back roads") val familyRoute: Route,
        )
        """,
    )
    val component = Src(
        "MovingDayComponent.kt",
        """
        package movemate

        import workbench.injector.annotations.Component

        @Component
        interface MovingDayComponent {
            fun movingDay(): MovingDay
        }
        """,
    )

    val all = listOf(route, routeModule, driver, truck, tapeRoll, packer, crew, movingDay, component)

    /** The crew as kctfork source files. */
    fun files(): Array<SourceFile> = all.map { it.file }.toTypedArray()

    /** The crew with some files swapped for broken ones (matched by file name). */
    fun with(vararg replacements: Src): Array<SourceFile> {
        val names = replacements.map { it.name }.toSet()
        return (all.filter { it.name !in names } + replacements).map { it.file }.toTypedArray()
    }

    fun kotlin(name: String, text: String) = Src(name, text)
}

/** A source file that remembers its name (kctfork's SourceFile keeps it private). */
class Src(val name: String, text: String) {
    val file: SourceFile = SourceFile.kotlin(name, text)
}
