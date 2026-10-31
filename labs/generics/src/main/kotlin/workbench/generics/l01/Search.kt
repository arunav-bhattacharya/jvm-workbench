package workbench.generics.l01

/** Returns the first item for which [predicate] is true, or null if nothing matches. */
fun <T> firstMatching(items: Iterable<T>, predicate: (T) -> Boolean): T? =
    TODO("loop over items and return the first match")

/**
 * Indexes [items] by [key]. When two items have the same key, keep the FIRST one.
 * Two type parameters: T is the item type, K is the key type. The caller picks both.
 */
fun <T, K> indexBy(items: Iterable<T>, key: (T) -> K): Map<K, T> =
    TODO("build a map from key(item) to item, keeping the first item per key")
