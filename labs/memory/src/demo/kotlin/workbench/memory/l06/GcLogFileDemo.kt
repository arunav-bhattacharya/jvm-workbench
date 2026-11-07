package workbench.memory.l06

import workbench.memory.Jvm
import workbench.memory.l04.serviceLoad
import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.createDirectories
import kotlin.io.path.deleteExisting
import kotlin.io.path.name
import kotlin.io.path.fileSize
import kotlin.io.path.listDirectoryEntries
import kotlin.io.path.readLines

/**
 * Runs two seconds of service load in a child JVM that writes its GC log the way a production service
 * should: to rotating files, with timestamps. Then it does the three checks you do first on any GC log.
 */
fun main(args: Array<String>) {
    if (args.isNotEmpty()) {
        serviceLoad(2.0, 0.55)
        return
    }
    val dir = Path.of("build", "gc-logs").createDirectories()        // labs/memory/build/gc-logs under Gradle
    dir.listDirectoryEntries().filter { it.name.startsWith("gc.log") }.forEach { it.deleteExisting() }
    val logging = "-Xlog:gc*:file=${dir.resolve("gc.log")}:time,uptime,level,tags:filecount=3,filesize=200k"
    Jvm.lines(listOf("-XX:+UseG1GC", "-Xmx256m", logging), "workbench.memory.l06.GcLogFileDemoKt", "load")

    // rotated files (gc.log.0, gc.log.1, ...) hold the older lines; gc.log is the current one
    val files = dir.listDirectoryEntries().sortedWith(compareBy({ it.toString().endsWith("gc.log") }, { it.toString() }))
    files.forEach { println("%-12s %,9d bytes".format(it.fileName, it.fileSize())) }
    val lines = files.flatMap { it.readLines() }
    // the three checks: full GCs, evacuation failures, and the heap left after young pauses
    println("Pause Full lines:          ${lines.count { "Pause Full" in it }}")
    println("(Evacuation Failure) lines: ${lines.count { "(Evacuation Failure)" in it }}")
    val young = lines.filter { "[gc " in it && "Pause Young" in it && it.endsWith("ms") }
    if (young.isNotEmpty()) {
        println("first young pause: GC${young.first().substringAfter("] GC")}")
        println("last young pause:  GC${young.last().substringAfter("] GC")}")
    }
    println("logs are in ${dir.toAbsolutePath()}")
}
