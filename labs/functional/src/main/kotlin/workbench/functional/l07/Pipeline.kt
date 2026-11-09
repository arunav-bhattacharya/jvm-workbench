package workbench.functional.l07

import arrow.core.Either

/** Fraud scores at or above this are refused. */
const val FRAUD_THRESHOLD = 80

/**
 * Authorizes, checks the fraud score, then captures, and stops at the FIRST failure:
 * - a failed authorization is returned as it is, and nothing else is called;
 * - a score of FRAUD_THRESHOLD or more gives FraudSuspected(score), and capture is never called;
 * - a failed capture is returned as it is.
 * On success, returns Receipt(authCode, captureId).
 */
fun pay(payment: ValidPayment, gateway: Gateway): Either<PaymentError, Receipt> =
    TODO("either { ... .bind() ... ensure(...) { ... } ... }")
