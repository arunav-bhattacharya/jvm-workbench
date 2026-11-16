package workbench.flows.l05

import kotlinx.coroutines.flow.Flow

/**
 * Every checkout price in EUR at the LATEST known rate.
 *
 * - Nothing is emitted until there is both a price and a rate.
 * - After that, a new price or a new rate each produce one EurPrice right away.
 * - eurCents = Math.round(usdCents * usdToEur).
 */
fun eurPrices(usdCents: Flow<Long>, usdToEur: Flow<Double>): Flow<EurPrice> =
    TODO("pair each update with the latest value of the other flow")
