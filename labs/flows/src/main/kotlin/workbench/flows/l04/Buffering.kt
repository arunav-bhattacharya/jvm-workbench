package workbench.flows.l04

import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.buffer

/**
 * Reprices the checkout for EVERY rate, in order. The FX feed may run ahead of a slow
 * [reprice], so the feed's waits and the repricing overlap.
 * With a tick every 100 ms and 300 ms per repricing, three ticks take 1000 ms, not 1200.
 */
fun everyRate(rates: Flow<Rate>, reprice: suspend (Rate) -> Quote): Flow<Quote> =
    TODO("let the feed run ahead into a buffer, then reprice")

/**
 * Reprices at the NEWEST rate: when [reprice] is busy, rates that arrive meanwhile are
 * skipped except the latest. Every repricing that starts is finished.
 * Three ticks at 100 ms with 300 ms repricing: ticks 1 and 3, done at 700 ms.
 * A repricer faster than the feed sees every tick.
 */
fun latestRate(rates: Flow<Rate>, reprice: suspend (Rate) -> Quote): Flow<Quote> =
    TODO("keep only the newest rate while the repricer is busy")

/**
 * A new rate CANCELS the repricing in progress, so only the newest rate's quote survives.
 * Three ticks at 100 ms with 300 ms repricing: only tick 3, done at 600 ms.
 */
fun cancelStale(rates: Flow<Rate>, reprice: suspend (Rate) -> Quote): Flow<Quote> =
    TODO("cancel the stale repricing when a new rate arrives")

/**
 * Lets the settlement-file reader run ahead of a slow ledger writer, so file reads and
 * ledger writes overlap.
 *
 * Rules: a posting must NEVER be dropped, and the reader may run at most 64 postings ahead
 * (64 waiting, plus the one the ledger is writing), so memory stays bounded.
 *
 * Bug: a teammate wrote this to "keep the latest 64 if the ledger falls behind".
 */
fun towardsLedger(postings: Flow<Posting>): Flow<Posting> =
    postings.buffer(onBufferOverflow = BufferOverflow.DROP_OLDEST)
