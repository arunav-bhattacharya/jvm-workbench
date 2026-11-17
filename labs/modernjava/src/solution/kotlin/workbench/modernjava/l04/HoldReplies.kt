package workbench.modernjava.l04

import java.time.Duration
import workbench.modernjava.l04.HoldResult.Ready
import workbench.modernjava.l04.HoldResult.Unavailable
import workbench.modernjava.l04.HoldResult.Waitlisted
import workbench.modernjava.l04.Parsed.Ok
import workbench.modernjava.l04.Parsed.Rejected

// the edge: untrusted fields in, a value of the closed model (or a reason) out
fun parse(raw: RawReply): Parsed = try {
    when (raw.status) {
        "READY" -> when {
            raw.reasonCode != null -> Rejected("contradictory reply: ready with reason code ${raw.reasonCode}")
            raw.pickupCode == null -> Rejected("ready without a pickup code")
            raw.holdShelf == null -> Rejected("ready without a hold shelf")
            else -> Ok(Ready(PickupCode(raw.pickupCode), raw.holdShelf))   // the constructors check the rest
        }
        "UNAVAILABLE" -> Ok(Unavailable(reason(raw.reasonCode)))
        "WAITLISTED" -> when (val days = raw.waitDays) {
            null -> Rejected("waiting list without a wait")
            else -> Ok(Waitlisted(Duration.ofDays(days.toLong())))
        }
        else -> Rejected("unknown status: ${raw.status}")
    }
} catch (e: IllegalArgumentException) {
    Rejected(e.message ?: "invalid reply")   // the model refused a value: report it, don't throw
}

private fun reason(code: String?): Reason = when (code) {
    "10" -> Reason.LOST
    "20" -> Reason.NOT_IN_CATALOGUE
    "30" -> Reason.ACCOUNT_BLOCKED
    else -> Reason.OTHER                     // here else is right: "every other code" is one answer
}

// an operation kept apart from the data: one function, one when, no else
fun screenMessage(result: HoldResult): String = when (result) {
    is Ready -> "Your book is waiting on hold shelf ${result.shelf}."
    is Unavailable if result.reason == Reason.NOT_IN_CATALOGUE -> "We don't have this title. Ask us to order it."
    is Unavailable if result.reason == Reason.ACCOUNT_BLOCKED -> "Please ask at the desk."
    is Unavailable -> "This title is not available right now."
    is Waitlisted -> "You're on the waiting list. Expected wait: ${result.expectedWait.toDays()} days."
}
