package workbench.patterns.l04

// A facade over stock, vans and messages: one call, the right order, cleanup on failure.

interface Stock { fun reserve(product: String): Boolean; fun release(product: String) }
fun interface Vans { fun book(product: String, address: String): String }
fun interface Notifier { fun send(to: String, message: String) }

class FrontDesk(
    private val stock: Stock,
    private val vans: Vans,
    private val notifier: Notifier,
) {
    fun order(product: String, address: String, email: String): String {
        check(stock.reserve(product)) { "out of stock: $product" }               // 1. reserve
        val booking = try {
            vans.book(product, address)                                         // 2. book a van
        } catch (e: RuntimeException) {
            stock.release(product)                                              // 3. undo the reservation
            throw e
        }
        notifier.send(email, "on its way, booking $booking")                    // 4. tell the customer
        return booking
    }
}

fun main() {
    val reserved = mutableSetOf<String>()
    val stock = object : Stock {
        override fun reserve(product: String) = reserved.add(product)
        override fun release(product: String) { reserved.remove(product) }
    }
    val vans = Vans { product, address ->
        check("Island" !in address) { "no van goes to $address" }
        "V-$product"
    }
    val notifier = Notifier { to, message -> println("  mail to $to: $message") }

    val desk = FrontDesk(stock, vans, notifier)
    println("booking: " + desk.order("flour", "12 Mill Lane", "anna@example.com"))
    try {
        desk.order("sugar", "Gull Island", "ben@example.com")
    } catch (e: IllegalStateException) {
        println("failed: ${e.message}; still reserved: $reserved")
    }
}
