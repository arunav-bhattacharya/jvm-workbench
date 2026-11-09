package workbench.functional.l03

import java.util.concurrent.ConcurrentHashMap

// The cache lives in the closure: one map per call of memoize, invisible to everyone else.
// ConcurrentHashMap.computeIfAbsent runs f at most once per key, even when threads race.
// It can't store null, which is why A and R are bounded by Any.
fun <A : Any, R : Any> memoize(f: (A) -> R): (A) -> R {
    val cache = ConcurrentHashMap<A, R>()
    return { a -> cache.computeIfAbsent(a) { f(it) } }
}
