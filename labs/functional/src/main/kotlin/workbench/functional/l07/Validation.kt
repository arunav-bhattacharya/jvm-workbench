package workbench.functional.l07

import arrow.core.Either
import arrow.core.NonEmptyList
import arrow.core.raise.Raise
import arrow.core.raise.ensure

/** Grams, millilitres and pieces. A scale left on ounces gives UnsupportedUnit("oz"). */
val SUPPORTED_UNITS = setOf("g", "ml", "pcs")

// One function per rule. Each runs inside a Raise<KitchenError> context: ensure(...) { error } raises
// the error when the condition is false, and otherwise the function returns the checked value.

fun Raise<KitchenError>.checkAmount(amount: Int): Int {
    ensure(amount > 0) { KitchenError.InvalidAmount(amount) }
    return amount
}

fun Raise<KitchenError>.checkUnit(unit: String): String {
    ensure(unit in SUPPORTED_UNITS) { KitchenError.UnsupportedUnit(unit) }
    return unit
}

/** A name is not blank and holds only letters and spaces: "strong flour" passes, "fl0ur" does not. */
fun Raise<KitchenError>.checkName(name: String): String =
    TODO("ensure not blank and only letters or spaces, else InvalidName(name)")

/** The note is printed on the shop's packing slip: at most 35 characters. */
fun Raise<KitchenError>.checkNote(note: String): String =
    TODO("ensure length <= 35, else NoteTooLong(note.length)")

/**
 * Checks all four rules and reports EVERY failure, in the order name, amount, unit, note, so the cook
 * can fix the whole line in one go. Returns the Ingredient when all four pass.
 */
fun validate(form: IngredientForm): Either<NonEmptyList<KitchenError>, Ingredient> =
    TODO("either { zipOrAccumulate(...) { ... } }")
