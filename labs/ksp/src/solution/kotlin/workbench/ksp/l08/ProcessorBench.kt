package workbench.ksp.l08

import com.google.devtools.ksp.processing.SymbolProcessorProvider
import java.io.File
import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Modifier

// Lesson 8: a small, reusable test bench for processors. It runs a practice pack in an empty room: compile a
// few source strings in memory with a processor, then make the four checks every processor test makes:
//   1. the exit code   2. the generated text (golden files)   3. the messages, by file and line   4. call the code
// The tests in src/test/kotlin/workbench/ksp/l08 check this bench and then use it on the given processors.
//   ./gradlew :ksp:test --tests 'workbench.ksp.l08.*'

/** One Kotlin source file for the bench, typed the way you'd type it in a test (indented is fine). */
data class Source(val fileName: String, val text: String)

/**
 * The one step that needs a Kotlin compiler with KSP inside it. That compiler, kctfork, is on the test and demo
 * classpaths only, so the bench takes it as a parameter: the tests pass `KctforkCompiler` (src/test), the demo
 * passes its own copy. The sources arrive already trimmed; the compiler must not change them.
 */
fun interface InMemoryCompiler {
    fun compile(sources: List<Source>, processors: List<SymbolProcessorProvider>, options: Map<String, String>): Compiled
}

/** What any in-memory compile hands back: exit code (`OK`, `COMPILATION_ERROR`, `INTERNAL_ERROR`), raw messages, the folder of generated Kotlin files, and a class loader that sees your classes and the generated ones. */
class Compiled(val exitCode: String, val messages: String, val generatedDir: File, val classLoader: ClassLoader)

/** One message, split into its parts. `file` is the file name only (`Shape.kt`): the folder is a temporary one. */
data class Message(val severity: Char, val file: String?, val line: Int?, val text: String)

class ProcessorBench(private val compiler: InMemoryCompiler) {

    /**
     * Compile [sources] with [processors]. Trims each source's indent first, so line 1 is the `package` line and
     * the line numbers in messages match what you count in the test.
     */
    fun run(vararg sources: Source, processors: List<SymbolProcessorProvider>, options: Map<String, String> = emptyMap()): BenchRun =
        BenchRun(compiler.compile(sources.map { it.copy(text = it.text.trimIndent()) }, processors, options))
}

/** What one practice pack produced, with the four checks. */
class BenchRun(val compiled: Compiled) {

    /** Check 1: `OK`, `COMPILATION_ERROR` (logger.error, or code that doesn't compile) or `INTERNAL_ERROR` (a processor threw). */
    val exitCode: String get() = compiled.exitCode

    /** Check 2: every generated file, by its path under the KSP output folder (`movemate/LampBuilder.kt`) to its text. */
    val generated: Map<String, String> by lazy {
        compiled.generatedDir.walk().filter { it.isFile }
            .associate { it.relativeTo(compiled.generatedDir).invariantSeparatorsPath to it.readText() }
            .toSortedMap()
    }

    /** One generated file; fails with the list of files that WERE generated, and every message. */
    fun generated(path: String): String = generated[path]
        ?: throw AssertionError("KSP generated no $path. Generated: ${generated.keys}. Messages:\n${compiled.messages}")

    /** Check 3: every message line, parsed. */
    val messages: List<Message> by lazy { compiled.messages.lines().mapNotNull(::parseMessage) }

    /** The errors only. */
    val errors: List<Message> get() = messages.filter { it.severity == 'e' }

    /** Check 4, part 1: an instance of a compiled class, through the constructor with that many parameters. */
    fun newInstance(className: String, vararg args: Any?): Any {
        val type = compiled.classLoader.loadClass(className)
        val constructor = type.constructors.firstOrNull { it.parameterCount == args.size }
            ?: throw AssertionError("$className has no constructor with ${args.size} parameters")
        return unwrapped { constructor.newInstance(*args) }
    }

