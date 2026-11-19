package workbench.ksp.l05.demo

import com.tschuchort.compiletesting.KotlinCompilation
import com.tschuchort.compiletesting.SourceFile
import com.tschuchort.compiletesting.configureKsp
import java.io.File
import java.io.OutputStream
import workbench.ksp.l05.BuilderProcessorProvider

// Lesson 5, Try it: a class whose label mentions a type that doesn't exist (yet). Without validate(), KotlinPoet
// throws inside the processor. With validate(), the class is set aside and the compiler reports the user's line.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l05.demo.SetAsideDemoKt
fun main() {
    val parcel = SourceFile.kotlin(
        "Parcel.kt",
        """
        package movemate

        import workbench.ksp.annotations.Builder

        @Builder
        class Parcel(val label: String, val sticker: Sticker)
        """,
    )
    val versions = listOf(
        "without validate(): lesson 4's processor" to provider(::Crashing),
        "with validate(): the lab's processor" to BuilderProcessorProvider(),
    )
    for ((i, version) in versions.withIndex()) {
        val (what, processor) = version
        val compilation = KotlinCompilation().apply {
            workingDir = File("build/kctfork/demo/l05-set-aside-$i").apply { deleteRecursively() }
            sources = listOf(parcel)
            inheritClassPath = true
            jvmTarget = "21"
            messageOutputStream = OutputStream.nullOutputStream()
            configureKsp { symbolProcessorProviders += processor }
        }
        val result = compilation.compile()
        println("=== $what: ${result.exitCode}")
        result.messages.lines()
            .filter { it.startsWith("java.") || it.startsWith("e: ") }
            .filterNot { it.startsWith("e: Error occurred in KSP") }
            .map { it.replace(Regex("file://\\S*/sources/"), "") }
            .take(2)
            .forEach(::println)
    }
}
