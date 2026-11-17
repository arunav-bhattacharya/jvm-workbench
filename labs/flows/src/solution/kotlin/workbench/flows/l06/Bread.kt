package workbench.flows.l06

import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.emitAll
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.timeout
import kotlin.time.Duration.Companion.milliseconds

@OptIn(FlowPreview::class) // timeout() is a preview API in 1.11.0
fun freshLoaf(kind: String, bakery: Bakery, backup: Bakery): Flow<Loaf> =
    bakery.order(kind)
        .timeout(300.milliseconds)        // 1. per attempt: above retryWhen, so each call gets its own 300 ms
        .retryWithBackoff()               // 2. retries IOException and TimeoutCancellationException
        .catch { e ->                     // 3. reached once retries are used up, or for an error that isn't transient
            if (!isTransient(e)) throw e  // 4. a bread nobody bakes, or a bug, is the caller's problem
            emitAll(backup.order(kind))
        }
// 5. needs no code: catch and retryWhen both let the caller's own cancellation pass through.

fun eachLineOnce(note: Flow<NoteLine>): Flow<NoteLine> = flow {
    val seen = HashSet<String>()           // one set per collection, so the flow stays cold and re-runnable
    note.retryWithBackoff().collect { line ->
        if (seen.add(line.id)) emit(line)  // a retry reads the note from the top: skip what we've sent
    }
}
