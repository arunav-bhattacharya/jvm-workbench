package workbench.coroutines.l11

import kotlinx.coroutines.runBlocking
import reactor.core.publisher.Mono

/**
 * The quote as a Reactor Mono, for a Spring WebFlux or Reactor-based caller.
 *
 * Rules: the Mono is cold (nothing runs until someone subscribes, and each subscription asks
 * again), it completes empty when [QuoteSource.quote] returns null, and disposing the
 * subscription cancels the coroutine.
 *
 * Bug: runBlocking asks for the quote the moment quoteMono is called, blocking the caller's
 * thread, before anyone subscribes, and only once however many subscribers come. Disposing a
 * subscription can't cancel a call that has already finished.
 */
fun quoteMono(source: QuoteSource, req: AuthRequest): Mono<Quote> =
    Mono.justOrEmpty(runBlocking { source.quote(req) })
