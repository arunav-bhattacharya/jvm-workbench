package workbench.memory.l04

import workbench.memory.Jvm

@Volatile
private var humongousSink: Any? = null

/**
 * Allocates 3 MiB "settlement files" in a 1 GB G1 heap, where regions are 1 MB, and prints the
 * region counts G1 logs for the first young pause.
 */
fun main(args: Array<String>) {
    if (args.isNotEmpty()) {
        repeat(40) {
            humongousSink = ByteArray(3 * 1024 * 1024)                 // 3 MiB + a 16-byte header
            repeat(20_000) { humongousSink = ByteArray(200) }          // some ordinary garbage in between
        }
        return
    }
    val firstPause = Regex(""".*GC\(0\) (Pause|.*regions).*""")
    Jvm.lines(listOf("-XX:+UseG1GC", "-Xmx1g", "-Xlog:gc,gc+init,gc+heap=info"), "workbench.memory.l04.HumongousDemoKt", "load")
        .filter { "Heap Region Size" in it || firstPause.matches(it) }
        .forEach { println(it.replace(Regex("\\s+"), " ")) }
}
