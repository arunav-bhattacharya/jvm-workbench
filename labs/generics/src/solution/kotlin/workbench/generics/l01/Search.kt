package workbench.generics.l01

fun <T> firstMatching(items: Iterable<T>, predicate: (T) -> Boolean): T? {
    for (item in items) {
        if (predicate(item)) return item   // item is a T, so the return type T? fits
    }
    return null
}

fun <T, K> indexBy(items: Iterable<T>, key: (T) -> K): Map<K, T> {
    val index = LinkedHashMap<K, T>()      // both type arguments come from the caller
    for (item in items) {
        index.putIfAbsent(key(item), item) // keep the first item per key
    }
    return index
}
