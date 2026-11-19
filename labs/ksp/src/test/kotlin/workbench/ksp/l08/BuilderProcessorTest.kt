package workbench.ksp.l08

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.fail
import org.junit.jupiter.api.Test
import java.io.File

// The four checks every processor test makes, written with your bench, on the given builder processor.
// The golden files live in src/test/resources/workbench/ksp/l08/golden/. To accept a change on purpose:
//   UPDATE_GOLDEN=true ./gradlew :ksp:test --tests 'workbench.ksp.l08.*'      then read the diff before you keep it
class BuilderProcessorTest {

    private val bench = ProcessorBench(KctforkCompiler)
    private val goldenDir = File("src/test/resources/workbench/ksp/l08/golden")

    private val lamp = Source(
        "Lamp.kt",
        """
        package movemate

        import workbench.ksp.annotations.Builder

        @Builder
        data class Lamp(val name: String, val bulbs: Int, val shade: String?)
        """,
    )

    @Test
    fun `LampBuilder compiles, matches its golden file, and builds a Lamp`() {
        val run = bench.run(lamp, processors = listOf(BuilderProcessorProvider()))

        // 1. the exit code
        assertThat(run.exitCode).isEqualTo("OK")
        // 2. the generated text, against the stored golden file
        assertMatchesGolden(run.generated("movemate/LampBuilder.kt"), goldenDir.resolve("LampBuilder.kt.golden"))
        // 3. the messages: none at all, not even a warning
        assertThat(run.messages).isEmpty()
        // 4. call the generated code, including the null that shade(shade: String?) must accept
        val builder = run.newInstance("movemate.LampBuilder")
        run.call(builder, "name", "desk lamp")
        run.call(builder, "bulbs", 1)
        run.call(builder, "shade", null)
        assertThat(run.call(builder, "build").toString()).isEqualTo("Lamp(name=desk lamp, bulbs=1, shade=null)")
    }

    @Test
    fun `a builder for a generic property and a type from another package`() {
        val shelf = Source(
            "Bookshelf.kt",
            """
            package movemate

            import java.time.LocalDate
            import workbench.ksp.annotations.Builder

            @Builder
            class Bookshelf(val shelves: Int, val books: List<String>, val boughtOn: LocalDate?)
            """,
        )

        val run = bench.run(shelf, processors = listOf(BuilderProcessorProvider()))

        assertThat(run.exitCode).isEqualTo("OK")
        assertMatchesGolden(run.generated("movemate/BookshelfBuilder.kt"), goldenDir.resolve("BookshelfBuilder.kt.golden"))
        val builder = run.newInstance("movemate.BookshelfBuilder")
        run.call(builder, "shelves", 3)
        run.call(builder, "books", listOf("Dune", "Emma"))
        val built = run.call(builder, "build")!!
        assertThat(run.call(built, "getBooks")).isEqualTo(listOf("Dune", "Emma"))
        assertThat(run.call(built, "getBoughtOn")).isNull()
    }

    @Test
    fun `every bad class is reported in one build, on its own file and line`() {
        val bad = Source(
            "Bad.kt",
            """
            package movemate

            import workbench.ksp.annotations.Builder

            @Builder
            interface Shape

            @Builder
            object Van

            @Builder
            class Safe private constructor(val code: String)
            """,
        )

        val run = bench.run(bad, processors = listOf(BuilderProcessorProvider()))

        assertThat(run.exitCode).isEqualTo("COMPILATION_ERROR")
        assertThat(run.errors).contains(
            Message('e', "Bad.kt", 6, "@Builder goes on a class, but Shape is an interface"),
            Message('e', "Bad.kt", 9, "@Builder goes on a class, but Van is an object"),
            Message('e', "Bad.kt", 12, "SafeBuilder can't call Safe's private constructor. Make the constructor public or internal."),
        )
        assertThat(run.generated).isEmpty()
    }

    @Test
    fun `using the builder wrongly is a compiler error in the user's file, with a column`() {
        val use = Source(
            "Use.kt",
            """
            package movemate

            fun wrong(): Lamp =
                LampBuilder().name("desk lamp").bulbs(1)
                    .shade(2).build()
            """,
        )

        val run = bench.run(lamp, use, processors = listOf(BuilderProcessorProvider()))

        assertThat(run.exitCode).isEqualTo("COMPILATION_ERROR")
        assertThat(run.errors.map { "${it.file}:${it.line} ${it.text}" })
            .contains("Use.kt:5 Argument type mismatch: actual type is 'Int', but 'String?' was expected.")
    }
}

/** Fails with a message a person can act on: which line changed, and how to accept the change on purpose. */
fun assertMatchesGolden(actual: String, golden: File) {
    when (val result = checkGolden(actual, golden)) {
        GoldenResult.Matches -> Unit
        is GoldenResult.Written -> fail<Unit>("Wrote the golden file ${result.file}. Read it, keep it if it's right, and run the test again.")
        is GoldenResult.Differs -> fail<Unit>(
            "${golden.name} line ${result.line}:\n  expected: ${result.expected}\n  actual:   ${result.actual}\n" +
                "If the change is on purpose, run with UPDATE_GOLDEN=true and review the diff.",
        )
    }
}
