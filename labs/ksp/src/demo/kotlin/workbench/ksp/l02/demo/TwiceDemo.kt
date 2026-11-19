package workbench.ksp.l02.demo

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.processing.CodeGenerator
import com.google.devtools.ksp.processing.Dependencies
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

// Naive: this will not work. A processor that looks through EVERY file in every round, instead of asking for
// the symbols with the sticky note. Round 1 writes Lamp's card. Round 2 sees Lamp again, among all the files,
// and writes the same card a second time.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l02.demo.TwiceDemoKt
class EveryFileProcessor(private val codeGenerator: CodeGenerator, private val logger: KSPLogger) : SymbolProcessor {
    override val apiFeatures: ApiFeatures = buildApiFeatures { enableBackingFields = true; enableContextParameters = true }
    private var round = 0

    override fun process(resolver: Resolver): List<KSAnnotated> {
        round++
        val files = resolver.getAllFiles().toList()
        logger.warn("round $round: getAllFiles() = ${files.map { it.fileName }}")
        for (cls in files.flatMap { it.declarations }.filterIsInstance<KSClassDeclaration>()) {
            if (cls.annotations.none { it.shortName.asString() == "Inventory" }) continue
            val name = cls.simpleName.asString()
            codeGenerator.createNewFile(Dependencies(false, cls.containingFile!!), "movemate", "${name}InventoryCard")
                .use { it.write("package movemate\n\nfun $name.inventoryCard() = \"$name\"\n".toByteArray()) }
        }
        return emptyList()
    }
}

fun main() {
    val lamp = SourceFile.kotlin(
        "Lamp.kt",
        """
        package movemate

        import workbench.ksp.annotations.Inventory

        @Inventory
        data class Lamp(val name: String, val bulbs: Int, val shade: String?)
        """,
    )
    val compilation = KotlinCompilation().apply {
        workingDir = File("build/kctfork/demo").apply { deleteRecursively() }
        sources = listOf(lamp)
        inheritClassPath = true
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream()
        configureKsp {
            symbolProcessorProviders += SymbolProcessorProvider { env -> EveryFileProcessor(env.codeGenerator, env.logger) }
        }
    }
    val result = compilation.compile()
    println("exit code: ${result.exitCode}")
    // the KSP lines and the exception's first line, with the long work-folder path cut down
    result.messages.lines().filter { "[ksp]" in it || "FileAlreadyExistsException:" in it }
        .forEach { println(it.replace(Regex("""/\S*/ksp/sources/"""), ".../")) }
}
