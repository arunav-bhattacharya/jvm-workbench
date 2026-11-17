package workbench.memory.l05

import workbench.memory.Jvm

private const val UPLOADS = 5_000_000
private const val USERS = 500

private fun boxedTotals(): Long {
    val totals = HashMap<Int, Long>()
    // every sum is a new Long stored in the map: at least 24 bytes per upload, even when the JIT
    // removes the temporary boxes for the key and the size
    for (i in 0 until UPLOADS) totals.merge(i % USERS, 1_000L + i % 9_000) { a, b -> a + b }
    return totals.values.sum()
}

private fun primitiveTotals(): Long {
    val totals = LongArray(USERS)
    for (i in 0 until UPLOADS) totals[i % USERS] += 1_000L + i % 9_000                         // no objects
    return totals.sum()
}

/**
 * Epsilon never frees anything, so a heap of 64 MB is an allocation budget. Two versions of lesson 2's
 * upload report (the bytes each user uploaded) run against that budget, each in its own child JVM.
 */
fun main(args: Array<String>) {
    if (args.isNotEmpty()) {
        val sum = if (args[0] == "boxed") boxedTotals() else primitiveTotals()
        println("finished inside the budget, total $sum")
        return
    }
    val epsilon = listOf("-XX:+UnlockExperimentalVMOptions", "-XX:+UseEpsilonGC", "-Xmx64m")
    for (version in listOf("primitive", "boxed")) {
        println("== $version")
        Jvm.lines(epsilon, "workbench.memory.l05.EpsilonDemoKt", version).forEach(::println)
    }
}
