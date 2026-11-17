package workbench.functional.l07

import arrow.core.Either

/** A delivery that takes this many minutes or more arrives after the guests: refuse it. */
const val LATEST_MINUTES = 120

/**
 * Reserves the ingredient at the shop, checks the delivery time, then books the delivery, and stops
 * at the FIRST failure:
 * - a failed reservation is returned as it is, and nothing else is called;
 * - LATEST_MINUTES or more gives TooLate(minutes), and book is never called;
 * - a failed booking is returned as it is.
 * On success, returns Delivery(basketId, slotId).
 */
fun order(ingredient: Ingredient, shop: Shop): Either<KitchenError, Delivery> =
    TODO("either { ... .bind() ... ensure(...) { ... } ... }")
