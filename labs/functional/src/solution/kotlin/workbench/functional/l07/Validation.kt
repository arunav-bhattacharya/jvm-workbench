package workbench.functional.l07

import arrow.core.Either
import arrow.core.NonEmptyList
import arrow.core.raise.Raise
import arrow.core.raise.either
import arrow.core.raise.ensure
import arrow.core.raise.zipOrAccumulate

/** Grams, millilitres and pieces. A scale left on ounces gives UnsupportedUnit("oz"). */
val SUPPORTED_UNITS = setOf("g", "ml", "pcs")

fun Raise<KitchenError>.checkAmount(amount: Int): Int {
    ensure(amount > 0) { KitchenError.InvalidAmount(amount) }
    return amount
}

fun Raise<KitchenError>.checkUnit(unit: String): String {
    ensure(unit in SUPPORTED_UNITS) { KitchenError.UnsupportedUnit(unit) }
    return unit
}

fun Raise<KitchenError>.checkName(name: String): String {
    ensure(name.isNotBlank() && name.all { it.isLetter() || it == ' ' }) { KitchenError.InvalidName(name) }
    return name
}

fun Raise<KitchenError>.checkNote(note: String): String {
    ensure(note.length <= 35) { KitchenError.NoteTooLong(note.length) }
    return note
}

fun validate(form: IngredientForm): Either<NonEmptyList<KitchenError>, Ingredient> = either {
    // every lambda runs, even after one fails; the errors are collected in order
    zipOrAccumulate(
        { checkName(form.name) },
        { checkAmount(form.amount) },
        { checkUnit(form.unit) },
        { checkNote(form.note) },
    ) { name, amount, unit, note -> Ingredient(name, amount, unit, note) }
}
