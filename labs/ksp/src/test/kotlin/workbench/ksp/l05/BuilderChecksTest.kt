package workbench.ksp.l05

import com.tschuchort.compiletesting.KotlinCompilation.ExitCode
import com.tschuchort.compiletesting.SourceFile
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import workbench.ksp.compileWithKsp

class BuilderChecksTest {

    // Line numbers count from `package movemate` (line 1): SourceFile.kotlin trims the indent.
    private val wardrobe = SourceFile.kotlin(
        "Wardrobe.kt",
        """
        package movemate

        import workbench.ksp.annotations.Builder

        @Builder
        interface Wardrobe

        @Builder
        object Settings

        @Builder
        enum class Size { SMALL, LARGE }
        """,
    )

    private val crates = SourceFile.kotlin(
        "Crate.kt",
        """
        package movemate

        import workbench.ksp.annotations.Builder

        @Builder
        class Crate {
            constructor(label: String)
        }

        @Builder
        class Safe private constructor(val code: String)
        """,
    )

    private val good = SourceFile.kotlin(
        "Box.kt",
        """
        package movemate

        import workbench.ksp.annotations.Builder

        @Builder
        data class Box(val label: String, val room: String, val weightGrams: Int)
        """,
    )

    @Test
    fun `reports an interface, an object and an enum class, each on its own line`() {
        val run = compileWithKsp(wardrobe, processors = listOf(BuilderProcessorProvider()))

        // the messages first: what is wrong, and where (the declaration's line, not the annotation's)
        assertThat(run.messages)
            .containsPattern("""e: \[ksp] \S*/Wardrobe\.kt:6: @Builder needs a class to build, but Wardrobe is an interface\. Put @Builder on a class with a primary constructor\.""")
            .containsPattern("""e: \[ksp] \S*/Wardrobe\.kt:9: @Builder needs a class to build, but Settings is an object\.""")
            .containsPattern("""e: \[ksp] \S*/Wardrobe\.kt:12: @Builder needs a class to build, but Size is an enum class\.""")
            .doesNotContain("NullPointerException")
        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        assertThat(run.generated).isEmpty()
    }

    @Test
    fun `reports a class without a primary constructor and a private constructor`() {
        val run = compileWithKsp(crates, processors = listOf(BuilderProcessorProvider()))

        assertThat(run.messages)
            .containsPattern("""e: \[ksp] \S*/Crate\.kt:6: Crate has no primary constructor, so CrateBuilder doesn't know what to pass\. Declare the properties in one: class Crate\(val label: String\)\.""")
            .containsPattern("""e: \[ksp] \S*/Crate\.kt:11: SafeBuilder can't call Safe's constructor, because it is private\. Make it internal or public, or remove @Builder\.""")
        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        assertThat(run.generated).isEmpty()
    }

    @Test
    fun `reports every problem in one build, and still writes the builders it can`() {
        val run = compileWithKsp(wardrobe, crates, good, processors = listOf(BuilderProcessorProvider()))

        val errors = run.messages.lines().filter { it.startsWith("e: [ksp] ") && "/sources/" in it }
        assertThat(errors).hasSize(5)
        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        // logger.error doesn't stop the round: the good class still got its builder
        assertThat(run.generated.keys).containsExactly("movemate/BoxBuilder.kt")
    }

    @Test
    fun `warns on the line of a parameter with a default value, and still writes the builder`() {
        val plant = SourceFile.kotlin(
            "Plant.kt",
            """
            package movemate

            import workbench.ksp.annotations.Builder

            @Builder
            data class Plant(
                val kind: String,
                val potLitres: Double,
                val waterEveryDays: Int = 7,
            )

            fun fern() = PlantBuilder().kind("fern").potLitres(2.5).waterEveryDays(3).build().toString()
            """,
        )

        val run = compileWithKsp(plant, processors = listOf(BuilderProcessorProvider()))

        assertThat(run.messages).containsPattern(
            """w: \[ksp] \S*/Plant\.kt:9: PlantBuilder can't see the default value of waterEveryDays, so build\(\) will require it\. Set it on the builder\.""",
        )
        // a warning is not an error: the build passes and the builder works
        assertThat(run.exitCode).isEqualTo(ExitCode.OK)
        assertThat(run.callTopLevel("movemate.PlantKt", "fern")).isEqualTo("Plant(kind=fern, potLitres=2.5, waterEveryDays=3)")
    }

    @Test
    fun `sets aside a class whose type can't be resolved instead of crashing`() {
        val sticker = SourceFile.kotlin(
            "Label.kt",
            """
            package movemate

            import workbench.ksp.annotations.Builder

            @Builder
            class Parcel(val label: String, val sticker: Sticker)
            """,
        )

        val run = compileWithKsp(sticker, good, processors = listOf(BuilderProcessorProvider()))

        // no crash inside the processor (that would be INTERNAL_ERROR with KotlinPoet's "Error type" message):
        // Parcel was set aside, Box still got its builder, and the compiler reports the unknown type on the user's line
        assertThat(run.generated.keys).containsExactly("movemate/BoxBuilder.kt")
        assertThat(run.messages).doesNotContain("is not resolvable in the current round")
        assertThat(run.messages).containsPattern("""Label\.kt:6:\d+ Unresolved reference 'Sticker'""")
        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
    }
}
