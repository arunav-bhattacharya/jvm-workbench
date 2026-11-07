package workbench.modernjava.l04

import java.time.Duration

/**
 * What the card issuer's API sends back, mapped field by field from its JSON.
 * Untrusted: any field may be missing, and the fields may contradict each other.
 */
data class RawReply(
    val status: String?,              // "APPROVED", "DECLINED" or "SOFT_DECLINE"
    val authCode: String?,            // should be there only when approved
    val declineCode: String?,         // should be there only when declined
    val retryAfterSeconds: Long?,     // should be there only on a soft decline
    val amountMinor: Long?,           // the approved amount
)

/**
 * An authorization code from the issuer. At run time it is just the String.
 *
 * TODO 1: add an init block that rejects anything that isn't exactly six upper-case
 * letters or digits, with IllegalArgumentException (use `require`).
 */
@JvmInline
value class AuthCode(val value: String)

enum class DeclineReason { INSUFFICIENT_FUNDS, CARD_BLOCKED, SUSPECTED_FRAUD, OTHER }

/** The result of an authorization: each outcome has exactly the fields it needs, and no others. */
sealed interface AuthResult {

    /** TODO 2: reject an amount that isn't positive. */
    data class Approved(val code: AuthCode, val amountMinor: Long) : AuthResult

    data class Declined(val reason: DeclineReason) : AuthResult

    /** TODO 3: reject a wait shorter than 1 second or longer than 1 hour. */
    data class RetryLater(val after: Duration) : AuthResult
}

/** What reading a reply at the edge of the service produces. */
sealed interface Parsed {
    data class Ok(val result: AuthResult) : Parsed
    data class Rejected(val problem: String) : Parsed
}
