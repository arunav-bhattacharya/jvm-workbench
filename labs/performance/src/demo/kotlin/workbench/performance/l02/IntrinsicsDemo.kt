package workbench.performance.l02

// Kotlin twin of IntrinsicsDemo.java. The Kotlin standard library calls the same JDK methods,
// so the same intrinsics apply: contentEquals calls Arrays.equals, countOneBits calls Long.bitCount.

fun totalCentsKt(cents: LongArray): Long {
    var sum = 0L
    for (c in cents) sum = Math.addExact(sum, c)     // throws on overflow instead of wrapping
    return sum
}

fun sameKeyKt(a: ByteArray, b: ByteArray) = a.contentEquals(b)

fun riskFlagsKt(mask: Long) = mask.countOneBits()

fun main(args: Array<String>) {
    if (args.firstOrNull() == "child") {
        val cents = LongArray(1_000) { 1_999 }
        val k1 = ByteArray(64)
        val k2 = ByteArray(64)
        var s = 0L
        for (i in 0 until 200_000) {
            s += totalCentsKt(cents)
            if (sameKeyKt(k1, k2)) s++
            s += riskFlagsKt(i.toLong())
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
