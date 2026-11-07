package workbench.modernjava.l04.demo

import java.time.Duration

// the "bag of optionals" a JSON mapper gives you for the issuer's reply
data class IssuerReplyDto(
    val status: String?,              // "APPROVED", "DECLINED" or "SOFT_DECLINE"
    val authCode: String?,            // should be set only when approved
    val declineCode: String?,         // should be set only when declined
    val retryAfterSeconds: Long?,     // should be set only on a soft decline
    val amountMinor: Long?,           // should be set only when approved
)

// a consumer of the DTO: it trusts that the fields match the status
fun captureCommand(r: IssuerReplyDto): String =
    if (r.status == "APPROVED") "capture ${r.amountMinor} with auth code ${r.authCode}" else "no capture"

// the same information as a closed model: three shapes, each with only its own fields
sealed interface AuthResult {
    data class Approved(val authCode: String, val amountMinor: Long) : AuthResult {   // String, not String?
        init {
            require(authCode.isNotBlank()) { "authCode is required" }
            require(amountMinor > 0) { "amount must be positive" }
        }
    }
    data class Declined(val declineCode: String?) : AuthResult
    data class RetryLater(val after: Duration) : AuthResult
}

fun captureCommand(r: AuthResult): String = when (r) {
    is AuthResult.Approved -> "capture ${r.amountMinor} with auth code ${r.authCode}"
    is AuthResult.Declined -> "no capture"
    is AuthResult.RetryLater -> "no capture yet"
}

/** One class with optional fields, against a sealed model that has only the valid shapes. */
fun main() {
    val statuses = 3
    val optionalFields = 4
    println("shapes the DTO allows: ${statuses * (1 shl optionalFields)}, shapes that make sense: 3")

    // approved, but with no auth code and a decline code: nothing stops it
    val broken = IssuerReplyDto("APPROVED", null, "51", null, 4_200)
    println("DTO consumer:    ${captureCommand(broken)}")

    // AuthResult.Approved(null, 4_200) doesn't even compile: the type says the code is there
    try {
        AuthResult.Approved("", 4_200)
    } catch (e: IllegalArgumentException) {
        println("sealed model:    refused, ${e.message}")
    }
    println("sealed consumer: ${captureCommand(AuthResult.Approved("A1B2C3", 4_200))}")
}
