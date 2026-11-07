package workbench.generics.l06.demo

/** Totals any mutable list of numbers. It only reads, so it asks for an out-projection. */
fun total(amounts: MutableList<out Number>): Double {
    var sum = 0.0
    for (a in amounts) sum += a.toDouble()      // reads come out as Number
    // amounts.add(0)                           // wrong move 1: no add() through an out-projection
    return sum
}

fun main() {
    val cents: MutableList<Int> = mutableListOf(1_200, 350, 99)
    val rates: MutableList<Double> = mutableListOf(0.5, 1.25)
    println("cents: ${total(cents)}, rates: ${total(rates)}")

    val view: MutableList<out Number> = cents   // the same projection on a variable
    view.removeAt(0)                            // still allowed: removeAt takes an Int, not a T
    println("after removeAt through the view: $cents")

    // Wrong move 2: no projection, so a MutableList<Int> is not a MutableList<Number>.
    // val strict: MutableList<Number> = cents
}
