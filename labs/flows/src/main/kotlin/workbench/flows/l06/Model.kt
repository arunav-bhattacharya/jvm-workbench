package workbench.flows.l06

import kotlinx.coroutines.flow.Flow

// Shared model. This file is the same in src/main and src/solution.

/** A loaf of bread, and which bakery baked it. */
data class Loaf(val kind: String, val baker: String)

/** A bakery that takes orders by phone. Every collection of [order] is one phone call. */
fun interface Bakery {
    fun order(kind: String): Flow<Loaf>
}

/** One line of the grocer's delivery note. [id] is unique per line. */
data class NoteLine(val id: String, val item: String)
