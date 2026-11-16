package workbench.flows.l05

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flatMapMerge
import kotlinx.coroutines.flow.flowOf

/**
 * The fee of every merchant in [merchants], with at most 4 lookups in flight at once.
 * Output order is completion order. 10 lookups of 100 ms each must finish in 300 ms.
 *
 * Bug: it looks concurrent, but the profile shows one lookup at a time, 1000 ms in all.
 */
@OptIn(ExperimentalCoroutinesApi::class) // flatMapMerge is experimental in 1.11.0
fun fees(merchants: Flow<String>, service: FeeService): Flow<Fee> =
    merchants.flatMapMerge(concurrency = 4) { merchant ->
        val fee = service.lookup(merchant)
        flowOf(fee)
    }

/**
 * Like [fees], but a lookup that throws IOException must not take the others down:
 * that merchant gets `default(merchant)` instead, at the moment its lookup failed, and every
 * other lookup carries on. At most 4 in flight.
 */
fun feesOrDefault(merchants: Flow<String>, service: FeeService, default: (String) -> Fee): Flow<Fee> =
    TODO("flatMapMerge, with the error handled inside each merchant's own flow")
