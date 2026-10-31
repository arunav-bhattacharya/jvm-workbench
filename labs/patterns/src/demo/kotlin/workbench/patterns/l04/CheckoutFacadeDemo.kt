package workbench.patterns.l04

// A facade over inventory, payments and notifications: one call, the right order, cleanup on failure.

interface Inventory { fun reserve(sku: String): Boolean; fun release(sku: String) }
fun interface Payments { fun charge(amountMinor: Long, token: String): String }
fun interface Notifier { fun send(to: String, message: String) }

class CheckoutFacade(
    private val inventory: Inventory,
    private val payments: Payments,
    private val notifier: Notifier,
) {
    fun checkout(sku: String, amountMinor: Long, token: String, email: String): String {
        check(inventory.reserve(sku)) { "out of stock: $sku" }                     // 1. reserve
        val receipt = try {
            payments.charge(amountMinor, token)                                     // 2. charge
        } catch (e: RuntimeException) {
            inventory.release(sku)                                                  // 3. undo the reservation
            throw e
        }
        notifier.send(email, "paid $receipt")                                       // 4. tell the customer
        return receipt
    }
}

fun main() {
    val reserved = mutableSetOf<String>()
    val inventory = object : Inventory {
        override fun reserve(sku: String) = reserved.add(sku)
        override fun release(sku: String) { reserved.remove(sku) }
    }
    val payments = Payments { amount, token ->
        check(token != "tok_declined") { "card declined" }
        "R-$amount"
    }
    val notifier = Notifier { to, message -> println("  mail to $to: $message") }

    val facade = CheckoutFacade(inventory, payments, notifier)
    println("receipt: " + facade.checkout("sku-1", 1_250, "tok_ok", "anna@example.com"))
    try {
        facade.checkout("sku-2", 990, "tok_declined", "anna@example.com")
    } catch (e: IllegalStateException) {
        println("failed: ${e.message}; still reserved: $reserved")
    }
}
