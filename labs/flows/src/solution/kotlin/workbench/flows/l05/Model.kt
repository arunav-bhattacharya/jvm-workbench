package workbench.flows.l05

// Shared model. This file is the same in src/main and src/solution.

/** One cooked dish, and who made it: "stove", or "substitute" when the dish burnt. */
data class Plate(val dish: String, val madeBy: String = "stove")

/** The stove. Cooking one dish takes tens to hundreds of ms, and a dish may burn (see [Burnt]). */
fun interface Stove {
    suspend fun cook(dish: String): Plate
}

/** What [Stove.cook] throws when a dish burns. */
class Burnt(dish: String) : Exception("burnt: $dish")

/** What the oven-door screen shows: a thermometer reading against the dial, and the degrees still to go. */
data class OvenGap(val celsius: Int, val dial: Int, val toGo: Int)
