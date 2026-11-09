package workbench.functional.l03

/** A fee adjustment takes a fee in cents and returns the adjusted fee in cents. */
typealias Adjust = (Long) -> Long

// ---- Building blocks. These are finished: each one is a function that returns a function. ----

/** Adds a flat amount, for example a 25-cent scheme fee. */
fun addFlat(cents: Long): Adjust = { fee -> fee + cents }

/** Takes [percent] off, rounding down. */
fun discountPercent(percent: Int): Adjust = { fee -> fee * (100 - percent) / 100 }

/** Never more than [maxCents]. */
fun capAt(maxCents: Long): Adjust = { fee -> minOf(fee, maxCents) }

/** Never less than [minCents]. */
fun floorAt(minCents: Long): Adjust = { fee -> maxOf(fee, minCents) }

/** Base rates in basis points (1 bp = 0.01 %) per country. */
val BASIS_POINTS: Map<String, Long> = mapOf("NL" to 140, "DE" to 150, "FR" to 160, "US" to 290)

// ---- Solutions ----

// this is the first function; the result feeds next. The stdlib has no andThen for function types.
infix fun <A, B, C> ((A) -> B).andThen(next: (B) -> C): (A) -> C = { a -> next(this(a)) }

// the same, written in math order: (g compose f)(x) == g(f(x))
infix fun <A, B, C> ((B) -> C).compose(first: (A) -> B): (A) -> C = { a -> this(first(a)) }

// fold starts from the identity function and adds one step at a time
fun <T> pipeline(steps: List<(T) -> T>): (T) -> T =
    steps.fold({ x: T -> x }) { acc, step -> acc andThen step }

// The lookup runs once, when the fee function is built. The returned lambda captures only bps.
fun feeFor(country: String): (Long) -> Long {
    val bps = requireNotNull(BASIS_POINTS[country]) { "no rate for $country" }
    return { amountCents -> amountCents * bps / 10_000 }
}

fun merchantFee(country: String, adjustments: List<Adjust>): (Long) -> Long =
    feeFor(country) andThen pipeline(adjustments)

fun <A, B, C> ((A, B) -> C).curried(): (A) -> (B) -> C = { a -> { b -> this(a, b) } }
