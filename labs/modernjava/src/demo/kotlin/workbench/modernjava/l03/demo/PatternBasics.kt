package workbench.modernjava.l03.demo

sealed interface Method {
    data class Card(val network: String, val last4: String) : Method
    data class Transfer(val iban: String) : Method
    data class Wallet(val provider: String) : Method
}

// an if-chain: kotlinc never checks that it covers every Method
fun viaChain(m: Method): String =
    if (m is Method.Card) "card ${m.network} ****${m.last4}"          // smart cast: m is a Card here
    else if (m is Method.Transfer) "transfer from ${m.iban}"
    else if (m is Method.Wallet) "wallet ${m.provider}"
    else throw IllegalStateException("unreachable?")

// when with a subject: kotlinc checks that every Method is covered
fun viaWhen(m: Method): String = when (m) {
    is Method.Card -> "card ${m.network} ****${m.last4}"
    is Method.Transfer -> "transfer from ${m.iban}"
    is Method.Wallet -> "wallet ${m.provider}"
}

// a smart cast lasts for the rest of the function after a negated check returns
fun last4(o: Any): String {
    if (o !is Method.Card) return "not a card"
    return "last four: ${o.last4}"
}

/** The same dispatch three ways: an if-chain, an early return, and a when. */
fun main() {
    val all = listOf(Method.Card("VISA", "1111"), Method.Transfer("DE89370400440532013000"), Method.Wallet("Paywave"))
    for (m in all) {
        println(viaChain(m) + "  |  " + viaWhen(m))
    }
    println(last4(all[0]) + ", " + last4("4111"))
}
