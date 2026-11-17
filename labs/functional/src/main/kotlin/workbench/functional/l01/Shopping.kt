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

/**
 * The shopping rule as a pure function. Everything it needs arrives as an argument.
 *
 * - What is left in [bag] counts only up to and including its best-before date. After that, it counts as nothing.
 * - What is missing is [neededGrams] minus what counts, and never less than 0.
 * - The shop sells whole bags, so round what is missing UP to whole bags of bag.sizeGrams each.
 *
 * TODO 1: write it. Do not read Cupboard, the clock or ShoppingList. Try it with `val`s and one `if`
 * expression, and no `var`.
 */
fun gramsToBuy(neededGrams: Int, bag: Bag, today: LocalDate): Int =
    TODO("what counts, what is missing, rounded up to whole bags")

/**
 * The shopping-list line for one call, built as a value. The shell writes it; this function only makes the text.
 * Format: "2026-03-02: buy 1000 g flour" (use the LocalDate's own toString for the date).
 *
 * TODO 2: write it.
 */
fun shoppingLine(ingredient: String, grams: Int, today: LocalDate): String =
    TODO("one string template")

/**
 * The original, impure helper. It reads the calendar and the global cupboard, does the arithmetic,
 * and writes the shopping list. Someone already added the Clock parameter so it could be tested at all.
 *
 * Its three tests pass already. They pin its behaviour, so your refactor can't change it by accident.
 *
 * TODO 3: once gramsToBuy and shoppingLine work, turn this into a thin shell: read the cupboard and the
 * date, call gramsToBuy, add shoppingLine(...) to the list, return the grams. No arithmetic stays here.
 */
fun flourToBuy(neededGrams: Int, clock: Clock = Clock.systemDefaultZone()): Int {
    val bag = Cupboard.flour                                  // a global: whoever cooked last may have changed it
    val today = LocalDate.now(clock)                          // the calendar
    val usable = if (today.isAfter(bag.bestBefore)) 0 else bag.leftGrams
    val missing = maxOf(neededGrams - usable, 0)
    val toBuy = (missing + bag.sizeGrams - 1) / bag.sizeGrams * bag.sizeGrams   // whole bags only
    ShoppingList.lines.add("$today: buy $toBuy g flour")      // writes to the list on the fridge
    return toBuy
}
