package workbench.patterns.l02

/** Asks the card network to approve a payment. Returns an auth code. */
fun interface Authorizer {
    fun authorize(card: Card, amountMinor: Long): String
}

/** Gives money back for an earlier authorization. Returns a refund reference. */
fun interface Refunder {
    fun refund(authCode: String, amountMinor: Long): String
}

/**
 * Abstract factory: one family of clients for one card network. Everything a family creates talks
 * to the same network, so you can never pair a Visa authorizer with a Mastercard refunder.
 *
 * The sandbox families behave like this (no real network calls):
 *
 * | network    | baseUrl                             | auth code               | refund reference  |
 * |------------|-------------------------------------|-------------------------|-------------------|
 * | VISA       | https://sandbox.visa.example        | "V-AUTH-<last4>-<amount>" | "V-REFUND-<amount>" |
 * | MASTERCARD | https://sandbox.mastercard.example  | "M-AUTH-<last4>-<amount>" | "M-REFUND-<amount>" |
 *
 * A family's authorizer throws IllegalArgumentException for a card of another network, and its
 * refunder throws IllegalArgumentException for an auth code that does not start with its own
 * prefix ("V-" or "M-").
 */
interface CardNetworkClients {
    val network: Network
    val baseUrl: String
    fun authorizer(): Authorizer
    fun refunder(): Refunder

    companion object {
        /** The sandbox family for [network]. Use an exhaustive `when`, with no `else`. */
        fun sandbox(network: Network): CardNetworkClients = TODO("return the right family for each network")
    }
}
