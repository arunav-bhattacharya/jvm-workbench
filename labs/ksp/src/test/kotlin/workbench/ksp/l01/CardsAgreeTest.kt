package workbench.ksp.l01

import com.tschuchort.compiletesting.KotlinCompilation.ExitCode
import com.tschuchort.compiletesting.SourceFile
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import workbench.ksp.compileWithKsp

// The third way: let a processor write the cards during the build. These tests compile MoveMate's classes in
// memory with the ready-made processor from ReadyMadeProcessor.kt and call the cards it generated.
class CardsAgreeTest {

    private val moveMate = SourceFile.kotlin(
        "MoveMate.kt",
        """
        package movemate

        import workbench.ksp.annotations.Inventory

        @Inventory
        data class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)

        @Inventory
        data class Lamp(val name: String, val bulbs: Int, val shade: String?)

        @Inventory
        class Bookshelf(val shelves: Int, val books: List<String>)

        @Inventory
        data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)
        """,
    )

    // calls the generated cards, so the test can call these functions through the result's class loader
    private val samples = SourceFile.kotlin(
        "Samples.kt",
        """
        package movemate

        fun boxCard() = Box("kitchen 1", "kitchen", 5200, fragile = true).inventoryCard()
        fun lampCard() = Lamp("desk lamp", 1, null).inventoryCard()
        fun bookshelfCard() = Bookshelf(3, listOf("atlas", "cookbook")).inventoryCard()
        fun plantCard() = Plant("fern", 2.5).inventoryCard()
        """,
    )

    @Test
    fun `the generated, hand-written and reflection cards agree`() {
        val run = compileWithKsp(moveMate, samples, processors = listOf(ReadyMadeInventoryProcessorProvider()))

        assertThat(run.exitCode).isEqualTo(ExitCode.OK)
        assertThat(run.generated("movemate/LampInventoryCard.kt")).contains(
            "fun Lamp.inventoryCard(): String =",
            "\"Lamp: name=\$name, bulbs=\$bulbs, shade=\$shade\"",
        )
        fun generated(function: String) = run.callTopLevel("movemate.SamplesKt", function)
        assertThat(generated("boxCard")).isEqualTo(box.inventoryCard()).isEqualTo(reflectionCard(box))
        assertThat(generated("lampCard")).isEqualTo(lamp.inventoryCard()).isEqualTo(reflectionCard(lamp))
        assertThat(generated("bookshelfCard")).isEqualTo(bookshelf.inventoryCard()).isEqualTo(reflectionCard(bookshelf))
        assertThat(generated("plantCard")).isEqualTo(plant.inventoryCard()).isEqualTo(reflectionCard(plant))
    }

    @Test
    fun `the generated card follows the label when Lamp gains a property`() {
        val newLamp = SourceFile.kotlin(
            "Lamp.kt",
            """
            package movemate

            import workbench.ksp.annotations.Inventory

            @Inventory
            data class Lamp(val name: String, val bulbs: Int, val shade: String?, val watts: Int)

            fun lampCard() = Lamp("desk lamp", 1, null, 40).inventoryCard()
            """,
        )

        val run = compileWithKsp(newLamp, processors = listOf(ReadyMadeInventoryProcessorProvider()))

        assertThat(run.exitCode).isEqualTo(ExitCode.OK)
        assertThat(run.callTopLevel("movemate.LampKt", "lampCard"))
            .isEqualTo("Lamp: name=desk lamp, bulbs=1, shade=null, watts=40")
    }
}
