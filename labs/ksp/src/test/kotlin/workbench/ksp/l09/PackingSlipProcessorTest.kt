package workbench.ksp.l09

import com.google.devtools.ksp.processing.Resolver
import com.google.devtools.ksp.processing.SymbolProcessor
import com.google.devtools.ksp.processing.SymbolProcessorEnvironment
import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSClassDeclaration
import com.tschuchort.compiletesting.KotlinCompilation.ExitCode
import com.tschuchort.compiletesting.SourceFile
import java.io.File
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import workbench.ksp.KspResult
import workbench.ksp.compileWithKsp

// The port is right when it writes what the javac processor wrote. src/test/resources/workbench/ksp/l09/ holds
// that output (javac-packing-slip.txt, javac-messages.txt) and how it was made (java-twins.txt).
class PackingSlipProcessorTest {

    private val resources = File("src/test/resources/workbench/ksp/l09")

    // the Kotlin twins of the Java classes in java-twins.txt: the same names, properties and rooms
    private val things = SourceFile.kotlin(
        "Things.kt",
        """
        package movemate

        import workbench.ksp.annotations.Inventory
        import workbench.ksp.annotations.Room

        @Inventory @Room("hall")
        data class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)

        @Inventory @Room("living room")
        data class Lamp(val name: String, val bulbs: Int, val shade: String?)

        @Inventory @Room("study")
        class Bookshelf(val shelves: Int, val books: List<String>)
        """,
    )
    private val plant = SourceFile.kotlin(
        "Plant.kt",
        """
        package movemate

        import workbench.ksp.annotations.Inventory

        @Inventory
        data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)
        """,
    )

    /** KSP writes a .txt output under resources/, next to the kotlin/ folder the shared helper reads. */
    private fun KspResult.slip(): String {
        val file = result.outputDirectory.parentFile.resolve("ksp/sources/resources/META-INF/movemate/packing-slip.txt")
        assertThat(file).describedAs("the packing slip. Messages:\n$messages").exists()
        return file.readText()
    }

    @Test
    fun `the KSP port writes the javac processor's packing slip, byte for byte`() {
        val run = compileWithKsp(things, plant, processors = listOf(PackingSlipProcessorProvider()), options = mapOf(HOUSEHOLD to "Okafor"))

        assertThat(run.exitCode).isEqualTo(ExitCode.OK)
        assertThat(run.slip()).isEqualTo(resources.resolve("javac-packing-slip.txt").readText())
    }

    @Test
    fun `without the household option the slip is headed MoveMate`() {
        val run = compileWithKsp(plant, processors = listOf(PackingSlipProcessorProvider()))

        assertThat(run.exitCode).isEqualTo(ExitCode.OK)
        assertThat(run.slip()).isEqualTo(
            "# MoveMate packing slip. Generated, do not edit.\n" +
                "Plant [no room]: kind, potLitres, waterEveryDays\n",
        )
    }

    @Test
    fun `an interface gets the javac processor's message, on the declaration's line`() {
        val shape = SourceFile.kotlin(
            "Shape.kt",
            """
            package movemate

            import workbench.ksp.annotations.Inventory

            @Inventory
            interface Shape
            """,
        )

        val run = compileWithKsp(shape, processors = listOf(PackingSlipProcessorProvider()))

        // javac said:  bad/movemate/Shape.java:6: error: @Inventory goes on a class, but Shape is an interface
        val javacText = resources.resolve("javac-messages.txt").readLines().first().substringAfter("error: ")
        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        assertThat(run.messages).containsPattern("""e: \[ksp] \S*/Shape\.kt:6: """ + Regex.escape(javacText))
    }

    @Test
    fun `a Kotlin object, a kind javac never sees, is rejected the same way`() {
        val van = SourceFile.kotlin(
            "Van.kt",
            """
            package movemate

            import workbench.ksp.annotations.Inventory

            @Inventory
            object Van
            """,
        )

        val run = compileWithKsp(van, processors = listOf(PackingSlipProcessorProvider()))

        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        assertThat(run.messages).containsPattern("""e: \[ksp] \S*/Van\.kt:6: @Inventory goes on a class, but Van is an object""")
    }

    @Test
    fun `the slip is an aggregating output from the file of every class on it`() {
        val run = compileWithKsp(things, plant, processors = listOf(SlipDependencySpyProvider()))

        assertThat(run.messages).contains("w: [ksp] aggregating=true allFiles=false files=[Plant.kt, Things.kt]")
    }
}

/** Test helper: finds the @Inventory classes, calls [slipDependencies] and logs what came back. */
class SlipDependencySpyProvider : SymbolProcessorProvider {
    override fun create(environment: SymbolProcessorEnvironment): SymbolProcessor = object : SymbolProcessor {
        override val apiFeatures = com.google.devtools.ksp.buildApiFeatures {
            enableBackingFields = true
            enableContextParameters = true
        }

        override fun process(resolver: Resolver): List<KSAnnotated> {
            val classes = resolver.getSymbolsWithAnnotation("workbench.ksp.annotations.Inventory")
                .filterIsInstance<KSClassDeclaration>().toList()
            if (classes.isNotEmpty()) {
                val d = try {
                    slipDependencies(classes)
                } catch (e: NotImplementedError) {
                    environment.logger.warn("slipDependencies is not done yet: ${e.message}")
                    return emptyList()
                }
                environment.logger.warn(
                    "aggregating=${d.aggregating} allFiles=${d.isAllSources} files=${d.originatingFiles.map { it.fileName }.sorted()}",
                )
            }
            return emptyList()
        }
    }
}
