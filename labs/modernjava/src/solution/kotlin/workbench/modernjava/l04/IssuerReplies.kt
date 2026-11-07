package workbench.modernjava.l04

import java.time.Duration
import workbench.modernjava.l04.AuthResult.Approved
import workbench.modernjava.l04.AuthResult.Declined
import workbench.modernjava.l04.AuthResult.RetryLater
import workbench.modernjava.l04.Parsed.Ok
import workbench.modernjava.l04.Parsed.Rejected

// the boundary: untrusted fields in, a value of the closed model (or a reason) out
fun parse(raw: RawReply): Parsed = try {
    when (raw.status) {
        "APPROVED" -> when {
            raw.declineCode != null -> Rejected("contradictory reply: approved with decline code ${raw.declineCode}")
            raw.authCode == null -> Rejected("approved without an auth code")
            raw.amountMinor == null -> Rejected("approved without an amount")
            else -> Ok(Approved(AuthCode(raw.authCode), raw.amountMinor))   // the constructors check the rest
        }
        "DECLINED" -> Ok(Declined(declineReason(raw.declineCode)))
        "SOFT_DECLINE" -> when (val seconds = raw.retryAfterSeconds) {
            null -> Rejected("soft decline without retry-after")
            else -> Ok(RetryLater(Duration.ofSeconds(seconds)))
        }
        else -> Rejected("unknown status: ${raw.status}")
    }
} catch (e: IllegalArgumentException) {
    Rejected(e.message ?: "invalid reply")   // the model refused a value: report it, don't throw
}

private fun declineReason(code: String?): DeclineReason = when (code) {
    "51" -> DeclineReason.INSUFFICIENT_FUNDS
    "62" -> DeclineReason.CARD_BLOCKED
    "59" -> DeclineReason.SUSPECTED_FRAUD
    else -> DeclineReason.OTHER              // here else is right: "every other code" is one answer
}

// an operation kept apart from the data: one function, one when, no else
fun customerMessage(result: AuthResult): String = when (result) {
    is Approved -> "Payment approved."
    is Declined if result.reason == DeclineReason.INSUFFICIENT_FUNDS -> "Not enough funds. Try another card."
    is Declined if result.reason == DeclineReason.SUSPECTED_FRAUD -> "Payment declined. Please contact your bank."
    is Declined -> "Payment declined."
    is RetryLater -> "Your bank is busy. We'll try again in ${result.after.seconds} seconds."
}
