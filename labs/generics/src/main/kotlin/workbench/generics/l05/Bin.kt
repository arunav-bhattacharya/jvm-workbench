package workbench.generics.l05

/**
 * Something you only drop items into: the compost bin, the pot for apple sauce, a paper bag at the till.
 * It is a consumer: items go in, and nothing typed T ever comes back out.
 *
 * TODO 1: make Bin contravariant, so a Bin<Fruit> can be used where a Bin<Apple> is expected.
 * Add `in` to the type parameter.
 */
interface Bin<T> {
    fun drop(item: T)
}

/**
 * A Bin that remembers everything dropped into it, in order. The class itself stays invariant:
 * it hands its items back out through [items], so its own T is both in and out.
 */
class CollectingBin<T> : Bin<T> {
    /** Everything dropped in so far, oldest first. */
    val items: List<T>
        get() = TODO("return a copy of what was dropped in")

    override fun drop(item: T) {
        TODO("remember the item")
    }
}

/** Drops every fruit into [bin], in order, and returns how many were dropped. */
fun dropAll(fruit: List<Fruit>, bin: Bin<Fruit>): Int =
    TODO("call bin.drop for each fruit")
