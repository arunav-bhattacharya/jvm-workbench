package workbench.performance.l02

// Kotlin twin of IntrinsicsDemo.java. The Kotlin standard library calls the same JDK methods,
// so the same intrinsics apply: contentEquals calls Arrays.equals, countOneBits calls Long.bitCount.

fun totalWordsKt(words: LongArray): Long {
    var sum = 0L
    for (w in words) sum = Math.addExact(sum, w)     // throws on overflow instead of wrapping
    return sum
}

fun sameTextKt(a: ByteArray, b: ByteArray) = a.contentEquals(b)

fun stylesOnKt(styleBits: Long) = styleBits.countOneBits()

fun main(args: Array<String>) {
    if (args.firstOrNull() == "child") {
        val words = LongArray(1_000) { 1_999 }       // the word counts of 1,000 documents
        val t1 = ByteArray(64)                      // two texts, as bytes
        val t2 = ByteArray(64)
        var s = 0L
        for (i in 0 until 200_000) {
            s += totalWordsKt(words)
            if (sameTextKt(t1, t2)) s++
            s += stylesOnKt(i.toLong())             // bold, italic, ...: one bit per style
        }
        println("checksum $s")
        return
    }
    val java = ProcessHandle.current().info().command().orElse("java")
    val p = ProcessBuilder(java, "-XX:+UnlockDiagnosticVMOptions", "-XX:+PrintInlining",
        "-cp", System.getProperty("java.class.path"), "workbench.performance.l02.IntrinsicsDemoKt", "child")
        .redirectErrorStream(true).start()
    val seen = sortedSetOf<String>()
    p.inputReader().useLines { lines ->
        lines.filter { "intrinsic" in it }
            .filter { "Math::addExact" in it || "Arrays::equals" in it || "Long::bitCount" in it }
            .mapTo(seen) { it.replaceFirst(Regex("""^\s*@ \d+\s+"""), "") }   // drop the indent and call-site index
    }
    p.waitFor()
    seen.forEach(::println)
}
