package workbench.injector.l03

import com.tschuchort.compiletesting.SourceFile

// The moving-day crew from cap5-03: the truck's GPS is expensive, so the truck asks for Lazy<GpsUnit>; a packer
// asks for () -> TapeRoll, a new roll for every room. Line 1 of each file is `package movemate`.
object MoveMateSources {
    val route = Src(
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
    val driver = Src(
        "Driver.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject
        import workbench.injector.annotations.Singleton

        @Singleton
        class Driver @Inject constructor(val route: Route)
        """,
    )
    val gpsUnit = Src(
        "GpsUnit.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject
        import workbench.injector.annotations.Singleton

        @Singleton
        class GpsUnit @Inject constructor() {
            init {
                switchedOn++
            }

            fun directionsTo(place: String): String = "turn left at the bakery for " + place

            companion object {
                var switchedOn: Int = 0
            }
        }
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
            private val gps: Lazy<GpsUnit>,
        ) {
            fun directions(): String = gps.value.directionsTo("the new house")
        }
        """,
    )
    val tapeRoll = Src(
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
    val packer = Src(
        "Packer.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject

        class Packer @Inject constructor(private val newTape: () -> TapeRoll) {
            fun pack(room: String): String = room + ": tape roll #" + newTape().number
        }
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
        import workbench.injector.annotations.Singleton

        @Singleton
        class MovingDay @Inject constructor(val crew: Crew, val route: Route)
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
            fun truck(): Truck
        }
        """,
    )

    val all = listOf(route, driver, gpsUnit, truck, tapeRoll, packer, crew, movingDay, component)

    fun files(): Array<SourceFile> = all.map { it.file }.toTypedArray()

    /** The crew with some files swapped (matched by file name). */
    fun with(vararg replacements: Src): Array<SourceFile> {
        val names = replacements.map { it.name }.toSet()
        return (all.filter { it.name !in names } + replacements).map { it.file }.toTypedArray()
    }
}

/** A source file that remembers its name (kctfork's SourceFile keeps it private). */
class Src(val name: String, text: String) {
    val file: SourceFile = SourceFile.kotlin(name, text)
}
