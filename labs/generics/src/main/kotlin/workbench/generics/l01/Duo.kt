package workbench.generics.l01

/** Two values of possibly different types. A small cousin of kotlin.Pair. */
data class Duo<A, B>(val first: A, val second: B) {

    /** Returns a Duo with the two values swapped. Look at the return type: Duo<B, A>. */
    fun swap(): Duo<B, A> = TODO("swap first and second")

    /**
     * Applies [f] to [second] and keeps [first].
     * C is a new type parameter that belongs to this function only: the caller's lambda decides it.
     */
    fun <C> mapSecond(f: (B) -> C): Duo<A, C> = TODO("keep first, transform second")
}

/**
 * Pairs up items by position: zipToDuos(listOf(1, 2), listOf("a", "b")) is [Duo(1, "a"), Duo(2, "b")].
 * Stops at the end of the shorter list.
 */
fun <A, B> zipToDuos(left: List<A>, right: List<B>): List<Duo<A, B>> =
    TODO("walk both lists by index up to the shorter size")
