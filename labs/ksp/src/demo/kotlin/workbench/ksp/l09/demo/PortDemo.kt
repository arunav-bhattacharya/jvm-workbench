package workbench.ksp.l09.demo

import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import com.tschuchort.compiletesting.kspSourcesDir
import java.io.File
import java.io.OutputStream
import workbench.ksp.l09.HOUSEHOLD
import workbench.ksp.l09.PackingSlipProcessorProvider

// Runs the KSP port of the javac packing slip processor on Kotlin classes, then puts its slip next to the one
// javac wrote for the Java twins (stored in src/test/resources/workbench/ksp/l09/). Reference port by default;
// add -Pmine=l09 for yours.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l09.demo.PortDemoKt
fun main() {
    val things = SourceFile.kotlin(
        "Things.kt",
        """
        package movemate

        import workbench.ksp.annotations.Inventory
        import workbench.ksp.annotations.Room

        @Inventory @Room("hall")
        data class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)

        @Inventory @Room("living room")
        data class Lamp(val name: String, val bulbs: Int, val shade: String?)

        @Inventory @Room("study")
        class Bookshelf(val shelves: Int, val books: List<String>)

        @Inventory
        data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)
        """,
    )
    val compilation = KotlinCompilation().apply {
        workingDir = File("build/kctfork/demo/l09").apply { deleteRecursively() }
        sources = listOf(things)
        inheritClassPath = true
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream()
        configureKsp {
            symbolProcessorProviders += PackingSlipProcessorProvider()
            processorOptions += mapOf(HOUSEHOLD to "Okafor")
        }
    }
    val result = compilation.compile()
    println("exit code: ${result.exitCode}")
    result.messages.lines().filter { it.startsWith("w: [ksp]") || it.startsWith("e: [ksp]") }.forEach(::println)

    val ksp = compilation.kspSourcesDir.resolve("resources/META-INF/movemate/packing-slip.txt")
    val javac = File("src/test/resources/workbench/ksp/l09/javac-packing-slip.txt")
    println("--- KSP wrote ${ksp.relativeTo(compilation.kspSourcesDir).invariantSeparatorsPath}:")
    print(if (ksp.exists()) ksp.readText() else "(nothing yet)\n")
    println("--- javac wrote META-INF/movemate/packing-slip.txt for the Java twins:")
    print(javac.readText())
    println("--- the same, byte for byte: ${ksp.exists() && ksp.readBytes().contentEquals(javac.readBytes())}")
}
