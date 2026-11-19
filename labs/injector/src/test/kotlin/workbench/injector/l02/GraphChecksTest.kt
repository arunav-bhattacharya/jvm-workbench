package workbench.injector.l02

import com.tschuchort.compiletesting.KotlinCompilation.ExitCode
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import workbench.injector.compileWithKsp
import workbench.injector.l02.MoveMateSources.kotlin

class GraphChecksTest {

    private val both = listOf(FactoryProcessorProvider(), ComponentProcessorProvider())

    // The mistakes, one file each. Line numbers in the comments count from `package movemate` (line 1).

    /** Driver forgot its @Inject, so nobody provides Driver; Truck.kt line 8 asks for one. */
    private val driverWithoutInject = kotlin(
        "Driver.kt",
        """
        package movemate

        import workbench.injector.annotations.Named

        class Driver(
            @Named("highway") val route: Route,
        )
        """,
    )

    /** The driver waits for the truck (line 10), and the truck waits for the driver. */
    private val driverWaitsForTruck = kotlin(
        "Driver.kt",
        """
        package movemate

        import workbench.injector.annotations.Inject
        import workbench.injector.annotations.Named
        import workbench.injector.annotations.Singleton

        @Singleton
        class Driver @Inject constructor(
            @Named("highway") val route: Route,
            val truck: Truck,
        )
        """,
    )

    /** Two routes and no names to tell them apart (lines 10 and 13), and a driver who asks for "a Route". */
    private val twoPlainRoutes = kotlin(
        "RouteModule.kt",
        """
        package movemate

        import workbench.injector.annotations.Module
        import workbench.injector.annotations.Provides
        import workbench.injector.annotations.Singleton

        @Module
        object RouteModule {
            @Provides @Singleton
            fun highway(): Route = Route("highway", 42)

            @Provides @Singleton
            fun backRoads(): Route = Route("back roads", 51)
        }
        """,
    )

    @Test
    fun `a missing binding names the whole path, on the parameter that asks for it`() {
        val run = compileWithKsp(*MoveMateSources.with(driverWithoutInject), processors = both)

        // Truck.kt line 8 is `val driver: Driver,`
        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        assertThat(run.messages).containsPattern(
            """e: \[ksp] \S*/Truck\.kt:8: MovingDay needs Crew needs Truck needs Driver: nobody provides Driver\. """ +
                """Add @Inject to its constructor, or a @Provides function in a @Module\.""",
        )
        assertThat(run.generated).doesNotContainKey("movemate/GeneratedMovingDayComponent.kt")
    }

    @Test
    fun `a misspelt qualifier is a missing binding too`() {
        val typo = kotlin(
            "Driver.kt",
            """
            package movemate

            import workbench.injector.annotations.Inject
            import workbench.injector.annotations.Named

            class Driver @Inject constructor(
                @Named("hihgway") val route: Route,
            )
            """,
        )

        val run = compileWithKsp(*MoveMateSources.with(typo), processors = both)

        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        assertThat(run.messages).containsPattern(
            """e: \[ksp] \S*/Driver\.kt:7: MovingDay needs Crew needs Truck needs Driver needs @Named\("hihgway"\) Route: """ +
                """nobody provides @Named\("hihgway"\) Route\. Add a @Provides function with @Named\("hihgway"\) to a @Module\.""",
        )
    }

    @Test
    fun `a cycle is reported with its path, on the parameter that closes it`() {
        val run = compileWithKsp(*MoveMateSources.with(driverWaitsForTruck), processors = both)

        // Driver.kt line 10 is `val truck: Truck,`
        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        assertThat(run.messages).containsPattern(
            """e: \[ksp] \S*/Driver\.kt:10: Dependency cycle: Truck needs Driver needs Truck\. """ +
                """Nothing in a cycle can be built first: change one of these constructors\.""",
        )
    }

    @Test
    fun `two bindings for one type are an error on the second one`() {
        val plainDriver = kotlin(
            "Driver.kt",
            """
            package movemate

            import workbench.injector.annotations.Inject

            class Driver @Inject constructor(val route: Route)
            """,
        )
        val plainDay = kotlin(
            "MovingDay.kt",
            """
            package movemate

            import workbench.injector.annotations.Inject

            class MovingDay @Inject constructor(val crew: Crew)
            """,
        )

        val run = compileWithKsp(*MoveMateSources.with(twoPlainRoutes, plainDriver, plainDay), processors = both)

        // RouteModule.kt line 13 is `fun backRoads(): Route = ...`, the second binding
        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        assertThat(run.messages).containsPattern(
            """e: \[ksp] \S*/RouteModule\.kt:13: Route is provided twice: by RouteModule\.highway\(\) and by RouteModule\.backRoads\(\)\. """ +
                """Give each one its own @Named qualifier and ask for the one you mean\.""",
        )
    }

