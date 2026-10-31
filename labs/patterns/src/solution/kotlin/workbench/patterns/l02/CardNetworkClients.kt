package workbench.patterns.l02

fun interface Authorizer {
    fun authorize(card: Card, amountMinor: Long): String
}

fun interface Refunder {
    fun refund(authCode: String, amountMinor: Long): String
}

interface CardNetworkClients {
    val network: Network
    val baseUrl: String
    fun authorizer(): Authorizer
    fun refunder(): Refunder

    companion object {
        // the one switch that knows which family belongs to which network; no else, so a new
        // Network constant is a compile error here and nowhere else
        fun sandbox(network: Network): CardNetworkClients = when (network) {
            Network.VISA -> SandboxClients(Network.VISA, "https://sandbox.visa.example", "V")
            Network.MASTERCARD -> SandboxClients(Network.MASTERCARD, "https://sandbox.mastercard.example", "M")
        }
    }
}

// one family = one network's settings; both products are built from the same settings, so they can't mismatch
private class SandboxClients(
    override val network: Network,
    override val baseUrl: String,
    private val prefix: String,
) : CardNetworkClients {

    override fun authorizer() = Authorizer { card, amountMinor ->
        require(card.network == network) { "a $network authorizer cannot authorize a ${card.network} card" }
        "$prefix-AUTH-${card.last4}-$amountMinor"
    }

    override fun refunder() = Refunder { authCode, amountMinor ->
        require(authCode.startsWith("$prefix-")) { "auth code $authCode is not from $network" }
        "$prefix-REFUND-$amountMinor"
    }
}
