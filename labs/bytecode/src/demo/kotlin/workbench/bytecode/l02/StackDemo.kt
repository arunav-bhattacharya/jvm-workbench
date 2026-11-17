package workbench.bytecode.l02

// Small functions to read with javap: run the demo once so Gradle compiles it,
// then javap -c -p on StackDemoKt.class (top-level functions live in a class named after the file).

/** How long a lighting fade runs: steps of stepMillis milliseconds each, in whole seconds. */
fun seconds(stepMillis: Long, steps: Int): Long = stepMillis * steps / 1_000

fun describe(unit: String, amount: Long): String = "$amount $unit"

fun main() {
    val fade = seconds(32, 12_500)
    println(describe("seconds", fade))   // 400 seconds
}
