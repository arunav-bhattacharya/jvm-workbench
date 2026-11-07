package workbench.events.l01

/** What the edge hands to the rest of the service: a valid event, or a reason it was refused. */
sealed interface Parsed {
    data class Ok(val event: PaymentEvent) : Parsed
    data class Rejected(val reason: String) : Parsed
}

/**
 * The edge of the service: turns the raw fields of one message (for example a Kafka record's JSON,
 * already read into a map of strings) into the model. Never throws. Behind this function nothing
 * checks events again, because no invalid PaymentEvent can be built.
 *
 * Fields: `type` (authorized, captured, refunded, declined), `paymentId`, `amountMinor` (whole euro
 * cents, for the first three types) and `reason` (a DeclineReason name, for declined).
 *
 * TODO 4:
 *  - a missing field gives Rejected("missing field '<name>'")
 *  - an amountMinor that isn't a whole number gives Rejected("amountMinor is not a whole number: '<raw>'")
 *  - an unknown type or decline reason gives Rejected naming the bad value
 *  - when a constructor refuses a value (it throws IllegalArgumentException), return
 *    Rejected(<its message>) instead of letting the exception out
 */
fun parseEvent(fields: Map<String, String>): Parsed {
    TODO("parse the fields into a PaymentEvent, and never throw")
}
