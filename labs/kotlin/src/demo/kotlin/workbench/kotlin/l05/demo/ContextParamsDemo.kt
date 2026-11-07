package workbench.kotlin.l05.demo

interface Logger {
    fun log(msg: String)
}

class TxId(val value: String)

data class Payment(val amountMinor: Long)

/** Two context parameters, then an extension receiver, then an ordinary parameter. */
context(logger: Logger, tx: TxId)
fun Payment.authorize(merchant: String): Boolean {
    logger.log("[${tx.value}] authorizing $amountMinor for $merchant")
    return amountMinor < 100_000
}

/** Calls authorize and audit without passing the logger or the tx id: the context flows on. */
context(logger: Logger, tx: TxId)
fun checkout(payment: Payment, merchant: String): String {
    val approved = payment.authorize(merchant)
    audit("checkout ${tx.value} ${if (approved) "approved" else "declined"}")
    return if (approved) "APPROVED" else "DECLINED"
}

/** An anonymous context parameter, read with contextOf. */
context(_: Logger)
fun audit(event: String) = contextOf<Logger>().log("AUDIT $event")

fun main() {
    val console = object : Logger {
        override fun log(msg: String) = println(msg)
    }
    context(console, TxId("tx-42")) {
        println(checkout(Payment(5_000), "coffee-shop"))
        println(checkout(Payment(250_000), "car-dealer"))
    }
    with(console) { audit("an implicit receiver works too") }

    // Wrong move. Uncomment, predict, run.
    // checkout(Payment(1), "kiosk")
}
