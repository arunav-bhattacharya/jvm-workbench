package workbench.patterns.l11;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Supplier;

/**
 * A small circuit breaker, safe to share between request threads.
 *
 * <pre>
 *   Closed(n)    calls go through. Each failure adds one to n; a success resets n to 0.
 *                The failure that makes n reach failureThreshold opens the breaker.
 *   Open(until)  calls are rejected with CallNotPermitted WITHOUT running the operation,
 *                until the clock reaches {@code until} (now + openFor when it opened).
 *   HalfOpen     the first call after {@code until} moves Open to HalfOpen and runs as the ONE probe.
 *                Other calls are rejected while the probe runs. A successful probe closes the
 *                breaker (Closed(0)); a failed one opens it again for another openFor.
 * </pre>
 *
 * The state lives in an AtomicReference and only changes through compareAndSet or updateAndGet.
 * Time comes from the injected Clock, so tests can move it forward without sleeping.
 */
public final class CircuitBreaker {

    public sealed interface State permits Closed, Open, HalfOpen {}
    public record Closed(int consecutiveFailures) implements State {}
    public record Open(Instant until) implements State {}
    public record HalfOpen() implements State {}

    /** Thrown instead of running the operation when the breaker is open or a probe is in flight. */
    public static final class CallNotPermitted extends RuntimeException {
        public CallNotPermitted(String message) { super(message); }
    }

    private final AtomicReference<State> state = new AtomicReference<>(new Closed(0));
    private final int failureThreshold;
    private final Duration openFor;
    private final Clock clock;

    public CircuitBreaker(int failureThreshold, Duration openFor, Clock clock) {
        this.failureThreshold = failureThreshold;
        this.openFor = openFor;
        this.clock = clock;
    }

    /** The current state. Given. */
    public State state() {
        return state.get();
    }

    /**
     * Runs {@code op} through the breaker and returns its result. If {@code op} throws a RuntimeException,
     * record the failure and rethrow the SAME exception.
     */
    public <T> T call(Supplier<T> op) {
        throw new UnsupportedOperationException("TODO: check the state, run op, then move the state on success or failure");
    }
}
