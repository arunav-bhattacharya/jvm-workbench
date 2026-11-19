package workbench.ksp.l01.demo

import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import com.tschuchort.compiletesting.kspSourcesDir
import java.io.File
import java.io.OutputStream
import workbench.ksp.l01.ReadyMadeInventoryProcessorProvider

// The third way, in memory: compile the new Lamp (with watts) together with the ready-made card processor,
// print the card file the processor wrote, then call it. Nobody writes a card, so nobody can forget one.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l01.demo.GeneratedCardDemoKt
fun main() {
    val lamp = SourceFile.kotlin(
        "Lamp.kt",
        """
        package movemate

        import workbench.ksp.annotations.Inventory

        @Inventory
        data class Lamp(val name: String, val bulbs: Int, val shade: String?, val watts: Int)

        fun deskLampCard() = Lamp("desk lamp", 1, null, 40).inventoryCard()
        """,
    )
    val compilation = KotlinCompilation().apply {
        workingDir = File("build/kctfork/demo").apply { deleteRecursively() }
        sources = listOf(lamp)
        inheritClassPath = true
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream()
        configureKsp { symbolProcessorProviders += ReadyMadeInventoryProcessorProvider() }
    }
    val result = compilation.compile()
    println("exit code: ${result.exitCode}")

    val generated = compilation.kspSourcesDir.resolve("kotlin")
    generated.walk().filter { it.isFile }.forEach { file ->
        println("--- ${file.relativeTo(generated).invariantSeparatorsPath}")
        print(file.readText())
    }
    val card = result.classLoader.loadClass("movemate.LampKt").getMethod("deskLampCard").invoke(null)
    println("--- deskLampCard() returns: $card")
}
