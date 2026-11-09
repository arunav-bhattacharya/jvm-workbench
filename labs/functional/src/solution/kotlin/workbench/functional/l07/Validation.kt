package workbench.functional.l07

import arrow.core.Either
import arrow.core.NonEmptyList
import arrow.core.raise.Raise
import arrow.core.raise.either
import arrow.core.raise.ensure
import arrow.core.raise.zipOrAccumulate

val SUPPORTED_CURRENCIES = setOf("EUR", "USD", "GBP")

fun Raise<PaymentError>.checkAmount(amountMinor: Long): Long {
    ensure(amountMinor > 0) { PaymentError.InvalidAmount(amountMinor) }
    return amountMinor
}

fun Raise<PaymentError>.checkCurrency(code: String): String {
    ensure(code in SUPPORTED_CURRENCIES) { PaymentError.UnsupportedCurrency(code) }
    return code
}

fun Raise<PaymentError>.checkCardNumber(number: String): String {
    ensure(number.length == 16 && number.all { it.isDigit() }) { PaymentError.InvalidCardNumber(number.takeLast(4)) }
    return number
}

fun Raise<PaymentError>.checkReference(reference: String): String {
    ensure(reference.length <= 35) { PaymentError.ReferenceTooLong(reference.length) }
    return reference
}

fun validate(request: PaymentRequest): Either<NonEmptyList<PaymentError>, ValidPayment> = either {
    // every lambda runs, even after one fails; the errors are collected in order
    zipOrAccumulate(
        { checkAmount(request.amountMinor) },
        { checkCurrency(request.currency) },
        { checkCardNumber(request.cardNumber) },
        { checkReference(request.reference) },
    ) { amount, currency, card, reference -> ValidPayment(amount, currency, card, reference) }
}
