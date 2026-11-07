package workbench.modernjava.l01.demo

// Kotlin generates copy(): one "wither" with a named, defaulted parameter per property
data class RefundRequest(val paymentId: String, val amountMinor: Long, val reasons: List<String>) {
    init {
        require(amountMinor > 0) { "refund must be positive: $amountMinor" }
    }
}

/** copy() runs init, and like a Java wither it copies references, not what they point to. */
fun main() {
    val full = RefundRequest("pay_81", 5_000, listOf("duplicate charge"))
    val part = full.copy(amountMinor = 2_000, reasons = full.reasons + "partial goodwill")

    println("original: $full")
    println("changed:  $part")
    println("same reasons list object: ${full.reasons === full.copy(amountMinor = 1_000).reasons}")
    try {
        full.copy(amountMinor = -1)
    } catch (e: IllegalArgumentException) {
        println("copy ran the checks: ${e.message}")
    }
}
