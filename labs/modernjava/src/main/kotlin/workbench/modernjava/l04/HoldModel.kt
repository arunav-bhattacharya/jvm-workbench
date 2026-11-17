package workbench.modernjava.l04

import java.time.Duration

/**
 * What the regional catalogue sends back when a member reserves a book, mapped field by field
 * from its JSON. Untrusted: any field may be missing, and the fields may contradict each other.
 */
data class RawReply(
    val status: String?,              // "READY", "UNAVAILABLE" or "WAITLISTED"
    val pickupCode: String?,          // should be there only when ready
    val reasonCode: String?,          // should be there only when unavailable
    val waitDays: Int?,               // should be there only when waitlisted
    val holdShelf: Int?,              // the numbered shelf where a ready book waits
)

/**
 * The code a member shows at the desk to collect a reserved book. At run time it is just the String.
 *
 * TODO 1: add an init block that rejects anything that isn't exactly six upper-case
 * letters or digits, with IllegalArgumentException (use `require`).
 */
@JvmInline
value class PickupCode(val value: String)

enum class Reason { LOST, NOT_IN_CATALOGUE, ACCOUNT_BLOCKED, OTHER }

/** The result of a hold request: each outcome has exactly the fields it needs, and no others. */
sealed interface HoldResult {

    /** TODO 2: reject a hold shelf below 1. */
    data class Ready(val code: PickupCode, val shelf: Int) : HoldResult

    data class Unavailable(val reason: Reason) : HoldResult

    /** TODO 3: reject a wait shorter than 1 day or longer than 365 days. */
    data class Waitlisted(val wait: Duration) : HoldResult
}

/** What reading a reply at the edge of the program produces. */
sealed interface Parsed {
    data class Ok(val result: HoldResult) : Parsed
    data class Rejected(val problem: String) : Parsed
}
