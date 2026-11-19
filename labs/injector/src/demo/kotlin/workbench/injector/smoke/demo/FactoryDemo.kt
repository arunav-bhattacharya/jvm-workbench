package workbench.injector.smoke.demo

import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import com.tschuchort.compiletesting.kspSourcesDir
import java.io.File
import java.io.OutputStream
import workbench.injector.smoke.FactoryProcessorProvider

// Smoke example (keep or delete). Runs the @Factory processor in memory and prints the file it generated.
//   ./gradlew :injector:demo -Pmain=workbench.injector.smoke.demo.FactoryDemoKt
fun main() {
    val route = SourceFile.kotlin(
        "Route.kt",
        """
        package movemate

        import workbench.injector.annotations.smoke.Factory

        @Factory
        class Route
        """,
    )
    val compilation = KotlinCompilation().apply {
        workingDir = File("build/kctfork/demo").apply { deleteRecursively() }
        sources = listOf(route)
        inheritClassPath = true
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream()
        configureKsp { symbolProcessorProviders += FactoryProcessorProvider() }
    }
    val result = compilation.compile()
    println("exit code: ${result.exitCode}")
    val generated = compilation.kspSourcesDir.resolve("kotlin")
    generated.walk().filter { it.isFile }.forEach { file ->
        println("--- ${file.relativeTo(generated).invariantSeparatorsPath}")
        print(file.readText())
    }
}
