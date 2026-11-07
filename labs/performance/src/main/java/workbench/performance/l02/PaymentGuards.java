package workbench.performance.l02;

/**
 * Guards that run on every payment request. Both are correct, and both are too big to inline
 * at a call site C2 doesn't consider hot: C2 counts the bytecode of the error path too, even
 * though that path almost never runs.
 *
 * <p>Your job: make {@link #requireAmount} and {@link #requireIdempotencyKey} at most 35 bytes
 * of bytecode each ({@code MaxInlineSize}), without changing what they return or the exact
 * exception messages. Check the size with
 * {@code javap -c -p -cp performance/build/classes/java/main workbench.performance.l02.PaymentGuards}.
 */
public final class PaymentGuards {
    public static final long MAX_CENTS = 100_000_000L;   // 1,000,000.00
    public static final int MAX_KEY_LENGTH = 64;

    private PaymentGuards() { }

    /**
     * Returns {@code cents} when it is between 1 and {@link #MAX_CENTS}. Otherwise throws
     * {@code IllegalArgumentException("amount must be between 1 and 100000000 cents, got <cents>")}.
     */
    public static long requireAmount(long cents) {
        if (cents <= 0 || cents > MAX_CENTS) {
            throw new IllegalArgumentException(
                    String.format("amount must be between 1 and %d cents, got %d", MAX_CENTS, cents));
        }
        return cents;
    }

    /**
     * Returns {@code key} when it has 1 to {@link #MAX_KEY_LENGTH} characters. Otherwise throws
     * {@code IllegalArgumentException("idempotency key must be 1 to 64 characters, got <n>")},
     * where {@code <n>} is the length, or {@code null} when the key is null.
     */
    public static String requireIdempotencyKey(String key) {
        if (key == null || key.isEmpty() || key.length() > MAX_KEY_LENGTH) {
            String got = key == null ? "null" : String.valueOf(key.length());
            throw new IllegalArgumentException(
                    String.format("idempotency key must be 1 to %d characters, got %s", MAX_KEY_LENGTH, got));
        }
        return key;
    }
}
