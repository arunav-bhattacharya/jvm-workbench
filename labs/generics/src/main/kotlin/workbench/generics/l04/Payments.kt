package workbench.generics.l04

/** A payment. An interface, so Feed<CardPayment> and Feed<BankTransfer> are both candidates for Feed<Payment>. */
interface Payment {
    val id: String
    val cents: Long
}

data class CardPayment(override val id: String, override val cents: Long, val last4: String) : Payment

data class BankTransfer(override val id: String, override val cents: Long, val iban: String) : Payment
