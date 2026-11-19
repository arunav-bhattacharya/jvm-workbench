package workbench.injector.l01.demo

import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import com.tschuchort.compiletesting.kspSourcesDir
import java.io.File
import java.io.OutputStream
import workbench.injector.l01.FactoryProcessorProvider

// Runs lesson 1's factory processor in memory on three classes and prints the cards it writes.
//   ./gradlew :injector:demo -Pmain=workbench.injector.l01.demo.FactoryDemoKt
fun main() {
    val sources = listOf(
        "Route" to "class Route @Inject constructor()",
        "Driver" to "class Driver @Inject constructor(val route: Route)",
        "Truck" to "class Truck @Inject constructor(val driver: Driver)",
    ).map { (name, line) ->
        SourceFile.kotlin("$name.kt", "package movemate\n\nimport workbench.injector.annotations.Inject\n\n$line\n")
    }
    val compilation = KotlinCompilation().apply {
        workingDir = File("build/kctfork/demo").apply { deleteRecursively() }
        this.sources = sources
        inheritClassPath = true
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream()
        configureKsp { symbolProcessorProviders += FactoryProcessorProvider() }
    }
    val result = compilation.compile()
    println("exit code: ${result.exitCode}")
    val generated = compilation.kspSourcesDir.resolve("kotlin")
    generated.walk().filter { it.isFile }.sortedBy { it.name }.forEach { file ->
        println("--- ${file.relativeTo(generated).invariantSeparatorsPath}")
        print(file.readText())
    }
}
