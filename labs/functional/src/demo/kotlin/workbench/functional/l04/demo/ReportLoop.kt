package workbench.functional.l04.demo

// Payment, Status and sampleDay are in SampleDay.kt, next to this file.

// The loop: four results built at once, and every line changes one of them.
fun reportLoop(payments: List<Payment>): String {
    var settled = 0L
    val net = LinkedHashMap<String, Long>()
    val failed = ArrayList<String>()
    var largest = payments.first()
    for (p in payments) {
        when (p.status) {
            Status.SETTLED -> {
                settled += p.amountCents
                net[p.merchant] = (net[p.merchant] ?: 0L) + p.amountCents - (p.refundCents ?: 0L)
                if (p.amountCents > largest.amountCents) largest = p
            }
            Status.FAILED -> failed.add(p.id)
            Status.PENDING -> {}
        }
    }
    return "settled=$settled net=$net failed=$failed largest=${largest.id}"
}

// The same report: one val per result, each computed from the list.
fun reportChain(payments: List<Payment>): String {
    val settledPayments = payments.filter { it.status == Status.SETTLED }
    val settled = settledPayments.sumOf { it.amountCents }
    val net = settledPayments.groupBy { it.merchant }
        .mapValues { (_, ps) -> ps.sumOf { it.amountCents - (it.refundCents ?: 0L) } }
    val failed = payments.filter { it.status == Status.FAILED }.map { it.id }
    val largest = settledPayments.maxByOrNull { it.amountCents }
    return "settled=$settled net=$net failed=$failed largest=${largest?.id}"
}

fun main(args: Array<String>) {
    val payments = if (args.firstOrNull() == "empty") emptyList() else sampleDay
    println("chain: ${reportChain(payments)}")
    try {
        println("loop:  ${reportLoop(payments)}")
    } catch (e: NoSuchElementException) {
        println("loop:  threw $e")
    }
}