    /**
     * Check 4, part 2: call a function by name and number of parameters. [target] is an instance for a member
     * function, or a class name for a top-level function (`movemate.LampInventoryCardKt`) or an object.
     */
    fun call(target: Any, function: String, vararg args: Any?): Any? {
        val type = if (target is String) compiled.classLoader.loadClass(target) else target.javaClass
        val method = type.methods.firstOrNull { it.name == function && it.parameterCount == args.size }
            ?: throw AssertionError("${type.name} has no function $function with ${args.size} parameters; it has ${type.methods.map { it.name }.sorted().distinct()}")
        val receiver = when {
            target !is String -> target
            Modifier.isStatic(method.modifiers) -> null
            else -> type.getField("INSTANCE").get(null) // a Kotlin object
        }
        return unwrapped { method.invoke(receiver, *args) }
    }

    /** Reflection wraps whatever the generated code throws; hand the test the real exception instead. */
    private inline fun <T> unwrapped(call: () -> T): T = try {
        call()
    } catch (e: InvocationTargetException) {
        throw e.cause ?: e
    }
}

private val kspMessage = Regex("""^([ewiv]): \[ksp] (?:(\S+?):(\d+): )?(.*)$""")
private val compilerMessage = Regex("""^([ewiv]): file://(\S+?):(\d+):\d+ (.*)$""")
private val plainMessage = Regex("""^([ewiv]): (.*)$""")

/**
 * Splits one line of compiler output into a [Message], or returns null for a line that isn't a message (a stack
 * trace line, a blank line). Three shapes:
 * - KSP, with a location:   `e: [ksp] /tmp/…/Shape.kt:6: @Builder goes on a class, but Shape is an interface`
 * - KSP, without one:       `w: [ksp] l08 not done yet`
 * - the Kotlin compiler:    `e: file:///tmp/…/Use.kt:5:44 Argument type mismatch: ...` (with a column)
 * Anything else that starts with `e: `, `w: `, `i: ` or `v: ` is a message without a location.
 */
fun parseMessage(line: String): Message? {
    kspMessage.matchEntire(line)?.let { m ->
        val (severity, path, number, text) = m.destructured
        return Message(severity[0], path.ifEmpty { null }?.substringAfterLast('/'), number.toIntOrNull(), text)
    }
    compilerMessage.matchEntire(line)?.let { m ->
        val (severity, path, number, text) = m.destructured
        return Message(severity[0], path.substringAfterLast('/'), number.toInt(), text)
    }
    plainMessage.matchEntire(line)?.let { m ->
        val (severity, text) = m.destructured
        return Message(severity[0], null, null, text)
    }
    return null
}

/** What a golden-file check found. */
sealed interface GoldenResult {
    /** The generated text is exactly the stored text. */
    data object Matches : GoldenResult

    /** There was no golden file yet (or you asked to update it), so the bench wrote one. Review it once. */
    data class Written(val file: File) : GoldenResult

    /** The first line that differs, counting from 1. A missing line reads `<end of file>`. */
    data class Differs(val line: Int, val expected: String, val actual: String) : GoldenResult
}

/** True when the tests run as `UPDATE_GOLDEN=true ./gradlew :ksp:test ...`. */
fun updateGoldenFiles(): Boolean = System.getenv("UPDATE_GOLDEN") == "true"

/**
 * Golden file: compare [actual] with the stored [golden] file. A missing file, or [update], writes [actual] to it
 * and returns [GoldenResult.Written], so a person reviews the new text once before it becomes the standard.
 */
fun checkGolden(actual: String, golden: File, update: Boolean = updateGoldenFiles()): GoldenResult {
    if (update || !golden.exists()) {
        golden.parentFile?.mkdirs()
        golden.writeText(actual)
        return GoldenResult.Written(golden)
    }
    val expected = golden.readText().lines()
    val got = actual.lines()
    for (i in 0 until maxOf(expected.size, got.size)) {
        val want = expected.getOrNull(i)
        val have = got.getOrNull(i)
        if (want != have) return GoldenResult.Differs(i + 1, want ?: "<end of file>", have ?: "<end of file>")
    }
    return GoldenResult.Matches
}
