package workbench.performance.l01

// Kotlin twin of WarmupDemo.java: times the same batch of 20,000 reading-time calculations 12 times in a row.
// No argument: normal tiered JVM. "int": interpreter only (-Xint). "c1": stop at C1 (-XX:TieredStopAtLevel=1).

private val words = LongArray(20_000)       // the word counts of 20,000 documents

// seconds to read a document at 238 words a minute, rounded up
fun readingSeconds(words: Long): Long = (words * 60 + 237) / 238

fun batch(): Long {
    var total = 0L
    for (w in words) total += readingSeconds(w)
    return total
}

fun main(args: Array<String>) {
    when (args.firstOrNull() ?: "tiered") {
        "int" -> return relaunch("-Xint")
        "c1" -> return relaunch("-XX:TieredStopAtLevel=1")
    }
    for (i in words.indices) words[i] = 50 + (i * 7919L) % 25_000
    var check = 0L
    for (round in 1..12) {
        val t0 = System.nanoTime()
        check += batch()
        val micros = (System.nanoTime() - t0) / 1_000
        println("batch %2d: %,6d us".format(round, micros))
    }
    println("(checksum $check)")             // use the result, so the JIT can't drop the work
}

// start a second JVM with extra flags and the same classpath, and show its output
private fun relaunch(flag: String) {
    val java = ProcessHandle.current().info().command().orElse("java")
    println("running with $flag")
    val p = ProcessBuilder(java, flag, "-cp", System.getProperty("java.class.path"),
        "workbench.performance.l01.WarmupDemoKt", "tiered").redirectErrorStream(true).start()
    p.inputReader().useLines { lines -> lines.filterNot { it.startsWith("Picked up") }.forEach(::println) }
    p.waitFor()
}
