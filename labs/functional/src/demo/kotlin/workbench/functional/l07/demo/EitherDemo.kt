package workbench.functional.l07.demo

import arrow.core.Either
import arrow.core.NonEmptyList
import arrow.core.raise.Raise
import arrow.core.raise.either
import arrow.core.raise.ensure
import arrow.core.raise.zipOrAccumulate
import kotlin.coroutines.cancellation.CancellationException

sealed interface FormError {
    data class InvalidAmount(val amount: Int) : FormError
    data class UnsupportedUnit(val unit: String) : FormError
}

data class Amount(val amount: Int, val unit: String)

fun Raise<FormError>.validAmount(a: Int): Int {
    ensure(a > 0) { FormError.InvalidAmount(a) }
    return a
}

fun Raise<FormError>.validUnit(u: String): String {
    ensure(u in setOf("g", "ml", "pcs")) { FormError.UnsupportedUnit(u) }
    return u
}

/** Stops at the first failure: the second check never runs. */
fun failFast(a: Int, u: String): Either<FormError, Amount> = either {
    Amount(validAmount(a), validUnit(u))
}

/** Runs every check and collects every failure. */
fun accumulate(a: Int, u: String): Either<NonEmptyList<FormError>, Amount> = either {
    zipOrAccumulate({ validAmount(a) }, { validUnit(u) }) { amount, unit -> Amount(amount, unit) }
}

fun main() {
    println("fail fast:  ${failFast(-5, "oz")}")
    println("accumulate: ${accumulate(-5, "oz")}")
    println("all good:   ${accumulate(250, "g")}")

    println("Either.catch around code that throws:")
    println("  ${Either.catch { "2OO".toInt() }.mapLeft { it::class.simpleName }}")   // the letter O, twice
    try {
        Either.catch { throw CancellationException("shopping cancelled") }
    } catch (e: CancellationException) {
        println("  CancellationException rethrown, not captured")
    }
}
