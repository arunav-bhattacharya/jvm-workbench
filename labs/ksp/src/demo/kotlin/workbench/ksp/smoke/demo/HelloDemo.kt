package workbench.ksp.smoke.demo

import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import com.tschuchort.compiletesting.kspSourcesDir
import java.io.File
import java.io.OutputStream
import workbench.ksp.smoke.HelloProcessorProvider

// Smoke example (keep or delete). Runs the @Hello processor on one source string in memory, prints the file it
// generated, then calls the generated function. Uses the reference processor; add -Pmine=smoke for yours.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.smoke.demo.HelloDemoKt
fun main() {
    val lamp = SourceFile.kotlin(
        "Lamp.kt",
        """
        package movemate

        import workbench.ksp.annotations.smoke.Hello

        @Hello
        class Lamp
        """,
    )
    val compilation = KotlinCompilation().apply {
        workingDir = File("build/kctfork/demo").apply { deleteRecursively() }
        sources = listOf(lamp)
        inheritClassPath = true
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream()
        configureKsp { symbolProcessorProviders += HelloProcessorProvider() }
    }
    val result = compilation.compile()
    println("exit code: ${result.exitCode}")

    val generated = compilation.kspSourcesDir.resolve("kotlin")
    generated.walk().filter { it.isFile }.forEach { file ->
        println("--- ${file.relativeTo(generated).invariantSeparatorsPath}")
        print(file.readText())
    }

    val hello = result.classLoader.loadClass("movemate.LampHelloKt").getMethod("helloFromLamp").invoke(null)
    println("--- helloFromLamp() returns: $hello")
}
