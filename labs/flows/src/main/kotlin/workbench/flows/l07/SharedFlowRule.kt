package workbench.flows.l07

import kotlinx.coroutines.channels.BufferOverflow

/**
 * Predicts what [calls] back-to-back `tryEmit(1)`, `tryEmit(2)`, ... return on a
 * `MutableSharedFlow<Int>(replay, extraBufferCapacity, policy)`.
 *
 * The setup: [subscribers] subscribers have subscribed and are waiting for a value, and the
 * calls run one after another on one thread, so no subscriber gets to take a value between
 * two calls. Write the rule from the lesson: what decides when the one shared buffer is full,
 * and what each policy does then. Don't create a real flow here.
 */
fun predictTryEmits(
    replay: Int,
    extraBufferCapacity: Int,
    policy: BufferOverflow,
    subscribers: Int,
    calls: Int,
): List<Boolean> = TODO("write the tryEmit rule: no subscribers, the buffer size, the policy")

/**
 * Same setup with exactly one waiting subscriber: which of the values 1..[calls] does it
 * receive in the end, once it is allowed to run? (Use what the buffer kept.)
 */
fun predictReceived(
    replay: Int,
    extraBufferCapacity: Int,
    policy: BufferOverflow,
    calls: Int,
): List<Int> = TODO("which values stayed in the buffer for the waiting subscriber?")
