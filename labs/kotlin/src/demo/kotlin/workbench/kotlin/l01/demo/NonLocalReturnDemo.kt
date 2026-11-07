package workbench.kotlin.l01.demo

/** A bare `return` inside forEach's lambda returns from firstDeclined: forEach is inline. */
fun firstDeclined(results: List<String>): String? {
    results.forEach { if (it.startsWith("DECLINED")) return it }
    return null
}

/** `return@forEach` leaves only the current lambda call, like `continue` in a loop. */
fun countApproved(results: List<String>): Int {
    var approved = 0
    results.forEach {
        if (!it.startsWith("APPROVED")) return@forEach
        approved++
    }
    return approved
}

/** Since Kotlin 2.2, `break` and `continue` work inside an inlined lambda too. */
fun totalUntilVoid(batches: List<List<Long>>): Long {
    var total = 0L
    for (batch in batches) {
        batch.forEach { amount ->
            if (amount < 0) break          // leaves the for loop, not just the lambda
            total += amount
        }
    }
    return total
}

fun main() {
    val results = listOf("APPROVED pay_1", "DECLINED pay_2 insufficient funds", "APPROVED pay_3")
    println("firstDeclined = ${firstDeclined(results)}")
    println("countApproved = ${countApproved(results)}")
    println("totalUntilVoid = ${totalUntilVoid(listOf(listOf(1_000L, 250L), listOf(400L, -1L, 900L), listOf(75L)))}")

    // Wrong move. Uncomment, predict the error, then run.
    // val lookup = { r: String -> if (r.isEmpty()) return; r.length }
}
