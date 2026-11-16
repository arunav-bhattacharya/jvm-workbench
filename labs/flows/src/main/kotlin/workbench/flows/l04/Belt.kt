package workbench.flows.l04

import kotlinx.coroutines.flow.Flow

/**
 * A buffer, written by hand. Don't call buffer(): build it from flow { }, coroutineScope,
 * a Channel with [capacity] slots, and launch.
 *
 * - A second coroutine collects this flow and sends each value into the channel.
 *   send suspends only when every slot is full.
 * - The collector's own coroutine receives from the channel and emits each value downstream.
 * - With capacity n, the upstream gets n + 1 emits ahead of a collector that is stuck on its
 *   first value: n wait in the channel, one is in the collector's hands. capacity 0 is a
 *   hand-over with no slots, so exactly one emit returns.
 * - Every value arrives, in order, and an upstream failure reaches the collector.
 */
fun <T> Flow<T>.belt(capacity: Int): Flow<T> =
    TODO("flow { coroutineScope { a Channel, a launch that sends into it and closes it, a loop that emits } }")
