package workbench.patterns.l10

// A cart that can hand out a snapshot of itself and later put it back.

class Cart {
    private val items = mutableListOf<String>()
    private var coupon = ""

    fun add(item: String) { items += item }
    fun coupon(code: String) { coupon = code }
    override fun toString() = "$items coupon=$coupon"

    // callers see an opaque Memento; only Cart can read the State inside it
    interface Memento
    private data class State(val items: List<String>, val coupon: String) : Memento

    fun save(): Memento = State(items.toList(), coupon)          // copy: later edits must not leak in

    fun restore(m: Memento) {
        val s = m as State
        items.clear()
        items += s.items                                          // copy back in: the memento stays as it was
        coupon = s.coupon
    }
}

fun main() {
    val cart = Cart()
    cart.add("sku-1")
    val before = cart.save()
    cart.add("sku-2")
    cart.coupon("AUTUMN10")
    println("edited:   $cart")
    cart.restore(before)
    println("restored: $cart")
}
