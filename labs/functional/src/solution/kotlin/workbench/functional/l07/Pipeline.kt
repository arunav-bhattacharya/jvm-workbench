package workbench.functional.l07

import arrow.core.Either
import arrow.core.raise.either
import arrow.core.raise.ensure

const val LATEST_MINUTES = 120

fun order(ingredient: Ingredient, shop: Shop): Either<KitchenError, Delivery> = either {
    val basketId = shop.reserve(ingredient).bind()           // a Left stops the block here
    val minutes = shop.deliveryMinutes(basketId)
    ensure(minutes < LATEST_MINUTES) { KitchenError.TooLate(minutes) }   // raise: stops here
    val slotId = shop.book(basketId).bind()
    Delivery(basketId, slotId)                               // reached only if every step succeeded
}
