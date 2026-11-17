package workbench.functional.l03

/** A step takes an amount in grams and returns the adjusted amount in grams. */
typealias Step = (Int) -> Int

// ---- Building blocks. These are finished: each one is a function that returns a function. ----

/** Adds a fixed amount, for example 20 g of flour to dust the table. */
fun add(grams: Int): Step = { g -> g + grams }

/** Takes [percent] off, rounding down. Plenty of cooks use 10 % less sugar than the recipe says. */
fun percentLess(percent: Int): Step = { g -> g * (100 - percent) / 100 }

/** Never more than [maxGrams], for example what is left in the bag. */
fun atMost(maxGrams: Int): Step = { g -> minOf(g, maxGrams) }

/** Never less than [minGrams]. */
fun atLeast(minGrams: Int): Step = { g -> maxOf(g, minGrams) }

/** Roughly what one litre of each ingredient weighs, in grams. The jug gives millilitres; the scale wants grams. */
val GRAMS_PER_LITRE: Map<String, Int> =
    mapOf("water" to 1_000, "milk" to 1_030, "flour" to 530, "sugar" to 850, "honey" to 1_420)

// ---- Solutions ----

// this is the first function; the result feeds next. The stdlib has no andThen for function types.
infix fun <A, B, C> ((A) -> B).andThen(next: (B) -> C): (A) -> C = { a -> next(this(a)) }

// the same, written in math order: (g compose f)(x) == g(f(x))
infix fun <A, B, C> ((B) -> C).compose(first: (A) -> B): (A) -> C = { a -> this(first(a)) }

// fold starts from the identity function and adds one step at a time
fun <T> pipeline(steps: List<(T) -> T>): (T) -> T =
    steps.fold({ x: T -> x }) { acc, step -> acc andThen step }

// The lookup runs once, when the function is built. The returned lambda captures only perLitre.
fun gramsFor(ingredient: String): (Int) -> Int {
    val perLitre = requireNotNull(GRAMS_PER_LITRE[ingredient]) { "unknown ingredient $ingredient" }
    return { ml -> ml * perLitre / 1_000 }
}

fun weighOut(ingredient: String, steps: List<Step>): (Int) -> Int =
    gramsFor(ingredient) andThen pipeline(steps)

fun <A, B, C> ((A, B) -> C).curried(): (A) -> (B) -> C = { a -> { b -> this(a, b) } }
