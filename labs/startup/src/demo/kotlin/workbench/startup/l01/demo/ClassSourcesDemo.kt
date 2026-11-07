package workbench.startup.l01.demo

import java.nio.file.Path
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.TreeMap

/**
 * Starts a second JVM with -Xlog:class+load, runs a little start-up work in it, and counts
 * where each loaded class came from. Extra arguments are passed to that JVM as flags.
 */
fun main(args: Array<String>) {
    if (args.firstOrNull() == "--work") {
        work()
        return
    }
    val cmd = buildList {
        add(Path.of(System.getProperty("java.home"), "bin", "java").toString())
        addAll(args)                                     // e.g. -Xshare:off
        addAll(listOf("-Xlog:class+load", "-cp", System.getProperty("java.class.path"),
            "workbench.startup.l01.demo.ClassSourcesDemoKt", "--work"))
    }
    val child = ProcessBuilder(cmd).redirectErrorStream(true).start()
    val bySource = TreeMap<String, Int>()
    child.inputReader().useLines { lines ->
        lines.filter { " source: " in it }.forEach { bySource.merge(bucket(it), 1, Int::plus) }
    }
    child.waitFor()
    println("JDK ${Runtime.version()}, flags ${args.toList()}: %,d classes loaded".format(bySource.values.sum()))
    bySource.forEach { (source, n) -> println("%7d  %s".format(n, source)) }
}

/** Groups the "source:" field of a class+load line into a few buckets. */
private fun bucket(line: String): String {
    val source = line.substringAfter(" source: ")
    return when {
        source == "shared objects file" -> "shared objects file (the CDS archive)"
        source.startsWith("jrt:/") -> "jrt:/ (the JDK's modules file, parsed now)"
        source.startsWith("file:") -> "file: (your classes and JARs, kotlin-stdlib too)"
        else -> "other (hidden classes: lambdas, method handles)"
    }
}

/** A small taste of what services do at start-up: config, regex, dates, collections, lambdas. */
private fun work() {
    val line = Regex("""(\w+(?:\.\w+)*)\s*=\s*(.*)""")
    val config = listOf("issuer.url = https://issuer.example", "pool.size = 20", "timeout.ms = 120")
        .mapNotNull { line.matchEntire(it)?.destructured }
        .associate { (key, value) -> key to value }
        .toSortedMap()
    val today = LocalDate.of(2026, 1, 15).format(DateTimeFormatter.ISO_LOCAL_DATE)
    val summary = config.entries.joinToString(", ") { (k, v) -> "%s=%s".format(k, v) }
    check(summary.isNotEmpty() && today.isNotEmpty())
}
