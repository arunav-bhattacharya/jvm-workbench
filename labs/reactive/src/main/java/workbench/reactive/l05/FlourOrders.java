package workbench.reactive.l05;

import reactor.core.publisher.Mono;

/**
 * Places flour orders with a flaky {@link Mill}, using a timer, retries with growing pauses, and a fallback.
 *
 * <p>{@link #place} must:
 * <ol>
 *   <li>give each attempt 500 ms; an attempt that takes longer counts as failed,</li>
 *   <li>retry {@link MillBusyException} and timeouts up to 3 times, waiting 100 ms,
 *       then 200 ms, then 400 ms (exponential backoff, no jitter, so the tests can check times),</li>
 *   <li>call the mill again for every attempt (the mill picks its answer when called),</li>
 *   <li>never retry an {@link OrderRefusedException}: pass it straight to the caller,</li>
 *   <li>when all retries are used up, emit {@code "PENDING:" + orderId} instead of failing,
 *       so someone can check with the mill later.</li>
 * </ol>
 */
public class FlourOrders {
    private final Mill mill;

    public FlourOrders(Mill mill) {
        this.mill = mill;
    }

    public Mono<String> place(String orderId) {
        throw new UnsupportedOperationException("TODO: timeout, retry with backoff, fallback");
    }
}
