package workbench.patterns.l02

/** What [Checkout.pay] returns. */
sealed interface PayResult {
    data class Paid(val authCode: String) : PayResult
    data class Rejected(val reason: String) : PayResult
}

/**
 * Takes a raw card number and an amount, and authorizes the payment with the right network.
 *
 * The factory comes in as a function, so a test can pass a fake one (or `CardNetworkClients::sandbox`).
 * Checkout must not build clients itself and must not know the network classes.
 */
class Checkout(private val clientsFor: (Network) -> CardNetworkClients) {

    /**
     * Parses [rawPan] with [Card.parse]. An invalid number is [PayResult.Rejected] with the parse
     * reason, and the factory is never called. A valid card is authorized by the authorizer of the
     * family for its network, and the result is [PayResult.Paid] with the auth code.
     */
    fun pay(rawPan: String, amountMinor: Long): PayResult = TODO("parse, then ask the factory for the card's family")
}
