package workbench.coroutines.l11

import kotlinx.coroutines.reactor.mono
import reactor.core.publisher.Mono

// mono {} is cold: it starts the coroutine on subscription, once per subscriber.
// A null result completes the Mono empty, and cancelling the subscription cancels the coroutine.
fun quoteMono(source: QuoteSource, req: AuthRequest): Mono<Quote> =
    mono { source.quote(req) }
