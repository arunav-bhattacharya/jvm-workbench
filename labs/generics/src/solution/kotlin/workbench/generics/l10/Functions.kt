package workbench.generics.l10

typealias Handler<E> = (E) -> Unit

// (A) -> C built from (A) -> B and (B) -> C. Variance of Function1 lets callers pass
// a more general `second`, such as (Any) -> String where (Money) -> String is expected.
fun <A, B, C> andThen(first: (A) -> B, second: (B) -> C): (A) -> C = { a -> second(first(a)) }

fun <E> fanOut(handlers: List<Handler<E>>): Handler<E> = { event ->
    for (h in handlers) h(event)
}

fun <T> List<T>.firstNotNullValue(): T & Any {
    for (item in this) if (item != null) return item   // smart cast: a non-null T is T & Any
    throw NoSuchElementException("no non-null element")
}
