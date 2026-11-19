package workbench.ksp.l06.demo

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.processing.CodeGenerator
import com.google.devtools.ksp.processing.KSPLogger
import com.google.devtools.ksp.processing.Resolver
import com.google.devtools.ksp.processing.SymbolProcessor
import com.google.devtools.ksp.processing.SymbolProcessorEnvironment
import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSClassDeclaration
import com.google.devtools.ksp.validate
import com.squareup.kotlinpoet.ksp.writeTo
import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import java.io.File
import java.io.OutputStream
import workbench.ksp.annotations.Moving
import workbench.ksp.l06.InventoryProcessorProvider
import workbench.ksp.l06.ReceiptProcessorProvider
import workbench.ksp.l06.nameOf
import workbench.ksp.l06.receiptFile

// Lesson 6, Try it: three receipt processors on the same move, each run together with the card processor.
// The last one is the lab's processor (the reference answer; add -Pmine=l06 for yours).
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l06.demo.RoundsDemoKt

/** Naive: writes a receipt for every @Moving class at once, ready or not. */
class Eager(private val codeGenerator: CodeGenerator, private val logger: KSPLogger) : SymbolProcessor {
    override val apiFeatures: ApiFeatures = buildApiFeatures {
        enableBackingFields = true
        enableContextParameters = true
    }

    override fun process(resolver: Resolver): List<KSAnnotated> {
        for (cls in resolver.getSymbolsWithAnnotation(Moving::class.qualifiedName!!).filterIsInstance<KSClassDeclaration>()) {
            receiptFile(cls).writeTo(codeGenerator, aggregating = false)
        }
        return emptyList()
    }
}

/** Sets aside what isn't valid yet, and logs each round. Says nothing about what is still set aside at the end. */
class Quiet(private val codeGenerator: CodeGenerator, private val logger: KSPLogger) : SymbolProcessor {
    override val apiFeatures: ApiFeatures = buildApiFeatures {
        enableBackingFields = true
        enableContextParameters = true
    }
    private var round = 0

    override fun process(resolver: Resolver): List<KSAnnotated> {
        round++
        val (ready, later) = resolver.getSymbolsWithAnnotation(Moving::class.qualifiedName!!).toList()
            .partition { it.validate(apiFeatures = apiFeatures) }
        val written = ready.filterIsInstance<KSClassDeclaration>().map { cls ->
            receiptFile(cls).also { it.writeTo(codeGenerator, aggregating = false) }.name
        }
        logger.warn("[receipts] round $round: wrote $written, set aside ${later.map(::nameOf)}")
        return later
    }
}

private fun provider(make: (CodeGenerator, KSPLogger) -> SymbolProcessor) =
    SymbolProcessorProvider { env: SymbolProcessorEnvironment -> make(env.codeGenerator, env.logger) }

private val move = SourceFile.kotlin(
    "MoveMate.kt",
    """
    package movemate

    import workbench.ksp.annotations.Inventory
    import workbench.ksp.annotations.Moving

    @Moving
    data class Lamp(val name: String, val bulbs: Int, val shade: String?)

    @Inventory
    data class Box(val label: String, val room: String, val weightGrams: Int)

    @Moving
    data class Van(val plate: String, val lastLoad: LampReceipt)
    """,
)

private val trailer = SourceFile.kotlin(
    "Trailer.kt",
    """
    package movemate

    import workbench.ksp.annotations.Moving

    data class Piano(val keys: Int)

    @Moving
    data class Trailer(val plate: String, val load: PianoReceipt)
    """,
)

fun main() {
    val runs = listOf(
        Triple("1. eager, no validate()", provider(::Eager), listOf(move)),
        Triple("2. validate() and set aside", provider(::Quiet), listOf(move)),
        Triple("3. a Trailer that waits for PianoReceipt, which nobody writes", provider(::Quiet), listOf(trailer)),
        Triple("4. the same Trailer, with the lab's check in finish()", ReceiptProcessorProvider(), listOf(trailer)),
    )
    for ((i, run) in runs.withIndex()) {
        val (what, receipts, input) = run
        val compilation = KotlinCompilation().apply {
            workingDir = File("build/kctfork/demo/l06-run-${i + 1}").apply { deleteRecursively() }
            sources = input
            inheritClassPath = true
            jvmTarget = "21"
            messageOutputStream = OutputStream.nullOutputStream()
            configureKsp { symbolProcessorProviders += listOf(receipts, InventoryProcessorProvider()) }
        }
        val result = compilation.compile()
        println("=== $what: ${result.exitCode}")
        // KSP's lines, a crash's first line, and the compiler's errors, with the work folder cut down to the file name
        result.messages.lines()
            .filter { it.startsWith("w: [ksp]") || it.startsWith("e: [ksp]") || it.startsWith("java.") || it.startsWith("e: file:") }
            .map { it.replace(Regex("(file://)?/\\S*/sources/"), "") }
            .forEach(::println)
    }
}
