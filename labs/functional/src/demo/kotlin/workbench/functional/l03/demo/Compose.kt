package workbench.functional.l03.demo

// The stdlib has no andThen for function types, so here it is. Remove it and the file stops compiling.
infix fun <A, B, C> ((A) -> B).andThen(next: (B) -> C): (A) -> C = { a -> next(this(a)) }

val forSixGuests: (Int) -> Int = { it * 6 / 4 }          // the recipe serves four
val tenPercentLess: (Int) -> Int = { it * 90 / 100 }     // less sugar, rounded down
val atMostTheBag: (Int) -> Int = { minOf(it, 250) }      // only 250 g left in the bag

fun main() {
    val sugar = forSixGuests andThen tenPercentLess andThen atMostTheBag
    val capFirst = atMostTheBag andThen forSixGuests andThen tenPercentLess
    for (grams in listOf(100, 200)) {
        println("recipe says $grams g -> ${sugar(grams)} g   (cap first: ${capFirst(grams)} g)")
    }

    // Built from a list, the way a saved set of adjustments would build it.
    val steps = listOf(forSixGuests, tenPercentLess, atMostTheBag)
    val fromList = steps.fold({ x: Int -> x }) { acc, step -> acc andThen step }
    println("fromList(200) = ${fromList(200)}")
}
