package workbench.injector.app.l03

import java.nio.file.Files
import java.nio.file.Path

/**
 * Cold starts, measured: runs WiringProbe in a fresh JVM, [runs] times for each way of wiring the same crew,
 * with -Xlog:class+load, and prints the medians.
 *   ./gradlew :injector:app:demo -Pmain=workbench.injector.app.l03.StartupRaceKt
 */
fun main(args: Array<String>) {
    val runs = args.firstOrNull()?.toInt() ?: 7
    val ways = listOf("generated", "reflection")
    val results = ways.associateWith { mutableListOf<Run>() }
    repeat(runs) { for (way in ways) results.getValue(way) += probe("workbench.injector.app.l03.WiringProbeKt", way) }

    println("$runs cold starts each, medians (a busy machine: compare the two rows, not the numbers with yours)")
    println("%-11s %9s %11s %12s %9s %8s %14s %12s".format(
        "", "create", "first get", "second get", "JVM run", "classes", "proxy classes", "annotations"))
    for (way in ways) {
        val r = results.getValue(way)
        println("%-11s %6.2f ms %8.2f ms %9.3f ms %6d ms %8d %14d %12d".format(way,
            median(r.map { it.createUs }) / 1000.0, median(r.map { it.firstUs }) / 1000.0,
            median(r.map { it.secondUs }) / 1000.0, median(r.map { it.wallMs }),
            median(r.map { it.classes.toLong() }), median(r.map { it.proxyClasses.toLong() }),
            median(r.map { it.annotationClasses.toLong() })))
    }
    Path.of("build/startup-race").toFile().deleteRecursively()
}

/**
 * One cold start: the probe's own timings, the JVM's run time, and what -Xlog:class+load counted: every class,
 * the proxy classes java.lang.reflect.Proxy made while the program ran (package jdk.proxy*), and the
 * annotation classes (the sticky notes) that had to be loaded.
 */
class Run(val createUs: Long, val firstUs: Long, val secondUs: Long, val wallMs: Long,
          val classes: Int, val proxyClasses: Int, val annotationClasses: Int)

fun probe(mainClass: String, way: String): Run {
    val dir = Files.createDirectories(Path.of("build/startup-race"))
    val log = dir.resolve("$way.log").also { Files.deleteIfExists(it) }
    val java = ProcessHandle.current().info().command().orElse("java")
    val command = listOf(java, "-Xlog:class+load:file=$log", "-cp", System.getProperty("java.class.path"), mainClass, way)
    val builder = ProcessBuilder(command).redirectErrorStream(true)
    builder.environment().remove("JAVA_TOOL_OPTIONS")         // keep the child JVM plain
    val started = System.nanoTime()
    val process = builder.start()
    val output = process.inputStream.bufferedReader().readText()
    process.waitFor()
    val wallMs = (System.nanoTime() - started) / 1_000_000
    val line = output.lines().first { it.startsWith("probe ") }
    fun field(name: String) = Regex("$name=(\\d+)").find(line)!!.groupValues[1].toLong()
    val loaded = Files.readAllLines(log).filter { "[class,load]" in it }.map { it.substringAfter("[class,load] ") }
    Files.delete(log)
    return Run(field("create"), field("first"), field("second"), wallMs, loaded.size,
        proxyClasses = loaded.count { it.startsWith("jdk.proxy") },
        annotationClasses = loaded.count { it.startsWith("workbench.injector.annotations.") })
}

fun median(values: List<Long>): Long = values.sorted()[values.size / 2]
