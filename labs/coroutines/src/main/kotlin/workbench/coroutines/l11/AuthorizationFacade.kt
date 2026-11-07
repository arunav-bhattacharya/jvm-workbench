package workbench.coroutines.l11

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.asExecutor
import kotlinx.coroutines.runBlocking
import java.util.concurrent.CompletableFuture

/**
 * Lets Java code (a Quarkus resource, a Temporal activity) call the Kotlin [authorize] function.
 *
 * Rules:
 * - [authorizeAsync] returns at once with a CompletableFuture of the decision.
 * - Cancelling that future cancels the authorization coroutine.
 * - A failure reaches the Java caller as the future's exception.
 * - [close] cancels every authorization still running. Give the facade a scope it owns.
 *
 * Bug: runBlocking inside supplyAsync blocks a dispatcher thread for every call, and the
 * coroutine has no link to the future: cancelling the future, or closing the facade, stops nothing.
 */
class AuthorizationFacade(
    private val authorize: suspend (AuthRequest) -> Decision,
    private val dispatcher: CoroutineDispatcher = Dispatchers.Default,
) : AutoCloseable {

    fun authorizeAsync(req: AuthRequest): CompletableFuture<Decision> =
        CompletableFuture.supplyAsync({ runBlocking { authorize(req) } }, dispatcher.asExecutor())

    override fun close() {
        // nothing to cancel: the facade owns no scope
    }
}
