package workbench.ksp.l02.demo

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.processing.KSPLogger
import com.google.devtools.ksp.processing.Resolver
import com.google.devtools.ksp.processing.SymbolProcessor
import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSClassDeclaration
import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import java.io.File
import java.io.OutputStream

// The first two rungs of lesson 2's ladder, run together on one MoveMate file in memory:
//   rung 1: a processor that only says which round it is in
//   rung 2: a processor that asks for the classes with the sticky note, once by full name and once
//           (the trap) by short name
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l02.demo.RungsDemoKt

/** Rung 1: KSP calls process() once per round; this processor only reports it. */
class RoundLogger(private val logger: KSPLogger) : SymbolProcessor {
    override val apiFeatures: ApiFeatures = buildApiFeatures { enableBackingFields = true; enableContextParameters = true }
    private var round = 0
    override fun process(resolver: Resolver): List<KSAnnotated> {
        round++
        logger.warn("[rung 1] round $round")
        return emptyList()
    }
}

/** Rung 2: find the annotated symbols and log their names. [annotation] is the name it asks for. */
class NoteFinder(private val logger: KSPLogger, private val annotation: String) : SymbolProcessor {
    override val apiFeatures: ApiFeatures = buildApiFeatures { enableBackingFields = true; enableContextParameters = true }
    override fun process(resolver: Resolver): List<KSAnnotated> {
        val found = resolver.getSymbolsWithAnnotation(annotation).toList()
        logger.warn("[rung 2] asked for \"$annotation\", found ${found.size}")
        for (symbol in found) {
            if (symbol is KSClassDeclaration) logger.warn("[rung 2] found ${symbol.simpleName.asString()}", symbol)
        }
        return emptyList()
    }
}

private val moveMate = SourceFile.kotlin(
    "MoveMate.kt",
    """
    package movemate

    import workbench.ksp.annotations.Inventory

    @Inventory
    data class Lamp(val name: String, val bulbs: Int, val shade: String?)

    @Inventory
    data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)

    class Wardrobe(val doors: Int)
    """,
)

fun main() {
    // all three processors in one compilation: KSP runs them one after the other in every round
    val compilation = KotlinCompilation().apply {
        workingDir = File("build/kctfork/demo").apply { deleteRecursively() }
        sources = listOf(moveMate)
        inheritClassPath = true
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream()
        configureKsp {
            symbolProcessorProviders += SymbolProcessorProvider { env -> RoundLogger(env.logger) }
            symbolProcessorProviders += SymbolProcessorProvider { env ->
                NoteFinder(env.logger, "workbench.ksp.annotations.Inventory")
            }
            symbolProcessorProviders += SymbolProcessorProvider { env -> NoteFinder(env.logger, "Inventory") }
        }
    }
    val result = compilation.compile()
    println("exit code: ${result.exitCode}")
    // the KSP lines only, with the long work-folder path cut down to the file name
    result.messages.lines().filter { "[ksp]" in it }
        .forEach { println(it.replace(Regex("""/\S*/sources/"""), ".../")) }
}
