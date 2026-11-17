package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext

class RecipeCardService(
    private val book: BlockingRecipeBook,
    private val printer: CardPrinter,
    private val io: CoroutineDispatcher,
    private val cpu: CoroutineDispatcher,
) {
    suspend fun printCard(dish: String): ByteArray {
        // 1. the blocking call runs on an IO thread; the caller's thread is free meanwhile
        val steps = withContext(io) { book.loadSteps(dish) }
        // 2. CPU work runs on the CPU dispatcher; withContext then resumes us on the caller's dispatcher
        return withContext(cpu) { printer.render(steps) }
    }
}
