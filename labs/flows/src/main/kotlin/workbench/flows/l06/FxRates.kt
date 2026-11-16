package workbench.flows.l06

import kotlinx.coroutines.flow.Flow

/**
 * The rate for [pair] from [primary], with a fallback:
 *
 * 1. each call to the primary gets 300 ms (timeout() on the primary's flow),
 * 2. a transient failure (see isTransient) is retried with retryWithBackoff() and its defaults,
 * 3. when the primary has given up on a transient failure, the rate comes from [fallback],
 * 4. a non-transient failure (a bad pair, a bug) reaches the caller unchanged, with no fallback,
 * 5. if the CALLER is cancelled, nothing is retried and the fallback is never called.
 */
fun fxRate(pair: String, primary: RateProvider, fallback: RateProvider): Flow<Rate> =
    TODO("timeout, then retryWithBackoff, then catch with a fallback")

/**
 * The payments of [feed], retried with retryWithBackoff() when the feed fails mid-way.
 * A retry collects the feed again from the top, so payments already delivered come again.
 * Every payment id must reach the collector exactly once per collection of this flow.
 *
 * Bug: duplicates after a retry.
 */
fun uniquePayments(feed: Flow<Payment>): Flow<Payment> =
    feed.retryWithBackoff()
