package workbench.modernjava.l02.demo

// Kotlin subtypes are final unless you open them, and there is no non-sealed keyword:
// a plain interface (or an open class) under a sealed parent is the open branch.
sealed interface PaymentMethod {
    data class Card(val network: String) : PaymentMethod                       // final: a leaf

    sealed interface BankTransfer : PaymentMethod                               // sealed: closed below
    data class Sepa(val iban: String) : BankTransfer
    data class Swift(val bic: String) : BankTransfer

    interface PartnerMethod : PaymentMethod {                                   // open below
        val partnerId: String
    }
}

// partner code, which could live in any package: PartnerMethod is an ordinary interface
data class GiftCard(override val partnerId: String, val code: String) : PaymentMethod.PartnerMethod

// A Kotlin sealed class is always abstract, so the trap in step 3 of the Java demo can't happen here.
sealed class Fee {
    class Flat(val minor: Long) : Fee()
    class Percent(val basisPoints: Int) : Fee()
}

fun describe(m: PaymentMethod): String = when (m) {
    is PaymentMethod.Card -> "card ${m.network}"
    is PaymentMethod.BankTransfer -> "bank transfer $m"                         // one branch for the sealed branch
    is PaymentMethod.PartnerMethod -> "partner ${m.partnerId}"                  // one branch for the open branch
}

fun fee(f: Fee, amountMinor: Long): Long = when (f) {
    is Fee.Flat -> f.minor
    is Fee.Percent -> amountMinor * f.basisPoints / 10_000
}

/** Each branch of a sealed hierarchy ends closed, sealed again, or open. */
fun main() {
    println(describe(PaymentMethod.Card("VISA")))
    println(describe(PaymentMethod.Sepa("DE89370400440532013000")))
    println(describe(GiftCard("giftly", "GC-7731")))
    println("PartnerMethod.isSealed(): ${PaymentMethod.PartnerMethod::class.java.isSealed}")
    println("fee: ${fee(Fee.Percent(290), 10_000)} and ${fee(Fee.Flat(35), 10_000)}")
}
