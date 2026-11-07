package workbench.startup.l02.demo

import java.nio.file.Files
import java.nio.file.Path
import java.util.jar.JarEntry
import java.util.jar.JarOutputStream
import javax.tools.ToolProvider
import kotlin.io.path.deleteIfExists
import kotlin.io.path.writeText

/**
 * Builds hello.jar printing "version ONE", trains a cache on it, rebuilds the JAR to print
 * "version TWO", and runs the new JAR with the old cache. On JDK 25+ the cache is an AOT cache;
 * on older JDKs it is a dynamic CDS archive. Needs a JDK (it compiles Java source).
 */
private object StaleAnchor

fun main() {
    val classes = Path.of(StaleAnchor::class.java.protectionDomain.codeSource.location.toURI())
    val dir = classes.parent.parent.parent.resolve("boot02-stale-kt")
    Files.createDirectories(dir)
    val jar = dir.resolve("hello.jar")
    val aot = Runtime.version().feature() >= 25
    val cache = dir.resolve(if (aot) "hello.aot" else "hello.jsa")
    cache.deleteIfExists()

    // 1. build version ONE and train a cache on it
    build(dir, jar, "version ONE")
    run(listOf(if (aot) "-XX:AOTCacheOutput=$cache" else "-XX:ArchiveClassesAtExit=$cache"), jar)

    // 2. rebuild the JAR, as a new commit would, but keep the old cache
    build(dir, jar, "version TWO, rebuilt")

    // 3. production: new JAR, old cache
    val flag = if (aot) "-XX:AOTCache=$cache" else "-XX:SharedArchiveFile=$cache"
    println("JDK ${Runtime.version()}: java ${flag.replace("$dir/", "")} -cp hello.jar stale.Hello")
    run(listOf(flag, "-Xlog:class+load"), jar)
        .filter { "stale.Hello source:" in it || it.startsWith("version") || "[warning]" in it || "[error" in it }
        .forEach { println("  " + it.replace("file:$dir/", "file:").replace("$dir/", "")) }
}

/** Compiles a one-class program that prints [message] and packs it into [jar]. */
private fun build(dir: Path, jar: Path, message: String) {
    val src = dir.resolve("src/stale/Hello.java")
    Files.createDirectories(src.parent)
    src.writeText("package stale;\npublic class Hello {\n    public static void main(String[] a) {\n" +
        "        System.out.println(\"$message\");\n    }\n}\n")
    val out = dir.resolve("classes")
    val javac = checkNotNull(ToolProvider.getSystemJavaCompiler()) { "run this on a JDK, not a JRE" }
    check(javac.run(null, null, null, "-d", out.toString(), src.toString()) == 0) { "javac failed" }
    jar.deleteIfExists()
    JarOutputStream(Files.newOutputStream(jar)).use { j ->
        j.putNextEntry(JarEntry("stale/Hello.class"))
        j.write(Files.readAllBytes(out.resolve("stale/Hello.class")))
        j.closeEntry()
    }
}

private fun run(flags: List<String>, jar: Path): List<String> {
    val cmd = listOf(Path.of(System.getProperty("java.home"), "bin", "java").toString()) +
        flags + listOf("-cp", jar.toString(), "stale.Hello")
    val p = ProcessBuilder(cmd).redirectErrorStream(true).start()
    return p.inputReader().readLines().also { p.waitFor() }
}
