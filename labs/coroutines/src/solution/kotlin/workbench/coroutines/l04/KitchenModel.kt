package workbench.coroutines.l04

import kotlin.coroutines.AbstractCoroutineContextElement
import kotlin.coroutines.CoroutineContext

// Shared model. This file is the same in src/main and src/solution.

/** One step of a recipe. */
data class Step(val dish: String, val text: String)

/** A recipe book kept in a database: every call BLOCKS the calling thread until the database answers. */
interface BlockingRecipeBook {
    fun loadSteps(dish: String): List<Step>
}

/** Pure CPU work: lays out a printable recipe card. Takes tens of milliseconds for a long recipe. */
interface CardPrinter {
    fun render(steps: List<Step>): ByteArray
}

/** A coroutine context element: a note clipped to the work, saying which guest it is for. */
class ForGuest(val name: String) : AbstractCoroutineContextElement(ForGuest) {
    companion object Key : CoroutineContext.Key<ForGuest>
    override fun toString() = "ForGuest($name)"
}
