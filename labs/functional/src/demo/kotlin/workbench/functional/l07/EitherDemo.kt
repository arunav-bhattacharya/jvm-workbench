package workbench.functional.l07

import arrow.core.Either
import arrow.core.NonEmptyList
import arrow.core.raise.Raise
import arrow.core.raise.either
import arrow.core.raise.ensure
import arrow.core.raise.zipOrAccumulate
import kotlin.coroutines.cancellation.CancellationException

sealed interface FormError {
    data class InvalidAmount(val amountMinor: Long) : FormError
    data class UnsupportedCurrency(val code: String) : FormError
}

data class Amount(val minor: Long, val currency: String)

fun Raise<FormError>.validAmount(a: Long): Long {
    ensure(a > 0) { FormError.InvalidAmount(a) }
    return a
}

fun Raise<FormError>.validCurrency(c: String): String {
    ensure(c in setOf("EUR", "USD", "GBP")) { FormError.UnsupportedCurrency(c) }
    return c
}

/** Stops at the first failure: the second check never runs. */
fun failFast(a: Long, c: String): Either<FormError, Amount> = either {
    Amount(validAmount(a), validCurrency(c))
}

/** Runs every check and collects every failure. */
fun accumulate(a: Long, c: String): Either<NonEmptyList<FormError>, Amount> = either {
    zipOrAccumulate({ validAmount(a) }, { validCurrency(c) }) { amount, currency -> Amount(amount, currency) }
}

fun main() {
    println("fail fast:  ${failFast(-5, "XYZ")}")
    println("accumulate: ${accumulate(-5, "XYZ")}")
    println("all good:   ${accumulate(4_250, "EUR")}")

    println("Either.catch around foreign code:")
    println("  ${Either.catch { "12x".toLong() }.mapLeft { it::class.simpleName }}")
    try {
        Either.catch { throw CancellationException("job cancelled") }
    } catch (e: CancellationException) {
        println("  CancellationException rethrown, not captured")
    }
}
