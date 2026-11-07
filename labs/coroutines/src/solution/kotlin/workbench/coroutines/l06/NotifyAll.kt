package workbench.coroutines.l06

import kotlinx.coroutines.async
import kotlinx.coroutines.supervisorScope
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.coroutines.cancellation.CancellationException
import kotlin.time.Duration

suspend fun notifyAll(paymentId: String, senders: Map<Channel, Sender>, timeout: Duration): Map<Channel, Outcome> =
    // 1. a supervisor: a failed child does not cancel its siblings or this scope.
    //    Its exception is kept in its Deferred, and await() rethrows it.
    supervisorScope {
        val sends = senders.mapValues { (_, sender) ->
            // 2. each channel gets its own deadline; null means "timed out"
            async { withTimeoutOrNull(timeout) { sender.send(paymentId) } }
        }
        sends.mapValues { (_, send) ->
            try {
                if (send.await() == null) Outcome.Failed("timed out") else Outcome.Delivered
            } catch (e: CancellationException) {
                throw e // 3. the caller was cancelled: don't turn that into an outcome
            } catch (e: Exception) {
                Outcome.Failed(e.message ?: e.toString())
            }
        }
    }
