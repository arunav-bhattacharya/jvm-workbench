package workbench.kotlin.l05.demo

import kotlin.contracts.ExperimentalContracts
import kotlin.contracts.InvocationKind
import kotlin.contracts.contract

sealed interface PaymentEvent
data class Captured(val paymentId: String, val amountMinor: Long) : PaymentEvent
data class Failed(val paymentId: String, val reason: String) : PaymentEvent

fun lookupCurrency(merchant: String): String? = if (merchant.startsWith("m-")) "eur" else null

/** Checks, but tells the compiler nothing. */
fun requireCurrencyPlain(currency: String?) {
    if (currency == null) throw IllegalArgumentException("currency missing")
}

/** The same check, plus a promise: if this returns, currency was not null. */
@OptIn(ExperimentalContracts::class)
fun requireCurrency(currency: String?) {
    contract { returns() implies (currency != null) }
    if (currency == null) throw IllegalArgumentException("currency missing")
}

/** A promise about the receiver: a true result means this is a Captured. */
@OptIn(ExperimentalContracts::class)
fun PaymentEvent.isCaptured(): Boolean {
    contract { returns(true) implies (this@isCaptured is Captured) }
    return this is Captured
}

/** A promise about the lambda: it runs exactly once, during this call. */
@OptIn(ExperimentalContracts::class)
inline fun <T> once(block: () -> T): T {
    contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }
    return block()
}

fun main() {
    val currency = lookupCurrency("m-981")
    requireCurrency(currency)
    println("currency = ${currency.uppercase()}")            // smart cast to String

    val event: PaymentEvent = Captured("pay_7", 1_999)
    if (event.isCaptured()) println("captured ${event.amountMinor}")   // smart cast to Captured

    val label: String                                         // a val, assigned inside a lambda
    once { label = "batch-17" }
    println("label = $label")

    // Wrong moves, one at a time. Predict the error, run, undo.
    // 1. Call requireCurrencyPlain(currency) instead of requireCurrency(currency).
    // 2. Delete the line `contract { callsInPlace(...) }` in once.
    // 3. Delete @OptIn(ExperimentalContracts::class) above isCaptured.
}
