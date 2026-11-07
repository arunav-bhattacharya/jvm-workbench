package workbench.events.l02

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
 */
fun parseEvent(fields: Map<String, String>): Parsed {
    // 1. small readers that throw IllegalArgumentException, like the constructors do
    fun field(name: String): String = fields[name] ?: throw IllegalArgumentException("missing field '$name'")

    fun amount(): Money {
        val raw = field("amountMinor")
        val minor = raw.toLongOrNull() ?: throw IllegalArgumentException("amountMinor is not a whole number: '$raw'")
        return Money(minor)                                   // Money refuses negative amounts
    }

    return try {
        // 2. one branch per type; the constructors make the final checks
        val type = field("type")
        val event = when (type) {
            "authorized" -> PaymentAuthorized(PaymentId(field("paymentId")), amount())
            "captured" -> PaymentCaptured(PaymentId(field("paymentId")), amount())
            "refunded" -> PaymentRefunded(PaymentId(field("paymentId")), amount())
            "declined" -> {
                val raw = field("reason")
                val reason = DeclineReason.entries.find { it.name == raw }
                    ?: throw IllegalArgumentException("unknown decline reason: '$raw'")
                PaymentDeclined(PaymentId(field("paymentId")), reason)
            }
            else -> return Parsed.Rejected("unknown event type: '$type'")
        }
        Parsed.Ok(event)
    } catch (e: IllegalArgumentException) {
        // 3. every refusal becomes a value the caller can route, log or count
        Parsed.Rejected(e.message ?: "invalid event")
    }
}
