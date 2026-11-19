package workbench.ksp.l04.demo

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.processing.CodeGenerator
import com.google.devtools.ksp.processing.Dependencies
import com.google.devtools.ksp.processing.Resolver
import com.google.devtools.ksp.processing.SymbolProcessor
import com.google.devtools.ksp.processing.SymbolProcessorEnvironment
import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSClassDeclaration
import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import com.tschuchort.compiletesting.kspSourcesDir
import java.io.File
import java.io.OutputStream
import workbench.ksp.annotations.Builder

// Lesson 4, Try it: the builder written as a string template, the way lesson 2 wrote the inventory card.
// It works for Lamp, then meets four ordinary classes. Each one is compiled on its own, so each failure shows.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l04.demo.TemplateBuilderDemoKt

/** Naive: a builder from a string template. It will not survive the four cases below. */
class TemplateBuilderProcessor(private val codeGenerator: CodeGenerator) : SymbolProcessor {
    override val apiFeatures: ApiFeatures = buildApiFeatures {
        enableBackingFields = true
        enableContextParameters = true
    }

    override fun process(resolver: Resolver): List<KSAnnotated> {
        val classes = resolver.getSymbolsWithAnnotation(Builder::class.qualifiedName!!).filterIsInstance<KSClassDeclaration>()
        for (cls in classes) {
            val name = cls.simpleName.asString()
            val pkg = cls.packageName.asString()
            val params = cls.primaryConstructor!!.parameters
            val text = buildString {
                appendLine("package $pkg")
                appendLine()
                appendLine("class ${name}Builder {")
                for (p in params) {
                    appendLine("    private var ${p.name!!.asString()}: ${p.type.resolve()}? = null")
                }
                for (p in params) {
                    val n = p.name!!.asString()
                    appendLine("    fun $n($n: ${p.type.resolve()}): ${name}Builder {")
                    appendLine("        this.$n = $n")
                    appendLine("        return this")
                    appendLine("    }")
                }
                appendLine("    fun build(): $name = $name(")
                for (p in params) {
                    val n = p.name!!.asString()
                    if (p.type.resolve().isMarkedNullable) appendLine("        $n = $n,")
                    else appendLine("        $n = $n ?: error(\"${name}Builder: $n was not set\"),")
                }
                appendLine("    )")
                appendLine("}")
            }
            codeGenerator.createNewFile(Dependencies(false, cls.containingFile!!), pkg, "${name}Builder")
                .use { it.write(text.toByteArray()) }
        }
        return emptyList()
    }
}

class TemplateBuilderProvider : SymbolProcessorProvider {
    override fun create(environment: SymbolProcessorEnvironment) = TemplateBuilderProcessor(environment.codeGenerator)
}

private val box = SourceFile.kotlin(
    "Box.kt",
    """
    package movemate

    data class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)
    """,
)

private val cases = listOf(
    "Lamp, the easy one" to SourceFile.kotlin(
        "Lamp.kt",
        """
        package movemate

        import workbench.ksp.annotations.Builder

        @Builder
        data class Lamp(val name: String, val bulbs: Int, val shade: String?)
        """,
    ),
    "a type from another package" to SourceFile.kotlin(
        "Load.kt",
        """
        package movemate.van

        import movemate.Box
        import workbench.ksp.annotations.Builder

        @Builder
        class Load(val first: Box)
        """,
    ),
    "a nullable list of nullable boxes" to SourceFile.kotlin(
        "Shelf.kt",
        """
        package movemate

        import workbench.ksp.annotations.Builder

        @Builder
        class Shelf(val boxes: List<Box?>?)
        """,
    ),
    "a nested class" to SourceFile.kotlin(
        "Kitchen.kt",
        """
        package movemate

        import workbench.ksp.annotations.Builder

        class Kitchen {
            @Builder
            data class Drawer(val label: String)
        }
        """,
    ),
    "a property named in" to SourceFile.kotlin(
        "Crate.kt",
        """
        package movemate

        import workbench.ksp.annotations.Builder

        @Builder
        class Crate(val `in`: String)
        """,
    ),
)

fun main() {
    for ((i, case) in cases.withIndex()) {
        val (what, source) = case
        val compilation = KotlinCompilation().apply {
            workingDir = File("build/kctfork/demo/l04-template-$i").apply { deleteRecursively() }
            sources = listOf(box, source)
            inheritClassPath = true
            jvmTarget = "21"
            messageOutputStream = OutputStream.nullOutputStream()
            configureKsp { symbolProcessorProviders += TemplateBuilderProvider() }
        }
        val result = compilation.compile()
        println("=== $what: ${result.exitCode}")
        val generated = compilation.kspSourcesDir.resolve("kotlin")
        generated.walk().filter { it.isFile }.forEach { print(it.readText()) }
        // the compiler's errors and warnings, with the long work folder cut down to the file name
        val problems = result.messages.lines().filter { it.startsWith("e: file:") || it.startsWith("w: file:") }
            .map { it.replace(Regex("file://\\S*/"), "") }
        problems.take(3).forEach(::println)
        if (problems.size > 3) println("... and ${problems.size - 3} more")
    }
}
