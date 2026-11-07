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

    public <T> T call(Supplier<T> op) {
        // 1. before the call: may we run it?
        State s = state.get();
        if (s instanceof Open(var until)) {
            if (clock.instant().isBefore(until)) {
                throw new CallNotPermitted("open until " + until);
            }
            // the cool-down is over: exactly one thread wins this compareAndSet and becomes the probe
            if (!state.compareAndSet(s, new HalfOpen())) {
                throw new CallNotPermitted("another call is probing");
            }
        } else if (s instanceof HalfOpen) {
            throw new CallNotPermitted("a probe is in flight");
        }

        // 2. run it, then move the state; each move is one atomic step
        try {
            T result = op.get();
            // success closes the breaker, unless another thread opened it while we were running
            state.updateAndGet(cur -> cur instanceof Open ? cur : new Closed(0));
            return result;
        } catch (RuntimeException e) {
            state.updateAndGet(cur -> switch (cur) {
                case HalfOpen h -> new Open(clock.instant().plus(openFor));                              // the probe failed
                case Closed(var n) when n + 1 >= failureThreshold -> new Open(clock.instant().plus(openFor));  // trip
                case Closed(var n) -> new Closed(n + 1);
                case Open o -> o;                                                                       // already open
            });
            throw e;                                                                                    // the caller sees the real error
        }
    }
}
