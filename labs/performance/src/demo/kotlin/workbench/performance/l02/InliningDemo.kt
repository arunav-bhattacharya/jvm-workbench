package workbench.performance.l02

// Kotlin twin of InliningDemo.java: the same two checks, compiled by kotlinc.
// Run it: a second JVM starts with -XX:+PrintInlining and the demo prints the decisions in refund().

const val MAX_CENTS = 100_000_000L

// the error message is built right here, so its bytecode counts against the inlining budget
fun requireAmountInline(cents: Long): Long {
    if (cents <= 0 || cents > MAX_CENTS) {
        throw IllegalArgumentException("amount must be between 1 and %d cents, got %d".format(MAX_CENTS, cents))
    }
    return cents
}

// same check, but the cold path lives in its own function
fun requireAmountSplit(cents: Long): Long {
    if (cents <= 0 || cents > MAX_CENTS) throw badAmount(cents)
    return cents
}

fun badAmount(cents: Long) =
    IllegalArgumentException("amount must be between 1 and %d cents, got %d".format(MAX_CENTS, cents))

// each check runs on 1 call in 8, so neither call site counts as hot for C2
fun refund(cents: Long, i: Int): Long {
    var r = cents / 2
    if ((i and 7) == 0) r += requireAmountInline(cents)
    if ((i and 7) == 1) r += requireAmountSplit(cents)
    return r
}

fun main(args: Array<String>) {
    if (args.firstOrNull() == "child") {
        var s = 0L
        for (i in 0 until 2_000_000) s += refund(1_000L + (i and 1023), i)
        println("checksum $s")
        return
    }
    val java = ProcessHandle.current().info().command().orElse("java")
    val p = ProcessBuilder(java, "-XX:+UnlockDiagnosticVMOptions", "-XX:+PrintInlining", "-XX:+PrintCompilation",
        "-cp", System.getProperty("java.class.path"), "workbench.performance.l02.InliningDemoKt", "child")
        .redirectErrorStream(true).start()
    p.inputReader().useLines { lines ->
        lines.filter { "InliningDemoKt::refund (" in it || "requireAmount" in it || it.startsWith("checksum") }
            .forEach(::println)
    }
    p.waitFor()
}
