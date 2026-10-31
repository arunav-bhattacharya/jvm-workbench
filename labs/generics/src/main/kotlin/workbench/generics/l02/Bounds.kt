package workbench.generics.l02

/**
 * Returns the largest item. Throws IllegalArgumentException when [items] is empty.
 *
 * The bound `T : Comparable<T>` is what lets you write `a > b` on two T values.
 * Write it with a loop and `>`, not with the standard library's max().
 */
fun <T : Comparable<T>> maxOfAll(items: List<T>): T =
    TODO("throw on empty, then keep the biggest item seen so far")

/**
 * Returns the shortest item. When two items have the same length, return the one that
 * compares smaller (its natural order, from Comparable).
 *
 * The where clause gives T two bounds at once, so you can call both `.length` and `<`.
 * Throws IllegalArgumentException when [items] is empty.
 */
fun <T> shortestLabel(items: List<T>): T where T : CharSequence, T : Comparable<T> =
    TODO("compare by length first, then by compareTo")

/**
 * Returns the first value that is not null. Throws IllegalArgumentException when all are null.
 *
 * With `T : Any`, T itself can never be a nullable type, so the return type T really is non-null
 * even though every parameter is a T?.
 */
fun <T : Any> coalesce(vararg values: T?): T =
    TODO("return the first non-null value")
