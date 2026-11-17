package workbench.events.l03

/** What the edge hands to the rest of the program: a valid event, or a reason it was refused. */
sealed interface Parsed {
    data class Ok(val event: ParcelEvent) : Parsed
    data class Rejected(val reason: String) : Parsed
}

/**
 * The edge of the program: turns the raw fields of one message (for example a scan sent by a
 * rider's handheld scanner, already read into a map of strings) into the model. Never throws.
 * Behind this function nothing checks events again, because no invalid ParcelEvent can be built.
 *
 * Fields: `type` (booked, collected, delivered, failed), `parcelId`, `grams` (a whole number of
 * grams, for the first three types) and `reason` (a FailReason name, for failed).
 */
fun parseEvent(fields: Map<String, String>): Parsed {
    // 1. small readers that throw IllegalArgumentException, like the constructors do
    fun field(name: String): String = fields[name] ?: throw IllegalArgumentException("missing field '$name'")

    fun weight(): Weight {
        val raw = field("grams")
        val grams = raw.toLongOrNull() ?: throw IllegalArgumentException("grams is not a whole number: '$raw'")
        return Weight(grams)                                  // Weight refuses negative numbers
    }

    return try {
        // 2. one branch per type; the constructors make the final checks
        val type = field("type")
        val event = when (type) {
            "booked" -> ParcelBooked(ParcelId(field("parcelId")), weight())
            "collected" -> ParcelCollected(ParcelId(field("parcelId")), weight())
            "delivered" -> ParcelDelivered(ParcelId(field("parcelId")), weight())
            "failed" -> {
                val raw = field("reason")
                val reason = FailReason.entries.find { it.name == raw }
                    ?: throw IllegalArgumentException("unknown fail reason: '$raw'")
                DeliveryFailed(ParcelId(field("parcelId")), reason)
            }
            else -> return Parsed.Rejected("unknown event type: '$type'")
        }
        Parsed.Ok(event)
    } catch (e: IllegalArgumentException) {
        // 3. every refusal becomes a value the caller can route, log or count
        Parsed.Rejected(e.message ?: "invalid event")
    }
}
