package workbench.injector.l01

import com.tschuchort.compiletesting.SourceFile

// The moving-day crew from cap5-01, as small source files the tests compile in memory.
// SourceFile.kotlin trims the indent, so line 1 of each file is `package movemate`.
object MoveMateSources {
    val route = SourceFile.kotlin(
        "Route.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject
        import workbench.injector.annotations.Singleton

        @Singleton
        class Route @Inject constructor() {
            val name: String = "highway"
        }
        """,
    )
    val driver = SourceFile.kotlin(
        "Driver.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject
        import workbench.injector.annotations.Singleton

        @Singleton
        class Driver @Inject constructor(val route: Route)
        """,
    )
    val truck = SourceFile.kotlin(
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
    val tapeRoll = SourceFile.kotlin(
        "TapeRoll.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject

        class TapeRoll @Inject constructor() {
            val number: Int = ++made

            companion object {
                var made: Int = 0
            }
        }
        """,
    )
    val packer = SourceFile.kotlin(
        "Packer.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject

        @Inject
        class Packer(val tape: TapeRoll)
        """,
    )
    val crew = SourceFile.kotlin(
        "Crew.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject
        import workbench.injector.annotations.Singleton

        @Singleton
        class Crew @Inject constructor(val truck: Truck, val kitchenPacker: Packer, val bedroomPacker: Packer)
        """,
    )
    val movingDay = SourceFile.kotlin(
        "MovingDay.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject
        import workbench.injector.annotations.Singleton

        @Singleton
        class MovingDay @Inject constructor(val crew: Crew, val route: Route)
        """,
    )
    val component = SourceFile.kotlin(
        "MovingDayComponent.kt",
        """
        package movemate

        import workbench.injector.annotations.Component

        @Component
        interface MovingDayComponent {
            fun movingDay(): MovingDay
            fun truck(): Truck
        }
        """,
    )

    /** The whole crew, the way lesson 1 wires it. */
    val all = arrayOf(route, driver, truck, tapeRoll, packer, crew, movingDay, component)
}
