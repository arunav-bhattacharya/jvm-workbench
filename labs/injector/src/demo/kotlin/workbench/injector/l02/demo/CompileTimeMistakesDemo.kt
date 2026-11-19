package workbench.injector.l02.demo

import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import java.io.File
import java.io.OutputStream
import workbench.injector.l02.ComponentProcessorProvider
import workbench.injector.l02.FactoryProcessorProvider

// The same three broken plans (the very files RunTimeMistakesDemo ran), checked the night before:
// lesson 2's processors compile all three in one build and report every mistake with its file and line.
//   ./gradlew :injector:demo -Pmain=workbench.injector.l02.demo.CompileTimeMistakesDemoKt
fun main() {
    val folder = File("src/demo/kotlin/workbench/injector/l02/demo")
    val sources = listOf("missing/Missing.kt", "cycle/Cycle.kt", "twice/Twice.kt").map { path ->
        val text = folder.resolve(path).readText()
            .replace("package workbench.injector.l02.demo.", "package movemate.")   // same lines, own package
        SourceFile.kotlin(path.substringAfter('/'), text)
    }
    val compilation = KotlinCompilation().apply {
        workingDir = File("build/kctfork/demo").apply { deleteRecursively() }
        this.sources = sources
        inheritClassPath = true
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream()
        configureKsp { symbolProcessorProviders += listOf(FactoryProcessorProvider(), ComponentProcessorProvider()) }
    }
    val result = compilation.compile()
    println("exit code: ${result.exitCode}")
    result.messages.lines().filter { it.startsWith("e: [ksp]") }
        .forEach { println(it.replace(Regex("""/\S*/sources/"""), "")) }   // keep the file name and the line
}
