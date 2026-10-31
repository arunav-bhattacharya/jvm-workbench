package workbench.vthreads.l01;

import java.time.Duration;

/**
 * Little's law: L = lambda x W.
 *
 * <p>L is how many requests are in the system at once, lambda is the arrival rate
 * (requests per second) and W is how long each request stays (its latency).
 * With thread-per-request, every request in flight holds one thread, so L is also
 * the number of threads you need.
 */
public final class LittlesLaw {
    private LittlesLaw() {}

    /** How many requests are in flight on average at {@code perSecond} requests per second. */
    public static double inFlight(double perSecond, Duration latency) {
        throw new UnsupportedOperationException("TODO: L = lambda x W (convert the latency to seconds)");
    }

    /** The most requests per second that {@code threads} threads can finish, when each request holds a thread for {@code latency}. */
    public static double maxThroughput(int threads, Duration latency) {
        throw new UnsupportedOperationException("TODO: lambda = L / W");
    }
}
