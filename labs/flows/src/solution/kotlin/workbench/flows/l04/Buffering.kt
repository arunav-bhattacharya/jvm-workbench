package workbench.flows.l04

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.conflate
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.mapLatest

fun everyRate(rates: Flow<Rate>, reprice: suspend (Rate) -> Quote): Flow<Quote> =
    rates.buffer()                    // the feed runs in its own coroutine, 64 slots ahead
        .map { reprice(it) }          // repricing runs in the collector's coroutine, below the buffer

fun latestRate(rates: Flow<Rate>, reprice: suspend (Rate) -> Quote): Flow<Quote> =
    rates.conflate()                  // a one-slot plate stand: a new rate replaces the waiting one
        .map { reprice(it) }          // a repricing that has started always finishes

@OptIn(ExperimentalCoroutinesApi::class) // mapLatest is experimental in 1.11.0
fun cancelStale(rates: Flow<Rate>, reprice: suspend (Rate) -> Quote): Flow<Quote> =
    rates.mapLatest { reprice(it) }   // a new rate cancels the block in progress, waits for it, starts again

fun towardsLedger(postings: Flow<Posting>): Flow<Posting> =
    postings.buffer(64)               // SUSPEND (the default policy): a full belt makes the reader wait.
                                      // buffer(onBufferOverflow = DROP_OLDEST) is a ONE-slot buffer that drops
