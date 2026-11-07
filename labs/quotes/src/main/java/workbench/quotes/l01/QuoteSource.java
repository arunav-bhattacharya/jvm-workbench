package workbench.quotes.l01;

import java.util.concurrent.CompletableFuture;

/**
 * Where the server gets its prices. The handler calls {@link #quote} on the event loop, so an
 * implementation must return at once and complete the future later, from any thread.
 * Cancelling the future means nobody wants the answer any more.
 */
public interface QuoteSource {
    CompletableFuture<Quote> quote(String symbol);
}
