package workbench.functional.l07

import arrow.core.Either
import arrow.core.raise.either
import arrow.core.raise.ensure

const val FRAUD_THRESHOLD = 80

fun pay(payment: ValidPayment, gateway: Gateway): Either<PaymentError, Receipt> = either {
    val authCode = gateway.authorize(payment).bind()        // a Left stops the block here
    val score = gateway.riskScore(authCode)
    ensure(score < FRAUD_THRESHOLD) { PaymentError.FraudSuspected(score) }   // raise: stops here
    val captureId = gateway.capture(authCode).bind()
    Receipt(authCode, captureId)                            // reached only if every step succeeded
}
