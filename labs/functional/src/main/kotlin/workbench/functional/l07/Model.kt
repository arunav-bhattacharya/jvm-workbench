package workbench.functional.l07

import arrow.core.Either

// The types for this lab. You don't need to change this file.

/** Every failure a caller is expected to handle. Bugs and broken infrastructure stay exceptions. */
sealed interface PaymentError {
    data class InvalidAmount(val amountMinor: Long) : PaymentError
    data class UnsupportedCurrency(val code: String) : PaymentError
    data class InvalidCardNumber(val last4: String) : PaymentError
    data class ReferenceTooLong(val length: Int) : PaymentError
    data object CardDeclined : PaymentError
    data class FraudSuspected(val score: Int) : PaymentError
    data object ProviderUnavailable : PaymentError
}

/** What the client sent: nothing is checked yet. */
data class PaymentRequest(val amountMinor: Long, val currency: String, val cardNumber: String, val reference: String)

/** A request that passed every check. Only validate() creates one. */
data class ValidPayment(val amountMinor: Long, val currency: String, val cardNumber: String, val reference: String)

data class Receipt(val authCode: String, val captureId: String)

/** The card gateway. Expected failures come back as Left values; nothing here throws for a decline. */
interface Gateway {
    /** An authorization code, or Left(CardDeclined) / Left(ProviderUnavailable). */
    fun authorize(payment: ValidPayment): Either<PaymentError, String>

    /** The fraud model's score for an authorization, 0 to 100. */
    fun riskScore(authCode: String): Int

    /** A capture id, or Left(ProviderUnavailable). */
    fun capture(authCode: String): Either<PaymentError, String>
}
