package workbench.coroutines.l06

// Shared model. This file is the same in src/main and src/solution.

/** The three trays a bake-sale order needs. */
enum class Tray { COOKIES, SCONES, MUFFINS }

/** What a tray throws when it is ruined. */
class BurnedException(message: String) : Exception(message)

/** Bakes one tray for one order. Throws (usually BurnedException) if the tray is ruined. */
fun interface Baker {
    suspend fun bake(order: String)
}

sealed interface Outcome {
    data object Baked : Outcome
    data class Failed(val reason: String) : Outcome
}
