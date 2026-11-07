package workbench.coroutines.l11

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.future.future
import java.util.concurrent.CompletableFuture

class AuthorizationFacade(
    private val authorize: suspend (AuthRequest) -> Decision,
    private val dispatcher: CoroutineDispatcher = Dispatchers.Default,
) : AutoCloseable {
    // the facade owns its coroutines: a supervisor, so one failed authorization doesn't cancel the rest
    private val scope = CoroutineScope(SupervisorJob() + dispatcher)

    // future {} starts a coroutine in the scope and returns a CompletableFuture for it.
    // Cancelling the future cancels the coroutine; a failure completes the future exceptionally.
    fun authorizeAsync(req: AuthRequest): CompletableFuture<Decision> =
        scope.future { authorize(req) }

    override fun close() = scope.cancel() // every future still running completes as cancelled
}
