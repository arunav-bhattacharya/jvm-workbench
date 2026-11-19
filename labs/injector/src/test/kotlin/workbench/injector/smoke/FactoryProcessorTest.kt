package workbench.injector.smoke

import com.tschuchort.compiletesting.KotlinCompilation.ExitCode
import com.tschuchort.compiletesting.SourceFile
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import workbench.injector.compileWithKsp

// Smoke example (keep or delete).
class FactoryProcessorTest {

    @Test
    fun `generates a factory object that builds the class`() {
        val route = SourceFile.kotlin(
            "Route.kt",
            """
            package movemate

            import workbench.injector.annotations.smoke.Factory

            @Factory
            class Route
            """,
        )

        val run = compileWithKsp(route, processors = listOf(FactoryProcessorProvider()))

        assertThat(run.exitCode).isEqualTo(ExitCode.OK)
        assertThat(run.generated("movemate/RouteFactory.kt")).contains(
            "public object RouteFactory {",
            "  public fun create(): Route = Route()",
        )
        val created = run.callOnObject("movemate.RouteFactory", "create")
        assertThat(created).isInstanceOf(run.loadClass("movemate.Route"))
    }

    @Test
    fun `reports an error on the constructor parameter it cannot supply`() {
        val truck = SourceFile.kotlin(
            "Truck.kt",
            """
            package movemate

            import workbench.injector.annotations.smoke.Factory

            @Factory
            class Truck(
                val driver: String,
            )
            """,
        )

        val run = compileWithKsp(truck, processors = listOf(FactoryProcessorProvider()))

        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        // line 7 is `val driver: String,`: the error points at the parameter, not at the class
        assertThat(run.messages).containsPattern(
            """e: \[ksp] \S*/Truck\.kt:7: Truck needs a driver, and the smoke factory only builds classes whose constructor takes no parameters""",
        )
        assertThat(run.generated).isEmpty()
    }
}
