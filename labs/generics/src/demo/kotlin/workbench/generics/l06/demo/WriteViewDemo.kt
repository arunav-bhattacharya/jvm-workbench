package workbench.generics.l06.demo

/** Appends [count] zero-amount placeholders. It only writes Ints, so any list that takes Ints will do. */
fun padWithZeros(target: MutableList<in Int>, count: Int) {
    repeat(count) { target.add(0) }             // writing an Int: fine
    val first: Any? = target.firstOrNull()      // reading compiles, but all you get is Any?
    println("  first is $first")
    // val firstInt: Int = target[0]            // wrong move 1: an in-projection can't promise an Int
}

fun main() {
    val ints = mutableListOf(1_200)
    val numbers = mutableListOf<Number>(2.5)
    val anything = mutableListOf<Any>("EUR")
    padWithZeros(ints, 1)
    padWithZeros(numbers, 2)
    padWithZeros(anything, 2)
    println("ints = $ints, numbers = $numbers, anything = $anything")

    java.util.Collections.fill(numbers, 7)      // the JDK's fill(List<? super T> list, T obj)
    println("after Collections.fill: $numbers")

    // Wrong move 2: a list of Doubles can't take an Int.
    val rates: MutableList<Double> = mutableListOf(0.5)
    // padWithZeros(rates, 1)
}
