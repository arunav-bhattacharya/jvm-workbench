package workbench.generics.l05.demo

/** Copy from a producer into a consumer: `from` only gives T, `to` only takes T. */
fun <T> copyInto(from: List<T>, to: MutableList<in T>) {   // List is already out; MutableList gets a use-site in
    for (x in from) to.add(x)
}

fun main() {
    val amounts: List<Int> = listOf(1_200, 350)
    val numbers: MutableList<Number> = mutableListOf(2.5)
    val anything: MutableList<Any> = mutableListOf("EUR")

    copyInto(amounts, numbers)        // T = Int; a MutableList<Number> accepts Ints
    copyInto(amounts, anything)
    println("numbers = $numbers, anything = $anything")

    // Wrong move. Uncomment, predict the error, then run.
    // copyInto(numbers, mutableListOf<Int>())
}
