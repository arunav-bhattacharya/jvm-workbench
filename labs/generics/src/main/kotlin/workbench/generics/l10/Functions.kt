package workbench.generics.l10

/** A handler of events of type E. A type alias is a new NAME, not a new type: it is still (E) -> Unit. */
typealias Handler<E> = (E) -> Unit

/**
 * A function that runs [first], then feeds its result to [second].
 * Because function types are Function1<in P, out R>, callers can pass a [second] that accepts
 * something more general than B, and use the result as something more general than C.
 */
fun <A, B, C> andThen(first: (A) -> B, second: (B) -> C): (A) -> C =
    TODO("return a lambda: a -> second(first(a))")

/** One handler that calls every handler in [handlers], in order. */
fun <E> fanOut(handlers: List<Handler<E>>): Handler<E> =
    TODO("return a lambda that loops over handlers")

/**
 * The first element that is not null. T may be a nullable type such as String?, so the return
 * type is `T & Any`: "T, but definitely not null". Throws NoSuchElementException("no non-null element")
 * when every element is null (or the list is empty).
 */
fun <T> List<T>.firstNotNullValue(): T & Any =
    TODO("loop, return the first element that is not null")
