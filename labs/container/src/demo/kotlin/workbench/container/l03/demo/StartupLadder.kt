package workbench.container.l03.demo

import workbench.container.l03.Container
import workbench.container.l03.Interception
import workbench.container.l03.RegistryGenerator
import workbench.container.l03.demo.app.DemoApp
import java.io.File
import java.nio.file.Files
import java.nio.file.Path
import java.util.jar.JarEntry
import java.util.jar.JarOutputStream
import javax.tools.ToolProvider
import kotlin.io.path.createDirectories
import kotlin.io.path.writeText

// Starts the demo app in fresh JVMs, wired by reflection and by a generated registry, and counts
// the classes each start loads. StartupLadder.java adds the AppCDS rows.
private object Ladder

fun main(args: Array<String>) {
    if (args.firstOrNull() == "--reflective") {                       // the child JVM's entry point
        val t0 = System.nanoTime()
        val result = DemoApp.run(Container(DemoApp.COMPONENTS))
        println("ready: %s in %.0f ms".format(result, (System.nanoTime() - t0) / 1e6))
        return
    }
    val out = location(Ladder::class.java).parent.parent.parent.resolve("cap4-kt").createDirectories()   // container/build/cap4-kt
    val jar = buildApp(out)
    val cp = (listOf(jar.toString()) + System.getProperty("java.class.path").split(File.pathSeparator)
        .filter { Path.of(it).fileName.toString().let { n -> n.startsWith("byte-buddy-") || n.startsWith("kotlin-stdlib-") } })
        .joinToString(File.pathSeparator)
    println("%-24s %7s %9s %11s %9s".format("setup", "loaded", "archived", "byte-buddy", "ready ms"))
    for ((name, main) in listOf("reflective + Byte Buddy" to listOf("workbench.container.l03.demo.StartupLadderKt", "--reflective"),
                                "generated registry" to listOf("workbench.container.l03.demo.gen.GeneratedStart"))) {
        val sources = run(listOf("-Xlog:class+load", "-cp", cp) + main)
            .filter { " source: " in it }.map { it.substringAfter(" source: ") }
        val ready = run(listOf("-cp", cp) + main).first { it.startsWith("ready: ") }.substringAfter(" in ").removeSuffix(" ms")
        println("%-24s %7d %9d %11d %9s".format(name, sources.size,
            sources.count { it.startsWith("shared objects file") }, sources.count { "byte-buddy-" in it }, ready))
    }
}

private fun run(args: List<String>): List<String> {
    val cmd = listOf(Path.of(System.getProperty("java.home"), "bin", "java").toString()) + args
    val p = ProcessBuilder(cmd).redirectErrorStream(true).start()
    val lines = p.inputReader().readLines()
    check(p.waitFor() == 0) { "child failed: $cmd\n${lines.joinToString("\n")}" }
    return lines
}

/** The "build": generate the registry, compile it, and pack it with the app into one JAR. */
private fun buildApp(out: Path): Path {
    val src = out.resolve("gen-src/workbench/container/l03/demo/gen").createDirectories()
    src.resolve("AppRegistry.java").writeText(
        RegistryGenerator.generate("workbench.container.l03.demo.gen", "AppRegistry", DemoApp.COMPONENTS))
    src.resolve("GeneratedStart.java").writeText("""
        package workbench.container.l03.demo.gen;

        public final class GeneratedStart {
            public static void main(String[] args) {
                long t0 = System.nanoTime();
                String result = workbench.container.l03.demo.app.DemoApp.run(new AppRegistry());
                System.out.println(String.format("ready: %s in %.0f ms", result, (System.nanoTime() - t0) / 1e6));
            }
        }
        """.trimIndent())
    val classes = out.resolve("gen-classes").createDirectories()
    val status = ToolProvider.getSystemJavaCompiler().run(null, null, null, "--release", "21", "-proc:none",
        "-cp", System.getProperty("java.class.path"), "-d", classes.toString(),
        src.resolve("AppRegistry.java").toString(), src.resolve("GeneratedStart.java").toString())
    check(status == 0) { "javac failed on the generated registry" }
    val jar = out.resolve("app.jar")
    JarOutputStream(Files.newOutputStream(jar)).use { zip ->
        val demoJava = location(DemoApp::class.java)                     // build/classes/java/demo
        add(zip, demoJava, "workbench/container/l03/demo")
        add(zip, location(Ladder::class.java), "workbench/container/l03/demo")   // this file's classes
        add(zip, location(Container::class.java), "workbench/container/l03")
        add(zip, location(Interception::class.java), "workbench/container/l03")
        add(zip, classes, "workbench/container/l03/demo/gen")
    }
    return jar
}

private fun add(zip: JarOutputStream, root: Path, pkg: String) {
    Files.walk(root.resolve(pkg)).use { files ->
        for (f in files.filter { it.toString().endsWith(".class") }.sorted().toList()) {
            val name = root.relativize(f).toString().replace('\\', '/')
            if (pkg == "workbench/container/l03" && "/" in name.removePrefix("$pkg/")) continue   // no subpackages
            zip.putNextEntry(JarEntry(name))
            zip.write(Files.readAllBytes(f))
            zip.closeEntry()
        }
    }
}

private fun location(c: Class<*>): Path = Path.of(c.protectionDomain.codeSource.location.toURI())
