package workbench.ksp.l03.demo

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.getConstructors
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
import workbench.ksp.l03.typeText

// Three ways to print a parameter's type, side by side, for every constructor parameter of the @Label classes:
//   toString()   what the type reference prints by itself
//   name only    the resolved type's declaration name, the first thing people try
//   typeText     lesson 3's typeText (the reference one, or yours with -Pmine=l03)
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l03.demo.ShapeDemoKt

class ShapeTable(private val rows: MutableList<List<String>>) : SymbolProcessor {
    override val apiFeatures: ApiFeatures = buildApiFeatures { enableBackingFields = true; enableContextParameters = true }

    override fun process(resolver: Resolver): List<KSAnnotated> {
        for (cls in resolver.getSymbolsWithAnnotation("workbench.ksp.annotations.Label").filterIsInstance<KSClassDeclaration>()) {
            val constructor = cls.primaryConstructor ?: cls.getConstructors().first()
            for (p in constructor.parameters) {
                val written = p.type.toString()
                val nameOnly = p.type.resolve().declaration.simpleName.asString()
                val ours = try { typeText(p.type) } catch (e: NotImplementedError) { "(not done yet)" }
                rows += listOf("${cls.simpleName.asString()}.${p.name!!.asString()}", written, nameOnly, ours)
            }
        }
        return emptyList()
    }
}

fun main() {
    val kotlin = SourceFile.kotlin(
        "Crate.kt",
        """
        package movemate

        import workbench.ksp.annotations.Label

        typealias Litres = Double

        @Label
        class Crate(
            val shade: String?,
            val books: List<String>,
            val water: Litres,
            val sizes: Map<String, List<Int?>>?,
            val odds: List<*>,
            val onDrop: (Int) -> Unit,
        )
        """,
    )
    val java = SourceFile.java(
        "MovingCrate.java",
        """
        package movemate;

        import workbench.ksp.annotations.Label;

        @Label
        public class MovingCrate {
            public MovingCrate(String label, int weightGrams) { }
        }
        """,
    )
    val rows = mutableListOf(listOf("parameter", "toString()", "name only", "typeText"))
    val compilation = KotlinCompilation().apply {
        workingDir = File("build/kctfork/demo").apply { deleteRecursively() }
        sources = listOf(kotlin, java)
        inheritClassPath = true
        jvmTarget = "21"
        messageOutputStream = OutputStream.nullOutputStream()
        configureKsp { symbolProcessorProviders += SymbolProcessorProvider { ShapeTable(rows) } }
    }
    val result = compilation.compile()
    println("exit code: ${result.exitCode}")
    val widths = (0..3).map { column -> rows.maxOf { it[column].length } + 2 }
    rows.forEach { row -> println(row.mapIndexed { i, cell -> cell.padEnd(widths[i]) }.joinToString("").trimEnd()) }
}
