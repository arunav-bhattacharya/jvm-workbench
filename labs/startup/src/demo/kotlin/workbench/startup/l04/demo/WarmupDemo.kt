package workbench.startup.l04.demo

import java.nio.file.Path

/**
 * Runs the same work in 10 rounds in a fresh JVM and prints how long each round took. A fresh
 * JVM starts in the interpreter, then the JIT compiles the hot code. Extra arguments are passed
 * to that JVM as flags, for example -Xint (interpreter only) or -XX:TieredStopAtLevel=1 (C1 only).
 */
fun main(args: Array<String>) {
    if (args.firstOrNull() == "--work") {
        work()
        return
    }
    val cmd = listOf(Path.of(System.getProperty("java.home"), "bin", "java").toString()) + args +
        listOf("-cp", System.getProperty("java.class.path"), "workbench.startup.l04.demo.WarmupDemoKt", "--work")
    println("fresh JVM, flags ${args.toList()}")
    ProcessBuilder(cmd).redirectErrorStream(true).inheritIO().start().waitFor()
}

/** Ten rounds of 20,000 check-digit tests on 16-digit tracking numbers, the test every typed-in number gets. */
private fun work() {
    var checksum = 0L
    for (round in 1..10) {
        val t0 = System.nanoTime()
        for (i in 0 until 20_000) {
            val number = "7000" + (1_000_003L * i + round).toString().padStart(12, '0')   // a 16-digit tracking number
            if (checkDigitOk(number)) checksum += i
        }
        val us = (System.nanoTime() - t0) / 1_000
        println("round %2d: %,7d us".format(round, us))
    }
    if (checksum == 42L) println()                      // keeps the JIT from dropping the work
}

/** The Luhn check: the last digit makes the weighted sum a multiple of 10, so most typos show. */
private fun checkDigitOk(number: String): Boolean {
    var sum = 0
    var twice = false
    for (i in number.indices.reversed()) {
        var d = number[i] - '0'
        if (twice) {
            d *= 2
            if (d > 9) d -= 9
        }
        sum += d
        twice = !twice
    }
    return sum % 10 == 0
}
