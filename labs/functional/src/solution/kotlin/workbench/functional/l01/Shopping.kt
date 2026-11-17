package workbench.functional.l01

import java.time.Clock
import java.time.LocalDate
import java.util.Collections

/** A bag of something in the cupboard. A plain value: nothing in it can change after it is built. */
data class Bag(
    val sizeGrams: Int,        // the shop sells whole bags of this size
    val leftGrams: Int,        // what is still in the bag at home
    val bestBefore: LocalDate, // the bag still counts on this date, and not after it
)

/** The flour in the cupboard when a test starts. */
val THE_FLOUR_BAG = Bag(sizeGrams = 1_000, leftGrams = 700, bestBefore = LocalDate.of(2026, 3, 31))

/** Global and mutable: whoever cooked last may have used some flour, or put a new bag in. */
object Cupboard {
    @Volatile
    var flour: Bag = THE_FLOUR_BAG
}

/** Every call of flourToBuy writes one line here. In the app, it is the shopping list on the fridge door. */
object ShoppingList {
    val lines: MutableList<String> = Collections.synchronizedList(ArrayList())
}

// The functional core: the result depends only on the three arguments, and the call changes nothing.
fun gramsToBuy(neededGrams: Int, bag: Bag, today: LocalDate): Int {
    val usable = if (today.isAfter(bag.bestBefore)) 0 else bag.leftGrams   // if is an expression
    val missing = maxOf(neededGrams - usable, 0)                            // never below zero
    val bags = (missing + bag.sizeGrams - 1) / bag.sizeGrams                // round up to whole bags
    return bags * bag.sizeGrams
}

// Also pure: it decides WHAT to write. Writing it is the shell's job.
fun shoppingLine(ingredient: String, grams: Int, today: LocalDate): String =
    "$today: buy $grams g $ingredient"

// The imperative shell: gather the inputs, call the core, perform the effect. No decisions left here.
fun flourToBuy(neededGrams: Int, clock: Clock = Clock.systemDefaultZone()): Int {
    val bag = Cupboard.flour                               // 1. read the hidden inputs once
    val today = LocalDate.now(clock)
    val grams = gramsToBuy(neededGrams, bag, today)        // 2. decide, purely
    ShoppingList.lines.add(shoppingLine("flour", grams, today))   // 3. do the effect
    return grams
}
