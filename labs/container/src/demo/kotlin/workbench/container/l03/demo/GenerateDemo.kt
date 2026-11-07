package workbench.container.l03.demo

import workbench.container.l03.ContainerException
import workbench.container.l03.RegistryGenerator
import workbench.container.l03.demo.app.DemoApp

// Runs the build-time half of the container on the demo app and prints the class it writes.
class GenPayouts(val statements: GenStatements)
class GenStatements(val payouts: GenPayouts)

fun main() {
    val source = RegistryGenerator.generate("workbench.container.l03.demo.gen", "AppRegistry", DemoApp.COMPONENTS)
    println(source)
    println("%d lines, %d holder classes, %d generated interceptor classes".format(
        source.trimEnd().lines().size,
        source.lines().count { "_Holder {" in it },
        source.lines().count { it.startsWith("    static final class") }))
    try {
        RegistryGenerator.generate("x", "Broken", listOf(GenPayouts::class.java, GenStatements::class.java))
    } catch (e: ContainerException) {
        println("the build fails: ${e.message}")
    }
}
