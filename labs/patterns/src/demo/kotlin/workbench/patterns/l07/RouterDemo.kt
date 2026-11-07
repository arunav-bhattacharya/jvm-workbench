package workbench.patterns.l07

// The same fee rules as a map of strategies and as a when. Add a payment method and watch which one tells you.

enum class PayMethod { CARD, SEPA, WALLET }
data class Pay(val method: PayMethod, val amountMinor: Long)

// open set: one function per method, in a map that config or plug-ins could fill
private val strategies: Map<PayMethod, (Pay) -> Long> = mapOf(
    PayMethod.CARD to { p -> 30 + p.amountMinor * 290 / 10_000 },
    PayMethod.SEPA to { _ -> 25L },
    PayMethod.WALLET to { p -> p.amountMinor * 150 / 10_000 },
)

// closed set: one when, checked by the compiler
private fun feeWhen(p: Pay): Long = when (p.method) {
    PayMethod.CARD -> 30 + p.amountMinor * 290 / 10_000
    PayMethod.SEPA -> 25
    PayMethod.WALLET -> p.amountMinor * 150 / 10_000
}

fun main() {
    for (m in PayMethod.entries) {
        val p = Pay(m, 10_000)
        print("%-7s when=%d".format(m, feeWhen(p)))
        println("  map=%d".format(strategies.getValue(m)(p)))
    }
}