    @Test
    fun `an @Inject class that a module provides as well is provided twice`() {
        val injectRoute = kotlin(
            "Route.kt",
            """
            package movemate

            import workbench.injector.annotations.Inject

            class Route @Inject constructor() {
                val name: String = "highway"
            }
            """,
        )
        val alsoProvided = kotlin(
            "RouteModule.kt",
            """
            package movemate

            import workbench.injector.annotations.Module
            import workbench.injector.annotations.Provides

            @Module
            object RouteModule {
                @Provides
                fun route(): Route = Route()
            }
            """,
        )
        val plainDriver = kotlin(
            "Driver.kt",
            """
            package movemate

            import workbench.injector.annotations.Inject

            class Driver @Inject constructor(val route: Route)
            """,
        )
        val plainDay = kotlin(
            "MovingDay.kt",
            """
            package movemate

            import workbench.injector.annotations.Inject

            class MovingDay @Inject constructor(val crew: Crew)
            """,
        )

        val run = compileWithKsp(*MoveMateSources.with(injectRoute, alsoProvided, plainDriver, plainDay), processors = both)

        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        assertThat(run.messages).containsPattern(
            """e: \[ksp] \S*/RouteModule\.kt:9: Route is provided twice: by Route's @Inject constructor and by RouteModule\.route\(\)\.""",
        )
    }

    @Test
    fun `every problem is reported in one build`() {
        val day = kotlin(
            "MovingDay.kt",
            """
            package movemate

            import workbench.injector.annotations.Inject

            class MovingDay @Inject constructor(val crew: Crew, val route: Route)
            """,
        )
        val truckWithoutDriver = kotlin(
            "Truck.kt",
            """
            package movemate

            import workbench.injector.annotations.Inject

            class Truck @Inject constructor(val driver: Driver, val ramp: LoadingRamp)

            class LoadingRamp
            """,
        )

        val driver = kotlin(
            "Driver.kt",
            """
            package movemate

            import workbench.injector.annotations.Inject

            class Driver @Inject constructor(
                val route: Route,
                val truck: Truck,
            )
            """,
        )

        val run = compileWithKsp(*MoveMateSources.with(twoPlainRoutes, driver, truckWithoutDriver, day), processors = both)

        // three different mistakes, three errors, one build: the duplicate, the cycle, the missing ramp
        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        val errors = run.messages.lines().filter { it.startsWith("e: [ksp]") }
        assertThat(errors).hasSize(3)
        assertThat(errors).anyMatch { it.contains("RouteModule.kt:13: Route is provided twice") }
        assertThat(errors).anyMatch { it.contains("Driver.kt:7: Dependency cycle: Truck needs Driver needs Truck.") }
        assertThat(errors).anyMatch { it.contains("Truck.kt:5: MovingDay needs Crew needs Truck needs LoadingRamp: nobody provides LoadingRamp.") }
    }

    @Test
    fun `@Named and @Module give the driver the highway and the family the back roads`() {
        val check = kotlin(
            "Check.kt",
            """
            package movemate

            fun check(): String {
                val day = GeneratedMovingDayComponent().movingDay()
                return "driver: " + day.crew.truck.driver.route.name + ", family: " + day.familyRoute.name
            }
            """,
        )

        val run = compileWithKsp(*MoveMateSources.files(), check.file, processors = both)

        assertThat(run.exitCode).withFailMessage(run.messages).isEqualTo(ExitCode.OK)
        assertThat(run.generated("movemate/GeneratedMovingDayComponent.kt")).contains(
            "private val highwayRoute: Route = RouteModule.highway()",
            "private val driver: Driver = DriverFactory.create(highwayRoute)",
            "private val backRoadsRoute: Route = RouteModule.backRoads()",
            "private val movingDay: MovingDay = MovingDayFactory.create(crew, backRoadsRoute)",
        )
        assertThat(run.callTopLevel("movemate.CheckKt", "check")).isEqualTo("driver: highway, family: back roads")
    }

    @Test
    fun `a module must be an object`() {
        val classModule = kotlin(
            "RouteModule.kt",
            """
            package movemate

            import workbench.injector.annotations.Module
            import workbench.injector.annotations.Named
            import workbench.injector.annotations.Provides

            @Module
            class RouteModule {
                @Provides @Named("highway")
                fun highway(): Route = Route("highway", 42)
            }
            """,
        )

        val run = compileWithKsp(*MoveMateSources.with(classModule), processors = both)

        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        assertThat(run.messages).containsPattern(
            """e: \[ksp] \S*/RouteModule\.kt:8: @Module goes on an object, so the component can call its functions, but RouteModule is not an object""",
        )
    }
}
