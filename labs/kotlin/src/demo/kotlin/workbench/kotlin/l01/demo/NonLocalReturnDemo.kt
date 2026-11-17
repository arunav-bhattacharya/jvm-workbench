package workbench.kotlin.l01.demo

/** A bare `return` inside forEach's lambda returns from firstJammed: forEach is inline. */
fun firstJammed(log: List<String>): String? {
    log.forEach { if (it.startsWith("JAMMED")) return it }
    return null
}

/** `return@forEach` leaves only the current lambda call, like `continue` in a loop. */
fun countDone(log: List<String>): Int {
    var done = 0
    log.forEach {
        if (!it.startsWith("DONE")) return@forEach
        done++
    }
    return done
}

/** Since Kotlin 2.2, `break` and `continue` work inside an inlined lambda too. */
fun pagesUntilEmpty(batches: List<List<Long>>): Long {
    var total = 0L
    for (batch in batches) {
        batch.forEach { pages ->
            if (pages < 0) break           // -1 means "out of paper": leaves the for loop, not just the lambda
            total += pages
        }
    }
    return total
}

fun main() {
    val log = listOf("DONE job_1", "JAMMED job_2 in tray 2", "DONE job_3")
    println("firstJammed = ${firstJammed(log)}")
    println("countDone = ${countDone(log)}")
    println("pagesUntilEmpty = ${pagesUntilEmpty(listOf(listOf(1_000L, 250L), listOf(400L, -1L, 900L), listOf(75L)))}")

    // Wrong move. Uncomment, predict the error, then run.
    // val lookup = { line: String -> if (line.isEmpty()) return; line.length }
}
