package workbench.functional.l01.demo

// A global the shopping helper reads. Whoever cooked last, or a test, can change it at any time.
object Cupboard {
    var flourLeft = 700                      // grams still in the bag
}

// Looks harmless. But its answer depends on something that is not in its parameter list.
fun flourMissing(neededGrams: Int): Int = maxOf(neededGrams - Cupboard.flourLeft, 0)

// Two little "tests". The second puts a new bag in the cupboard and never takes it out again.
fun halfBagTest(): String {
    val missing = flourMissing(1_500)
    return if (missing == 800) "pass" else "FAIL (expected 800, got $missing)"
}

fun newBagTest(): String {
    Cupboard.flourLeft = 1_700               // a new 1 kg bag next to the old one
    val missing = flourMissing(1_500)
    return if (missing == 0) "pass" else "FAIL (expected 0, got $missing)"
}

fun main(args: Array<String>) {
    val tests = listOf("halfBag" to ::halfBagTest, "newBag" to ::newBagTest)
    val order = if (args.firstOrNull() == "reverse") tests.reversed() else tests
    for ((name, test) in order) println("$name: ${test()}")
}
