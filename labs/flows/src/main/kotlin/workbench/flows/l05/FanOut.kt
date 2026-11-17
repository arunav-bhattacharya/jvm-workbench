package workbench.flows.l05

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flatMapMerge
import kotlinx.coroutines.flow.flowOf

/**
 * Every dish of [dishes], cooked on [stove], with at most 4 dishes on the burners at once.
 * Plates come out in the order they are ready. 10 dishes of 100 ms each must be ready in 300 ms.
 *
 * Bug: it looks concurrent, but the kitchen log shows one dish at a time, 1,000 ms in all.
 */
@OptIn(ExperimentalCoroutinesApi::class) // flatMapMerge is experimental in 1.11.0
fun cookAll(dishes: Flow<String>, stove: Stove): Flow<Plate> =
    dishes.flatMapMerge(concurrency = 4) { dish ->
        val plate = stove.cook(dish)
        flowOf(plate)
    }

/**
 * Like [cookAll], but a dish that burns must not take the others down: that dish gets
 * `substitute(dish)` instead, at the moment it burnt, and every other dish carries on.
 * Any other failure is rethrown. At most 4 dishes on the burners.
 */
fun cookAllOrSubstitute(dishes: Flow<String>, stove: Stove, substitute: (String) -> Plate): Flow<Plate> =
    TODO("flatMapMerge, with the burnt dish handled inside that dish's own flow")
