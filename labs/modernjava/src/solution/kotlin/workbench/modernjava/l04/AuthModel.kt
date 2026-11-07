package workbench.modernjava.l04

import java.time.Duration

data class RawReply(
    val status: String?,
    val authCode: String?,
    val declineCode: String?,
    val retryAfterSeconds: Long?,
    val amountMinor: Long?,
)

@JvmInline
value class AuthCode(val value: String) {
    init {
        // every AuthCode in the service went through this check
        require(SHAPE.matches(value)) { "auth code must be 6 upper-case letters or digits: $value" }
    }

    private companion object {
        val SHAPE = Regex("[A-Z0-9]{6}")
    }
}

enum class DeclineReason { INSUFFICIENT_FUNDS, CARD_BLOCKED, SUSPECTED_FRAUD, OTHER }

sealed interface AuthResult {

    data class Approved(val code: AuthCode, val amountMinor: Long) : AuthResult {
        init {
            require(amountMinor > 0) { "approved amount must be positive: $amountMinor" }
        }
    }

    // no fields to check: the enum already allows only the four reasons
    data class Declined(val reason: DeclineReason) : AuthResult

    data class RetryLater(val after: Duration) : AuthResult {
        init {
            require(after >= Duration.ofSeconds(1) && after <= Duration.ofHours(1)) { "retry wait out of range: $after" }
        }
    }
}

sealed interface Parsed {
    data class Ok(val result: AuthResult) : Parsed
    data class Rejected(val problem: String) : Parsed
}
