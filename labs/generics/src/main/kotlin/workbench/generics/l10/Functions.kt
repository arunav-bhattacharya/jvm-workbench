package workbench.generics.l10

/** A listener for items of type E. A type alias is a new NAME, not a new type: it is still (E) -> Unit. */
typealias Listener<E> = (E) -> Unit

/**
 * A function that runs [first], then feeds its result to [second].
 * Because function types are Function1<in P, out R>, callers can pass a [second] that accepts
 * something more general than B, and use the result as something more general than C.
 */
fun <A, B, C> andThen(first: (A) -> B, second: (B) -> C): (A) -> C =
    TODO("return a lambda: a -> second(first(a))")

/** One listener that calls every listener in [listeners], in order. */
fun <E> fanOut(listeners: List<Listener<E>>): Listener<E> =
    TODO("return a lambda that loops over listeners")

/**
 * The first element that is not null. T may be a nullable type such as String?, so the return
 * type is `T & Any`: "T, but definitely not null". Throws NoSuchElementException("no non-null element")
 * when every element is null (or the list is empty).
 */
fun <T> List<T>.firstNotNullValue(): T & Any =
    TODO("loop, return the first element that is not null")
