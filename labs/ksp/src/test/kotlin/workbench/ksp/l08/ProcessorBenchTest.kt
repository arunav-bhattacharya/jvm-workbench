package workbench.ksp.l08

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import java.io.File

// Checks the bench itself, one piece at a time. The first three need no compiler at all.
class ProcessorBenchTest {

    @Test
    fun `parseMessage splits a KSP message with a location`() {
        assertThat(parseMessage("e: [ksp] /tmp/run-7/sources/Shape.kt:6: @Builder goes on a class, but Shape is an interface"))
            .isEqualTo(Message('e', "Shape.kt", 6, "@Builder goes on a class, but Shape is an interface"))
    }

    @Test
    fun `parseMessage reads KSP lines without a location, compiler lines, and skips the rest`() {
        assertThat(parseMessage("w: [ksp] l08 not done yet: write the bench"))
            .isEqualTo(Message('w', null, null, "l08 not done yet: write the bench"))
        assertThat(parseMessage("e: file:///tmp/run-7/sources/Use.kt:5:44 Argument type mismatch: actual type is 'Int', but 'String?' was expected."))
            .isEqualTo(Message('e', "Use.kt", 5, "Argument type mismatch: actual type is 'Int', but 'String?' was expected."))
        assertThat(parseMessage("e: Error occurred in KSP, check log for detail"))
            .isEqualTo(Message('e', null, null, "Error occurred in KSP, check log for detail"))
        assertThat(parseMessage("\tat workbench.ksp.l08.BuilderProcessor.process(GivenProcessors.kt:97)")).isNull()
        assertThat(parseMessage("")).isNull()
    }

    @Test
    fun `checkGolden writes a missing file, then matches it, then reports the first changed line`(@TempDir dir: File) {
        val golden = dir.resolve("golden/LampBuilder.kt.golden")

        assertThat(checkGolden("line one\nline two\n", golden, update = false)).isEqualTo(GoldenResult.Written(golden))
        assertThat(golden.readText()).isEqualTo("line one\nline two\n")
        assertThat(checkGolden("line one\nline two\n", golden, update = false)).isEqualTo(GoldenResult.Matches)
        assertThat(checkGolden("line one\nline 2\n", golden, update = false))
            .isEqualTo(GoldenResult.Differs(2, "line two", "line 2"))
        assertThat(checkGolden("line one\n", golden, update = false))
            .isEqualTo(GoldenResult.Differs(2, "line two", ""))
        assertThat(checkGolden("line one\nline two\nline three\n", golden, update = false))
            .isEqualTo(GoldenResult.Differs(3, "", "line three"))
    }

    @Test
    fun `checkGolden with update rewrites the stored file`(@TempDir dir: File) {
        val golden = dir.resolve("Card.kt.golden").apply { writeText("old\n") }

        assertThat(checkGolden("new\n", golden, update = true)).isEqualTo(GoldenResult.Written(golden))
        assertThat(golden.readText()).isEqualTo("new\n")
    }

    @Test
    fun `run trims the indent, so an error lands on the line you count from the package line`() {
        val bench = ProcessorBench(KctforkCompiler)

        val run = bench.run(
            Source(
                "Shape.kt",
                """
                package movemate

                import workbench.ksp.annotations.Builder

                @Builder
                interface Shape
                """,
            ),
            processors = listOf(BuilderProcessorProvider()),
        )

        assertThat(run.exitCode).isEqualTo("COMPILATION_ERROR")
        assertThat(run.errors).contains(Message('e', "Shape.kt", 6, "@Builder goes on a class, but Shape is an interface"))
        assertThat(run.generated).isEmpty()
    }

    @Test
    fun `generated lists every file by path, and call reaches top-level functions, members and objects`() {
        val bench = ProcessorBench(KctforkCompiler)

        val run = bench.run(
            Source(
                "Lamp.kt",
                """
                package movemate

                import workbench.ksp.annotations.Builder
                import workbench.ksp.annotations.Inventory

                @Inventory @Builder
                data class Lamp(val name: String, val bulbs: Int, val shade: String?)

                object Van {
                    fun seats(): Int = 3
                }
                """,
            ),
            processors = listOf(InventoryProcessorProvider(), BuilderProcessorProvider()),
        )

        assertThat(run.exitCode).isEqualTo("OK")
        assertThat(run.generated.keys).containsExactly("movemate/LampBuilder.kt", "movemate/LampInventoryCard.kt")
        assertThat(run.generated("movemate/LampInventoryCard.kt")).contains("public fun Lamp.inventoryCard(): String")
        val lamp = run.newInstance("movemate.Lamp", "desk lamp", 1, null)
        assertThat(run.call("movemate.LampInventoryCardKt", "inventoryCard", lamp)).isEqualTo("Lamp: name=desk lamp, bulbs=1, shade=null")
        assertThat(run.call("movemate.Van", "seats")).isEqualTo(3)
        val builder = run.newInstance("movemate.LampBuilder")
        assertThat(run.call(builder, "name", "desk lamp")).isSameAs(builder)
        // what the generated code throws reaches the test as itself, not wrapped by reflection
        assertThatThrownBy { run.call(builder, "build") }
            .isInstanceOf(IllegalStateException::class.java)
            .hasMessage("LampBuilder needs bulbs")
    }
}
