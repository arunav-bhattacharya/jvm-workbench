package workbench.generics.l05.demo

/** Function types: in on the parameter, out on the result. (P) -> R is Function1<in P, out R>. */
fun main() {
    val weighAny: (Fruit) -> Unit = { println("scale: $it, ${it.grams} g") }
    val label: (Fruit) -> String = { "price card for $it" }

    val weighApple: (Apple) -> Unit = weighAny       // takes more general input: fine
    val appleLabel: (Apple) -> Any = label            // in on the left, out on the right: fine
    weighApple(Apple("Gala", 180))
    println(appleLabel(Apple("Fuji", 150)))

    // Wrong move. Uncomment, predict the error, then run.
    // val tooBroad: (Fruit) -> Unit = weighApple
}

/** The sign rule: uncomment ONE member at a time. Which are legal in a type declared `in T`? */
interface SortingBin<in T> {
    fun drop(item: T)                               // in-position: fine
    fun dropAll(items: List<T>)                     // List<out E> inside a parameter: in x out = in, fine
    // fun peek(): T                                // 1
    // fun forEachInside(f: (T) -> Unit)            // 2
    // fun keepIf(p: (T) -> Boolean): SortingBin<T>  // 3
}
