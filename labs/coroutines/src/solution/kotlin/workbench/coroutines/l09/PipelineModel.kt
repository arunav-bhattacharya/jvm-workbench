package workbench.coroutines.l09

// Shared model. This file is the same in src/main and src/solution.

/** One reading from the oven probe: which dish, and how hot it is inside. */
data class Reading(val dish: String, val celsius: Int)

/** A handle for one registered listener. */
fun interface Registration {
    fun unregister()
}

/**
 * An older wireless oven probe with a listener API. It calls each listener on its own thread,
 * with every new reading, and keeps calling it until the listener is unregistered.
 */
interface OvenProbe {
    fun register(listener: (Reading) -> Unit): Registration
}

/** A shop's answer when we phone round for eggs. */
data class Offer(val shop: String, val priceCents: Int)
