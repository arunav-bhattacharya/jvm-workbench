package workbench.injector.l03

import com.tschuchort.compiletesting.KotlinCompilation.ExitCode
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import workbench.injector.compileWithKsp

class LazyAndProvidersTest {

    private val both = listOf(FactoryProcessorProvider(), ComponentProcessorProvider())

    private val check = Src(
        "Check.kt",
        """
        package movemate

        fun check(): String {
            val plan = GeneratedMovingDayComponent()
            val day = plan.movingDay()
            val before = GpsUnit.switchedOn
            plan.truck().directions()
            val after = GpsUnit.switchedOn
            plan.truck().directions()
            val kitchen = day.crew.kitchenPacker
            return "GPS on before: " + before + ", after: " + after + ", after two: " + GpsUnit.switchedOn + "; " +
                kitchen.pack("kitchen") + ", " + kitchen.pack("pantry")
        }
        """,
    )

    @Test
    fun `holds a lazily asked singleton in a Lazy and hands a packer a function for new tape`() {
        val run = compileWithKsp(*MoveMateSources.files(), processors = both)

        assertThat(run.exitCode).withFailMessage(run.messages).isEqualTo(ExitCode.OK)
        assertThat(run.generated("movemate/GeneratedMovingDayComponent.kt")).contains(
            "private val gpsUnit: Lazy<GpsUnit> = lazy { GpsUnitFactory.create() }",
            "private val truck: Truck = TruckFactory.create(driver, gpsUnit)",
            "private fun newPacker(): Packer = PackerFactory.create({ newTapeRoll() })",
        )
        assertThat(run.generated("movemate/TruckFactory.kt"))
            .contains("public fun create(driver: Driver, gps: Lazy<GpsUnit>): Truck = Truck(driver, gps)")
        assertThat(run.generated("movemate/PackerFactory.kt"))
            .contains("public fun create(newTape: () -> TapeRoll): Packer = Packer(newTape)")
    }

    @Test
    fun `the GPS stays off until the truck first asks for directions, and a packer gets a new roll per room`() {
        val run = compileWithKsp(*MoveMateSources.files(), check.file, processors = both)

        assertThat(run.exitCode).withFailMessage(run.messages).isEqualTo(ExitCode.OK)
        assertThat(run.callTopLevel("movemate.CheckKt", "check")).isEqualTo(
            "GPS on before: 0, after: 1, after two: 1; kitchen: tape roll #1, pantry: tape roll #2",
        )
    }

    @Test
    fun `the generated code uses no reflection`() {
        val run = compileWithKsp(*MoveMateSources.files(), processors = both)

        assertThat(run.exitCode).withFailMessage(run.messages).isEqualTo(ExitCode.OK)
        assertThat(run.generated).hasSize(9)        // eight factories and the component
        for ((path, text) in run.generated) {
            assertThat(text).withFailMessage("$path uses reflection:\n$text")
                .doesNotContain("java.lang.reflect", "kotlin.reflect", "::class", "Class.forName", "javaClass", "getDeclared")
        }
    }

    @Test
    fun `a Lazy request still has to be answered, and the error names the path`() {
        val gpsWithoutInject = Src(
            "GpsUnit.kt",
            """
            package movemate

            class GpsUnit {
                fun directionsTo(place: String): String = "turn left at the bakery for " + place
            }
            """,
        )

        val run = compileWithKsp(*MoveMateSources.with(gpsWithoutInject), processors = both)

        // Truck.kt line 9 is `private val gps: Lazy<GpsUnit>,`
        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        assertThat(run.messages).containsPattern(
            """e: \[ksp] \S*/Truck\.kt:9: MovingDay needs Crew needs Truck needs GpsUnit: nobody provides GpsUnit\.""",
        )
    }
}
