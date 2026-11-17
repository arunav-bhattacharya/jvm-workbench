package workbench.functional.l03.demo

// Roughly what one litre weighs, in grams. The jug measures millilitres; the scale wants grams.
val WEIGHT_PER_LITRE = mapOf("flour" to 530, "milk" to 1_030, "honey" to 1_420)

// Both arguments at once.
fun grams(ingredient: String, ml: Int): Int = ml * WEIGHT_PER_LITRE.getValue(ingredient) / 1_000

// Partial application: fix the ingredient now, get back a function of the volume.
fun gramsFor(ingredient: String): (Int) -> Int {
    val perLitre = WEIGHT_PER_LITRE.getValue(ingredient)    // looked up once, right here
    return { ml -> ml * perLitre / 1_000 }
}

// Currying by hand: take one argument, return a function that takes the next one.
val curriedGrams: (String) -> (Int) -> Int = { ingredient -> { ml -> grams(ingredient, ml) } }

fun main() {
    val honey = gramsFor("honey")
    println("gramsFor(\"honey\")(250)      = ${honey(250)}")
    println("curriedGrams(\"flour\")(500)  = ${curriedGrams("flour")(500)}")

    // Kotlin idioms that usually read better than a curried signature:
    val milkGrams = { ml: Int -> grams("milk", ml) }                 // a lambda that fixes one argument
    println("lambda that fixes milk      = ${milkGrams(250)}")
    println("named arguments             = ${grams(ml = 250, ingredient = "honey")}")

    val jugs = listOf(100, 250, 1_000)
    println("jugs.map(honey)             = ${jugs.map(honey)}")
}
