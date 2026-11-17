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
 * TODO 4: partial application. Return the jug-to-scale function for [ingredient]: ml * gramsPerLitre / 1000.
 * Look the weight up NOW, once, not on every call. An unknown ingredient is a bug in the recipe:
 * throw IllegalArgumentException("unknown ingredient <ingredient>") here, before anything is weighed.
 */
fun gramsFor(ingredient: String): (Int) -> Int =
    TODO("look up GRAMS_PER_LITRE[ingredient] once, then return a lambda that uses it")

/** TODO 5: what to weigh out for a measured volume: the ingredient's grams, then each step in order. */
fun weighOut(ingredient: String, steps: List<Step>): (Int) -> Int =
    TODO("gramsFor, andThen, pipeline")

/** TODO 6: currying by hand. Turn a two-argument function into a chain of one-argument functions. */
fun <A, B, C> ((A, B) -> C).curried(): (A) -> (B) -> C =
    TODO("a lambda that takes a and returns a lambda that takes b")
