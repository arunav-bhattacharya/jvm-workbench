package workbench.kotlin.l04.demo

@DslMarker
@Target(AnnotationTarget.CLASS, AnnotationTarget.TYPE)
annotation class PaymentDsl

data class Party(val name: String, val iban: String)

data class PaymentRequest(val id: String, val currency: String, val payer: Party, val payee: Party)

@PaymentDsl
class PartyBuilder {
    var name = ""
    var iban = ""

    fun build(): Party {
        require(iban.isNotBlank()) { "iban required for '$name'" }
        return Party(name, iban)
    }
}

@PaymentDsl
class PaymentRequestBuilder(private val id: String) {
    var currency = "EUR"
    private var payer: Party? = null
    private var payee: Party? = null

    fun payer(block: PartyBuilder.() -> Unit) { payer = PartyBuilder().apply(block).build() }

    fun payee(block: PartyBuilder.() -> Unit) { payee = PartyBuilder().apply(block).build() }

    fun build() = PaymentRequest(id, currency, checkNotNull(payer) { "payer missing" }, checkNotNull(payee) { "payee missing" })
}

fun paymentRequest(id: String, block: PaymentRequestBuilder.() -> Unit): PaymentRequest =
    PaymentRequestBuilder(id).apply(block).build()

fun main() {
    val req = paymentRequest("PR-1") {
        currency = "GBP"
        payer { name = "ACME Ltd"; iban = "GB33BUKB20201555555555" }
        payee {
            name = "Corner Shop"
            iban = "GB94BARC10201530093459"
            this@paymentRequest.currency = "EUR"      // an outer receiver needs an explicit label
        }
    }
    println(req)

    // Wrong move. Uncomment the block, predict, run. Then remove @PaymentDsl from both builder
    // classes and run it again.
    // paymentRequest("PR-2") {
    //     payer {
    //         name = "ACME Ltd"
    //         payee { name = "oops" }
    //         iban = "GB33BUKB20201555555555"
    //     }
    // }
}
