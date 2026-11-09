package workbench.functional.l06

data class Charge(val id: String, val amountMinor: Long, val currency: String)

class ChargeRequest {
    var amountMinor: Long = 0
    var currency: String = ""
    override fun toString() = "ChargeRequest($amountMinor $currency)"
}

// The two shapes, written by hand. A scope function is nothing more than this.
fun <T, R> T.myLet(block: (T) -> R): R = block(this)          // object as `it`, returns the block's result
fun <T> T.myApply(block: T.() -> Unit): T { block(); return this }   // object as `this`, returns the object

fun main() {
    val charge = Charge("ch_1", 1_999, "EUR")

    // the same block, five ways: what comes back?
    println("let   -> ${charge.let { it.amountMinor * 2 }}")
    println("run   -> ${charge.run { amountMinor * 2 }}")
    println("with  -> ${with(charge) { amountMinor * 2 }}")
    println("also  -> ${charge.also { it.amountMinor * 2 }}")
    println("apply -> ${charge.apply { amountMinor * 2 }}")

    // the hand-written versions behave the same way
    println("myLet   -> ${charge.myLet { it.amountMinor * 2 }}")
    println("myApply -> ${ChargeRequest().myApply { amountMinor = 1_999; currency = "EUR" }}")
}
