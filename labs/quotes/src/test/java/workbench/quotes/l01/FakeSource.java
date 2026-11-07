package workbench.quotes.l01;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CancellationException;
import java.util.concurrent.CompletableFuture;

/**
 * An in-process provider the test controls. {@link #holding()} keeps every quote pending until
 * {@link #releaseAll()}; {@link #answering()} answers at once. It counts calls and cancellations.
 */
final class FakeSource implements QuoteSource {
    private final List<Map.Entry<String, CompletableFuture<Quote>>> pending = new ArrayList<>();   // guarded by this
    private boolean answerAtOnce;
    private int calls;
    private int cancelled;

    static FakeSource holding() {
        return new FakeSource();
    }

    static FakeSource answering() {
        FakeSource s = new FakeSource();
        s.answerAtOnce = true;
        return s;
    }

    @Override
    public CompletableFuture<Quote> quote(String symbol) {
        CompletableFuture<Quote> f = new CompletableFuture<>();
        f.whenComplete((q, e) -> {
            if (e instanceof CancellationException) {
                synchronized (this) { cancelled++; notifyAll(); }
            }
        });
        boolean now;
        synchronized (this) {
            calls++;
            now = answerAtOnce;
            if (!now) pending.add(Map.entry(symbol, f));
            notifyAll();
        }
        if (now) f.complete(Quote.live(symbol, "1.0842", "fake"));
        return f;
    }

    /** Answers everything pending, and every later call at once. */
    void releaseAll() {
        List<Map.Entry<String, CompletableFuture<Quote>>> todo;
        synchronized (this) {
            answerAtOnce = true;
            todo = List.copyOf(pending);
            pending.clear();
        }
        todo.forEach(e -> e.getValue().complete(Quote.live(e.getKey(), "1.0842", "fake")));
    }

    synchronized int calls() {
        return calls;
    }

    /** Waits up to 5 s for at least {@code n} calls; returns how many there were. */
    synchronized int awaitCalls(int n) throws InterruptedException {
        long end = System.nanoTime() + 5_000_000_000L;
        while (calls < n && System.nanoTime() < end) wait(100);
        return calls;
    }

    /** Waits up to 5 s for at least {@code n} cancellations; returns how many there were. */
    synchronized int awaitCancelled(int n) throws InterruptedException {
        long end = System.nanoTime() + 5_000_000_000L;
        while (cancelled < n && System.nanoTime() < end) wait(100);
        return cancelled;
    }
}
