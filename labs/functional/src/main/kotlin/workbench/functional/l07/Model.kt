package workbench.functional.l07

import arrow.core.Either

// The types for this lab. You don't need to change this file.

/** Every failure a caller is expected to handle. Bugs and broken machinery stay exceptions. */
sealed interface KitchenError {
    data class InvalidName(val name: String) : KitchenError
    data class InvalidAmount(val amount: Int) : KitchenError
    data class UnsupportedUnit(val unit: String) : KitchenError
    data class NoteTooLong(val length: Int) : KitchenError
    data object OutOfStock : KitchenError
    data class TooLate(val minutes: Int) : KitchenError
    data object ShopClosed : KitchenError
}

/** One ingredient line as the cook typed it into the app: nothing is checked yet. */
data class IngredientForm(val name: String, val amount: Int, val unit: String, val note: String)

/** A line that passed every check. Only validate() creates one. */
data class Ingredient(val name: String, val amount: Int, val unit: String, val note: String)

/** What the shop confirmed: the basket it packed and the delivery slot it booked. */
data class Delivery(val basketId: String, val slotId: String)

/** The grocery shop's app. Expected failures come back as Left values; nothing here throws for an empty shelf. */
interface Shop {
    /** A basket id, or Left(OutOfStock) / Left(ShopClosed). */
    fun reserve(ingredient: Ingredient): Either<KitchenError, String>

    /** How many minutes from now the basket can be at your door. */
    fun deliveryMinutes(basketId: String): Int

    /** A delivery slot id, or Left(ShopClosed). */
    fun book(basketId: String): Either<KitchenError, String>
}
