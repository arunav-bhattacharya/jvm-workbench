package workbench.ksp.l08

import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import com.tschuchort.compiletesting.kspSourcesDir
import java.io.File
import java.io.OutputStream
import java.util.concurrent.atomic.AtomicInteger

// Given: the bench's compiler, plugged in for the tests. kctfork runs KSP2 on the sources in memory, then the
// Kotlin compiler on the sources together with what the processors generated. Each compile gets its own folder,
// build/kctfork/<test task>/l08-<nnn>/: open ksp/sources/kotlin there to read what a test generated.
object KctforkCompiler : InMemoryCompiler {
    private val runs = AtomicInteger()

    override fun compile(sources: List<Source>, processors: List<SymbolProcessorProvider>, options: Map<String, String>): Compiled {
        val root = System.getProperty("kctfork.dir")?.let(::File) ?: File("build/kctfork/ide")
        val compilation = KotlinCompilation().apply {
            workingDir = root.resolve("l08-%03d".format(runs.incrementAndGet())).apply { deleteRecursively() }
            this.sources = sources.map { SourceFile.kotlin(it.fileName, it.text, trimIndent = false) } // the bench trimmed them
            inheritClassPath = true
            jvmTarget = "21"
            messageOutputStream = OutputStream.nullOutputStream()
            configureKsp {
                symbolProcessorProviders += processors
                processorOptions += options
            }
        }
        val result = compilation.compile()
        return Compiled(result.exitCode.name, result.messages, compilation.kspSourcesDir.resolve("kotlin"), result.classLoader)
    }
}
