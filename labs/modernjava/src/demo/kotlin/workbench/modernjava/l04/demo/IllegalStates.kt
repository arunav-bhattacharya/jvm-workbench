package workbench.modernjava.l04.demo

import java.time.Duration

// the "bag of optionals" a JSON mapper gives you for the catalogue's reply to a hold request
data class HoldReplyDto(
    val status: String?,              // "READY", "UNAVAILABLE" or "WAITLISTED"
    val pickupCode: String?,          // should be set only when ready
    val reasonCode: String?,          // should be set only when unavailable
    val waitDays: Int?,               // should be set only when waitlisted
    val holdShelf: Int?,              // should be set only when ready
)

// a consumer of the DTO: it trusts that the fields match the status
fun pickupSlip(r: HoldReplyDto): String =
    if (r.status == "READY") "print slip: shelf ${r.holdShelf}, code ${r.pickupCode}" else "no slip"

// the same information as a closed model: three shapes, each with only its own fields
sealed interface HoldResult {
    data class Ready(val pickupCode: String, val shelf: Int) : HoldResult {   // String, not String?
        init {
            require(pickupCode.isNotBlank()) { "pickupCode is required" }
            require(shelf >= 1) { "hold shelves start at 1" }
        }
    }
    data class Unavailable(val reasonCode: String?) : HoldResult
    data class Waitlisted(val expectedWait: Duration) : HoldResult
}

fun pickupSlip(r: HoldResult): String = when (r) {
    is HoldResult.Ready -> "print slip: shelf ${r.shelf}, code ${r.pickupCode}"
    is HoldResult.Unavailable -> "no slip"
    is HoldResult.Waitlisted -> "no slip yet"
}

/** One class with optional fields, against a sealed model that has only the valid shapes. */
fun main() {
    val statuses = 3
    val optionalFields = 4
    println("shapes the DTO allows: ${statuses * (1 shl optionalFields)}, shapes that make sense: 3")

    // ready, but with no pickup code and a reason code: nothing stops it
    val broken = HoldReplyDto("READY", null, "10", null, 12)
    println("DTO consumer:    ${pickupSlip(broken)}")

    // HoldResult.Ready(null, 12) doesn't even compile: the type says the code is there
    try {
        HoldResult.Ready("", 12)
    } catch (e: IllegalArgumentException) {
        println("sealed model:    refused, ${e.message}")
    }
    println("sealed consumer: ${pickupSlip(HoldResult.Ready("K7P2QX", 12))}")
}
