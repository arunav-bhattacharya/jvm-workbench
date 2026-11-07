package workbench.kotlin.l02.demo

/** A value class: a Cents in your code, a long in the bytecode. */
@JvmInline
value class Cents(val value: Long) {
    init {
        require(value >= 0) { "negative amount: $value" }
    }

    operator fun plus(other: Cents): Cents = Cents(value + other.value)

    override fun toString(): String = "$value cents"
}

/** A type alias is only a second name. Any Long is accepted where a CentsAlias is expected. */
typealias CentsAlias = Long

fun charge(amount: Cents): String = "charged $amount"

@JvmName("chargeFromJava")
fun chargeJava(amount: Cents): String = "charged $amount"

fun chargeAlias(amount: CentsAlias): String = "charged $amount (alias)"

fun main() {
    val fee = Cents(150) + Cents(49)
    println(charge(fee))
    println(chargeAlias(System.currentTimeMillis() % 1_000))   // compiles: an alias is just a Long
    try {
        Cents(-1)
    } catch (e: IllegalArgumentException) {
        println("rejected: ${e.message}")
    }

    // Wrong move. Uncomment, predict the error, then run.
    // println(charge(199L))
}
