package workbench.flows.l07

import kotlinx.coroutines.channels.BufferOverflow

fun predictTryEmits(
    replay: Int,
    extraBufferCapacity: Int,
    policy: BufferOverflow,
    subscribers: Int,
    calls: Int,
): List<Boolean> {
    val capacity = replay + extraBufferCapacity        // ONE buffer, shared by every subscriber
    return List(calls) { i ->
        when {
            subscribers == 0 -> true                   // nobody to wait for: it never fails
            policy != BufferOverflow.SUSPEND -> true   // a drop policy always "succeeds" (it drops)
            else -> i < capacity                       // full once the slowest has `capacity` untaken values
        }
    }
}

fun predictReceived(
    replay: Int,
    extraBufferCapacity: Int,
    policy: BufferOverflow,
    calls: Int,
): List<Int> {
    val capacity = replay + extraBufferCapacity
    val all = (1..calls).toList()
    return when (policy) {
        BufferOverflow.SUSPEND -> all.take(capacity)      // tryEmit refused the rest (0 capacity: nothing)
        BufferOverflow.DROP_LATEST -> all.take(capacity)  // the new values were dropped, for everyone
        BufferOverflow.DROP_OLDEST -> all.takeLast(capacity) // the subscriber was pushed past the old ones
    }
}
