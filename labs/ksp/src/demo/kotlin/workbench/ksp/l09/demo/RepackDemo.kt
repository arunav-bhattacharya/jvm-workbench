package workbench.ksp.l09.demo

import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.processing.Dependencies
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

// A helper who tries to repack a box: this processor wants to give Lamp a member function, so it writes Lamp
// again, with the function inside. KSP lets it write the file; the Kotlin compiler then meets two Lamps.
// The second compile does the job the KSP way: a new file with an extension function, next to Lamp.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l09.demo.RepackDemoKt
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
    val repack = "data class Lamp(val name: String, val bulbs: Int, val shade: String?) {\n" +
        "    fun inventoryCard(): String = \"Lamp: name=\$name, bulbs=\$bulbs, shade=\$shade\"\n}\n"
    val extension = "fun Lamp.inventoryCard(): String = \"Lamp: name=\$name, bulbs=\$bulbs, shade=\$shade\"\n"

    for ((label, body) in listOf("repack Lamp itself" to repack, "add a new card next to it" to extension)) {
        val compilation = KotlinCompilation().apply {
            workingDir = File("build/kctfork/demo/l09-repack").apply { deleteRecursively() }
            sources = listOf(lamp)
            inheritClassPath = true
            jvmTarget = "21"
            messageOutputStream = OutputStream.nullOutputStream()
            configureKsp { symbolProcessorProviders += writer(body) }
        }
        val result = compilation.compile()
        println("=== $label: ${result.exitCode}")
        result.messages.lines().dropWhile { !it.startsWith("e: ") }.filter { it.isNotBlank() }
            .forEach { println(it.replace(Regex("file://\\S*/"), "")) } // the folder is a temporary one
        if (result.exitCode == KotlinCompilation.ExitCode.OK) {
            val lampClass = result.classLoader.loadClass("movemate.Lamp")
            val desk = lampClass.getConstructor(String::class.java, Int::class.java, String::class.java).newInstance("desk lamp", 1, null)
            println("desk.inventoryCard() returns: " + result.classLoader.loadClass("movemate.LampExtraKt").getMethod("inventoryCard", lampClass).invoke(null, desk))
        }
    }
}

/** A processor that writes `body` into movemate/LampExtra.kt, once. */
private fun writer(body: String) = SymbolProcessorProvider { env ->
    object : SymbolProcessor {
        override val apiFeatures = buildApiFeatures {
            enableBackingFields = true
            enableContextParameters = true
        }
        var written = false

        override fun process(resolver: Resolver): List<KSAnnotated> {
            if (written) return emptyList()
            val lamp = resolver.getSymbolsWithAnnotation("workbench.ksp.annotations.Inventory").first() as KSClassDeclaration
            env.codeGenerator.createNewFile(Dependencies(false, lamp.containingFile!!), "movemate", "LampExtra")
                .use { it.write("package movemate\n\n$body".toByteArray()) }
            written = true
            return emptyList()
        }
    }
}
