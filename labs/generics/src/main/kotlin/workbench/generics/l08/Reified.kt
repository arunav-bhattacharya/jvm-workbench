package workbench.generics.l08

/**
 * This value as a [T], or null if it is not a T.
 *
 * TODO 1: as written, T is erased: inside this function nobody knows what T is, so `this as? T`
 * would compile with an "unchecked cast" warning and never return null. Make the function
 * `inline` and its type parameter `reified`, then write `this as? T`.
 */
fun <T> Any?.asOrNull(): T? = TODO("make it inline with a reified T, then use as?")

/**
 * The elements of [items] that are [T], in their original order.
 *
 * TODO 2: write it with a loop and `is T` (don't call filterIsInstance, that's the answer).
 * Try `is T` first, before adding `inline` and `reified`, and read the error.
 */
fun <T> instancesOf(items: Iterable<*>): List<T> = TODO("inline + reified, then loop and keep the items that are T")
