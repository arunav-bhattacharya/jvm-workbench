package workbench.bytecode.l02

// Small functions to read with javap: run the demo once so Gradle compiles it,
// then javap -c -p on StackDemoKt.class (top-level functions live in a class named after the file).

/** Card fee in minor units: amount times basis points, divided by 10,000. */
fun feeMinor(amountMinor: Long, bps: Int): Long = amountMinor * bps / 10_000

fun describe(currency: String, amountMinor: Long): String = "$amountMinor $currency"

fun main() {
    val fee = feeMinor(125_000, 290)
    println(describe("EUR", fee))   // 3625 EUR
}
