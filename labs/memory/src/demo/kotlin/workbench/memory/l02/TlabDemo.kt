package workbench.memory.l02

import workbench.memory.Jvm

@Volatile
private var tlabSink: Any? = null

/**
 * Allocates 2,000,000 small arrays in a child JVM that logs a TLAB summary at every GC.
 * Each "refills" count is how often a thread went back to eden for a fresh buffer.
 */
fun main(args: Array<String>) {
    if (args.isEmpty()) {
        Jvm.lines(listOf("-Xmx256m", "-Xlog:gc,gc+tlab=debug"), "workbench.memory.l02.TlabDemoKt", "allocate")
            .forEach { println(it.replace(Regex("\\s+"), " ")) }
        return
    }
    repeat(2_000_000) { tlabSink = ByteArray(24) }                 // 16-byte header + 24 bytes = 40 bytes each
    println("allocated 2,000,000 arrays of 40 bytes: 80,000,000 bytes")
}
