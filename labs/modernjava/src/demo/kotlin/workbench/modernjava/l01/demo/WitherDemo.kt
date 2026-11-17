package workbench.modernjava.l01.demo

// Kotlin generates copy(): one "wither" with a named, defaulted parameter per property
data class LoanRequest(val memberId: String, val days: Int, val titles: List<String>) {
    init {
        require(days > 0) { "days must be positive: $days" }
    }
}

/** copy() runs init, and like a Java wither it copies references, not what they point to. */
fun main() {
    val first = LoanRequest("M-1042", 21, listOf("Dune"))
    val renewed = first.copy(days = 35, titles = first.titles + "Emma")

    println("original: $first")
    println("changed:  $renewed")
    println("same titles list object: ${first.titles === first.copy(days = 14).titles}")
    try {
        first.copy(days = -1)
    } catch (e: IllegalArgumentException) {
        println("copy ran the checks: ${e.message}")
    }
}
