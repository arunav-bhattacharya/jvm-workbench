package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineDispatcher

/**
 * Prints a recipe card for one dish.
 *
 * Callers run on a small pool of threads. This version does all the work on the caller's thread:
 * the blocking database call and the CPU-heavy layout both hold a caller's thread.
 *
 * Move the blocking [BlockingRecipeBook.loadSteps] call to [io] and the
 * [CardPrinter.render] call to [cpu]. The caller must get the result back on its own dispatcher.
 */
class RecipeCardService(
    private val book: BlockingRecipeBook,
    private val printer: CardPrinter,
    private val io: CoroutineDispatcher,
    private val cpu: CoroutineDispatcher,
) {
    suspend fun printCard(dish: String): ByteArray {
        val steps = book.loadSteps(dish)
        return printer.render(steps)
    }
}
