package workbench.ksp

import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.tschuchort.compiletesting.JvmCompilationResult
import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import com.tschuchort.compiletesting.kspSourcesDir
import java.io.File
import java.io.OutputStream
import java.util.concurrent.atomic.AtomicInteger
import org.assertj.core.api.Assertions.fail

// Shared test helper for every lesson (keep it). It wraps kctfork: compile Kotlin source strings in memory,
// run KSP2 with the processors you pass, then compile the sources together with what the processors generated.
// Tests pass the provider directly, so only that lesson's processor runs; the services files are not used here.

private val runs = AtomicInteger()

/**
 * Compiles [sources] with [processors] and returns what happened. [options] become the processors'
 * `environment.options`, as `ksp { arg(...) }` would in Gradle.
 */
fun compileWithKsp(
    vararg sources: SourceFile,
    processors: List<SymbolProcessorProvider>,
    options: Map<String, String> = emptyMap(),
): KspResult {
    // build/kctfork/<test task>/<nnn>-<test method>/: open ksp/sources/kotlin there to read what was generated
    val root = System.getProperty("kctfork.dir")?.let(::File) ?: File("build/kctfork/ide")
    val compilation = KotlinCompilation().apply {
        workingDir = root.resolve("%03d-%s".format(runs.incrementAndGet(), callingTest())).apply { deleteRecursively() }
        this.sources = sources.toList()
        inheritClassPath = true // the test's own classpath: the annotations, the stdlib, the processors under test
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream() // read result.messages instead of printing
        configureKsp {
            symbolProcessorProviders += processors
            processorOptions += options
        }
    }
    return KspResult(compilation.compile(), compilation.kspSourcesDir.resolve("kotlin"))
}

/** The name of the test method that called [compileWithKsp], made safe for a folder name. */
private fun callingTest(): String = StackWalker.getInstance().walk { frames ->
    frames.map { it.methodName }.filter { it != "compileWithKsp" && !it.startsWith("compileWithKsp$") && it != "callingTest" }
        .findFirst().orElse("run")
}.replace(Regex("[^A-Za-z0-9_-]+"), "-").trim('-').take(60)

/** What one in-memory compilation produced. */
class KspResult(val result: JvmCompilationResult, private val generatedDir: File) {
    /** OK, or COMPILATION_ERROR when a processor called logger.error or the code does not compile. */
    val exitCode: KotlinCompilation.ExitCode get() = result.exitCode

    /**
     * Everything the compiler and the processors printed, one message per line, for example
     * `e: [ksp] /…/sources/Shape.kt:3: @Hello goes on a class, but Shape is an interface`.
     */
    val messages: String get() = result.messages

    /** Generated Kotlin files by path under the KSP output folder, for example `movemate/LampHello.kt`. */
    val generated: Map<String, String> by lazy {
        generatedDir.walk().filter { it.isFile }
            .associate { it.relativeTo(generatedDir).invariantSeparatorsPath to it.readText() }
    }

    /** The text of one generated file; fails with the list of files that were generated if it is missing. */
    fun generated(path: String): String = generated[path]
        ?: fail("KSP generated no $path. Generated: ${generated.keys.sorted()}. Messages:\n$messages")

    /** Loads a compiled class (yours or generated) by its binary name, for example `movemate.LampHelloKt`. */
    fun loadClass(name: String): Class<*> = result.classLoader.loadClass(name)

    /** Calls a top-level function without parameters, for example ("movemate.LampHelloKt", "helloFromLamp"). */
    fun callTopLevel(fileClass: String, function: String): Any? =
        loadClass(fileClass).getMethod(function).invoke(null)

    /** Calls a function without parameters on a Kotlin `object`, for example ("movemate.LampFactory", "create"). */
    fun callOnObject(objectClass: String, function: String): Any? {
        val type = loadClass(objectClass)
        return type.getMethod(function).invoke(type.getField("INSTANCE").get(null))
    }
}
