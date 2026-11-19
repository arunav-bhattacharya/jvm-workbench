package workbench.ksp.l03.demo

import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import com.tschuchort.compiletesting.kspSourcesDir
import java.io.File
import java.io.OutputStream
import workbench.ksp.l03.LabelProcessorProvider

// The whole @Label processor on two MoveMate classes, in memory: what KSP said, the label files it wrote, and
// one label read back through the result's class loader. Reference processor by default; -Pmine=l03 for yours.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l03.demo.LabelDemoKt
fun main() {
    val moveMate = SourceFile.kotlin(
        "MoveMate.kt",
        """
        package movemate

        import workbench.ksp.annotations.Label
        import workbench.ksp.annotations.Room
        import workbench.ksp.annotations.l03.Care
        import workbench.ksp.annotations.l03.Handling

        @Label
        data class Lamp(val name: String, val bulbs: Int, val shade: String?)

        @Label @Room("study") @Handling(care = Care.UPRIGHT, packWith = Lamp::class)
        class Bookshelf(val shelves: Int, val books: List<String>)
        """,
    )
    val compilation = KotlinCompilation().apply {
        workingDir = File("build/kctfork/demo").apply { deleteRecursively() }
        sources = listOf(moveMate)
        inheritClassPath = true
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream()
        configureKsp { symbolProcessorProviders += LabelProcessorProvider() }
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
        val handling = result.classLoader.loadClass("movemate.BookshelfLabel").getField("HANDLING").get(null)
        println("--- BookshelfLabel.HANDLING is: $handling")
    }
}
