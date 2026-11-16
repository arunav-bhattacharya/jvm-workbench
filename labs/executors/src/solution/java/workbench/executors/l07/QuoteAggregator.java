package workbench.executors.l07;

import java.time.Duration;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;
import java.util.function.BiConsumer;

public final class QuoteAggregator {
    private final List<QuoteProvider> providers;
    private final Executor io;
    private final Duration timeout;
    private final BiConsumer<String, Throwable> onSkip;

    public QuoteAggregator(List<QuoteProvider> providers, Executor io, Duration timeout, BiConsumer<String, Throwable> onSkip) {
        this.providers = List.copyOf(providers);
        this.io = io;
        this.timeout = timeout;
        this.onSkip = onSkip;
    }

    public CompletableFuture<Quote> best(String item) {
        // 1. ask every supplier now; each ask can't fail, it turns a failure into an empty Optional
        List<CompletableFuture<Optional<Quote>>> asks = providers.stream()
                .map(p -> ask(p, item))
                .toList();

        // 2. allOf completes when every ask has completed
        return CompletableFuture.allOf(asks.toArray(CompletableFuture[]::new))
                // 3. every ask is done here, so join() returns at once and never blocks
                .thenApply(done -> asks.stream()
                        .map(CompletableFuture::join)
                        .flatMap(Optional::stream)
                        .min(Comparator.comparing(Quote::price))
                        // 4. throwing here fails the returned future with this exception as the cause
                        .orElseThrow(() -> new NoQuoteException(item)));
    }

    private CompletableFuture<Optional<Quote>> ask(QuoteProvider p, String item) {
        return CompletableFuture.supplyAsync(() -> new Quote(p.name(), p.quote(item)), io)
                // the deadline belongs to this supplier, not to the whole call
                .orTimeout(timeout.toMillis(), TimeUnit.MILLISECONDS)
                .handle((quote, ex) -> {
                    if (ex == null) {
                        return Optional.of(quote);
                    }
                    // supplyAsync wraps the supplier's exception in a CompletionException; orTimeout doesn't
                    onSkip.accept(p.name(), unwrap(ex));
                    return Optional.<Quote>empty();      // recover: one bad supplier is not a failed call
                });
    }

    public static Throwable unwrap(Throwable t) {
        Throwable current = t;
        while ((current instanceof CompletionException || current instanceof ExecutionException)
                && current.getCause() != null) {
            current = current.getCause();
        }
        return current;
    }
}
