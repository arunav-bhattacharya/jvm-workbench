package workbench.startup.l01.demo

/** Prints the moment each initializer runs. Predict the order before you run it. */
private val log = mutableListOf<String>()

private fun build(who: String): Map<String, String> {
    log += who                                           // the expensive part would go here
    return mapOf("411111" to "Northwind Bank")
}

/** A companion's properties are static fields of Fees: built when Fees is initialized. */
class Fees {
    companion object {
        val table = build("Fees companion: table built with the outer class")
        fun version() = "fees-v1"
    }
}

/** A nested object is its own class, with its own initializer: the Kotlin holder idiom. */
object Bins {
    fun version() = "bins-v1"
    fun table() = Holder.table

    private object Holder {
        val table = build("Bins.Holder: table built")
    }
}

/** by lazy: built on the first get, under a lock by default (LazyThreadSafetyMode.SYNCHRONIZED). */
object Rates {
    fun version() = "rates-v1"
    val table by lazy { build("Rates lazy: table built") }
}

fun main() {
    log += "main starts"
    Fees.version()
    Bins.version()
    Rates.version()
    log += "-- all three versions read --"
    Bins.table()
    Rates.table
    log += "-- Bins.table() and Rates.table read --"
    log.forEach(::println)
}
