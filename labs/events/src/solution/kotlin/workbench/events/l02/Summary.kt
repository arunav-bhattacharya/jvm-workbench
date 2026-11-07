package workbench.events.l02

/**
 * One log line per event. No `else` branch: when someone adds an event type, this function stops
 * compiling until it says what the new event looks like in the log.
 */
fun summary(event: PaymentEvent): String = when (event) {
    is PaymentAuthorized -> "${event.paymentId} authorized ${event.amount} EUR"
    is PaymentDeclined -> "${event.paymentId} declined: ${event.reason}"
    is PaymentCaptured -> "${event.paymentId} captured ${event.amount} EUR"
    is PaymentRefunded -> "${event.paymentId} refunded ${event.amount} EUR"
}
