package workbench.ksp.l04.demo

import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import com.tschuchort.compiletesting.kspSourcesDir
import java.io.File
import java.io.OutputStream
import workbench.ksp.l04.BuilderProcessorProvider

// Lesson 4, Try it: the same five classes as TemplateBuilderDemo, now with the KotlinPoet builder processor.
// Prints each generated file, then calls every builder. Uses the reference processor; add -Pmine=l04 for yours.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l04.demo.PoetBuilderDemoKt
fun main() {
    val moveMate = SourceFile.kotlin(
        "MoveMate.kt",
        """
        package movemate

        import workbench.ksp.annotations.Builder

        data class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)

        @Builder
        data class Lamp(val name: String, val bulbs: Int, val shade: String?)

        @Builder
        class Shelf(val boxes: List<Box?>?)

        class Kitchen {
            @Builder
            data class Drawer(val label: String)
        }

        @Builder
        class Crate(val `in`: String)
        """,
    )
    val van = SourceFile.kotlin(
        "Load.kt",
        """
        package movemate.van

        import movemate.Box
        import workbench.ksp.annotations.Builder

        @Builder
        class Load(val first: Box)
        """,
    )
    val use = SourceFile.kotlin(
        "Use.kt",
        """
        package movemate

        import movemate.van.LoadBuilder

        fun useEveryBuilder(): List<String> = listOf(
            LampBuilder().name("desk lamp").bulbs(1).shade(null).build().toString(),
            LoadBuilder().first(Box("plates", "kitchen", 4200)).build().first.label,
            ShelfBuilder().boxes(listOf(null, Box("cups", "kitchen", 900))).build().boxes.toString(),
            KitchenDrawerBuilder().label("spoons").build().toString(),
            CrateBuilder().`in`("hall").build().`in`,
        )
        """,
    )
    val compilation = KotlinCompilation().apply {
        workingDir = File("build/kctfork/demo/l04-poet").apply { deleteRecursively() }
        sources = listOf(moveMate, van, use)
        inheritClassPath = true
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream()
        configureKsp { symbolProcessorProviders += BuilderProcessorProvider() }
    }
    val result = compilation.compile()
    println("exit code: ${result.exitCode}")

    val generated = compilation.kspSourcesDir.resolve("kotlin")
    generated.walk().filter { it.isFile }.sortedBy { it.name }.forEach { file ->
        println("--- ${file.relativeTo(generated).invariantSeparatorsPath}")
        print(file.readText())
    }
    if (result.exitCode != KotlinCompilation.ExitCode.OK) {
        println(result.messages)
        return
    }
    val built = result.classLoader.loadClass("movemate.UseKt").getMethod("useEveryBuilder").invoke(null)
    println("--- every builder, called:")
    (built as List<*>).forEach { println("  $it") }
}
