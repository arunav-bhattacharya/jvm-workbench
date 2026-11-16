package workbench.generics.l04

/**
 * Hands out items one at a time, in order, like the apple dispenser by the shop door.
 * It is a producer: values of T only come out of it.
 *
 * TODO 1: make Dispenser covariant, so a Dispenser<Apple> can be used where a Dispenser<Fruit> is
 * expected. Add `out` to the type parameter. The compiler will then reject `lastServed`, even though
 * its setter is private. Read the error, then fix it so that callers can still read `lastServed`.
 *
 * TODO 2: write hasNext and next.
 */
class Dispenser<T>(items: List<T>) {
    private val queue = ArrayDeque(items)   // private members are exempt from the variance check

    /** The item most recently returned by next(), or null before the first call. Read-only for callers. */
    var lastServed: T? = null
        private set

    /** True while there are items left. */
    fun hasNext(): Boolean = TODO("are there items left in the queue?")

    /** Removes and returns the next item, and remembers it in lastServed. Throws NoSuchElementException when empty. */
    fun next(): T = TODO("take the first item from the queue and remember it")
}

/**
 * Returns the next item, or [fallback] when the dispenser is empty.
 * This is an extension on purpose: as a member of Dispenser<out T>, a parameter of type T would be an
 * in-position. Here T belongs to the function, so it is free.
 */
fun <T> Dispenser<T>.nextOr(fallback: T): T = TODO("next() if there is one, else fallback")

/** Takes every remaining item out of [dispenser], in order. */
fun drainAll(dispenser: Dispenser<Fruit>): List<Fruit> = TODO("call next() until hasNext() is false")

/** The total weight in grams of every remaining piece of fruit. Empties the dispenser. */
fun totalGrams(dispenser: Dispenser<Fruit>): Int = TODO("drain and add up the grams")
