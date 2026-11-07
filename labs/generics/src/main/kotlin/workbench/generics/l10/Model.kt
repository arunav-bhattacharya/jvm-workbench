package workbench.generics.l10

data class CardPayment(val cents: Long, val currency: String, val reference: String, val cardToken: String)
data class BankTransfer(val cents: Long, val currency: String, val reference: String, val iban: String)

interface PaymentEvent { val paymentId: String }
data class CardAuthorized(override val paymentId: String, val cents: Long) : PaymentEvent
