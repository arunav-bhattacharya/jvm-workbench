package workbench.generics.l02

fun <T : Comparable<T>> maxOfAll(items: List<T>): T {
    require(items.isNotEmpty()) { "maxOfAll of an empty list" }
    var best = items[0]
    for (item in items) {
        if (item > best) best = item   // > is compareTo, available because of the bound
    }
    return best
}

fun <T> shortestLabel(items: List<T>): T where T : CharSequence, T : Comparable<T> {
    require(items.isNotEmpty()) { "shortestLabel of an empty list" }
    var best = items[0]
    for (item in items) {
        // .length comes from the CharSequence bound, < from the Comparable bound
        if (item.length < best.length || (item.length == best.length && item < best)) best = item
    }
    return best
}

fun <T : Any> coalesce(vararg values: T?): T {
    for (value in values) {
        if (value != null) return value   // smart cast: value is a T, and T is never nullable
    }
    throw IllegalArgumentException("all values were null")
}
