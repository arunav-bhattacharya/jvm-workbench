package workbench.generics.l04.demo

/** Kotlin's List is declared List<out E>, so a List<Payment> parameter accepts a List<CardPayment>. */
fun sumCents(payments: List<Payment>): Long = payments.sumOf { it.cents }

/** MutableList is invariant: this one only accepts a MutableList<Payment>. */
fun sumCentsMutable(payments: MutableList<Payment>): Long = payments.sumOf { it.cents }

fun main() {
    val cards: MutableList<CardPayment> = mutableListOf(CardPayment("pay_1", 1_200, "4242"), CardPayment("pay_2", 350, "0005"))
    println("sumCents(cards) = ${sumCents(cards)}")

    // Wrong move. Uncomment, predict the error, then run.
    // println(sumCentsMutable(cards))
}
