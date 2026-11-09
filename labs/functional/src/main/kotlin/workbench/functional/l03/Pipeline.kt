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

// ---- Your part ----

/** TODO 1: `f andThen g` is a function that runs f first, then g on f's result. */
infix fun <A, B, C> ((A) -> B).andThen(next: (B) -> C): (A) -> C =
    TODO("return a lambda that calls this, then next")

/** TODO 2: `g compose f` runs f first, then g. It is `f andThen g` read from right to left. */
infix fun <A, B, C> ((B) -> C).compose(first: (A) -> B): (A) -> C =
    TODO("return a lambda that calls first, then this")

/**
 * TODO 3: chain [steps] left to right into one function. An empty list gives a function that
 * returns its input unchanged.
 */
fun <T> pipeline(steps: List<(T) -> T>): (T) -> T =
    TODO("fold over the steps, starting from the function that returns its input")

/**
 * TODO 4: partial application. Return the base fee function for [country]: amountCents * bps / 10_000.
 * Look the rate up NOW, once, not on every call. An unknown country is a configuration bug:
 * throw IllegalArgumentException("no rate for <country>") here, before any fee is computed.
 */
fun feeFor(country: String): (Long) -> Long =
    TODO("look up BASIS_POINTS[country] once, then return a lambda that uses it")

/** TODO 5: the full fee function for a merchant: the country's base fee, then each adjustment in order. */
fun merchantFee(country: String, adjustments: List<Adjust>): (Long) -> Long =
    TODO("feeFor, andThen, pipeline")

/** TODO 6: currying by hand. Turn a two-argument function into a chain of one-argument functions. */
fun <A, B, C> ((A, B) -> C).curried(): (A) -> (B) -> C =
    TODO("a lambda that takes a and returns a lambda that takes b")
