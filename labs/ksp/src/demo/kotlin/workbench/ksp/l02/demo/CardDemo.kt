package workbench.ksp.l02.demo

import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import com.tschuchort.compiletesting.kspSourcesDir
import java.io.File
import java.io.OutputStream
import workbench.ksp.l02.InventoryProcessorProvider

// Rung 3: the whole @Inventory processor on two MoveMate classes, in memory. Prints what KSP said, every file the
// processor wrote, and the result of calling one generated card. Reference processor by default; -Pmine=l02 for yours.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l02.demo.CardDemoKt
fun main() {
    val moveMate = SourceFile.kotlin(
        "MoveMate.kt",
        """
        package movemate

        import workbench.ksp.annotations.Inventory

        @Inventory
        data class Lamp(val name: String, val bulbs: Int, val shade: String?)

        @Inventory
        data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)

        fun lampCard() = Lamp("desk lamp", 1, null).inventoryCard()
        """,
    )
    val compilation = KotlinCompilation().apply {
        workingDir = File("build/kctfork/demo").apply { deleteRecursively() }
        sources = listOf(moveMate)
        inheritClassPath = true
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream()
        configureKsp { symbolProcessorProviders += InventoryProcessorProvider() }
    }
    val result = compilation.compile()
    println("exit code: ${result.exitCode}")
    result.messages.lines().filter { "[ksp]" in it }.forEach(::println)

    val generated = compilation.kspSourcesDir.resolve("kotlin")
    generated.walk().filter { it.isFile }.sorted().forEach { file ->
        println("--- ${file.relativeTo(generated).invariantSeparatorsPath}")
        print(file.readText())
    }
    if (result.exitCode == KotlinCompilation.ExitCode.OK) {
        val card = result.classLoader.loadClass("movemate.MoveMateKt").getMethod("lampCard").invoke(null)
        println("--- lampCard() returns: $card")
    }
}
