package workbench.coroutines.l11

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.asExecutor
import kotlinx.coroutines.runBlocking
import java.util.concurrent.CompletableFuture

/**
 * The door that Java code uses to reach the Kotlin [cook] function.
 *
 * Rules:
 * - [cookAsync] returns at once with a CompletableFuture of the outcome.
 * - Cancelling that future cancels the cooking coroutine.
 * - A failure reaches the Java caller as the future's exception.
 * - [close] cancels every order still cooking. Give the door a scope it owns.
 *
 * Bug: runBlocking inside supplyAsync blocks a dispatcher thread for every order, and the
 * coroutine has no link to the future: cancelling the future, or closing the door, stops nothing.
 */
class KitchenDoor(
    private val cook: suspend (Order) -> Outcome,
    private val dispatcher: CoroutineDispatcher = Dispatchers.Default,
) : AutoCloseable {

    fun cookAsync(order: Order): CompletableFuture<Outcome> =
        CompletableFuture.supplyAsync({ runBlocking { cook(order) } }, dispatcher.asExecutor())

    override fun close() {
        // nothing to cancel: the door owns no scope
    }
}
