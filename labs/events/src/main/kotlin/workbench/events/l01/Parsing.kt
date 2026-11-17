package workbench.events.l01

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
 *
 * TODO 4:
 *  - a missing field gives Rejected("missing field '<name>'")
 *  - a grams field that isn't a whole number gives Rejected("grams is not a whole number: '<raw>'")
 *  - an unknown type or fail reason gives Rejected naming the bad value
 *  - when a constructor refuses a value (it throws IllegalArgumentException), return
 *    Rejected(<its message>) instead of letting the exception out
 */
fun parseEvent(fields: Map<String, String>): Parsed {
    TODO("parse the fields into a ParcelEvent, and never throw")
}
