package workbench.ksp.l03.demo

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.processing.Resolver
import com.google.devtools.ksp.processing.SymbolProcessor
import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSClassDeclaration
import com.google.devtools.ksp.symbol.KSFile
import com.google.devtools.ksp.symbol.KSFunctionDeclaration
import com.google.devtools.ksp.symbol.KSPropertyDeclaration
import com.google.devtools.ksp.symbol.KSVisitorVoid
import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import java.io.File
import java.io.OutputStream

// Everything KSP shows a processor about one Kotlin file and one Java file: the label on each box, printed as a
// tree. Look for what is there (names, types, hasDefault, a local val) and what is not (any expression).
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l03.demo.TreeDemoKt

/** A processor that prints the symbol tree of every source file once, in round 1. */
class TreeProcessor(private val lines: MutableList<String>) : SymbolProcessor {
    override val apiFeatures: ApiFeatures = buildApiFeatures { enableBackingFields = true; enableContextParameters = true }
    private var round = 0

    override fun process(resolver: Resolver): List<KSAnnotated> {
        if (++round == 1) resolver.getNewFiles().forEach { it.accept(TreePrinter(), Unit) }
        return emptyList()
    }

    /** A visitor: KSP calls the visit function that matches each node; each one decides where to go next. */
    inner class TreePrinter : KSVisitorVoid(apiFeatures) {
        private var depth = 0

        private fun line(text: String) {
            lines += "  ".repeat(depth) + text
        }

        private fun children(nodes: Sequence<KSAnnotated>) {
            depth++
            nodes.forEach { it.accept(this, Unit) }
            depth--
        }

        override fun visitFile(file: KSFile, data: Unit) {
            line("file ${file.fileName}  package=${file.packageName.asString()}")
            children(file.declarations)
        }

        override fun visitClassDeclaration(classDeclaration: KSClassDeclaration, data: Unit) {
            line("class ${classDeclaration.simpleName.asString()}  kind=${classDeclaration.classKind}  " +
                "modifiers=${classDeclaration.modifiers}  origin=${classDeclaration.origin}")
            children(classDeclaration.declarations)
        }

        override fun visitFunctionDeclaration(function: KSFunctionDeclaration, data: Unit) {
            val parameters = function.parameters.joinToString(", ") { p ->
                "${p.name?.asString()}: ${p.type}" + if (p.hasDefault) " (hasDefault)" else ""
            }
            line("function ${function.simpleName.asString()}($parameters): ${function.returnType}  origin=${function.origin}")
            children(function.declarations) // a function's own named declarations, such as a local val
        }

        override fun visitPropertyDeclaration(property: KSPropertyDeclaration, data: Unit) {
            line("property ${property.simpleName.asString()}: ${property.type}")
        }
    }
}

fun main() {
    val kotlin = SourceFile.kotlin(
        "Rooms.kt",
        """
        package movemate

        data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)

        class Mirror(val widthCm: Int, val heightCm: Int, val glass: String) {
            fun areaCm2(): Int {
                val area = widthCm * heightCm
                return area
            }
        }
        """,
    )
    val java = SourceFile.java(
        "MovingCrate.java",
        """
        package movemate;

        public class MovingCrate {
            private final String label;

            public MovingCrate(String label) { this.label = label; }

            public String getLabel() { return label.trim(); }
        }
        """,
    )
    val lines = mutableListOf<String>()
    val compilation = KotlinCompilation().apply {
        workingDir = File("build/kctfork/demo").apply { deleteRecursively() }
        sources = listOf(kotlin, java)
        inheritClassPath = true
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream()
        configureKsp { symbolProcessorProviders += SymbolProcessorProvider { TreeProcessor(lines) } }
    }
    val result = compilation.compile()
    println("exit code: ${result.exitCode}")
    lines.forEach(::println)
}
