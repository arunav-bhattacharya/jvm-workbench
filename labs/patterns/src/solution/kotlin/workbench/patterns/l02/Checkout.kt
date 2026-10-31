package workbench.patterns.l02

sealed interface PayResult {
    data class Paid(val authCode: String) : PayResult
    data class Rejected(val reason: String) : PayResult
}

class Checkout(private val clientsFor: (Network) -> CardNetworkClients) {

    fun pay(rawPan: String, amountMinor: Long): PayResult =
        when (val parsed = Card.parse(rawPan)) {                 // exhaustive: Valid or Invalid, no else
            is CardResult.Invalid -> PayResult.Rejected(parsed.reason)
            is CardResult.Valid -> {
                val card = parsed.card
                // the factory picks the family; Checkout only knows the Authorizer interface
                PayResult.Paid(clientsFor(card.network).authorizer().authorize(card, amountMinor))
            }
        }
}
