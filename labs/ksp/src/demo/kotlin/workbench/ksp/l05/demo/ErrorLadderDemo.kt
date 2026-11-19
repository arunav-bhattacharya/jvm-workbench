package workbench.ksp.l05.demo

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.processing.CodeGenerator
import com.google.devtools.ksp.processing.KSPLogger
import com.google.devtools.ksp.processing.Resolver
import com.google.devtools.ksp.processing.SymbolProcessor
import com.google.devtools.ksp.processing.SymbolProcessorEnvironment
import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.google.devtools.ksp.symbol.ClassKind
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSClassDeclaration
import com.squareup.kotlinpoet.ksp.writeTo
import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import java.io.File
import java.io.OutputStream
import workbench.ksp.annotations.Builder
import workbench.ksp.l05.BuilderProcessorProvider
import workbench.ksp.l05.builderFile
import workbench.ksp.l05.describe

// Lesson 5, Try it: the same bad input, four versions of the builder processor, one rung each.
// Rung 4 is the lab's processor (the reference answer; add -Pmine=l05 for yours).
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l05.demo.ErrorLadderDemoKt

/** The three early rungs share everything but [rung], which decides what happens to one @Builder symbol. */
abstract class RungProcessor(private val codeGenerator: CodeGenerator, protected val logger: KSPLogger) : SymbolProcessor {
    override val apiFeatures: ApiFeatures = buildApiFeatures {
        enableBackingFields = true
        enableContextParameters = true
    }

    override fun process(resolver: Resolver): List<KSAnnotated> {
        for (cls in resolver.getSymbolsWithAnnotation(Builder::class.qualifiedName!!).filterIsInstance<KSClassDeclaration>()) {
            if (!rung(cls)) return emptyList()   // stops at the first problem
            builderFile(cls).writeTo(codeGenerator, aggregating = false)
        }
        return emptyList()
    }

    abstract fun rung(cls: KSClassDeclaration): Boolean
}

/** Rung 1, naive: lesson 4's processor. No check at all, so primaryConstructor!! meets an interface. */
class Crashing(cg: CodeGenerator, log: KSPLogger) : RungProcessor(cg, log) {
    override fun rung(cls: KSClassDeclaration) = true
}

/** Rung 2: a check, but the message says neither what nor where. */
class Vague(cg: CodeGenerator, log: KSPLogger) : RungProcessor(cg, log) {
    override fun rung(cls: KSClassDeclaration): Boolean {
        if (cls.classKind != ClassKind.CLASS || cls.primaryConstructor == null) {
            logger.error("@Builder can't build this")
            return false
        }
        return true
    }
}

/** Rung 3: what is wrong, how to fix it, and the symbol for where. Still stops at the first problem. */
class Precise(cg: CodeGenerator, log: KSPLogger) : RungProcessor(cg, log) {
    override fun rung(cls: KSClassDeclaration): Boolean {
        if (cls.classKind != ClassKind.CLASS) {
            logger.error("@Builder needs a class to build, but ${describe(cls)}. Put @Builder on a class with a primary constructor.", cls)
            return false
        }
        if (cls.primaryConstructor == null) {
            logger.error("${cls.simpleName.asString()} has no primary constructor", cls)
            return false
        }
        return true
    }
}

fun provider(make: (CodeGenerator, KSPLogger) -> SymbolProcessor) =
    SymbolProcessorProvider { env: SymbolProcessorEnvironment -> make(env.codeGenerator, env.logger) }

private val badInput = listOf(
    SourceFile.kotlin(
        "Wardrobe.kt",
        """
        package movemate

        import workbench.ksp.annotations.Builder

        @Builder
        interface Wardrobe

        @Builder
        object Settings
        """,
    ),
    SourceFile.kotlin(
        "Crate.kt",
        """
        package movemate

        import workbench.ksp.annotations.Builder

        @Builder
        class Crate {
            constructor(label: String)
        }
        """,
    ),
    SourceFile.kotlin(
        "Plant.kt",
        """
        package movemate

        import workbench.ksp.annotations.Builder

        @Builder
        data class Plant(
            val kind: String,
            val potLitres: Double,
            val waterEveryDays: Int = 7,
        )
        """,
    ),
)

fun main() {
    val rungs = listOf(
        "1. no check: lesson 4's processor" to provider(::Crashing),
        "2. a check with a vague message" to provider(::Vague),
        "3. a precise message on the symbol" to provider(::Precise),
        "4. every problem in one build, plus a warning" to BuilderProcessorProvider(),
    )
    for ((i, rung) in rungs.withIndex()) {
        val (what, processor) = rung
        val compilation = KotlinCompilation().apply {
            workingDir = File("build/kctfork/demo/l05-rung-${i + 1}").apply { deleteRecursively() }
            sources = badInput
            inheritClassPath = true
            jvmTarget = "21"
            messageOutputStream = OutputStream.nullOutputStream()
            configureKsp { symbolProcessorProviders += processor }
        }
        val result = compilation.compile()
        println("=== $what: ${result.exitCode}")
        // KSP's own lines only, with the long work folder cut down to the file name; a crash shows its first lines
        result.messages.lines()
            .filter { it.startsWith("e: [ksp]") || it.startsWith("w: [ksp]") || it.startsWith("java.") || it.startsWith("\tat ") }
            .map { it.replace(Regex("/\\S*/sources/"), "") }
            .take(4)
            .forEach(::println)
    }
}
