package workbench.executors.l07;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.function.BiConsumer;

/**
 * Asks several suppliers for a quote (a price offer) and returns the lowest price.
 *
 * <p>{@link #best} must return at once and complete later:
 * <ol>
 *   <li>Ask every supplier at the same time, each on {@code io} (the calls block).</li>
 *   <li>Give each supplier its own deadline of {@code timeout}. A supplier that throws or misses
 *       its deadline is skipped: report it once with {@code onSkip.accept(providerName, cause)},
 *       where {@code cause} is the supplier's own exception (or a {@code TimeoutException}),
 *       never a {@code CompletionException} wrapper.</li>
 *   <li>Complete with the lowest quote among the suppliers that answered.</li>
 *   <li>If every supplier was skipped, fail with {@link NoQuoteException}.</li>
 * </ol>
 */
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
        throw new UnsupportedOperationException("TODO: supplyAsync per supplier, orTimeout, handle, then allOf and pick the lowest");
    }

    /**
     * Strips {@code CompletionException} and {@code ExecutionException} wrappers and returns the
     * first exception that is neither (or the last wrapper, if it has no cause).
     */
    public static Throwable unwrap(Throwable t) {
        throw new UnsupportedOperationException("TODO: loop while t is a CompletionException or ExecutionException with a cause");
    }
}
