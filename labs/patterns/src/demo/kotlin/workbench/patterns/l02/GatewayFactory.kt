package workbench.patterns.l02

// A factory over a sealed family, and the same factory passed around as a function.

enum class Provider { ADYEN, STRIPE, FAKE }

sealed interface PaymentGateway {
    fun charge(amountMinor: Long, token: String): String

    companion object {
        // the factory: an exhaustive when over the enum, with no else branch
        fun of(p: Provider): PaymentGateway = when (p) {
            Provider.ADYEN -> AdyenGateway()
            Provider.STRIPE -> StripeGateway()
            Provider.FAKE -> FakeGateway()
        }
    }
}

class AdyenGateway : PaymentGateway {
    override fun charge(amountMinor: Long, token: String) = "adyen:$token:$amountMinor"
}
class StripeGateway : PaymentGateway {
    override fun charge(amountMinor: Long, token: String) = "stripe:$token:$amountMinor"
}
class FakeGateway : PaymentGateway {
    override fun charge(amountMinor: Long, token: String) = "fake:ok"
}

// the modern "factory method": the caller hands in how to make the product
class GatewayCheckout(private val gateways: () -> PaymentGateway) {
    fun pay(amountMinor: Long, token: String) = gateways().charge(amountMinor, token)
}

fun main() {
    for (p in Provider.entries) {
        println("$p -> ${PaymentGateway.of(p).charge(1_250, "tok_42")}")
    }
    println("test checkout -> ${GatewayCheckout(::FakeGateway).pay(1_250, "tok_42")}")
}
