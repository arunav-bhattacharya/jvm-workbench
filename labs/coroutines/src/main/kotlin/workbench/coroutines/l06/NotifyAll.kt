package workbench.coroutines.l06

import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlin.time.Duration

/**
 * Sends the "payment received" notification on every channel at the same time and returns
 * the outcome per channel. The caller is the payment request, which waits for the result.
 *
 * Rules:
 * - One failing channel must not stop the others: its outcome is Failed(<exception message>).
 * - A channel that takes longer than [timeout] counts as Failed("timed out").
 * - If the caller is cancelled, every send is cancelled and notifyAll does not return a map.
 *
 * Bug: runCatching around await() looks like it handles failures, but a failed async
 * cancels this coroutineScope (and the other sends) whether or not anyone awaits it.
 * There is no timeout either.
 */
suspend fun notifyAll(paymentId: String, senders: Map<Channel, Sender>, timeout: Duration): Map<Channel, Outcome> =
    coroutineScope {
        val sends = senders.mapValues { (_, sender) -> async { sender.send(paymentId) } }
        sends.mapValues { (_, send) ->
            runCatching { send.await() }
                .fold({ Outcome.Delivered }, { Outcome.Failed(it.message ?: it.toString()) })
        }
    }
