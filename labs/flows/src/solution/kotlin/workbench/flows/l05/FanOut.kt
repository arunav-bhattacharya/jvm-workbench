package workbench.flows.l05

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.flatMapMerge
import kotlinx.coroutines.flow.flow

@OptIn(ExperimentalCoroutinesApi::class) // flatMapMerge is experimental in 1.11.0
fun cookAll(dishes: Flow<String>, stove: Stove): Flow<Plate> =
    dishes.flatMapMerge(concurrency = 4) { dish ->
        // this lambda runs in ONE producer coroutine, one dish at a time, before a burner is free.
        // So it only builds the inner flow; the slow cooking goes inside it, where 4 can run at once.
        flow { emit(stove.cook(dish)) }
    }

@OptIn(ExperimentalCoroutinesApi::class)
fun cookAllOrSubstitute(dishes: Flow<String>, stove: Stove, substitute: (String) -> Plate): Flow<Plate> =
    dishes.flatMapMerge(concurrency = 4) { dish ->
        flow { emit(stove.cook(dish)) }
            // catch INSIDE the inner flow: only this dish's lane ends with a substitute.
            // A catch after flatMapMerge would see the error only after it had cancelled every other lane.
            .catch { e -> if (e is Burnt) emit(substitute(dish)) else throw e }
    }
