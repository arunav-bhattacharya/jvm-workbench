package workbench.startup.l01.demo

/** Prints the moment each initializer runs. Predict the order before you run it. */
private val log = mutableListOf<String>()

private fun build(who: String): Map<String, String> {
    log += who                                           // the expensive part would go here
    return mapOf("411111" to "North depot")
}

/** A companion's properties are static fields of Postcodes: built when Postcodes is initialized. */
class Postcodes {
    companion object {
        val table = build("Postcodes companion: table built with the outer class")
        fun version() = "postcodes-v1"
    }
}

/** A nested object is its own class, with its own initializer: the Kotlin holder idiom. */
object Depots {
    fun version() = "depots-v1"
    fun table() = Holder.table

    private object Holder {
        val table = build("Depots.Holder: table built")
    }
}

/** by lazy: built on the first get, under a lock by default (LazyThreadSafetyMode.SYNCHRONIZED). */
object Routes {
    fun version() = "routes-v1"
    val table by lazy { build("Routes lazy: table built") }
}

fun main() {
    log += "main starts"
    Postcodes.version()
    Depots.version()
    Routes.version()
    log += "-- all three versions read --"
    Depots.table()
    Routes.table
    log += "-- Depots.table() and Routes.table read --"
    log.forEach(::println)
}
