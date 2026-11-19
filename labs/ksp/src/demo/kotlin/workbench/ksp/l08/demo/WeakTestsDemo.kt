package workbench.ksp.l08.demo

import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.squareup.kotlinpoet.ksp.toTypeName
import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import com.tschuchort.compiletesting.kspSourcesDir
import java.io.File
import java.io.OutputStream
import workbench.ksp.l08.BuilderProcessor
import workbench.ksp.l08.Compiled
import workbench.ksp.l08.GoldenResult
import workbench.ksp.l08.InMemoryCompiler
import workbench.ksp.l08.ProcessorBench
import workbench.ksp.l08.Source
import workbench.ksp.l08.checkGolden

// A builder processor with one planted bug: it drops the '?' from every parameter type, so shade(shade: String?)
// comes out as shade(shade: String). Then the four checks, weakest first. Which ones notice?
// Uses the reference bench; add -Pmine=l08 for yours.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l08.demo.WeakTestsDemoKt
fun main() {
    val buggy = SymbolProcessorProvider { env ->
        BuilderProcessor(env.codeGenerator, env.logger, typeOf = { it.toTypeName().copy(nullable = false) })
    }
    val lamp = Source(
        "Lamp.kt",
        """
        package movemate

        import workbench.ksp.annotations.Builder

        @Builder
        data class Lamp(val name: String, val bulbs: Int, val shade: String?)
        """,
    )
    val run = ProcessorBench(DemoCompiler).run(lamp, processors = listOf(buggy))
    val text = run.generated("movemate/LampBuilder.kt")

    println("check 1, the exit code is OK:            ${verdict(run.exitCode == "OK")}   (${run.exitCode})")
    println("check 2, the text contains LampBuilder:  ${verdict("class LampBuilder" in text)}")
    val golden = File("src/test/resources/workbench/ksp/l08/golden/LampBuilder.kt.golden")
    when (val g = checkGolden(text, golden, update = false)) {
        is GoldenResult.Differs -> {
            println("check 3, the golden file:                FAILS at line ${g.line}")
            println("    expected: ${g.expected.trim()}")
            println("    actual:   ${g.actual.trim()}")
        }
        else -> println("check 3, the golden file:                $g")
    }
    val builder = run.newInstance("movemate.LampBuilder")
    run.call(builder, "name", "desk lamp")
    run.call(builder, "bulbs", 1)
    try {
        run.call(builder, "shade", null)
        println("check 4, call shade(null):               passes")
    } catch (e: NullPointerException) {
        println("check 4, call shade(null):               FAILS with ${e.javaClass.simpleName}: ${e.message}")
    }
}

private fun verdict(ok: Boolean) = if (ok) "passes" else "FAILS "

/** The demo's own copy of the bench's compiler (the tests' copy lives in src/test, which demos can't see). */
private object DemoCompiler : InMemoryCompiler {
    override fun compile(sources: List<Source>, processors: List<SymbolProcessorProvider>, options: Map<String, String>): Compiled {
        val compilation = KotlinCompilation().apply {
            workingDir = File("build/kctfork/demo/l08").apply { deleteRecursively() }
            this.sources = sources.map { SourceFile.kotlin(it.fileName, it.text, trimIndent = false) }
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
