package workbench.memory.l07;

import java.util.Arrays;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

/**
 * Remembers the response to each idempotency key, so a client that retries a payment gets the same
 * answer instead of a second charge.
 *
 * <p>In production this cache runs the service out of memory after a few days. Find what it keeps
 * alive and fix it. The cache must keep at most {@code maxEntries} entries, dropping the least
 * recently used one first, and it must keep rejecting a retry whose body differs from the original,
 * without holding on to request bodies.
 */
public final class IdempotencyCache {
    private final int maxEntries;
    private final Map<String, Entry> entries = new ConcurrentHashMap<>();

    public IdempotencyCache(int maxEntries) {
        this.maxEntries = maxEntries;
    }

    /**
     * Returns the response stored for the request's idempotency key. For a new key, calls
     * {@code handler}, stores its response and returns it. Throws {@link IdempotencyConflictException}
     * when the key was seen before with a different body.
     */
    public PaymentResponse getOrCompute(PaymentRequest request, Function<PaymentRequest, PaymentResponse> handler) {
        Entry seen = entries.get(request.idempotencyKey());
        if (seen != null) {
            if (!Arrays.equals(seen.request().rawBody(), request.rawBody())) {
                throw new IdempotencyConflictException(request.idempotencyKey());
            }
            return seen.response();
        }
        PaymentResponse response = handler.apply(request);
        entries.put(request.idempotencyKey(), new Entry(request, response));
        return response;
    }

    /** How many responses the cache holds. */
    public int size() {
        return entries.size();
    }

    private record Entry(PaymentRequest request, PaymentResponse response) {}
}
