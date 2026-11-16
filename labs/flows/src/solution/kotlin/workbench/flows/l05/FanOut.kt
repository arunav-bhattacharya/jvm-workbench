package workbench.flows.l05

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.flatMapMerge
import kotlinx.coroutines.flow.flow
import java.io.IOException

@OptIn(ExperimentalCoroutinesApi::class) // flatMapMerge is experimental in 1.11.0
fun fees(merchants: Flow<String>, service: FeeService): Flow<Fee> =
    merchants.flatMapMerge(concurrency = 4) { merchant ->
        // this lambda runs in ONE producer coroutine, one merchant at a time, before a permit is taken.
        // So it only builds the inner flow; the slow call goes inside it, where 4 can run at once.
        flow { emit(service.lookup(merchant)) }
    }

@OptIn(ExperimentalCoroutinesApi::class)
fun feesOrDefault(merchants: Flow<String>, service: FeeService, default: (String) -> Fee): Flow<Fee> =
    merchants.flatMapMerge(concurrency = 4) { merchant ->
        flow { emit(service.lookup(merchant)) }
            // catch INSIDE the inner flow: only this merchant's lane ends with a default.
            // A catch after flatMapMerge would see the error only after it had cancelled every other lane.
            .catch { e -> if (e is IOException) emit(default(merchant)) else throw e }
    }
