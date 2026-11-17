package workbench.performance.l01

// Kotlin twin of Hot.java: the same program, so you can compare what the JIT does with Kotlin bytecode.
// Run without arguments: it starts a second JVM with -XX:+PrintCompilation and prints the lines
// about this file's classes. Pass "all" to see every line.

// a document is a list of blocks, and each kind of block knows how long it takes to read
interface KBlock { fun millis(): Long }
class KParagraph(private val words: Long) : KBlock { override fun millis() = words * 250 }       // 4 words a second
class KHeading(private val words: Long) : KBlock { override fun millis() = 1_000 + words * 400 } // a pause, then slower
class KQuote(private val words: Long) : KBlock { override fun millis() = words * 300 }           // a little slower

fun readingMillis(blocks: Array<KBlock>): Long {
    var sum = 0L
    for (b in blocks) sum += b.millis()      // one call site: first only paragraphs, later three types
    return sum
}

fun longLoop(): Long {      // called once, but its loop runs 50 million times, like one pass over a huge book: OSR
    var acc = 0L
    for (i in 0 until 50_000_000) acc += (i xor (i ushr 3))
    return acc
}

fun work() {
    println(longLoop())
    val article = Array<KBlock>(1000) { KParagraph(it.toLong()) }
    var r = 0L
    repeat(20_000) { r += readingMillis(article) }   // only KParagraph seen so far
    val mixed = Array(999) {
        when (it % 3) { 0 -> KParagraph(it.toLong()); 1 -> KHeading(it.toLong()); else -> KQuote(it.toLong()) }
    }
    repeat(20_000) { r += readingMillis(mixed) }     // two new types reach the same call site
    println(r)
}

fun main(args: Array<String>) {
    if (args.firstOrNull() == "child") { work(); return }
    val all = args.firstOrNull() == "all"
    // the same as: java -XX:+PrintCompilation -cp <classpath> workbench.performance.l01.HotKt child
    val java = ProcessHandle.current().info().command().orElse("java")
    val p = ProcessBuilder(java, "-XX:+PrintCompilation", "-cp", System.getProperty("java.class.path"),
        "workbench.performance.l01.HotKt", "child").redirectErrorStream(true).start()
    p.inputReader().useLines { lines ->
        lines.filter { all || it.contains("l01.HotKt") || it.contains("l01.K") || !it.contains("::") }
            .filterNot { it.startsWith("Picked up") }
            .forEach(::println)
    }
    p.waitFor()
}
