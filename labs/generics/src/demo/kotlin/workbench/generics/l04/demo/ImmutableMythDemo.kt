package workbench.generics.l04.demo

/** `out` limits which TYPES flow in. It does not stop state from changing. */
class Shelf<out T>(private val items: MutableList<T>) {   // a private MutableList<T> is fine in an out class
    fun take(): T = items.removeAt(0)                       // changes state, still only hands T out
    fun clear() = items.clear()                             // changes state, mentions no T at all
    val size: Int get() = items.size
}

fun main() {
    val shelf: Shelf<Payment> = Shelf(mutableListOf(CardPayment("pay_1", 1_200, "4242"), CardPayment("pay_2", 350, "0005")))
    println("took ${shelf.take().id}, ${shelf.size} left")
    shelf.clear()
    println("after clear: ${shelf.size} left")

    // The same is true of a use-site out projection: no add, but clear and removeAt still work.
    val view: MutableList<out Payment> = mutableListOf(CardPayment("pay_3", 99, "1111"))
    view.removeAt(0)
    println("view after removeAt: ${view.size} left")
    // view.add(CardPayment("pay_4", 10, "2222"))      // uncomment: which rule stops this?
}
