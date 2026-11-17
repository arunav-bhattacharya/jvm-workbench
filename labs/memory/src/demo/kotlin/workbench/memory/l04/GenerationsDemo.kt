package workbench.memory.l04

import workbench.memory.Jvm

/**
 * Runs the service load for one second with G1's age table logged, and prints the first four young
 * collections: how much of the heap each one freed, how old the survivors are, the age at which G1
 * promotes them (the tenuring threshold), and how many old regions they fill.
 */
fun main(args: Array<String>) {
    if (args.isNotEmpty()) {
        serviceLoad(1.0, 0.30)
        return
    }
    val firstFour = Regex(""".*GC\([0-3]\) (Pause Young|- age|Desired survivor|Old regions).*""")
    val flags = listOf("-XX:+UseG1GC", "-Xmx256m", "-Xlog:gc,gc+age=trace,gc+heap=info")
    Jvm.lines(flags, "workbench.memory.l04.GenerationsDemoKt", "load")
        .filter { firstFour.matches(it) }
        .forEach { println(it.replace(Regex("\\s+"), " ")) }
}
