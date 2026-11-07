package workbench.events.l01

/**
 * One log line per event, for example `pay_7781 captured 19.99 EUR` or
 * `pay_7781 declined: CARD_EXPIRED`.
 *
 * TODO 5: delete the else branch, compile, and let the compiler list the cases you still need.
 */
fun summary(event: PaymentEvent): String = when (event) {
    is PaymentAuthorized -> "${event.paymentId} authorized ${event.amount} EUR"
    else -> "event ${event.paymentId}"
}
