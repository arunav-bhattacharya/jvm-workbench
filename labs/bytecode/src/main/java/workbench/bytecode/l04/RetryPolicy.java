package workbench.bytecode.l04;

import java.util.Set;

/**
 * How many attempts a call gets, and which failures are worth another attempt.
 * A failure is retryable when it is an instance of one of {@code retryOn}.
 */
public record RetryPolicy(int maxAttempts, Set<Class<? extends Throwable>> retryOn) {
    public RetryPolicy {
        if (maxAttempts < 1) throw new IllegalArgumentException("maxAttempts must be at least 1");
        retryOn = Set.copyOf(retryOn);
    }

    public boolean retries(Throwable failure) {
        return retryOn.stream().anyMatch(t -> t.isInstance(failure));
    }
}
