package workbench.modernjava.l04

import java.time.Duration

data class RawReply(
    val status: String?,
    val pickupCode: String?,
    val reasonCode: String?,
    val waitDays: Int?,
    val holdShelf: Int?,
)

@JvmInline
value class PickupCode(val value: String) {
    init {
        // every PickupCode in the program went through this check
        require(SHAPE.matches(value)) { "pickup code must be 6 upper-case letters or digits: $value" }
    }

    private companion object {
        val SHAPE = Regex("[A-Z0-9]{6}")
    }
}

enum class Reason { LOST, NOT_IN_CATALOGUE, ACCOUNT_BLOCKED, OTHER }

sealed interface HoldResult {

    data class Ready(val code: PickupCode, val shelf: Int) : HoldResult {
        init {
            require(shelf >= 1) { "hold shelves start at 1: $shelf" }
        }
    }

    // no fields to check: the enum already allows only the four reasons
    data class Unavailable(val reason: Reason) : HoldResult

    data class Waitlisted(val wait: Duration) : HoldResult {
        init {
            require(wait >= Duration.ofDays(1) && wait <= Duration.ofDays(365)) { "wait out of range: $wait" }
        }
    }
}

sealed interface Parsed {
    data class Ok(val result: HoldResult) : Parsed
    data class Rejected(val problem: String) : Parsed
}
