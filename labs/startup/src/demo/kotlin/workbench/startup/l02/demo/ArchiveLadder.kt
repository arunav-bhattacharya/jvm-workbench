package workbench.startup.l02.demo

import java.nio.file.Files
import java.nio.file.Path
import java.time.LocalDate
import java.util.jar.JarEntry
import java.util.jar.JarOutputStream
import kotlin.io.path.deleteIfExists
import kotlin.io.path.fileSize
import kotlin.io.path.listDirectoryEntries

/**
 * Packs this demo package into build/boot02/app-kt.jar, then starts it under each
 * class-sharing setup: no sharing, the default CDS archive, a dynamic AppCDS archive, and on
 * JDK 25+ the AOT cache. For each it prints classes loaded, classes from an archive, and the
 * median wall time of 3 runs. Timings are noisy; the class counts are the part to trust.
 */
private object Anchor

private data class Payment(val id: String, val amountMinor: Long, val currency: String)

private enum class Status { AUTHORIZED, DECLINED }

fun main(args: Array<String>) {
    if (args.firstOrNull() == "--work") {
        work()
        return
    }
    val classes = Path.of(Anchor::class.java.protectionDomain.codeSource.location.toURI())
    val dir = classes.parent.parent.parent.resolve("boot02")                    // startup/build/boot02
    Files.createDirectories(dir)
    val jar = packJar(classes, dir.resolve("app-kt.jar"))                       // CDS wants JARs, not directories
    val stdlib = Path.of(KotlinVersion::class.java.protectionDomain.codeSource.location.toURI())
    val classPath = listOf(jar, stdlib).joinToString(java.io.File.pathSeparator)
    val app = listOf("-cp", classPath, "workbench.startup.l02.demo.ArchiveLadderKt", "--work")
    println("JDK ${Runtime.version()}, app $jar (+ kotlin-stdlib)")
    println("%-20s %8s %13s %10s".format("setup", "loaded", "from archive", "wall ms"))

    row("no sharing", listOf("-Xshare:off"), app)
    row("default CDS", emptyList(), app)

    val jsa = dir.resolve("app-kt.jsa")                       // 1. training run: archive written at exit
    jsa.deleteIfExists()
    run(listOf("-XX:ArchiveClassesAtExit=$jsa"), app)
    row("AppCDS (dynamic)", listOf("-XX:SharedArchiveFile=$jsa"), app)

    if (Runtime.version().feature() >= 25) {
        val aot = dir.resolve("app-kt.aot")                   // 2. JEP 514: train and assemble in one command
        aot.deleteIfExists()
        run(listOf("-XX:AOTCacheOutput=$aot"), app)
        row("AOT cache", listOf("-XX:AOTCache=$aot"), app)
        println("archive sizes: app-kt.jsa %,d bytes, app-kt.aot %,d bytes".format(jsa.fileSize(), aot.fileSize()))
    } else {
        println("archive size: app-kt.jsa %,d bytes. Run on JDK 25+ to add the AOT cache row.".format(jsa.fileSize()))
    }
}

/** One line of the table: one logged run for the class counts, three quiet runs for the time. */
private fun row(name: String, flags: List<String>, app: List<String>) {
    val lines = run(flags + "-Xlog:class+load", app)
    val loaded = lines.count { " source: " in it }
    val shared = lines.count { it.endsWith("source: shared objects file") }
    val ms = List(3) {
        val t0 = System.nanoTime()
        run(flags, app)
        (System.nanoTime() - t0) / 1_000_000
    }.sorted()
    println("%-20s %8d %13d %10d".format(name, loaded, shared, ms[1]))
}

/** Runs a child JVM with these flags and returns its output lines. */
private fun run(flags: List<String>, app: List<String>): List<String> {
    val cmd = listOf(Path.of(System.getProperty("java.home"), "bin", "java").toString()) + flags + app
    val p = ProcessBuilder(cmd).redirectErrorStream(true).start()
    val out = p.inputReader().readLines()
    check(p.waitFor() == 0) { "child failed: $cmd\n${out.joinToString("\n")}" }
    return out
}

/** Puts every class file of this package into a JAR. */
private fun packJar(classes: Path, jar: Path): Path {
    JarOutputStream(Files.newOutputStream(jar)).use { out ->
        for (f in classes.resolve("workbench/startup/l02/demo").listDirectoryEntries("*.class").sorted()) {
            out.putNextEntry(JarEntry(classes.relativize(f).toString().replace('\\', '/')))
            out.write(Files.readAllBytes(f))
            out.closeEntry()
        }
    }
    return jar
}

/** The "service" being started: a few classes, lambdas, regex, java.time and formatting. */
private fun work() {
    val line = Regex("""(\w+);(\d+);([A-Z]{3})""")
    val payments = listOf("p1;1250;EUR", "p2;990;EUR", "p3;150000;USD", "p4;20;GBP")
        .mapNotNull { line.matchEntire(it)?.destructured }
        .map { (id, amount, currency) -> Payment(id, amount.toLong(), currency) }
    val withinLimit: (Payment) -> Boolean = { it.amountMinor <= 100_000 }
    val byStatus = payments
        .groupBy({ if (withinLimit(it)) Status.AUTHORIZED else Status.DECLINED }, { it.id })
        .toSortedMap()
    val report = "%s %s".format(LocalDate.of(2026, 3, 2), byStatus)
    check(report.isNotEmpty())
}
