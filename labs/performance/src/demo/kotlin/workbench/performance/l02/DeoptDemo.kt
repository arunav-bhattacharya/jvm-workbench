package workbench.performance.l02

// Kotlin twin of DeoptDemo.java: paragraphs only, then a folded block appears, then headings and quotes.
// Run it: a second JVM starts with -XX:+PrintCompilation and -Xlog:deoptimization=debug.

interface KBlock { fun millis(): Long }   // how long one block of a document takes to read
class KParagraph(private val words: Long) : KBlock { override fun millis() = words * 250 }
class KHeading(private val words: Long) : KBlock { override fun millis() = 1_000 + words * 400 }
class KQuote(private val words: Long) : KBlock { override fun millis() = words * 300 }

const val GLANCE_MILLIS = 200L               // a folded block, such as a hidden spoiler, costs only a glance

fun readingMillis(blocks: Array<KBlock>, folded: BooleanArray): Long {
    var total = 0L
    for (i in blocks.indices) {
        val ms = blocks[i].millis()            // call site: which types has it seen?
        if (folded[i]) total += GLANCE_MILLIS  // branch: has it ever been taken?
        else total += ms
    }
    return total
}

private fun work() {
    val n = 1_000
    val blocks = Array<KBlock>(n) { KParagraph(20L + it % 80) }
    val folded = BooleanArray(n)
    var total = 0L

    println("phase 1: paragraphs only")
    repeat(3_000) { total += readingMillis(blocks, folded) }

    println("phase 2: one folded block per document")
    folded[500] = true
    repeat(3_000) { total += readingMillis(blocks, folded) }

    println("phase 3: headings and quotes arrive")
    for (i in 0 until n step 3) blocks[i] = KHeading(6)
    for (i in 1 until n step 3) blocks[i] = KQuote(40)
    repeat(3_000) { total += readingMillis(blocks, folded) }
    println("done, checksum $total")
}

fun main(args: Array<String>) {
    if (args.firstOrNull() == "child") return work()
    val java = ProcessHandle.current().info().command().orElse("java")
    val p = ProcessBuilder(java, "-XX:+PrintCompilation", "-Xlog:deoptimization=debug",
        "-cp", System.getProperty("java.class.path"), "workbench.performance.l02.DeoptDemoKt", "child")
        .redirectErrorStream(true).start()
    p.inputReader().useLines { lines ->
        lines.filter { "DeoptDemoKt::readingMillis" in it || "DeoptDemoKt.readingMillis" in it || it.startsWith("phase") || it.startsWith("done") }
            .map { it.replace(Regex(" pc=.*"), "") }   // drop machine addresses
            .forEach(::println)
    }
    p.waitFor()
}
