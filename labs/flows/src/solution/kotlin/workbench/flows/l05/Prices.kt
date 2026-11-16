package workbench.flows.l05

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine

fun eurPrices(usdCents: Flow<Long>, usdToEur: Flow<Double>): Flow<EurPrice> =
    // combine keeps a board with the latest value of each flow. It emits once both slots are filled,
    // then once per update. zip would pair the n-th price with the n-th rate instead.
    combine(usdCents, usdToEur) { cents, rate -> EurPrice(cents, rate, Math.round(cents * rate)) }
