package workbench.memory.l07;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.function.Function;

public final class IdempotencyCache {
    private final Map<String, Entry> entries;

    public IdempotencyCache(int maxEntries) {
        // leak 1 fixed: a bound. accessOrder = true makes get() move an entry to the end,
        // so the eldest entry is the least recently used one, and removeEldestEntry drops it.
        this.entries = new LinkedHashMap<>(16, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<String, Entry> eldest) {
                return size() > maxEntries;
            }
        };
    }

    // synchronized: LinkedHashMap is not thread-safe, and even get() changes its order in access mode.
    // The lock also covers the handler, so two copies of a retry can't both charge; a real service would
    // lock per key instead of for the whole cache.
    public synchronized PaymentResponse getOrCompute(PaymentRequest request, Function<PaymentRequest, PaymentResponse> handler) {
        byte[] digest = sha256(request.rawBody());
        Entry seen = entries.get(request.idempotencyKey());
        if (seen != null) {
            if (!MessageDigest.isEqual(seen.bodyDigest(), digest)) {
                throw new IdempotencyConflictException(request.idempotencyKey());
            }
            return seen.response();
        }
        PaymentResponse response = handler.apply(request);
        entries.put(request.idempotencyKey(), new Entry(digest, response));
        return response;
    }

    public synchronized int size() {
        return entries.size();
    }

    // leak 2 fixed: keep a 32-byte fingerprint of the body instead of the whole request
    private record Entry(byte[] bodyDigest, PaymentResponse response) {}

    private static byte[] sha256(byte[] body) {
        try {
            return MessageDigest.getInstance("SHA-256").digest(body);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("every JDK has SHA-256", e);
        }
    }
}
