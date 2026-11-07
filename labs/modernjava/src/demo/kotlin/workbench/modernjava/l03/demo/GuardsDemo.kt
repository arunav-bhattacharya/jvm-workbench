package workbench.modernjava.l03.demo

enum class Network { VISA, MASTERCARD, AMEX }

sealed interface Charge {
    data class Card(val network: Network, val corporate: Boolean, val amountMinor: Long) : Charge
    data class Transfer(val instant: Boolean, val amountMinor: Long) : Charge
}

// guards in when branches (`is T if condition`) are stable since Kotlin 2.2
fun fee(c: Charge): Long = when (c) {
    is Charge.Card if c.network == Network.AMEX -> c.amountMinor * 350 / 10_000   // 1
    is Charge.Card if c.corporate -> c.amountMinor * 290 / 10_000                 // 2
    is Charge.Card -> c.amountMinor * 30 / 10_000                                 // 3
    is Charge.Transfer if c.instant -> 50
    is Charge.Transfer -> 20
}

/** Branches are tried from the top, and the first one that matches wins. Guards decide the order. */
fun main() {
    val charges = listOf(
        Charge.Card(Network.AMEX, false, 10_000),
        Charge.Card(Network.AMEX, true, 10_000),
        Charge.Card(Network.VISA, true, 10_000),
        Charge.Card(Network.VISA, false, 10_000),
        Charge.Transfer(true, 10_000),
    )
    for (c in charges) {
        println("%-62s fee %d".format(c, fee(c)))
    }
}
