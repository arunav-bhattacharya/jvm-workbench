package workbench.functional.l03

/**
 * TODO 7: return a function that gives the same answers as [f], but calls [f] at most once per
 * distinct argument and remembers the result. Every memoized function has its own cache.
 *
 * Only memoize pure functions: a remembered answer is only right if f would have returned it again.
 * Several threads may call the result, so pick a map that is safe for that.
 */
fun <A : Any, R : Any> memoize(f: (A) -> R): (A) -> R =
    TODO("a map captured by the returned lambda")
