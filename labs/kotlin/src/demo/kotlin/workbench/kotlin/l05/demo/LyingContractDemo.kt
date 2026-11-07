package workbench.kotlin.l05.demo

import kotlin.contracts.ExperimentalContracts
import kotlin.contracts.contract

/** A contract that lies. The compiler checks neither the promise nor the body. */
@OptIn(ExperimentalContracts::class)
fun PaymentEvent.lyingIsCaptured(): Boolean {
    contract { returns(true) implies (this@lyingIsCaptured is Captured) }
    return true
}

fun main() {
    val failed: PaymentEvent = Failed("pay_8", "insufficient funds")
    try {
        if (failed.lyingIsCaptured()) println("captured ${failed.amountMinor}")
    } catch (e: ClassCastException) {
        println("ClassCastException: ${e.message}")
    }
}
