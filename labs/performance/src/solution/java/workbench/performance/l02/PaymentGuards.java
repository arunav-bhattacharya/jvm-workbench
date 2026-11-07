package workbench.performance.l02;

public final class PaymentGuards {
    public static final long MAX_CENTS = 100_000_000L;
    public static final int MAX_KEY_LENGTH = 64;

    private PaymentGuards() { }

    // hot path only: two comparisons and a call to the cold helper (21 bytes of bytecode)
    public static long requireAmount(long cents) {
        if (cents <= 0 || cents > MAX_CENTS) throw badAmount(cents);
        return cents;
    }

    // the same idea: the message is built somewhere C2 doesn't need to look (27 bytes)
    public static String requireIdempotencyKey(String key) {
        if (key == null || key.isEmpty() || key.length() > MAX_KEY_LENGTH) throw badKey(key);
        return key;
    }

    // cold paths: big, rarely run, and no longer counted against the callers' inlining budget.
    // They return the exception, so the caller writes "throw badAmount(cents)" and javac
    // (and the next reader) can see that the method ends there.
    private static IllegalArgumentException badAmount(long cents) {
        return new IllegalArgumentException(
                String.format("amount must be between 1 and %d cents, got %d", MAX_CENTS, cents));
    }

    private static IllegalArgumentException badKey(String key) {
        String got = key == null ? "null" : String.valueOf(key.length());
        return new IllegalArgumentException(
                String.format("idempotency key must be 1 to %d characters, got %s", MAX_KEY_LENGTH, got));
    }
}
