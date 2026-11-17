package workbench.performance.l02

// Kotlin twin of InliningDemo.java: the same two checks, compiled by kotlinc.
// Run it: a second JVM starts with -XX:+PrintInlining and the demo prints the decisions in summarize().

const val MAX_WORDS = 10_000_000L

// the error message is built right here, so its bytecode counts against the inlining budget
fun requireWordCountInline(words: Long): Long {
    if (words <= 0 || words > MAX_WORDS) {
        throw IllegalArgumentException("word count must be between 1 and %d, got %d".format(MAX_WORDS, words))
    }
    return words
}

// same check, but the cold path lives in its own function
fun requireWordCountSplit(words: Long): Long {
    if (words <= 0 || words > MAX_WORDS) throw badWordCount(words)
    return words
}

fun badWordCount(words: Long) =
    IllegalArgumentException("word count must be between 1 and %d, got %d".format(MAX_WORDS, words))

// a summary is about a tenth of the text; each check runs on 1 call in 8, so neither call site is hot for C2
fun summarize(words: Long, i: Int): Long {
    var r = words / 10
    if ((i and 7) == 0) r += requireWordCountInline(words)
    if ((i and 7) == 1) r += requireWordCountSplit(words)
    return r
}

fun main(args: Array<String>) {
    if (args.firstOrNull() == "child") {
        var s = 0L
        for (i in 0 until 2_000_000) s += summarize(1_000L + (i and 1023), i)
        println("checksum $s")
        return
    }
    val java = ProcessHandle.current().info().command().orElse("java")
    val p = ProcessBuilder(java, "-XX:+UnlockDiagnosticVMOptions", "-XX:+PrintInlining", "-XX:+PrintCompilation",
        "-cp", System.getProperty("java.class.path"), "workbench.performance.l02.InliningDemoKt", "child")
        .redirectErrorStream(true).start()
    p.inputReader().useLines { lines ->
        lines.filter { "InliningDemoKt::summarize (" in it || "requireWordCount" in it || it.startsWith("checksum") }
            .forEach(::println)
    }
    p.waitFor()
}
