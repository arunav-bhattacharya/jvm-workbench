package workbench.ksp.l07.demo

import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import com.tschuchort.compiletesting.kspSourcesDir
import java.io.File
import java.io.OutputStream
import workbench.ksp.l07.MasterListProcessorProvider

// Runs the master list processor twice in memory: once with the job sheet (the processor options), once
// without it. Uses the reference processor; add -Pmine=l07 for yours.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l07.demo.MasterListDemoKt
fun main() {
    val things = SourceFile.kotlin(
        "Things.kt",
        """
        package movemate

        import workbench.ksp.annotations.Inventory

        @Inventory
        data class Lamp(val name: String, val bulbs: Int, val shade: String?)

        @Inventory
        data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)
        """,
    )

    println("=== with ksp { arg(\"movemate.listName\", \"MovingDayList\") }")
    val withSheet = compile("with-options", things, mapOf("movemate.listName" to "MovingDayList"))
    println("exit code: ${withSheet.first.exitCode}")
    print(withSheet.second.resolve("movemate/MovingDayList.kt").readText())
    val list = withSheet.first.classLoader.loadClass("movemate.MovingDayList")
    val instance = list.getField("INSTANCE").get(null)
    val lamp = withSheet.first.classLoader.loadClass("movemate.Lamp")
        .getConstructor(String::class.java, Int::class.java, String::class.java).newInstance("desk lamp", 1, null)
    println("--- MovingDayList.cardFor(lamp) returns: ${list.getMethod("cardFor", Any::class.java).invoke(instance, lamp)}")

    println()
    println("=== with no options at all")
    val without = compile("without-options", things, emptyMap())
    println("exit code: ${without.first.exitCode}")
    without.first.messages.lines().filter { it.startsWith("e: ") }.forEach(::println)
    println("generated files: ${without.second.walk().filter { it.isFile }.map { it.name }.toList()}")
}

private fun compile(name: String, source: SourceFile, options: Map<String, String>) =
    KotlinCompilation().run {
        workingDir = File("build/kctfork/demo/l07-$name").apply { deleteRecursively() }
        sources = listOf(source)
        inheritClassPath = true
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream()
        configureKsp {
            symbolProcessorProviders += MasterListProcessorProvider()
            processorOptions += options
        }
        compile() to kspSourcesDir.resolve("kotlin")
    }
