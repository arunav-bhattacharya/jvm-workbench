package workbench.generics.l04.demo

interface Payment { val id: String; val cents: Long }
data class CardPayment(override val id: String, override val cents: Long, val last4: String) : Payment
data class BankTransfer(override val id: String, override val cents: Long, val iban: String) : Payment

/** A producer: T only comes out. `out` tells the compiler so. */
interface Source<out T> {
    fun next(): T?                     // null when there is nothing left
}

class ListSource<out T>(items: List<T>) : Source<T> {
    private val it = items.iterator()
    override fun next(): T? = if (it.hasNext()) it.next() else null
}

/** Needs a Source<Payment>. Because Source is `out`, a Source<CardPayment> fits. */
fun totalCents(source: Source<Payment>): Long {
    var sum = 0L
    while (true) {
        val p = source.next() ?: break
        sum += p.cents
    }
    return sum
}

fun main() {
    val cards: Source<CardPayment> = ListSource(listOf(CardPayment("pay_1", 1_200, "4242"), CardPayment("pay_2", 350, "0005")))
    println("card total: ${totalCents(cards)}")      // a Source<CardPayment> used as a Source<Payment>

    val anything: Source<Any> = ListSource(listOf("EUR"))   // Source<String> used as Source<Any>
    println("first of anything: ${anything.next()}")
}
