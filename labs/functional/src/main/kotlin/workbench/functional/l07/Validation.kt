package workbench.functional.l07

import arrow.core.Either
import arrow.core.NonEmptyList
import arrow.core.raise.Raise
import arrow.core.raise.ensure

val SUPPORTED_CURRENCIES = setOf("EUR", "USD", "GBP")

// One function per rule. Each runs inside a Raise<PaymentError> context: ensure(...) { error } raises
// the error when the condition is false, and otherwise the function returns the checked value.

fun Raise<PaymentError>.checkAmount(amountMinor: Long): Long {
    ensure(amountMinor > 0) { PaymentError.InvalidAmount(amountMinor) }
    return amountMinor
}

fun Raise<PaymentError>.checkCurrency(code: String): String {
    ensure(code in SUPPORTED_CURRENCIES) { PaymentError.UnsupportedCurrency(code) }
    return code
}

/** A card number is exactly 16 digits. The error carries only the last four characters, never the full number. */
fun Raise<PaymentError>.checkCardNumber(number: String): String =
    TODO("ensure 16 digits, else InvalidCardNumber(number.takeLast(4))")

/** The reference goes on the cardholder's statement: at most 35 characters. */
fun Raise<PaymentError>.checkReference(reference: String): String =
    TODO("ensure length <= 35, else ReferenceTooLong(reference.length)")

/**
 * Checks all four rules and reports EVERY failure, in the order amount, currency, card number, reference,
 * so the client can fix the whole form in one go. Returns the ValidPayment when all four pass.
 */
fun validate(request: PaymentRequest): Either<NonEmptyList<PaymentError>, ValidPayment> =
    TODO("either { zipOrAccumulate(...) { ... } }")
